import importlib
import sys
import traceback
import zipfile
from pathlib import Path

from unrealsdk import logging

_full_traceback = False


while not logging.is_console_ready():
    pass

mods_to_import: list[str] = []

for entry in Path(__file__).parent.iterdir():
    if entry.is_dir():
        if entry.name.startswith(".") or entry.name == "__pycache__":
            continue

        if not (entry / "__init__.py").exists() and (entry / entry.name / "__init__.py").exists():
            logging.error(
                f"'{entry.name}' appears to be double nested, which may prevent it from being it"
                f" from being loaded. Move the inner folder up a level.",
            )

        mods_to_import.append(entry.name)

    elif entry.is_file():
        if entry.name.startswith(".") or entry.suffix != ".sdkmod":
            continue

        valid_zip: bool
        try:
            zip_iter = zipfile.Path(entry).iterdir()
            zip_entry = next(zip_iter)
            valid_zip = zip_entry.name == entry.stem and next(zip_iter, None) is None
        except (zipfile.BadZipFile, StopIteration):
            valid_zip = False

        if not valid_zip:
            logging.error(
                f"'{entry.name}' does not appear to be valid, and has been ignored.",
            )
            logging.dev_warning(
                "'.sdkmod' files must be a zip, and may only contain a single root folder, which"
                " must be named the same as the zip (excluding suffix).",
            )
            continue

        sys.path.append(str(entry))
        mods_to_import.append(entry.stem)

for name in mods_to_import:
    try:
        importlib.import_module(name)
    except Exception as ex:  # noqa: BLE001
        logging.error(f"Failed to import mod '{name}'")

        tb = traceback.extract_tb(ex.__traceback__)
        if not _full_traceback:
            tb = tb[-1:]

        logging.error("".join(traceback.format_exception_only(ex)))
        logging.error("".join(traceback.format_list(tb)))
