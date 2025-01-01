# Changelog

## v1.6: (codename tbd)

### BL3 Mod Menu v1.5
- Fixed the handling of spinner option updates, so that they're actually usable.

### [Mods Base v1.6](https://github.com/bl-sdk/mods_base/blob/master/Readme.md#v16)
> - Changed default type of `HookType` generic type hint to any, so that by default pre and post hooks
>   can be combined under the same type. As an example, previously if you passed an explicit hook list
>   to `build_mod`, the type hinting would only accept a list where all hooks were of the same type.
>
> - Fixed that defining an option, keybind, hook, or command as a class member, and then constructing
>   it via the `build_mod` factory, would pass empty lists to the constructor and thus prevent the
>   auto member collection from running.
>
> - Changed the display version to be sourced from `mod_manager.display_version` in the unrealsdk
>   config file, rather than an environment variable.
>
> - Gave `@command` and `ArgParseCommand.add_argument` default type hinting for the args they forward.

### Keybinds v2.4
- Linting fixes.

### [pyunrealsdk v1.5.1](https://github.com/bl-sdk/pyunrealsdk/blob/master/changelog.md#v151)
> - Deprecated `unrealsdk.hooks.inject_next_call` in favour of a new
>   `unrealsdk.hooks.prevent_hooking_direct_calls` context manager.
> 
> - The `WeakPointer` constructor can now be called with no args, to create a null pointer.
> 
> - As with unrealsdk, reworked the configuration system to no longer rely on environment variables.
>   All sdk configuration is now also done through the `unrealsdk.toml`.
> 
>   The full contents of the unrealsdk config are parsed and exposed to Python in `unrealsdk.config`.
> 
> - `unrealsdk.construct_object` now throws a `RuntimeError` instead of silently returning `None` when
>   constructing the object fails. This is how the type hints already assumed it worked.
>
> - Changed type hinting of `unrealsdk.find_all` to return an `Iterable[UObject]`, instead of
>   `Iterator[UObject]`. This mirrors what was actually happening at runtime.

### [unrealsdk v1.6.0](https://github.com/bl-sdk/unrealsdk/blob/master/changelog.md#v160)
> - Completely reworked the configuration system.
> 
>   Environment variables and the `unrealsdk.env` are no longer used, due to issues with them not fully
>   propagating within the same process. The new configuration now uses an `unrealsdk.toml` instead.
>   
>   Also added support for a user specific override file - `unrealsdk.user.toml`. This allows projects
>   to ship their own `unrealsdk.toml`, without overwriting user's settings on update.
> 
> - `unrealsdk::hook_manager::inject_next_call` is now thread local.
> 
> - Fixed that `unrealsdk::commands::has_command` and `unrealsdk::commands::remove_command` were case
>   sensitive, while `unrealsdk::commands::add_command` and the callbacks were not. Commands should be
>   now be case insensitive everywhere.
> 
> - Fixed that the executed command message of custom sdk commands would not appear in console if you
>   increased the minimum log level, and that they may have appeared out of order with respects to
>   native engine messages.
> 
> - Added an additional console command hook in BL2, to cover commands not run directly via console.
> 
> - Renamed the `unrealsdk.locking_process_event` (previously `UNREALSDK_LOCKING_PROCESS_EVENT`)
>   setting to `unrealsdk.locking_function_calls`, and expanded it's scope to cover all function
>   calls. This fixes a few more possibilities for lockups.
> 
> - Trying to set a struct, array, or multicast delegate to itself is now a no-op, and prints a
>   warning.
> 
> - The console key will now also be overwritten if it was previously set to `Undefine`.
>
> - Handled `UStruct` differing in size between BL2 and TPS.
>
> - Fixed all BL3 console output being treated as console commands instead. (Broken only in v1.5.0)

## v1.5: Time Skip

### General
- Upgraded to Python 3.13.

### BL3 Mod Menu v1.4
- Grouped options with no visible children no longer show their header.

### [Console Mod Menu v1.4](https://github.com/bl-sdk/console_mod_menu/blob/master/Readme.md#v14)
> - Improved suggestions when trying to bind a key by name, and misspelling it.
> - Swap known controller key names between UE3/UE4 versions, based on game.
> - Grouped options with no visible children no longer show their header.

