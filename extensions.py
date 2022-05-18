from bpy.types import Scene
from bpy.props import StringProperty, BoolProperty


def register():
    Scene.commit_message = StringProperty(
        name="Comment",
        description="Commit message")

    Scene.lfs_check_done = BoolProperty(
        name="LfsCheckDone")
