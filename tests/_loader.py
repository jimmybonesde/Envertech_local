"""Load integration modules directly so Home Assistant is not required."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

_PKG = Path(__file__).resolve().parents[1] / "custom_components" / "envertech_local"


def load(name: str) -> ModuleType:
    """Load ``custom_components/envertech_local/<name>.py`` standalone."""
    module_name = f"envertech_local_standalone_{name}"
    if module_name in sys.modules:
        return sys.modules[module_name]
    spec = importlib.util.spec_from_file_location(module_name, _PKG / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module
