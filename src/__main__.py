# This file is part of the BL3/WL Oak Mod Manager.
# <https://github.com/bl-sdk/oak-mod-manager>
#
# The Oak Mod Manager is free software: you can redistribute it and/or modify it under the terms of
# the GNU Lesser General Public License Version 3 as published by the Free Software Foundation.
#
# The Oak Mod Manager is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with the Oak Mod Manager.
# If not, see <https://www.gnu.org/licenses/>.

from __future__ import annotations

import contextlib
import importlib
import json
import re
import sys
import traceback
import warnings
import zipfile
from dataclasses import dataclass, field
from functools import cache, wraps
from pathlib import Path
from typing import TYPE_CHECKING, TextIO

# Note we try to import as few third party modules as possible before the console is ready, in case
# any of them cause errors we'd like to have logged
# Trusting that we can keep all the above standard library modules without issue
import unrealsdk
from unrealsdk import logging

if TYPE_CHECKING:
    from collections.abc import Collection, Sequence

# If true, displays the full traceback when a mod fails to import, rather than the shortened one
FULL_TRACEBACKS: bool = False
# If true, makes debugpy wait for a client before continuing - useful for debugging errors which
# happen at import time
WAIT_FOR_CLIENT: bool = False


@dataclass
class ModInfo:
    module: str
    location: Path
    duplicates: list[ModInfo] = field(default_factory=list["ModInfo"])


def init_debugpy() -> None:
    """Tries to import and setup debugpy. Does nothing if unable to."""
    try:
        import debugpy  # pyright: ignore[reportMissingImports]  # noqa: T100

        debugpy.listen(  # pyright: ignore[reportUnknownMemberType]  # noqa: T100
            ("localhost", 5678),
            in_process_debug_adapter=True,
        )

        if WAIT_FOR_CLIENT:
            debugpy.wait_for_client()  # pyright: ignore[reportUnknownMemberType]  # noqa: T100
            debugpy.breakpoint()  # pyright: ignore[reportUnknownMemberType]  # noqa: T100

        if not unrealsdk.config.get("pyunrealsdk", {}).get("debugpy", False):
            logging.dev_warning(
                "Was able to start debugpy, but the `pyunrealsdk.debugpy` config variable is not"
                " set to true. This may prevent breakpoints from working properly.",
            )

        # Make WrappedArrays resolve the same as lists
        from _pydevd_bundle.pydevd_resolver import (  # pyright: ignore[reportMissingImports]
            tupleResolver,  # pyright: ignore[reportUnknownVariableType]
        )
        from _pydevd_bundle.pydevd_xml import (  # pyright: ignore[reportMissingImports]
            _TYPE_RESOLVE_HANDLER,  # pyright: ignore[reportUnknownVariableType]
        )
        from unrealsdk.unreal import WrappedArray

        if not _TYPE_RESOLVE_HANDLER._initialized:  # pyright: ignore[reportUnknownMemberType]
            _TYPE_RESOLVE_HANDLER._initialize()  # pyright: ignore[reportUnknownMemberType]
        _TYPE_RESOLVE_HANDLER._default_type_map.append(  # pyright: ignore[reportUnknownMemberType]
            (WrappedArray, tupleResolver),
        )

    except (ImportError, AttributeError):
        pass


def get_all_mod_folders() -> Sequence[Path]:
    """
    Gets all mod folders to try import from, including extra folders defined via config file.

    Returns:
        A sequence of mod folder paths.
    """

    extra_folders = []
    with contextlib.suppress(json.JSONDecodeError, TypeError):
        extra_folders = [
            Path(x) for x in unrealsdk.config.get("mod_manager", {}).get("extra_folders", [])
        ]

    return [Path(__file__).parent, *extra_folders]


