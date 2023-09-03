from __future__ import annotations

from collections.abc import Callable
from dataclasses import InitVar, dataclass, field
from typing import Any, ClassVar, Self

from mods_base import ENGINE, hook
from unrealsdk import logging, make_struct
from unrealsdk.hooks import Block, Type
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct

from .native.dialog_box import show_dialog_box

# Track a stack incase someone opens a dialog while another is still open
_dialog_stack: list[DialogBox] = []


@dataclass
class DialogBoxChoice:
    """
    Dataclass for an individual choice of a dialog box.

    Attributes:
        label: The labvel this options displays on the dialog box.
        action: The "action" this choice performs when selected. Defaults to copying the label.
        close_on_select: If true, selecting this choice will close the menu.
        controller_default: The first choice with this set to true will be selected by default when
                            using a controller.
    """

    label: str
    action: str = None  # type: ignore
    close_on_select: bool = True
    controller_default: bool = False

    def __post_init__(self) -> None:
        if self.action is None:  # type: ignore
            self.action = self.label


@dataclass
class DialogBox:
    """
    Class representing a dialog box.

    When the dialog box is closed, the `on_press` callback will be called with the choice which was
    selected. This is detected using the choice's action. The dialog being cancel emits an event
    with the `Cancel` action - if you have a button with this action already, it will be used,
    otherwise falls back to using the `DialogBox.CANCEL` class var.

    Class Vars:
        CANCEL: The choice passed to the on press callback when the dialog is cancelled, but there
                is no existing cancel choice.

    Attributes:
        header: The dialog box's header.
        choices: The list of choices to offer.
        body: The main body of the dialog box.
        may_cancel: True if the dialog box may be canceled out of.
        on_press: The on press callback to run. May also be set using decorator-like syntax.
    Init Args:
        dont_show: If true, does not automatically show the dialog box after construction.
    """

    CANCEL: ClassVar[DialogBoxChoice] = DialogBoxChoice("Cancel", close_on_select=True)

    header: str
    choices: list[DialogBoxChoice]
    body: str = ""
    may_cancel: bool = True

    dont_show: InitVar[bool] = False

    on_press: Callable[[DialogBoxChoice], None] | None = field(default=None, kw_only=True)

    _controler_default_idx: int | None = field(default=None, init=False, repr=False)
    _result_mapping: dict[str, DialogBoxChoice] = field(
        default_factory=dict,
        init=False,
        repr=False,
    )

    def __post_init__(self, dont_show: bool) -> None:
        seen_default = False
        for idx, choice in enumerate(self.choices):
            if not seen_default and choice.controller_default:
                self._controler_default_idx = idx

            lower_action = choice.action.lower()
            if lower_action in self._result_mapping:
                logging.dev_warning(f"Clash in dialog box choice actions: {lower_action}")
            self._result_mapping[lower_action] = choice

        if not dont_show:
            self.show()

    def __call__(self, on_press: Callable[[DialogBoxChoice], None]) -> Self:
        """
        Sets the on press callback.

        This allows this class to be constructed using decorator syntax, though note it is *not* a
        decorator, it returns itself so must be the outermost level.

        Args:
            on_press: The callback to set.
        Returns:
            This keybind instance.
        """
        if self.on_press is not None:
            logging.dev_warning(
                "DialogBox.__call__ was called on a box which already has a on press callback",
            )

        self.on_press = on_press
        return self

    def show(self) -> None:
        """Displays the dialog box."""

        def setup_callback(struct: WrappedStruct) -> None:
            struct.HeaderText = self.header
            struct.BodyText = self.body
            struct.Choices = [
                make_struct(
                    "GbxGFxDialogBoxChoiceInfo",
                    LabelText=c.label,
                    ActionName=c.action or c.label,
                    bCloseDialogOnSelection=c.close_on_select,
                )
                for c in self.choices
            ]
            struct.bCanCancel = self.may_cancel

            if self._controler_default_idx is not None:
                struct.InitialChoiceIndex = self._controler_default_idx

        _dialog_stack.append(self)
        show_dialog_box(ENGINE.GameInstance, setup_callback)

    @hook("/Script/OakGame.OakGameInstance:OnNATHelpChoiceMade", Type.PRE, auto_enable=True)
    @staticmethod
    def _on_dialog_closed_hook(
        _1: UObject,
        args: WrappedStruct,
        _3: Any,
        _4: BoundFunction,
    ) -> type[Block] | None:
        if len(_dialog_stack) == 0:
            return None

        dialog = _dialog_stack[-1]

        choice: DialogBoxChoice | None = None

        lower_action = args.ChoiceNameId.lower()
        if lower_action in dialog._result_mapping:
            choice = dialog._result_mapping[lower_action]
        elif lower_action == "cancel":
            choice = DialogBox.CANCEL

        if choice is None:
            logging.error(f"Selected unknown dialog box choice {args.ChoiceNameId}!")
            return Block

        if choice.close_on_select:
            _dialog_stack.pop()

        if dialog.on_press is not None:
            dialog.on_press(choice)

        return Block
