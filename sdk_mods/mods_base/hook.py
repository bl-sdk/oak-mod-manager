from collections.abc import Callable
from types import EllipsisType
from typing import Any, ClassVar, Literal, Protocol, TypeAlias, cast, overload

from unrealsdk.hooks import Block, Type, add_hook, has_hook, remove_hook
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct

HookBlockSignal: TypeAlias = None | EllipsisType | Block | type[Block]
PreHookCallback: TypeAlias = Callable[
    [UObject, WrappedStruct, Any, BoundFunction],
    HookBlockSignal | tuple[HookBlockSignal, Any],
]
PostHookCallback: TypeAlias = Callable[[UObject, WrappedStruct, Any, BoundFunction], None]


class HookProtocol(Protocol):
    # The attribute used to detect hook instances at runtime
    _unreal_hook_func: Any
    IS_HOOK_ATTR: ClassVar[str] = "_unreal_hook_func"

    hook_funcs: list[tuple[str, Type]]
    hook_identifier: str

    def enable(self) -> None:
        """Enables all hooks this function is bound to."""
        raise NotImplementedError

    def disable(self) -> None:
        """Disables all hooks this function is bound to."""
        raise NotImplementedError

    def get_active_count(self) -> int:
        """
        Gets the amount of hooks this function is bound to which are active.

        Note this doesn't necessarily mean they're bound to this function.

        Returns:
            The number of active hooks.
        """
        raise NotImplementedError

    def __call__(
        self,
        obj: UObject,
        args: WrappedStruct,
        ret: Any,
        func: BoundFunction,
    ) -> HookBlockSignal | tuple[HookBlockSignal, Any]:
        """The hook callback."""
        raise NotImplementedError


def _hook_enable(self: HookProtocol) -> None:
    for hook_func, hook_type in self.hook_funcs:
        add_hook(hook_func, hook_type, self.hook_identifier, self.__call__)


def _hook_disable(self: HookProtocol) -> None:
    for hook_func, hook_type in self.hook_funcs:
        remove_hook(hook_func, hook_type, self.hook_identifier)


def _hook_get_active_count(self: HookProtocol) -> int:
    return sum(
        1
        for hook_func, hook_type in self.hook_funcs
        if has_hook(hook_func, hook_type, self.hook_identifier)
    )


@overload
def hook(
    hook_func: str,
    hook_type: Literal[Type.PRE],
) -> Callable[[PreHookCallback], HookProtocol]:
    ...


@overload
def hook(
    hook_func: str,
    hook_type: Literal[Type.POST, Type.POST_UNCONDITIONAL],
) -> Callable[[PostHookCallback], HookProtocol]:
    ...


@overload
def hook(
    hook_func: str,
    hook_type: Type,
) -> Callable[[PreHookCallback], HookProtocol] | Callable[[PostHookCallback], HookProtocol]:
    ...


def hook(
    hook_func: str,
    hook_type: Type,
) -> Callable[[PreHookCallback], HookProtocol] | Callable[[PostHookCallback], HookProtocol]:
    """Decorator to add a hook."""

    def decorator(func: PreHookCallback | PostHookCallback) -> HookProtocol:
        func = cast(HookProtocol, func)

        if not hasattr(func, HookProtocol.IS_HOOK_ATTR):
            setattr(func, HookProtocol.IS_HOOK_ATTR, True)

            # Check if this function is a wrapper of an existing hook, and if so copy it's funcs/id
            wrapped_func = func
            while (wrapped_func := getattr(wrapped_func, "__wrapped__", None)) is not None:
                if hasattr(wrapped_func, HookProtocol.IS_HOOK_ATTR):
                    func.hook_funcs = wrapped_func.hook_funcs
                    func.hook_identifier = wrapped_func.hook_identifier
                    break
            else:
                # Didn't find an existing hook, initalize our own
                func.hook_funcs = []
                func.hook_identifier = f"{__name__}.hook-id.{id(func)}"

            func.enable = _hook_enable.__get__(func, func.__class__)
            func.disable = _hook_disable.__get__(func, func.__class__)
            func.get_active_count = _hook_get_active_count.__get__(func, func.__class__)

        func.hook_funcs.append((hook_func, hook_type))

        return func

    return decorator
