def import_bpy():
    try:
        import bpy
        in_blender = True
    except ImportError:
        from unittest.mock import MagicMock
        bpy = MagicMock()
        attrs = {'data.filepath': "./test.blend"}
        bpy.configure_mock(**attrs)
        in_blender = False

    return in_blender, bpy
