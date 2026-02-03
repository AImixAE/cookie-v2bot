import tomllib
from pathlib import Path


class Config:
    def __init__(self, path: str | Path = "config/config.toml"):
        self.path = Path(path)
        self.data = {}
        self.load_all()

    def load(self) -> dict:
        if not self.path.exists():
            return {}
        with self.path.open("rb") as f:
            return tomllib.load(f)

    def load_all(self):
        # load main config
        self.data = self.load()
        # try to load other files in config/ for modularity
        cfg_dir = self.path.parent
        for p in cfg_dir.glob("*.toml"):
            if p == self.path:
                continue
            try:
                with p.open("rb") as f:
                    self.data.update(tomllib.load(f))
            except Exception:
                continue

    def get(self, *keys, default=None):
        d = self.data
        for k in keys:
            if not isinstance(d, dict) or k not in d:
                return default
            d = d[k]
        return d