### [Mods Base v1.5](https://github.com/bl-sdk/mods_base/blob/master/Readme.md#v15)
> - Added a default `rlm` command, which is a helper to reload Python modules during development.
> - Deprecated the `auto_enable` arg in the `@hook` decorator, since it was misleading and in 99% of
>   cases was not needed.
> - Reworked `@hook` decorator internals to better support use on methods. It essentially creates a
>   factory, which must be bound to the specific object before use. This is done automatically on
>   mod instances.
> - `KeybindOption.from_keybind()` now forwards the `default_key` -> `default_value`, so that
>   resetting to default works consistently.

### Keybinds v2.3
- Linting fixes.

### [pyunrealsdk v1.4.0](https://github.com/bl-sdk/pyunrealsdk/blob/master/changelog.md#v140)
> - Fixed weak pointer type hinting to allow for null pointers. This always worked at runtime.
> - Added support for Delegate and Multicast Delegate properties.
> - Added a repr to `BoundFunction`, as these are now returned by delegates.
> - The `WrappedStruct` constructor can now be used to construct function arg structs, like what's
    passed to a hook. This *does not* also apply to `unrealsdk.make_struct`, since function names
    conflict far more often.
> - Removed the suggestion to return `Ellipsis` in hooks when overwriting a return value but not
    blocking execution. This still works at runtime, but is no longer present in the type hinting,
    since it made `Ellipsis` be typed as a valid return in several places it shouldn't have been,
    and it's an obscure use case to begin with.

### UI Utils v1.3
- Linting fixes.

### [unrealsdk v1.4.0](https://github.com/bl-sdk/unrealsdk/blob/master/changelog.md#v140)
> - Fixed that UE3 `WeakPointer`s would always return null, due to an incorrect offset in the
>   `UObject` header layout.
> - Added support for Delegate and Multicast Delegate properties.
> - Changed `unrealsdk::hook_manager::log_all_calls` to write to a dedicated file.
> - Fixed missing all `CallFunction` based hooks in TPS - notably including the say bypass.
> - Added the offline mode say crash fix for BL2+TPS as a base sdk hook.

## v1.4: White Elephant