@cache
def validate_folder_in_mods_folder(folder: Path) -> bool:
    """
    Checks if a folder inside the mods folder is actually a mod we should try import.

    Args:
        folder: The folder to analyse.
    Returns:
        True if the file is a valid module to try import.
    """
    if folder.name == "__pycache__":
        return False

    # A lot of people accidentally extract into double nested folders - they have a
    # `sdk_mods/MyCoolMod/MyCoolMod/__init__.py` instead of a `sdk_mods/MyCoolMod/__init__.py`
    # Usually this silently fails - we import `MyCoolMod` but there's nothing there
    # Detect this and give a proper error message
    if not (folder / "__init__.py").exists() and (folder / folder.name / "__init__.py").exists():
        logging.error(
            f"'{folder.name}' appears to be double nested, which may prevent it from being it from"
            f" being loaded. Move the inner folder up a level.",
        )
        # Since it's a silent error, may as well continue in case it's actually what you wanted

    # In the case we have a `sdk_mods/My Cool Mod v1.2`, python will try import `My Cool Mod v1`
    # first, and fail when it doesn't exist. Try detect this to throw a better error.
    # When this happens we're likely also double nested - `sdk_mods/My Cool Mod v1.2/MyCoolMod`
    # - but we can't detect that as easily, and the problem's the same anyway
    if "." in folder.name:
        logging.error(
            f"'{folder.name}' is not a valid python module - have you extracted the right folder?",
        )
        return False

    return True


# Catch when someone downloaded a mod a few times and ended up with a "MyMod (3).sdkmod"
RE_NUMBERED_DUPLICATE = re.compile(r"^(.+?) \(\d+\)\.sdkmod$", flags=re.I)


@cache
def validate_file_in_mods_folder(file: Path) -> bool:
    """
    Checks if a folder inside the mods folder is actually a mod we should try import.

    Sets up sys.path as required.

    Args:
        file: The file to analyse.
    Returns:
        True if the file is a valid .sdkmod to try import.
    """
    match file.suffix.lower():
        # Since hotfix mods can be any text file, this won't be exhaustive, but match and warn
        # about what we can
        # OHL often uses .url files to download the latest version of a mod, so also match that
        case ".bl3hotfix" | ".wlhotfix" | ".url":
            logging.error(
                f"'{file.name}' appears to be a hotfix mod, not an SDK mod. Move it to your hotfix"
                f" mods folder.",
            )
            return False

        case ".sdkmod":
            # Handled below
            pass

        case _:
            return False

    valid_zip = False
    name_suggestion: str | None = None
    with contextlib.suppress(zipfile.BadZipFile, StopIteration, OSError):
        zip_iter = zipfile.Path(file).iterdir()
        zip_entry = next(zip_iter)
        valid_zip = zip_entry.name == file.stem and next(zip_iter, None) is None

        if (
            not valid_zip
            and (match := RE_NUMBERED_DUPLICATE.match(file.name))
            and (base_name := match.group(1)) == zip_entry.name
        ):
            name_suggestion = base_name + ".sdkmod"

    if not valid_zip:
        error_msg = f"'{file.name}' does not appear to be valid, and has been ignored."
        if name_suggestion is not None:
            error_msg += f" Is it supposed to be called '{name_suggestion}'?"
        logging.error(error_msg)
        logging.dev_warning(
            "'.sdkmod' files must be a zip, and may only contain a single root folder, which must"
            " be named the same as the zip (excluding suffix).",
        )
        return False

    str_path = str(file)
    if str_path not in sys.path:
        sys.path.append(str_path)

    return True


def find_mods_to_import(all_mod_folders: Sequence[Path]) -> Collection[ModInfo]:
    """
    Given the sequence of mod folders, find all individual mod modules within them to try import.

    Any '.sdkmod's found are added to `sys.path` as part of this step.

    Args:
        all_mod_folders: A sequence of all mod folders to import from, in the order they are listed
                         in `sys.path`.
    Returns:
        A collection of the module names to import.
    """
    mods_to_import: dict[str, ModInfo] = {}

    for folder in all_mod_folders:
        if not folder.exists():
            continue

        for entry in folder.iterdir():
            if entry.name.startswith("."):
                continue

            mod_info: ModInfo
            if entry.is_dir() and validate_folder_in_mods_folder(entry):
                mod_info = ModInfo(entry.name, entry)

            elif entry.is_file() and validate_file_in_mods_folder(entry):
                mod_info = ModInfo(entry.stem, entry)
            else:
                continue

            if mod_info.module in mods_to_import:
                mods_to_import[mod_info.module].duplicates.append(mod_info)
            else:
                mods_to_import[mod_info.module] = mod_info

    return mods_to_import.values()


