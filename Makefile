.PHONY: all
all: sdk_mods/mod_menu/native_keybinds.pyd

%.pyd: %.cpp .pyric/.gitignore
	pyric build $<
