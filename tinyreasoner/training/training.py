import itertools
import random
import traceback
import warnings
from collections.abc import Sequence

import numpy as np
import torch
import tqdm
from accelerate import Accelerator
from torch.nn import functional as F
from torchalgos import SPlus

from .. import chat_api
from ..logger import DictLogger
from ..models import BaseModel, copy_state_dict


class Pretrainer:
    model: BaseModel

    def __init__(
        self,
        dataset: Sequence[str],
        model: BaseModel,
        sequence_length: int,
        optimizer: torch.optim.Optimizer,
        scheduler: torch.optim.lr_scheduler.LRScheduler,
        batch_size: int,
        test_batch_size: int,
        test_every: int,
        test_steps: int,
        mixed_precision = None,
        frac_test: float = 0.1,
        device: torch.types.Device = "cuda",
        data_device: torch.types.Device = "cpu"
    ):
        shuffled = random.sample(dataset, k=len(dataset))
        n_test = int(len(shuffled) * frac_test)
        train_part = shuffled[:-n_test]
        test_part = shuffled[-n_test:]

        data_train = [torch.tensor(model.tokenizer.encode_text(item), device=data_device) for item in tqdm.tqdm(train_part)]
        data_test = [torch.tensor(model.tokenizer.encode_text(item), device=data_device) for item in tqdm.tqdm(test_part)]

        self.accelerator = Accelerator(mixed_precision=mixed_precision)
        self.model, self.optimizer, self.scheduler, self.data_train, self.data_test = (
            self.accelerator.prepare(model, optimizer, scheduler, data_train, data_test)
        )

        self.lengths_train = [max(len(s), sequence_length) for s in data_train]
        self.lengths_test = [max(len(s), sequence_length) for s in data_test]

        self.sequence_length = sequence_length
        self.batch_size = batch_size
        self.test_batch_size = test_batch_size
        self.test_every = test_every
        self.test_steps = test_steps
        self.device = device
        self.mixed_precision = mixed_precision

        self.logger = DictLogger()
        self.current_step = 0
        self.best_state_dict = copy_state_dict(self.model.state_dict(), 'cpu')
        self.best_test_loss = float("inf")

        self.last_train_loss = None
        self.last_test_loss = None

    def log(self, metric, value, lazy=False):
        if lazy: self.logger.lazy_log(self.current_step, metric, value)
        else: self.logger.log(self.current_step, metric, value)

    def process_sample(self, sample: torch.Tensor):
        if len(sample) <= self.sequence_length:
            padding = torch.full(
                size = (self.sequence_length - len(sample),),
                fill_value = self.model.tokenizer.pad_idx,
                device = sample.device,
                dtype = sample.dtype,
            )
            return torch.cat([sample, padding])

        start = random.randrange(0, len(sample)-self.sequence_length)
        end = start + self.sequence_length
        return sample[start : end]

    def get_loss(self, train: bool):
        data = self.data_train if train else self.data_test
        lengths = self.lengths_train if train else self.lengths_test

        samples = random.choices(data, k=self.batch_size, weights=lengths)
        samples = torch.stack([self.process_sample(s) for s in samples], 0).to(self.device, non_blocking=True)
        inputs = samples[:, :-1]
        targets = samples[:, 1:]

        preds, _ = self.model(inputs) # (B, L, vocab_size)

        losses = F.cross_entropy(preds.movedim(2, 1), targets, ignore_index=self.model.tokenizer.pad_idx, reduction='none') # (B, L)
        return losses[losses != 0].mean() # don't use padding with 0 loss in mean

    @torch.inference_mode()
    def preview_generation(self):
        sample = random.choices(self.data_test, weights=self.lengths_test, k=1)[0]
        sample = self.process_sample(sample)
        print(f'input:\n{self.model.tokenizer.decode(sample)!r}')
        print(f'output:\n{self.model.tokenizer.decode(self.model.predict(sample, 1024).output_tokens)!r}')

    @torch.inference_mode()
    def _test_epoch(self, p_ema: bool):

        test_losses = []
        for _ in range(self.test_steps):
            test_losses.append(self.get_loss(train=False).detach())

        test_loss = float(np.mean([t.cpu() for t in test_losses]))

        if test_loss < self.best_test_loss:
            self.best_state_dict = copy_state_dict(self.model.state_dict(), 'cpu')
            self.best_test_loss = test_loss

        self.log("test loss ema" if p_ema else "test loss", test_loss)
        self.last_test_loss = test_loss

        self.preview_generation()

        return test_loss

    def test_epoch(self):
        self.model.eval()

        # test with train params and eval params
        self.optimizer.train()
        self._test_epoch(p_ema=False)

        self.optimizer.eval()
        self._test_epoch(p_ema=True)

        self.optimizer.train()
        self.model.train()
        self.logger.lazy_finalize()

    def train_step(self, pbar):

        # test epoch every TEST_EVERY
        if self.current_step % self.test_every == 0:
            self.test_epoch()

        # train step
        def closure(backward=True):
            loss = self.get_loss(train=True)
            if backward:
                self.optimizer.zero_grad()
                self.accelerator.backward(loss)
            self.last_train_loss = loss.detach()
            return loss

        self.optimizer.step(closure) # type:ignore
        assert self.last_train_loss is not None
        self.scheduler.step()
        self.log("train loss", self.last_train_loss, lazy=True)
        self.current_step += 1

        pbar.update(1)
        pbar.set_postfix_str(f"train_loss={self.last_train_loss:.5g}, test_loss={self.last_test_loss:.5g}, best={self.best_test_loss:.5g}")


    def run(self, n_steps:int):
        pbar = tqdm.tqdm(total=n_steps)
        try:
            while self.current_step < n_steps:
                    self.train_step(pbar)

        except KeyboardInterrupt:
            self.test_epoch()

        except Exception as e:
            warnings.warn(''.join(traceback.format_exception(e)))

        finally:
            self.logger.lazy_finalize()

        return self