def import_mods(mods_to_import: Collection[ModInfo]) -> None:
    """
    Tries to import a list of mods.

    Args:
        mods_to_import: The list of mods to import.
    """
    for mod in mods_to_import:
        try:
            importlib.import_module(mod.module)

        except Exception as ex:  # noqa: BLE001
            logging.error(f"Failed to import mod '{mod.module}'")

            tb = traceback.extract_tb(ex.__traceback__)
            if not FULL_TRACEBACKS:
                tb = tb[-1:]

            logging.error("".join(traceback.format_exception_only(ex)))
            logging.error("".join(traceback.format_list(tb)))


def hookup_warnings() -> None:
    """Hooks up the Python warnings system to the dev warning log type."""

    original_show_warning = warnings.showwarning
    dev_warn_logger = logging.Logger(logging.Level.DEV_WARNING)

    @wraps(warnings.showwarning)
    def showwarning(
        message: Warning | str,
        category: type[Warning],
        filename: str,
        lineno: int,
        file: TextIO | None = None,
        line: str | None = None,
    ) -> None:
        if file is None:
            # Typeshed has this as a TextIO, but the implementation only actually uses `.write`
            file = dev_warn_logger  # type: ignore
        original_show_warning(message, category, filename, lineno, file, line)

    warnings.showwarning = showwarning
    warnings.resetwarnings()  # Reset filters, show all warnings


def check_proton_bugs() -> None:
    """Tries to detect and warn about various known proton issues."""

    """
    The exception bug
    -----------------
    Usually pybind detects exceptions using a catch all, which eventually calls through to
    `std::current_exception` to get the exact exception, and then runs a bunch of translators on it
    to convert it to a Python exception. When running under a bad Proton version, this call fails,
    and returns an empty exception pointer, so pybind is unable to translate it.

    This means Python throws a:
    ```
    SystemError: <built-in method __getattr__ of PyCapsule object at 0x00000000069AC780> returned NULL without setting an exception
    ```
    This is primarily a problem for `StopIteration`.
    """  # noqa: E501
    cls = unrealsdk.find_class("Object")
    try:
        # Cause an attribute error
        _ = cls._check_for_proton_null_exception_bug
    except AttributeError:
        # Working properly
        pass
    except SystemError:
        # Have the bug
        logging.error(
            "===============================================================================",
        )
        traceback.print_exc()
        logging.error(
            "\n"
            "Some particular Proton versions cause this, try switch to another one.\n"
            "Alternatively, the nightly release has builds from other compilers, which may\n"
            "also prevent it.\n"
            "\n"
            "Will attempt to import mods, but they'll likely break with a similar error.\n"
            "===============================================================================",
        )


# Don't really want to put a `__name__` check here, since it's currently just `builtins`, and that
# seems a bit unstable, like something that pybind might eventually change

# Do as little as possible before console's ready

# Add all mod folders to `sys.path` first
mod_folders = get_all_mod_folders()
for folder in mod_folders:
    sys.path.append(str(folder.resolve()))

init_debugpy()

while not logging.is_console_ready():
    pass

# Now that the console's ready, hook up the warnings system, and show some other warnings users may
# be interested in
hookup_warnings()

check_proton_bugs()
for folder in mod_folders:
    if not folder.exists() or not folder.is_dir():
        logging.dev_warning(f"Extra mod folder does not exist: {folder}")

mods_to_import = find_mods_to_import(mod_folders)

# Warn about duplicate mods
for mod in mods_to_import:
    if not mod.duplicates:
        continue
    logging.warning(f"Found multiple versions of mod '{mod.module}'. In order of priority:")
    # All folders always have higher priority than any files
    folders = (info.location for info in (mod, *mod.duplicates) if info.location.is_dir())
    files = (info.location for info in (mod, *mod.duplicates) if info.location.is_file())
    for location in (*folders, *files):
        logging.warning(str(location.resolve()))

# Import any mod manager modules which have specific initialization order requirements.
# Most modules are fine to get imported as a mod/by another mod, but we need to do a few manually.
# Prefer to import these after console is ready so we can show errors
import keybinds  # noqa: F401, E402  # pyright: ignore[reportUnusedImport]
from mods_base.mod_list import register_base_mod  # noqa: E402

import_mods(mods_to_import)

# After importing everything, register the base mod
register_base_mod()
