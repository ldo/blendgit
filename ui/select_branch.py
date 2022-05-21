import bpy

from ..templates import ToolPanel
from ..tools.select_branch import SwitchBranch, CreateBranch, list_branches
from ..tools.register import register_wrap


@register_wrap
class SelectBranch(bpy.types.Panel, ToolPanel):
    """Select branch"""
    bl_idname = "BLENDGIT_PT_select_branch"
    bl_label = "Branches"

    bpy.types.WindowManager.branch = bpy.props.EnumProperty(
        items=list_branches,
        description="The local branches of the repo",
    )
    bpy.types.WindowManager.new_branch = bpy.props.StringProperty(
        description="The name of the branch to be created",
    )

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        row = box.row(align=True)
        row.prop(context.window_manager, "branch", text='')
        row = box.row(align=True)
        row.operator(SwitchBranch.bl_idname)

        box = layout.box()
        row = box.row(align=True)
        row.prop(context.window_manager, "new_branch", text='')
        row = box.row()
        row.operator(CreateBranch.bl_idname)