Also see the unrealsdk v1.3.0 changelog [here](https://github.com/bl-sdk/unrealsdk/blob/master/changelog.md#v130)
and the pyunrealsdk v1.3.0 changelog [here](https://github.com/bl-sdk/pyunrealsdk/blob/master/changelog.md#v130).

### General
- Fixed that in some cases a mod couldn't be disabled, or wouldn't enable actively, due to hooks not
  getting added/removed properly.

  [unrealsdk@227a93d2](https://github.com/bl-sdk/unrealsdk/commit/227a93d2)
  
- Mods now show how well they support coop. This is unknown by default, developers need to set it.

  [db89e4b3](https://github.com/bl-sdk/oak-mod-manager/commit/db89e4b3)

- The mod manager now occasionally checks for updates. These will appear on the "Python SDK" mod
  menu entry.

  [9bf295b0](https://github.com/bl-sdk/oak-mod-manager/commit/9bf295b0)

### General - Developer
- Set `PYUNREALSDK_PYEXEC_ROOT` to the sdk mods folder by default.

  [2f15c5ba](https://github.com/bl-sdk/oak-mod-manager/commit/2f15c5ba)

- Fixed that pyright would always error on creating a HiddenOption (due to mismatching generics).

  [9bf295b0](https://github.com/bl-sdk/oak-mod-manager/commit/9bf295b0)

### BL3 Mod Menu v1.3
- Display mods' coop support.

  [db89e4b3](https://github.com/bl-sdk/oak-mod-manager/commit/db89e4b3)

### Console Mod Menu v1.3
- Display mods' coop support.

  [db89e4b3](https://github.com/bl-sdk/oak-mod-manager/commit/db89e4b3)

### Mods Base v1.4
- Added the "Coop Support" field.

  [db89e4b3](https://github.com/bl-sdk/oak-mod-manager/commit/db89e4b3)
  
- Automatically check for mod manager updates.

  [9bf295b0](https://github.com/bl-sdk/oak-mod-manager/commit/9bf295b0)

### UI Utils v1.2

- Added a helper to show a tutorial dialog, `show_modal_tutorial_dialog`.

  [51d3c872](https://github.com/bl-sdk/oak-mod-manager/commit/51d3c872)

- Fixed an attribute error when calling `show_hud_message` during a load screen (from a thread).

  [51d3c872](https://github.com/bl-sdk/oak-mod-manager/commit/51d3c872)

## v1.3: Lethal Catch

Also see the unrealsdk v1.2.0 changelog [here](https://github.com/bl-sdk/unrealsdk/blob/master/changelog.md#v120)
and the pyunrealsdk v1.2.0 changelog [here](https://github.com/bl-sdk/pyunrealsdk/blob/master/changelog.md#v120).

### General
- The BL3 release zip now also includes the Console Mod Menu, as it's use proved handy when the
  dedicated BL3 Mod Menu broke.

  [07283ae3](https://github.com/bl-sdk/oak-mod-manager/commit/07283ae3)

- Added a warning for when Proton fails to propagate environment variables, which mods or the mod
  manager may have been expecting.
  
  An example consequence of this is that the base mod may end up as version "Unknown Version".

  [9744640f](https://github.com/bl-sdk/oak-mod-manager/commit/9744640f)

- Added warnings when loading duplicate and/or renamed mod files.

  [d6d4476b](https://github.com/bl-sdk/oak-mod-manager/commit/d6d4476b)

### General - Developer
- When developing third party native modules, you can now include this repo as a submodule to
  automatically keep the Python version in sync. There was a bit of build system restructuring to
  allow our `CMakeLists.txt` to define this.

  [6f9a8717](https://github.com/bl-sdk/oak-mod-manager/commit/6f9a8717)

- Changed the `OAK_MOD_MANAGER_EXTRA_FOLDERS` env var to read from `MOD_MANAGER_EXTRA_FOLDERS`
  instead, for consistency.
  
  [9744640f](https://github.com/bl-sdk/oak-mod-manager/commit/9744640f)

- Python warnings are now hooked up to the logging system.
  
  [9744640f](https://github.com/bl-sdk/oak-mod-manager/commit/9744640f)

- `Option.on_change` now fires automatically when the value is changed.

  [a09f92c1](https://github.com/bl-sdk/oak-mod-manager/commit/a09f92c1)

- Updated type hinting to use 3.12 syntax.

  [dfb72a92](https://github.com/bl-sdk/oak-mod-manager/commit/dfb72a92),
  [95cc37eb](https://github.com/bl-sdk/oak-mod-manager/commit/95cc37eb)

### BL3 Mod Menu v1.2

- Fixed the crashes that occurred in the latest game update when opening a mod with slider options or
  keybinds.
  
  [650fdfb5](https://github.com/bl-sdk/oak-mod-manager/commit/650fdfb5)

### Console Mod Menu v1.2

- You can now press back while on the home screen to exit the menu, same as pressing quit.
  [df12460d](https://github.com/bl-sdk/oak-mod-manager/commit/df12460d)

- Improved the suggestions when rebinding a key by name. Multiple suggestions may now be shown, and
  symbols now try to suggest their name (e.g. typing `.` will suggest `Decimal` and `Period`).
  
  [a488305b](https://github.com/bl-sdk/oak-mod-manager/commit/a488305b)

- Changed strict keybind and ui utils dependencies to be soft dependencies. This is of no
  consequence to this project, but it makes the mod menu more game-agnostic for other ones.
  
  These dependencies were only used for the "Rebind using key press" screen, this functionality will
  now gracefully degrade based on what's available. 

  [9ab26173](https://github.com/bl-sdk/oak-mod-manager/commit/9ab26173),
  [c7dfc4a6](https://github.com/bl-sdk/oak-mod-manager/commit/c7dfc4a6),
  [81aeb178](https://github.com/bl-sdk/oak-mod-manager/commit/81aeb178)

### Keybinds v2.2

- Moved `raw_keybinds` out of mods base, into keybinds.

  [c7dfc4a6](https://github.com/bl-sdk/oak-mod-manager/commit/c7dfc4a6)

### Mods Base v1.3

- Moved `raw_keybinds` out of mods base, into keybinds.

  [c7dfc4a6](https://github.com/bl-sdk/oak-mod-manager/commit/c7dfc4a6)

## v1.2: Hand of Glory

Also see the pyunrealsdk v1.1.1 changelog [here](https://github.com/bl-sdk/pyunrealsdk/blob/master/changelog.md#v111).

### General

- Changed the shipped pluginloader again, to `dsound.dll`. This addresses that when running under
  proton, overriding xinput would break all controller input.

  [bab823ff](https://github.com/bl-sdk/oak-mod-manager/commit/bab823ff)

- Added an explicit mod manager version, separating it from Mods Base. This means future mod manager
  updates are not required to also update Mods Base.

  [3e0b4d8a](https://github.com/bl-sdk/oak-mod-manager/commit/3e0b4d8a)

- Fixed that debugpy had to be placed in the base mod folder, and would break if placed in an extra
  one.

  [4971b8c0](https://github.com/bl-sdk/oak-mod-manager/commit/4971b8c0)

### Keybinds v2.1
- Fixed that rebinding a key wouldn't update the hooks until the mod was next enabled.

  [05891ad4](https://github.com/bl-sdk/oak-mod-manager/commit/05891ad4)

- Fixed that controller inputs weren't picked up while in menus - effectively meaning you couldn't
  bind anything to a controller without editing files.

  [b0b6881c](https://github.com/bl-sdk/oak-mod-manager/commit/b0b6881c)

### Mods Base v1.2
- Added `KeybindType.is_enabled`.

  [05891ad4](https://github.com/bl-sdk/oak-mod-manager/commit/05891ad4)

- Added a hook for keybind implementations to detect rebinds.

  [05891ad4](https://github.com/bl-sdk/oak-mod-manager/commit/05891ad4)

## v1.1: Rowan's Call
Also see the unrealsdk v1.1.0 changelog [here](https://github.com/bl-sdk/unrealsdk/blob/master/changelog.md#v110)
and the pyunrealsdk v1.1.0 changelog [here](https://github.com/bl-sdk/pyunrealsdk/blob/master/changelog.md#v110).

### General

- Added various developer experience improvements. See the [Developing SDK Mods](https://bl-sdk.github.io/oak-mod-db/developing/)
  guide on the project site for more details.

  - Added integration with [debugpy](https://github.com/microsoft/debugpy).

    [2259a225](https://github.com/bl-sdk/oak-mod-manager/commit/2259a225),
    [5a5f5a32](https://github.com/bl-sdk/oak-mod-manager/commit/5a5f5a32)

  - Added support for multiple mods folders, so your own in-development mods can be kept separate.

    [0d1c76e3](https://github.com/bl-sdk/oak-mod-manager/commit/0d1c76e3),
    [e42e89ac](https://github.com/bl-sdk/oak-mod-manager/commit/e42e89ac)

- Changed the shipped pluginloader to use `xinput1_3.dll`, since this won't conflict with dxvk, and
  since the `d3d11.dll` one broke the steam overlay.
  
  [e485dcf6](https://github.com/bl-sdk/oak-mod-manager/commit/e485dcf6)

- Added a warning when the Proton exception bug is detected.

  [9046f7d9](https://github.com/bl-sdk/oak-mod-manager/commit/9046f7d9)

- Added support for building using standard GCC-based MinGW. This is not tested in CI however, as it
  requires a newer version than that available in Github Actions.

  [74f483c5](https://github.com/bl-sdk/oak-mod-manager/commit/74f483c5)

- Various linting/type hinting improvements.

### BL3 Mod Menu v1.1

- Made the menu work from the pause menu. Also added options to suppress existing menu entries so
  that this doesn't mess up SQ muscle memory.

  [b221614d](https://github.com/bl-sdk/oak-mod-manager/commit/b221614d),
  [1e260663](https://github.com/bl-sdk/oak-mod-manager/commit/1e260663),
  [1d30db37](https://github.com/bl-sdk/oak-mod-manager/commit/1d30db37)

- Implemented the "option header" directly, rather than relying on `Mod.iter_display_options`.

  [707a403b](https://github.com/bl-sdk/oak-mod-manager/commit/707a403b)

- Now display mod statuses in the mod list.
  
  [921179ef](https://github.com/bl-sdk/oak-mod-manager/commit/921179ef)

### Console Mod Menu v1.1

- Now handle nested options properly, rather than listing all at once. This significantly improves
  readability for mods with large amounts of options, which use nested options to group them.

  [3e88d2b4](https://github.com/bl-sdk/oak-mod-manager/commit/3e88d2b4),
  [27af0c7a](https://github.com/bl-sdk/oak-mod-manager/commit/27af0c7a)


- Implemented the "option header" directly, including adding mod statuses to it, rather than relying
  on `Mod.iter_display_options`.

  [707a403b](https://github.com/bl-sdk/oak-mod-manager/commit/707a403b),
  [921179ef](https://github.com/bl-sdk/oak-mod-manager/commit/921179ef)

- Improved the display of a few forms of rich text when converted to plain text for console.

  [370d80b3](https://github.com/bl-sdk/oak-mod-manager/commit/370d80b3)

### Keybinds v2.0

- Fixed the large hangs caused when scrolling, by completely rewriting to be registration based.

  [0dfe676a](https://github.com/bl-sdk/oak-mod-manager/commit/0dfe676a),
  [09407718](https://github.com/bl-sdk/oak-mod-manager/commit/09407718)

### Mods Base v1.1

- Options improvements:

  - No longer warn on "saving" a button option. While useless, this is the only standard option type
    which wasn't handled, it's now just a silent no-op.

    [cb99aba9](https://github.com/bl-sdk/oak-mod-manager/commit/cb99aba9)

  - No longer warn when a keybind option is included in the option list. You may want to do this to
    get a key to use in menus, for example.

    [4f2e17c9](https://github.com/bl-sdk/oak-mod-manager/commit/4f2e17c9)

  - `NestedOption` no longer inherits from `ButtonOption`. This was true in how the BL2/BL3 Mod
    Menus implemented them, but does not make much sense functionally.

    [3e88d2b4](https://github.com/bl-sdk/oak-mod-manager/commit/3e88d2b4)

  - Removed `mod` from the repr.

    [e28423c3](https://github.com/bl-sdk/oak-mod-manager/commit/e28423c3)

- Addressed the fact that `get_pc` may very rarely return `None`.

  [11470d75](https://github.com/bl-sdk/oak-mod-manager/commit/11470d75)

- Made `hook` default to pre-hooks.

  [4ca004a8](https://github.com/bl-sdk/oak-mod-manager/commit/4ca004a8)

- Reworked keybinds and raw keybinds to support registration based keybind implementations. A
  polling based implementation can simply use no-op enable/disable functions.

  [0dfe676a](https://github.com/bl-sdk/oak-mod-manager/commit/0dfe676a)

- `Mod.iter_display_options` no longer yields the "option header". Instead, mod menus directly check
  `Mod.description`, `Mod.supported_games`, and the new `Mod.enabling_locked`. This both gives mod
  menus more flexibility in displaying these, and makes it easier for mods to overwrite their
  display options while retianing the standard header.

  [707a403b](https://github.com/bl-sdk/oak-mod-manager/commit/707a403b)

- Added `Mod.get_status()`, the default implementation of which returns enabled/disabled.
  
  [921179ef](https://github.com/bl-sdk/oak-mod-manager/commit/921179ef)

- Improved the HTML to plain-text converter, parsing a few tags into plain text equivalents. This
  primarily improves descriptions viewed in the console mod menu.

  [370d80b3](https://github.com/bl-sdk/oak-mod-manager/commit/370d80b3)

- Did initial work to support willow. In a future update, this module will be shifted to another
  repo, and be common to both mod managers.
  
  [aa9764ea](https://github.com/bl-sdk/oak-mod-manager/commit/aa9764ea)

### UI Utils v1.1

- Handled that triggering a queued HUD message while in a loading screen would get a player
  controller of `None`.

  [11470d75](https://github.com/bl-sdk/oak-mod-manager/commit/11470d75)

## v1.0: Major Kong
- Initial Release