class SFTTrainer:
    model: BaseModel

    def __init__(
        self,
        dataset: Sequence[Sequence[chat_api.AnyItem]],
        model: BaseModel,
        optimizer: torch.optim.Optimizer,
        scheduler: torch.optim.lr_scheduler.LRScheduler,
        batch_size: int,
        test_batch_size: int,
        test_every: int,
        scale_loss: bool = False,
        mixed_precision = None,
        frac_test: float = 0.1,
        device: torch.types.Device = "cuda",
        data_device: torch.types.Device = "cpu"
    ):
        dataset = chat_api.deduplicate(dataset)
        shuffled = random.sample(dataset, k=len(dataset))
        n_test = int(len(shuffled) * frac_test)

        def load_sample(s):
            tokens, mask = model.tokenizer.encode_chat(s)
            return (torch.as_tensor(tokens, device=data_device), torch.as_tensor(mask, device=data_device))

        data_train = [load_sample(s) for s in tqdm.tqdm(shuffled[:-n_test])]
        data_test = [load_sample(s) for s in tqdm.tqdm(shuffled[-n_test:])]

        self.accelerator = Accelerator(mixed_precision=mixed_precision)
        self.model, self.optimizer, self.scheduler, self.data_train, self.data_test = (
            self.accelerator.prepare(model, optimizer, scheduler, data_train, data_test)
        )

        self.batch_size = batch_size
        self.test_batch_size = test_batch_size
        self.test_every = test_every
        self.device = device
        self.mixed_precision = mixed_precision
        self.scale_loss = scale_loss

        self.logger = DictLogger()
        self.current_step = 0
        self.best_state_dict = copy_state_dict(self.model.state_dict(), 'cpu')
        self.best_test_loss = float("inf")

        self.last_train_loss = None
        self.last_test_loss = None

    def log(self, metric, value, lazy=False):
        if lazy: self.logger.lazy_log(self.current_step, metric, value)
        else: self.logger.log(self.current_step, metric, value)

    def get_loss(self, batch: Sequence[tuple[torch.Tensor, torch.Tensor]]):
        pad_idx = self.model.tokenizer.pad_idx
        tokens, masks = list(zip(*batch))
        tokens_padded = torch.nn.utils.rnn.pad_sequence(list(tokens), padding_value=pad_idx, batch_first=True).to(self.device, non_blocking=True)
        masks_padded = torch.nn.utils.rnn.pad_sequence(list(masks), padding_value=0, batch_first=True).to(self.device, non_blocking=True)[:, 1:]

        inputs = tokens_padded[:, :-1]
        targets = tokens_padded[:, 1:]

        preds, _ = self.model(inputs) # (B, L, vocab_size)
        losses = F.cross_entropy(preds.movedim(2, 1), targets, ignore_index=pad_idx, reduction='none') # (B, L)
        assert losses.shape == masks_padded.shape, f"{losses.shape = }, {masks_padded.shape = }"

        if self.scale_loss:
            with torch.no_grad():
                scale = 1 - masks_padded.float().mean(1, keepdim=True)
            losses = losses * scale

        losses = losses[masks_padded.bool()]
        return losses[losses != 0].mean() # don't use padding with 0 loss in mean

    @torch.inference_mode()
    def preview_generation(self):
        sample, mask = random.choice(self.data_test)
        start = (mask == 1).int().argmax().item()
        if start <= 1:
            start = random.randint(int(start), len(sample)-2)
            if start + 1 > len(sample): start = 0

        sample_before = sample[:start]
        print(f'input:\n{self.model.tokenizer.decode(sample_before)!r}')
        print(f'output:\n{self.model.tokenizer.decode(self.model.predict(sample_before, 1024).output_tokens)!r}')

    @torch.inference_mode()
    def _test_epoch(self, p_ema: bool):
        test_losses = []

        for batch in itertools.batched(self.data_test, self.test_batch_size):
            test_losses.append(self.get_loss(batch).detach())

        test_loss = float(np.mean([t.cpu() for t in test_losses]))

        if test_loss < self.best_test_loss:
            self.best_state_dict = copy_state_dict(self.model.state_dict(), 'cpu')
            self.best_test_loss = test_loss

        self.log("test loss ema" if p_ema else "test loss", test_loss)
        self.last_test_loss = test_loss
        self.preview_generation()

        return test_loss

    def test_epoch(self):
        self.model.eval()

        # test with train params and eval params
        self.optimizer.train()
        self._test_epoch(p_ema=False)

        self.optimizer.eval()
        self._test_epoch(p_ema=True)

        self.optimizer.train()
        self.model.train()
        self.logger.lazy_finalize()

    def train_epoch(self, pbar, n_steps: int):
        samples = random.sample(self.data_train, k=len(self.data_train))
        for batch in itertools.batched(samples, self.batch_size):

            # test epoch every TEST_EVERY
            if self.current_step % self.test_every == 0:
                self.test_epoch()

            if self.current_step >= n_steps:
                break

            # train step
            def closure(backward=True):
                loss = self.get_loss(batch)
                if backward:
                    self.optimizer.zero_grad()
                    self.accelerator.backward(loss)
                self.last_train_loss = loss.detach()
                return loss

            self.optimizer.step(closure) # type:ignore
            assert self.last_train_loss is not None
            self.scheduler.step()
            self.log("train loss", self.last_train_loss, lazy=True)
            self.current_step += 1

            pbar.update(1)
            pbar.set_postfix_str(f"train_loss={self.last_train_loss:.5g}, test_loss={self.last_test_loss:.5g}, best={self.best_test_loss:.5g}")

        self.logger.lazy_finalize()

    def run(self, n_steps: int):
        pbar = tqdm.tqdm(total=n_steps)
        try:
            while self.current_step < n_steps:
                self.train_epoch(pbar, n_steps=n_steps)

        except KeyboardInterrupt:
            self.test_epoch()

        except Exception as e:
            warnings.warn(''.join(traceback.format_exception(e)))

        finally:
            self.logger.lazy_finalize()

        return self

