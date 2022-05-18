import bpy


class Data:
    """Data store capture class"""

    def __getattr__(self, name):
        val = None
        try:
            val = getattr(bpy.data.scenes[0], name)
        except AttributeError:
            val = self.__getattribute__(name)

        return val

    def __setattr__(self, name, value):
        setattr(bpy.types.Scene, name, value)


class ToolPanel:
    bl_category = "Git"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    # bl_options = {"DEFAULT_CLOSED"}
