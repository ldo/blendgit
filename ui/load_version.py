import bpy

from .templates import ToolPanel

from ..tools.register import register_wrap
from ..tools.load_commit import LoadCommit


@register_wrap
class LoadVersion(bpy.types.Panel, ToolPanel):
    """Load a version"""
    bl_idname = "BLENDGIT_PT_load_version"
    bl_label = "Load Version"

    def draw(self, context: bpy.types.Context):
        layout = self.layout
        box = layout.box()

        row = box.row(align=True)
        row.prop(context.window_manager, "commit", text="")
        row = box.row(align=True)
        row.operator(LoadCommit.bl_idname)
