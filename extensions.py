import bpy
from bpy.props import EnumProperty

from .tools.load_commit import get_commits


def register():
    bpy.types.WindowManager.commit = EnumProperty(
        items=get_commits,
        description="Which previously-saved commit to restore",
    )
