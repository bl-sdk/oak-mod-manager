# Oak Mod Manager
[![Support Discord](https://img.shields.io/static/v1?label=&message=Support%20Discord&logo=discord&color=424)](https://discord.gg/bXeqV8Ef9R)
[![Developer Discord](https://img.shields.io/static/v1?label=&message=Developer%20Discord&logo=discord&color=222)](https://discord.gg/VJXtHvh)

The [pyunrealsdk](https://github.com/bl-sdk/pyunrealsdk) mod manager for:
- Borderlands 3
- Wonderlands

# Development
When developing, it's recommended to point pyunrealsdk directly at this repo. To do this:

1. Navigate to the plugins folder - `<game>\OakGame\Binaries\Win64\Plugins\`

2. Edit `python3XX._pth`, replacing `..\..\..\..\sdk_mods` with `<path to repo>\src`. If you have a
   debug build, also edit `python3XX_d._pth`.

3. Edit `unrealsdk.env`, setting `PYUNREALSDK_INIT_SCRIPT=<path to repo>\src\__main__.py`.

4. (Optional) Copy any mods you were using and their settings into the `src` folder, and setup gitignores for them.

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

2. Setup the python dev files. The simplest way is as follows:
   ```sh
   apt install msitools # Or equivalent for other package managers, not required on Windows

   cd libs/pyunrealsdk/common_cmake/explicit_python
   pip install requests
   python download.py 3.11.5 amd64
   ```
   Make sure to copy the same python version as your install is already using.

   See the [readme](https://github.com/bl-sdk/common_cmake/blob/master/explicit_python/Readme.md)
   for more advanced details.

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
