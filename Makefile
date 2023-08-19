.PHONY: all
all: sdk_mods/mod_menu/native_keybinds.pyd sdk_mods/mod_menu/native_menu.pyd

PYRIC_DIR := .pyric
BUILD_TYPE := --release

%.pyd: %.cpp $(PYRIC_DIR)/.gitignore
	pyric build -d $(PYRIC_DIR) $(BUILD_TYPE) $<
