import os
import bpy
import avalon.api as api


class CreatorOperator(bpy.types.Operator):
    """Launch Avalon Creator.."""

    bl_idname = "object.avalon_creator"
    bl_label = "Create.."

    def execute(self, context):
        from ..tools import creator
        creator.show()
        return {'FINISHED'}


class LoaderOperator(bpy.types.Operator):
    """Launch Avalon Loader.."""

    bl_idname = "object.avalon_loader"
    bl_label = "Load.."

    def execute(self, context):
        from ..tools import cbloader
        cbloader.show()
        return {'FINISHED'}


class ManagerOperator(bpy.types.Operator):
    """Launch Avalon Scene Inventory Manager.."""

    bl_idname = "object.avalon_manager"
    bl_label = "Manage.."

    def execute(self, context):
        from ..tools import cbsceneinventory
        cbsceneinventory.show()
        return {'FINISHED'}


class PublishOperator(bpy.types.Operator):
    """Launch Pyblish.."""

    bl_idname = "object.avalon_publish"
    bl_label = "Publish"

    def execute(self, context):
        from ..tools import publish
        publish.show()
        return {'FINISHED'}


class WorkFilesOperator(bpy.types.Operator):
    """Launch Avalon Work Files..

    You can use this to easily load files or save your current scene,
    including doing an incremental save of your work file.

    """

    bl_idname = "object.avalon_workfiles"
    bl_label = "Work Files"

    def execute(self, context):
        from ..tools import workfiles
        root = os.path.join(os.environ["AVALON_WORKDIR"], "scenes")
        workfiles.show(root)
        return {'FINISHED'}


class ContextManagerOperator(bpy.types.Operator):
    """Launch Avalon Context Manager.."""

    bl_idname = "object.avalon_contextmanager"
    bl_label = "Set Avalon Context.."

    def execute(self, context):
        from ..tools import contextmanager
        contextmanager.show()
        return {'FINISHED'}


class VIEW3D_MT_AvalonContextManagerSubMenu(bpy.types.Menu):
    bl_label = "Avalon"
    bl_idname = "AvalonContextManagerSubMenu"

    def draw(self, context):
        layout = self.layout
        layout.operator(ContextManagerOperator.bl_idname)


class VIEW3D_MT_AvalonMenu(bpy.types.Menu):
    bl_label = "Avalon"
    bl_idname = "AvalonMenu"
    bl_context = "objectmode"
    bl_category = "Avalon"

    def draw(self, context):
        layout = self.layout

        context_label = "{}, {}".format(api.Session["AVALON_ASSET"],
                                        api.Session["AVALON_TASK"])
        layout.menu(VIEW3D_MT_AvalonContextManagerSubMenu.bl_idname,
                    text=context_label)

        layout.separator()

        layout.operator(CreatorOperator.bl_idname)
        layout.operator(LoaderOperator.bl_idname)
        layout.operator(PublishOperator.bl_idname)

        layout.separator()

        layout.operator(WorkFilesOperator.bl_idname)


def avalon_menu_draw(self, context):
    self.layout.menu(VIEW3D_MT_AvalonMenu.bl_idname)


def register():
    if bpy.app.background:
        return

    bpy.utils.register_class(CreatorOperator)
    bpy.utils.register_class(LoaderOperator)
    bpy.utils.register_class(ManagerOperator)
    bpy.utils.register_class(PublishOperator)
    bpy.utils.register_class(WorkFilesOperator)
    bpy.utils.register_class(ContextManagerOperator)

    # Add menu
    bpy.utils.register_class(VIEW3D_MT_AvalonMenu)
    bpy.utils.register_class(VIEW3D_MT_AvalonContextManagerSubMenu)
    bpy.types.VIEW3D_MT_editor_menus.append(avalon_menu_draw)


def unregister():
    if bpy.app.background:
        return

    bpy.utils.unregister_class(CreatorOperator)
    bpy.utils.unregister_class(LoaderOperator)
    bpy.utils.unregister_class(ManagerOperator)
    bpy.utils.unregister_class(PublishOperator)
    bpy.utils.unregister_class(WorkFilesOperator)
    bpy.utils.unregister_class(ContextManagerOperator)

    # Remove menu
    bpy.utils.unregister_class(VIEW3D_MT_AvalonMenu)
    bpy.utils.unregister_class(VIEW3D_MT_AvalonContextManagerSubMenu)
    bpy.types.VIEW3D_MT_editor_menus.remove(avalon_menu_draw)
