import os
def read_file(path):
    with open(path, "r", encoding='utf-8-sig') as f:
        return f.read()

def gather_files(root, extensions: list[str]) -> list[str]:
    samples = []
    for r, d, f in os.walk(root):
        for file in f:
            if file.lower().endswith(tuple(e.lower() for e in extensions)):
                try:
                    samples.append(read_file(os.path.join(r, file)))
                except Exception as e:
                    print(e)
    return samples