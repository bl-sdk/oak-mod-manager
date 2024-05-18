# Oak Mod Manager
[![Support Discord](https://img.shields.io/static/v1?label=&message=Support%20Discord&logo=discord&color=424)](https://discord.gg/bXeqV8Ef9R)
[![Developer Discord](https://img.shields.io/static/v1?label=&message=Developer%20Discord&logo=discord&color=222)](https://discord.gg/VJXtHvh)

[For installation instructions / the mod database, see the project site.](https://bl-sdk.github.io/oak-mod-db/)

<br>

The [pyunrealsdk](https://github.com/bl-sdk/pyunrealsdk) mod manager for:
- Borderlands 3
- Wonderlands

# Development
When developing, it's recommended to point pyunrealsdk directly at this repo. To do this:

1. Navigate to the plugins folder - `<game>\OakGame\Binaries\Win64\Plugins\`

2. Edit `python3XX._pth`, replacing `..\..\..\..\sdk_mods` with `<path to repo>\src`. If you have a
   debug build, also edit `python3XX_d._pth`.

3. Edit `unrealsdk.env`, setting `PYUNREALSDK_INIT_SCRIPT=<path to repo>\src\__main__.py`.

4. (Optional) Edit `unrealsdk.env`, adding/updating
   `OAK_MOD_MANAGER_EXTRA_FOLDERS=["C:\\path\\to\\new\\mod\\folder"]`, pointing at your old
   `sdk_mods` folder. This is a json list of paths to folders to load, though note it must stay on
   one line.

5. (Optional) Copy/symlink your original settings folder into `src\settings` - settings are only
   loaded from the base mods folder.

Once you've done this, you can modify the python files in place.

To build the native modules:

1. Initialize the git submodules.
   ```sh
   git submodule update --init --recursive
   ```
   You can also clone and initialize the submodules in a single step.
   ```sh
   git clone --recursive https://github.com/bl-sdk/oak-mod-manager.git
   ```

2. Make sure you have Python with requests on your PATH. This doesn't need to be the same version
   as what the SDK uses, it's just used by the script which downloads the correct one.
   ```sh
   pip install requests
   python -c 'import requests'
   ```

   If not running on Windows, make sure `msiextract` is also on your PATH. This is typically part
   of an `msitools` package.
   ```sh
   apt install msitools # Or equivalent
   msiextract --version 
   ```

   See the explicit python [readme](https://github.com/bl-sdk/common_cmake/blob/master/explicit_python/Readme.md)
   for a few extra details.

3. Choose a preset, and run CMake. Most IDEs will be able to do this for you,
   ```
   cmake . --preset msvc-debug
   cmake --build out/build/msvc-debug
   ```

4. (OPTIONAL) If you need to debug your module, and you own the game on Steam, add a
   `steam_appid.txt` in the same folder as the executable, containing the game's Steam App Id.

   Normally, games compiled with Steamworks will call
   [`SteamAPI_RestartAppIfNecessary`](https://partner.steamgames.com/doc/sdk/api#SteamAPI_RestartAppIfNecessary),
   which will drop your debugger session when launching the exe directly - adding this file prevents
   that. Not only does this let you debug from entry, it also unlocks some really useful debugger
   features which you can't access from just an attach (i.e. Visual Studio's Edit and Continue).
