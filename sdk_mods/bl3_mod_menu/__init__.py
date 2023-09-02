from .dialog_box import DialogBox, DialogBoxChoice

__all__: tuple[str, ...] = (
    "__version__",
    "__version_info__",
    "DialogBox",
    "DialogBoxChoice",
)

__version_info__: tuple[int, int] = (1, 0)
__version__: str = f"{__version_info__[0]}.{__version_info__[1]}"

# Setup the actual mod
from . import mod  # noqa: F401  # pyright: ignore[reportUnusedImport]
