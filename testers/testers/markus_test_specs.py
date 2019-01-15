import json
from collections.abc import Mapping

class MarkusTestSpecs(Mapping):
    def __init__(self, *args, **kwargs):
        self._specs = dict(*args, **kwargs)

    @classmethod
    def from_json(cls, json_str):
        return cls(json.loads(json_str))

    def __getitem__(self, key):
        return self._specs[key]

    def __iter__(self):
        return iter(self._specs)

    def __len__(self):
        return len(self._specs)
