from typing import TYPE_CHECKING, TypeAlias

import unrealsdk
from unrealsdk.unreal import UObject, WrappedStruct

from . import engine

if TYPE_CHECKING:
    from enum import auto

    from unrealsdk.unreal._uenum import UnrealEnum  # pyright: ignore[reportMissingModuleSource]

    class EOptionItemType(UnrealEnum):
        Title = auto()
        Slider = auto()
        Spinner = auto()
        BooleanSpinner = auto()
        Button = auto()
        Controls = auto()
        Keybinding_Button = auto()
        KeyBinding_Axis = auto()
        TodoItem = auto()
        DropDownList = auto()
        EOptionItemType_MAX = auto()

else:
    EOptionItemType = unrealsdk.find_enum("EOptionItemType")


EOptionType: TypeAlias = int  # Not using an enum for this since we deliberately use invalid values
GbxInputKeyRebindData_Button: TypeAlias = UObject
GbxInputKeyRebindData_Axis: TypeAlias = UObject
OptionDescriptionItem: TypeAlias = UObject
UTexture2D: TypeAlias = UObject
FVector: TypeAlias = WrappedStruct


# ruff: noqa: N803, ARG001
def create_option_description_item(  # noqa: D417
    outer: UObject | None = engine.Outer,
    /,
    OptionType: EOptionType | None = None,
    OptionItemType: EOptionItemType | None = None,
    OptionItemName: str | None = None,
    OptionDescriptionTitle: str | None = None,
    OptionDescriptionText: str | None = None,
    SliderMin: float | None = None,
    SliderMax: float | None = None,
    SliderStep: float | None = None,
    SliderIsInteger: bool | None = None,
    SpinnerOptions: list[str] | None = None,
    SpinnerWrapEnabled: bool | None = None,
    DropDownOptions: list[str] | None = None,
    ButtonBinding: GbxInputKeyRebindData_Button | None = None,
    AxisBinding: GbxInputKeyRebindData_Axis | None = None,
    AxisScaleVector: FVector | None = None,
    DrivingOptionDescriptionLink: OptionDescriptionItem | None = None,
    BooleanOnText: str | None = None,
    BooleanOffText: str | None = None,
    IsDesktop: bool | None = None,
    IsQuail: bool | None = None,
    IsXboxOne: bool | None = None,
    AvailableOnNewerXboxes: bool | None = None,
    IsPS4: bool | None = None,
    AvailableOnNewerPlayStations: bool | None = None,
    IsOnlyAvailableInFrontendForSplitscreen: bool | None = None,
    IsPrimaryPlayerOnly: bool | None = None,
    HelperTexture: UTexture2D | None = None,
) -> OptionDescriptionItem:
    """
    Helper to construct a OptionDescriptionItem and set fields on it.

    Args:
        outer: The outer object to construct within.

        All remaining args set the property with the same name.
    Returns:
        The newly constructed object.
    """
    obj = unrealsdk.construct_object("OptionDescriptionItem", outer)

    for field, value in locals().items():
        if field in ("obj", "outer"):
            continue

        if value is not None:
            setattr(obj, field, value)

    return obj
