import importlib

import bpy
from bpy.app.handlers import persistent
from pyblish import api as pyblish

from ..lib import logger
from .. import api, schema, io

from . import operators

AVALON_CONTAINERS = "AVALON_CONTAINERS"
# todo: set file open browser default path (like a maya workspace)


def install(config):
    """Install Blender-specific functionality of avalon-core.

    This function is called automatically on calling `api.install(blender)`.

    """

    _register_callbacks()
    operators.register()

    if not bpy.app.background:
        # If not in background batch mode, so blender gui is running..
        print("Running blender in gui mode..")
        # TODO: install a menu

    pyblish.register_host("blender")

    config = find_host_config(config)
    if hasattr(config, "install"):
        config.install()


def find_host_config(config):
    name = config.__name__ + ".blender"
    try:
        config = importlib.import_module(name)
    except (ImportError, ModuleNotFoundError) as exc:
        if str(exc) != "No module name {}".format(name):
            raise
        config = None

    return config


def uninstall(config):
    """Uninstall Blender-specific functionality of avalon-core.

    This function is called automatically on calling `api.uninstall()`.

    """
    config = find_host_config(config)
    if hasattr(config, "uninstall"):
        config.uninstall()

    pyblish.deregister_host("blender")
    operators.unregister()


def containerise(name,
                 namespace,
                 nodes,
                 context,
                 loader=None,
                 suffix="CON"):
    """Bundle `nodes` into an assembly and imprint it with metadata

    Containerisation enables a tracking of version, author and origin
    for loaded assets.

    Arguments:
        name (str): Name of resulting assembly
        namespace (str): Namespace under which to host container
        nodes (list): Long names of nodes to containerise
        context (dict): Asset information
        loader (str, optional): Name of loader used to produce this container.
        suffix (str, optional): Suffix of container, defaults to `_CON`.

    Returns:
        container (str): Name of container assembly

    """
    node_name = "%s_%s_%s" % (namespace, name, suffix)
    container = bpy.data.collections.new(node_name)

    data = [
        ("schema", "avalon-core:container-2.0"),
        ("id", "pyblish.avalon.container"),
        ("name", name),
        ("namespace", namespace),
        ("loader", str(loader)),
        ("representation", str(context["representation"]["_id"])),
    ]

    # TODO: Blender 2.8 Collection doesn't have .data? like objects
    #       instead it should store directly into the container.
    #       Is this good enough?
    container["avalon"] = dict(data)

    # Link the children nodes
    for obj in nodes:
        container.objects.link(obj)

    # Link this to the Avalon container
    avalon_container = bpy.data.collections.get(AVALON_CONTAINERS)
    if not avalon_container:
        avalon_container = bpy.data.collections.new(AVALON_CONTAINERS)

        # Link the container to the scene so it's easily visible to the
        # artist and can be managed easily. Otherwise it's only found in
        # "Blender File" view
        bpy.context.scene.collection.children.link(avalon_container)

    avalon_container.children.link(container)

    return container


def parse_container(container, validate=True):
    """Return the container node's full container data.

    Args:
        container (bpy.object): A blender collection (an avalon container).
        validate (bool, optional): Whether to validate the container
            with the avalon-core:container-1.0 schema.

    Returns:
        dict: The container schema data for this container node.

    """
    data = dict(container.get("avalon", {}))
    if not data:
        return None

    # Append required data
    data["objectName"] = container.name

    # Append transient data
    data["node"] = container

    if validate:
        schema.validate(data)

    return data


def ls():
    """List containers from active Blender scene

    This is the host-equivalent of api.ls(), but instead of listing
    assets on disk, it lists assets already loaded in Blender; once loaded
    they are called 'containers'

    """

    for collection in bpy.data.collections:
        if "avalon" not in collection:
            continue

        data = collection["avalon"]
        if data.get("id", None) != "pyblish.avalon.container":
            continue

        yield parse_container(collection)


def _register_callbacks():

    # todo: on_init callback

    bpy.app.handlers.load_post.append(_on_open)
    logger.info("Installed event handler _on_open..")

    bpy.app.handlers.save_pre.append(_on_before_scene_save)
    logger.info("Installed event handler _on_before_scene_save..")

    bpy.app.handlers.save_post.append(_on_scene_save)
    logger.info("Installed event handler _on_scene_save..")


@persistent
def _on_init(*args):
    api.emit("init", args)


@persistent
def _on_open(*args):

    # Detect new or actual open
    if bpy.data.filepath:
        # Likely this was an open operation since it has a filepath
        print("Open..")
        api.emit("open", args)
    else:
        print("New..")
        api.emit("new", args)


@persistent
def _on_scene_save(*args):
    print("Save..")
    api.emit("save", args)


@persistent
def _on_before_scene_save(*args):
    print("Before save..")
    api.emit("before_save", args)
