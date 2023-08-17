import importlib
import traceback
from pathlib import Path

import unrealsdk

_full_traceback = False


while not unrealsdk.logging.is_console_ready():
    pass

for folder in Path(__file__).parent.iterdir():
    if not folder.is_dir():
        continue

    if folder.name.startswith(".") or folder.name == "__pycache__":
        continue

    try:
        importlib.import_module(folder.name)
    except Exception as ex:  # noqa: BLE001, PERF203
        print(f"Failed to import mod: {folder.name}")

        tb = traceback.extract_tb(ex.__traceback__)
        if not _full_traceback:
            tb = tb[-1:]
        print("".join(traceback.format_list(tb)))
