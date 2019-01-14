import contextlib
import bpy


def imprint(node, data):
    """Write `data` to `node` as user-defined data.

    Arguments:
        node (str): Long name of node
        data (dict): Dictionary of key/value pairs

    """
    for key, value in data.items():
        node.data[key] = value


def read(node):
    """Return user-defined attributes from `node`"""
    data = dict(node.data)

    # Ignore hidden/internal data
    data = {key: value for key, value in data.items() if
            not key.startswith("_")}

    return data


@contextlib.contextmanager
def maintained_selection():
    """Maintain selection during context.

    Example:
        >>> with maintained_selection():
        ...     # Modify selection
        ...     node.setSelected(on=False, clear_all_selected=True)
        >>> # Selection restored

    """

    previous_selection = bpy.context.selected_objects
    previous_active = bpy.context.view_layer.objects.active
    try:
        yield
    finally:
        # Clear the selection
        for node in bpy.context.selected_objects:
            node.select_set(state=False)

        if previous_selection:
            for node in previous_selection:
                node.select_set(state=True)

        bpy.context.view_layer.objects.active = previous_active
