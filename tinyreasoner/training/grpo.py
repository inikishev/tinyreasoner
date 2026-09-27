import itertools
import random
import traceback
import warnings
from collections.abc import Callable, Sequence

import numpy as np
import torch
import tqdm
from accelerate import Accelerator
from langchain_core.tools import BaseTool
from torch.nn import functional as F

from .. import chat_api
from ..logger import DictLogger
from ..models import BaseModel, copy_state_dict
from ..optim import SPlus
from ..tokenizer import BaseTokenizer


class GRPOSample:
    def __init__(
        self,
        chat: Sequence[chat_api.AnyItem],
        score_fn: Callable[[Sequence[chat_api.AnyItem], float]],
        tools: Sequence[BaseTool] = (),
        data_device: torch.types.Device = "cuda",
    ):
        self.chat = chat
        self.score_fn = score_fn
        self.tools = list(tools)
        self.data_device = data_device

    def initialize(self, tokenizer: BaseTokenizer):
        tokens, mask = tokenizer.encode_chat(self.chat)

        self.tokens = torch.as_tensor(tokens, device=self.data_device)
        self.mask = torch.as_tensor(mask, device=self.data_device)

class GRPOTrainer:
    model: BaseModel

    def __init__(
        self,
        dataset: Sequence[GRPOSample],
        model: BaseModel,
        reference_model: BaseModel,
        optimizer: torch.optim.Optimizer,
        scheduler: torch.optim.lr_scheduler.LRScheduler,
        batch_size: int,
        group_size: int,
        temperature: float,
        test_batch_size: int,
        test_every: int,
        max_tokens: int = 8192,
        scale_loss: bool = False,
        mixed_precision = None,
        frac_test: float = 0.1,
        device: torch.types.Device = "cuda",
        data_device: torch.types.Device = "cuda"
    ):
        self.batch_size = batch_size
        self.group_size = group_size
        self.temperature = temperature
        self.test_batch_size = test_batch_size
        self.test_every = test_every
        self.scale_loss = scale_loss
        self.device = device
        self.max_tokens = max_tokens
        self.data_device = data_device

        # tokenize and split the dataset
        for item in tqdm.tqdm(dataset):
            item.initialize(model.tokenizer)

        shuffled = random.sample(dataset, k=len(dataset))
        n_test = int(len(shuffled) * frac_test)
        data_train = shuffled[:-n_test]
        data_test = shuffled[-n_test:]

        # accelerete
        self.accelerator = Accelerator(mixed_precision=mixed_precision)
        self.model, self.reference_model, self.optimizer, self.scheduler, self.data_train, self.data_test = (
            self.accelerator.prepare(model, reference_model, optimizer, scheduler, data_train, data_test)
        )

        # metrics
        self.logger = DictLogger()
        self.current_step = 0
        self.best_state_dict = copy_state_dict(self.model.state_dict(), 'cpu')
        self.best_test_loss = float("inf")

        self.last_train_loss = None
        self.last_test_loss = None

    def log(self, metric, value, lazy=False):
        if lazy: self.logger.lazy_log(self.current_step, metric, value)
        else: self.logger.log(self.current_step, metric, value)

    def get_loss(self, sample: GRPOSample):
        completions = [
            self.model.predict(sample.tokens, max_tokens=self.max_tokens, temperature=self.temperature)
            for _ in range(self.group_size)
        ]

        decoded = [self.model.tokenizer.decode(c) for c in completions]

