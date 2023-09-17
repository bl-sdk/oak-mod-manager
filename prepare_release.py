#!/usr/bin/env python3
import re
import subprocess
import textwrap
from functools import cache
from os import path
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

LIST_PRESETS_RE = re.compile('  "(.+)"')


@cache
def cmake_get_presets() -> list[str]:
    """
    Gets the presets which may be used.

    Returns:
        A list of presets.
    """
    proc = subprocess.run(
        ["cmake", "--list-presets"],
        check=True,
        stdout=subprocess.PIPE,
        encoding="utf8",
    )
    return LIST_PRESETS_RE.findall(proc.stdout)


def cmake_install(build_dir: Path) -> None:
    """
    Builds and installs a cmake configuration.

    Args:
        build_dir: The preset's build dir.
    """
    subprocess.check_call(["cmake", "--build", build_dir, "--target", "install"])


ZIP_MODS_FOLDER = Path("sdk_mods")
ZIP_STUBS_FOLDER = ZIP_MODS_FOLDER / ".stubs"
ZIP_EXECUTABLE_FOLDER = Path("OakGame") / "Binaries" / "Win64"
ZIP_PLUGINS_FOLDER = ZIP_EXECUTABLE_FOLDER / "Plugins"


def _zip_init_script(zip_file: ZipFile, init_script: Path) -> None:
    output_init_script = ZIP_MODS_FOLDER / init_script.name
    zip_file.write(init_script, output_init_script)
    zip_file.writestr(
        str(ZIP_PLUGINS_FOLDER / "unrealsdk.env"),
        textwrap.dedent(
            # Path.relative_to doesn't work when where's no common base, need to use os.path
            # While the file goes in the plugins folder, this path is relative to *the executable*
            f"""
            PYUNREALSDK_INIT_SCRIPT={path.relpath(output_init_script, ZIP_EXECUTABLE_FOLDER)}
            """,
        )[1:-1],
    )


def _zip_mod_folders(zip_file: ZipFile, mod_folders: list[Path], debug: bool) -> None:
    for mod in mod_folders:
        for file in mod.glob("**/*"):
            if not file.is_file():
                continue
            if file.parent.name == "__pycache__":
                continue

            if file.suffix == ".cpp":
                continue
            if file.suffix == ".pyd" and file.stem.endswith("_d") != debug:
                continue

            zip_file.write(
                file,
                ZIP_MODS_FOLDER / mod.name / file.relative_to(mod),
            )


def _zip_stubs(zip_file: ZipFile, stubs_dir: Path) -> None:
    for file in stubs_dir.glob("**/*"):
        if not file.is_file():
            continue
        if file.suffix != ".pyi":
            continue

        zip_file.write(
            file,
            ZIP_STUBS_FOLDER / file.relative_to(stubs_dir),
        )


def _zip_dlls(zip_file: ZipFile, install_dir: Path) -> None:
    for file in install_dir.glob("**/*"):
        if not file.is_file():
            continue

        zip_file.write(
            file,
            ZIP_PLUGINS_FOLDER / file.relative_to(install_dir),
        )

    py_stem = next(install_dir.glob("python*.zip")).stem
    zip_file.writestr(
        str(ZIP_PLUGINS_FOLDER / (py_stem + "._pth")),
        textwrap.dedent(
            f"""
            {path.relpath(ZIP_MODS_FOLDER, ZIP_PLUGINS_FOLDER)}
            {py_stem}.zip
            DLLs
            """,
        )[1:-1],
    )


def zip_release(
    output: Path,
    init_script: Path,
    mod_folders: list[Path],
    debug: bool,
    stubs_dir: Path,
    install_dir: Path,
) -> None:
    """
    Creates a release zip.

    Args:
        output: The location of the zip to create.
        init_script: The pyunrealsdk init script to use.
        mod_folders: A list of mod folders to include in the zip.
        debug: True if this is a debug release.
        stubs_dir: The stubs dir to include.
        install_dir: The CMake install dir to copy the dlls from.
    """

    with ZipFile(output, "w", ZIP_DEFLATED, compresslevel=9) as zip_file:
        _zip_init_script(zip_file, init_script)
        _zip_mod_folders(zip_file, mod_folders, debug)
        _zip_stubs(zip_file, stubs_dir)
        _zip_dlls(zip_file, install_dir)


if __name__ == "__main__":
    from argparse import ArgumentParser, BooleanOptionalAction

    BASE_MOD = Path("src") / "mods_base"
    BL3_MENU = Path("src") / "bl3_mod_menu"
    WL_MENU = Path("src") / "console_mod_menu"

    INIT_SCRIPT = Path("src") / "__main__.py"

    BUILD_DIR_BASE = Path("out") / "build"
    INSTALL_DIR_BASE = Path("out") / "install"

    STUBS_DIR = Path("libs") / "pyunrealsdk" / "stubs"

    parser = ArgumentParser(description="Prepares a release zip.")
    parser.add_argument(
        "preset",
        choices=cmake_get_presets(),
        help="The CMake preset to use.",
    )
    parser.add_argument(
        "--skip-install",
        action="store_true",
        help="If specified, skips performing a CMake install. The directory must still exist.",
    )
    parser.add_argument(
        "--bl3",
        action=BooleanOptionalAction,
        default=True,
        help="Create a BL3 release zip. Defaults to on.",
    )
    parser.add_argument(
        "--wl",
        action=BooleanOptionalAction,
        default=True,
        help="Create a WL release zip. Defaults to on.",
    )
    parser.add_argument(
        "--unified",
        action=BooleanOptionalAction,
        default=False,
        help="Create a unified release zip. Defaults to off.",
    )
    args = parser.parse_args()

    if not args.skip_install:
        cmake_install(BUILD_DIR_BASE / args.preset)

    install_dir = INSTALL_DIR_BASE / str(args.preset)
    assert install_dir.exists() and install_dir.is_dir(), "install dir doesn't exist"

    for prefix, arg, mods in (
        ("bl3", args.bl3, [BASE_MOD, BL3_MENU]),
        ("wl", args.wl, [BASE_MOD, WL_MENU]),
        ("unified", args.unified, [BASE_MOD, BL3_MENU, WL_MENU]),
    ):
        if not arg:
            continue
        name = f"{prefix}-sdk-{args.preset}.zip"
        print(f"Zipping {name} ...")
        zip_release(
            Path(name),
            INIT_SCRIPT,
            mods,
            "debug" in args.preset,
            STUBS_DIR,
            install_dir,
        )
