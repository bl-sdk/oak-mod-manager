import importlib
import traceback
from pathlib import Path

from unrealsdk import logging

_full_traceback = False


while not logging.is_console_ready():
    pass

for folder in Path(__file__).parent.iterdir():
    if not folder.is_dir():
        continue

    if folder.name.startswith(".") or folder.name == "__pycache__":
        continue

    if not (folder / "__init__.py").exists() and (folder / folder.name / "__init__.py").exists():
        logging.error(
            f"'{folder.name}' appears to be double nested, which may prevent it from being it from"
            f" being loaded. Move the inner folder up a level.",
        )

    try:
        importlib.import_module(folder.name)
    except Exception as ex:  # noqa: BLE001
        logging.error(f"Failed to import mod '{folder.name}'")

        tb = traceback.extract_tb(ex.__traceback__)
        if not _full_traceback:
            tb = tb[-1:]

        logging.error("".join(traceback.format_exception_only(ex)))
        logging.error("".join(traceback.format_list(tb)))
