import json
import os
from typing import Tuple

from .paths import get_config_file_path
from core.model import AppConfig, parse_config, create_default_config


def load_config() -> Tuple[AppConfig, bool]:
    """Load configuration from disk.

    Returns (config, created_new)
    - created_new=True when a new default file was created.
    """
    path = get_config_file_path()
    if not os.path.exists(path):
        cfg = create_default_config()
        save_config(cfg)
        return cfg, True

    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    cfg = parse_config(raw)
    return cfg, False


def save_config(config: AppConfig) -> None:
    path = get_config_file_path()
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(config.to_dict(), f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, path)


