import functools
from collections.abc import Callable
from types import EllipsisType
from typing import Any, Literal, Protocol, Self, TypeAlias, cast, overload, runtime_checkable

from unrealsdk.hooks import Block, Type, add_hook, has_hook, remove_hook
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct

HookBlockSignal: TypeAlias = None | EllipsisType | Block | type[Block]

AnyPreHook: TypeAlias = (
    Callable[
        [UObject, WrappedStruct, Any, BoundFunction],
        HookBlockSignal | tuple[HookBlockSignal, Any],
    ]
    | Callable[
        [Any, UObject, WrappedStruct, Any, BoundFunction],
        HookBlockSignal | tuple[HookBlockSignal, Any],
    ]
)
AnyPostHook: TypeAlias = (
    Callable[[UObject, WrappedStruct, Any, BoundFunction], None]
    | Callable[[Any, UObject, WrappedStruct, Any, BoundFunction], None]
)


@runtime_checkable
class HookProtocol(Protocol):
    hook_funcs: list[tuple[str, Type]]
    hook_identifier: str

    obj_to_bind_hooks_to: Any | None = None

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

    def bind(self, obj: Any) -> Self:
        """
        Binds this hook to a specific object - to be used if this function is a method.

        If this function is a method, this must be done before enabling the hook.

        Args:
            obj: The object to bind to.
        Return:
            A reference to this hook.
        """
        raise NotImplementedError

    @overload
    def __call__(
        self,
        obj: UObject,
        args: WrappedStruct,
        ret: Any,
        func: BoundFunction,
    ) -> HookBlockSignal | tuple[HookBlockSignal, Any]:
        ...

    @overload
    def __call__(
        self,
        bound_obj: Any,
        obj: UObject,
        args: WrappedStruct,
        ret: Any,
        func: BoundFunction,
    ) -> HookBlockSignal | tuple[HookBlockSignal, Any]:
        ...


def _hook_enable(self: HookProtocol) -> None:
    func = (
        self.__call__
        if self.obj_to_bind_hooks_to is None
        else functools.partial(self.__call__, self.obj_to_bind_hooks_to)
    )
    for hook_func, hook_type in self.hook_funcs:
        add_hook(hook_func, hook_type, self.hook_identifier, func)


def _hook_disable(self: HookProtocol) -> None:
    for hook_func, hook_type in self.hook_funcs:
        remove_hook(hook_func, hook_type, self.hook_identifier)


def _hook_get_active_count(self: HookProtocol) -> int:
    return sum(
        1
        for hook_func, hook_type in self.hook_funcs
        if has_hook(hook_func, hook_type, self.hook_identifier)
    )


def _hook_bind(self: HookProtocol, obj: Any) -> HookProtocol:
    self.obj_to_bind_hooks_to = obj
    return self


@overload
def hook(
    hook_func: str,
    hook_type: Literal[Type.PRE],
) -> Callable[[AnyPreHook], HookProtocol]:
    ...


@overload
def hook(
    hook_func: str,
    hook_type: Literal[Type.POST, Type.POST_UNCONDITIONAL],
) -> Callable[[AnyPostHook], HookProtocol]:
    ...


def hook(
    hook_func: str,
    hook_type: Type,
) -> Callable[[AnyPreHook], HookProtocol] | Callable[[AnyPostHook], HookProtocol]:
    """Decorator to add a hook."""

    def decorator(func: AnyPreHook | AnyPostHook) -> HookProtocol:
        if not isinstance(func, HookProtocol):
            func = cast(HookProtocol, func)

            # Check if this function is a wrapper of an existing hook, and if so copy it's data
            wrapped_func = func
            while (wrapped_func := getattr(wrapped_func, "__wrapped__", None)) is not None:
                if isinstance(wrapped_func, HookProtocol):
                    func.hook_funcs = wrapped_func.hook_funcs
                    func.hook_identifier = wrapped_func.hook_identifier
                    func.obj_to_bind_hooks_to = wrapped_func.obj_to_bind_hooks_to
                    break
            else:
                # Didn't find an existing hook, initalize our own data
                func.hook_funcs = []
                func.hook_identifier = f"{__name__}.hook-id.{id(func)}"
                func.obj_to_bind_hooks_to = None

            func.enable = _hook_enable.__get__(func, type(func))
            func.disable = _hook_disable.__get__(func, type(func))
            func.get_active_count = _hook_get_active_count.__get__(func, type(func))
            func.bind = _hook_bind.__get__(func, type(func))

        func.hook_funcs.append((hook_func, hook_type))

        return func

    return decorator
