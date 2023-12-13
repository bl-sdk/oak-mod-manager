import importlib
import sys
import traceback
import zipfile
from pathlib import Path

from unrealsdk import logging

try:
    import debugpy  # pyright: ignore[reportMissingImports]

    debugpy.listen(  # pyright: ignore[reportUnknownMemberType]
        ("localhost", 5678),
        in_process_debug_adapter=True,
    )
except ImportError:
    pass

_full_traceback = False


while not logging.is_console_ready():
    pass

mods_to_import: list[str] = []

for entry in Path(__file__).parent.iterdir():
    if entry.is_dir():
        if entry.name.startswith(".") or entry.name == "__pycache__":
            continue

        # A lot of people accidentally extract into double nested folders - they have a
        # `sdk_mods/MyCoolMod/MyCoolMod/__init__.py` instead of a `sdk_mods/MyCoolMod/__init__.py`
        # Usually this silently fails - we import `MyCoolMod` but there's nothing there
        # Detect this and give a proper error message
        if not (entry / "__init__.py").exists() and (entry / entry.name / "__init__.py").exists():
            logging.error(
                f"'{entry.name}' appears to be double nested, which may prevent it from being it"
                f" from being loaded. Move the inner folder up a level.",
            )
            # Since it's a silent error, may as well continue in case it's actually what you wanted

        # In the case we have a `sdk_mods/My Cool Mod v1.2`, python will try import `My Cool Mod v1`
        # first, and fail when it doesn't exist. Try detect this to throw a better error.
        # When this happens we're likely also double nested - `sdk_mods/My Cool Mod v1.2/MyCoolMod`
        # - but we can't detect that as easily, and the problem's the same anyway
        if "." in entry.name:
            logging.error(
                f"'{entry.name}' is not a valid python module - have you extracted the right"
                f" folder?",
            )
            continue

        mods_to_import.append(entry.name)

    elif entry.is_file():
        if entry.name.startswith("."):
            continue

        match entry.suffix.lower():
            # Since hotfix mods can be any text file, this won't be exhaustive, but match and warn
            # about what we can
            # OHL often uses .url files to download the latest version of a mod, so also match that
            case ".bl3hotfix" | ".wlhotfix" | ".url":
                logging.error(
                    f"'{entry.name}' appears to be a hotfix mod, not an SDK mod. Move it to your"
                    f" hotfix mods folder.",
                )
                continue

            case ".sdkmod":
                # Handled below the match
                pass

            case _:
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
