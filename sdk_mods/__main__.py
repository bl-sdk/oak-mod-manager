import importlib
import traceback
from pathlib import Path

_full_traceback = False

for folder in Path(__file__).parent.iterdir():
    if not folder.is_dir():
        continue

    if folder.name.startswith(".") or folder.name == "__pycache__":
        continue

    try:
        importlib.import_module(folder.name)
    except Exception:  # noqa: BLE001, PERF203
        print(f"Failed to import mod: {folder.name}")
        traceback.print_exc(limit=None if _full_traceback else 1)
