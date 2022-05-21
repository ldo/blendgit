import bpy
from bpy.props import StringProperty

from ..templates import ToolPanel
from ..tools.register import register_wrap
from ..tools.lfs import InitLfs, lfs_data_update_async
from ..tools import lfs
from ..tools.saving import SaveCommit


@register_wrap
class SaveVersion(bpy.types.Panel, ToolPanel):
    """Save a version"""
    bl_idname = "BLENDGIT_PT_save_version"
    bl_label = "Save Version"

    bpy.types.WindowManager.commit_message = StringProperty(
        name="Comment",
        description="Commit message")

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        box = layout.box()

        lfs_data_update_async()

        commit_msg_row = box.row(align=True)
        commit_msg_row.prop(context.window_manager, "commit_message", text='')
        save_commit_button_row = box.row(align=True)
        save_commit_button_row.operator(SaveCommit.bl_idname)

        if not lfs.lfs_installed:
            # Tell user to install git-lfs, disable commit button
            save_commit_button_row.enabled = False
            row = box.row(align=True)
            row.label(text="Please install LFS",
                      icon="INFO")
        elif not lfs.lfs_initialized:
            # Disable commit button, tell user to initialize LFS
            save_commit_button_row.enabled = False
            row = box.row(align=True)
            row.label(text="Enable LFS for your project first!",
                      icon="INFO")
            row = box.row(align=True)
            row.operator(InitLfs.bl_idname)
