from app.ui.streamlined_lifecycle_workspace import (
    STREAMLINED_LIFECYCLE_SCRIPT as RAW_STREAMLINED_LIFECYCLE_SCRIPT,
    STREAMLINED_LIFECYCLE_STYLE,
)


STREAMLINED_LIFECYCLE_SCRIPT = RAW_STREAMLINED_LIFECYCLE_SCRIPT.replace(
    "if (insertionPoint && grid.children.length) fieldset.insertBefore(grid, insertionPoint);",
    "if (grid.children.length) fieldset.insertBefore(grid, fieldset.querySelector(':scope > .status') || null);",
)
