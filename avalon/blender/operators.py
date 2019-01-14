import os
import bpy
import avalon.api as api


class QtModalOperator(bpy.types.Operator):
    """A base class for Operators that run a Qt interface."""

    def modal(self, context, event):

        if self._app:
            self._app.processEvents()
            return {'PASS_THROUGH'}

        return {"FINISHED"}

    def execute(self, context):
        """Execute the Operator.

        The child class must implement execute() and call super to trigger this
        class' execute() at the beginning. The execute() method must finally
        return {'RUNNING_MODAL"}

        Note that the Qt code should *not* call QApplication.exec_() as it
        seems that magically the Qt application already processes straight
        away in Blender. Maybe due to:
        https://stackoverflow.com/questions/28060218/where-is-pyqt-event
        -loop-running


        """
        from avalon.vendor.Qt import QtWidgets

        self._app = QtWidgets.QApplication.instance()
        if not self._app:
            self._app = QtWidgets.QApplication(["blender"])


class CreatorOperator(QtModalOperator):
    """Launch Avalon Creator.."""

    bl_idname = "object.avalon_creator"
    bl_label = "Create.."

    def execute(self, context):
        # Initialize Qt operator execution
        super(CreatorOperator, self).execute(context)

        from ..tools import creator
        creator.show()
        return {'RUNNING_MODAL'}


class LoaderOperator(QtModalOperator):
    """Launch Avalon Loader.."""

    bl_idname = "object.avalon_loader"
    bl_label = "Load.."

    def execute(self, context):
        # Initialize Qt operator execution
        super(LoaderOperator, self).execute(context)

        from ..tools import cbloader
        cbloader.show()
        return {'RUNNING_MODAL'}


class ManagerOperator(QtModalOperator):
    """Launch Avalon Scene Inventory Manager.."""

    bl_idname = "object.avalon_manager"
    bl_label = "Manage.."

    def execute(self, context):
        # Initialize Qt operator execution
        super(ManagerOperator, self).execute(context)

        from ..tools import cbsceneinventory
        cbsceneinventory.show()
        return {'RUNNING_MODAL'}


class PublishOperator(QtModalOperator):
    """Launch Pyblish.."""

    bl_idname = "object.avalon_publish"
    bl_label = "Publish"

    def execute(self, context):
        # Initialize Qt operator execution
        super(PublishOperator, self).execute(context)

        from ..tools import publish
        publish.show()
        return {'RUNNING_MODAL'}


class WorkFilesOperator(QtModalOperator):
    """Launch Avalon Work Files..

    You can use this to easily load files or save your current scene,
    including doing an incremental save of your work file.

    """

    bl_idname = "object.avalon_workfiles"
    bl_label = "Work Files"

    def execute(self, context):
        # Initialize Qt operator execution
        super(WorkFilesOperator, self).execute(context)

        from ..tools import workfiles
        root = os.path.join(os.environ["AVALON_WORKDIR"], "scenes")
        workfiles.show(root)
        return {'RUNNING_MODAL'}


class ContextManagerOperator(QtModalOperator):
    """Launch Avalon Context Manager.."""

    bl_idname = "object.avalon_contextmanager"
    bl_label = "Set Avalon Context.."

    def execute(self, context):
        # Initialize Qt operator execution
        super(ContextManagerOperator, self).execute(context)

        from ..tools import contextmanager
        contextmanager.show()
        return {'RUNNING_MODAL'}


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
