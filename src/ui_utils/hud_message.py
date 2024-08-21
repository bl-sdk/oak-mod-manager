import threading
from typing import Any

from unrealsdk.hooks import Block, Type
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct

from mods_base import get_pc, hook

__all__: tuple[str, ...] = ("show_hud_message",)


def show_hud_message(title: str, msg: str, duration: float = 2.5) -> None:
    """
    Displays a short, non-blocking message in the main in game hud.

    Uses the same message style as those for coop players joining/leaving or shift going down.

    Note this should not be used for critical messages, it may silently fail at any point, and
    messages may be dropped if multiple are shown too close to each other.

    Args:
        title: The title of the message box.
        msg: The message to display.
        duration: The duration to display the message for.
    """
    get_pc().DisplayRolloutNotification(title, msg, duration)


"""
Calling display rollout notification while one's still actively displaying will cause a crash.
This may reasonably happen if someone ties this to a keybind - e.g. a user might quickly press the
key a few times to cycle through states, showing a message each time.

While we could block all calls while one's displaying, this means we drop the last few messages,
including the one displaying the final state, the most useful message.

Instead, we'll queue the single latest message queue up, and only drop the earlier ones.
"""

queued_message: tuple[str, str, float] | None = None
display_timer: threading.Timer | None = None


def cycle_next_message() -> None:
    global queued_message, display_timer
    display_timer = None

    if queued_message is None:
        return

    title, msg, duration = queued_message
    queued_message = None

    # Since we're on a thread, the user may have started loading since we were queued
    # Just drop the message if we can't find the pc
    pc = get_pc(possibly_loading=True)
    if pc is not None:
        pc.DisplayRolloutNotification(title, msg, duration)


@hook("/Script/OakGame.OakPlayerController:DisplayRolloutNotification", Type.PRE, auto_enable=True)
def display_rollout_hook(
    _1: UObject,
    args: WrappedStruct,
    _3: Any,
    _4: BoundFunction,
) -> type[Block] | None:
    global queued_message, display_timer

    if display_timer is None:
        # Nothing's being displayed, start a new timer, then let this function continue
        display_timer = threading.Timer(args.Duration + 0.5, cycle_next_message)
        display_timer.start()
        return None

    # Otherwise, a message's currently being displayed, queue the new one and block execution
    queued_message = (args.Title, args.MESSAGE, args.Duration)
    return Block
