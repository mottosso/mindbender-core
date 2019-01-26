import contextlib
import bpy


def get_selected():
    """Return the currently selected objects in the current scene.

    Note: It may seem trivial in Blender to use bpy.context.selected_objects
        however the context may vary on how the code is being run and the
        `selected_objects` might not be available. So this function queries
        it explicitly from the current scene.

    See: https://blender.stackexchange.com/questions/36281/bpy-context-
         selected-objects-context-object-has-no-attribute-selected-objects

    Returns:
        list: The selected objects.

    """
    # Note that in Blender 2.8+ the code to see if an object is selected is
    # object.select_get() as opposed to the object.select getter property
    # it was before.
    return [o for o in bpy.context.scene.objects if o.select_get()]


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

    previous_selection = get_selected()
    previous_active = bpy.context.view_layer.objects.active

    try:
        yield
    finally:
        # Clear the selection
        for node in get_selected():
            node.select_set(state=False)

        if previous_selection:
            for node in previous_selection:
                try:
                    node.select_set(state=True)
                except Exception as exc:
                    # This could happen if a selected node was
                    # deleted during the context
                    print("Failed to reselect.. %s" % (exc,))
                    continue

        bpy.context.view_layer.objects.active = previous_active
