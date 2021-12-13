bl_info = {
    "name": "Blendgit",
    "author": "Nat Osaka",
    "version": (0, 8, 0),
    "blender": (3, 0, 0),
    "location": "File > Version Control",
    "description": "manage versions of a .blend file using Git",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "System",
}

from . import common
from . import blendgit

in_blender, bpy = common.import_bpy()

_classes_ = (
    blendgit.LoadVersion,
    blendgit.SaveVersion,
    blendgit.SelectBranch,
    blendgit.VersionControlMenu,
)


def register():
    for _cls in _classes_:
        bpy.utils.register_class(_cls)

    bpy.types.TOPBAR_MT_file.append(blendgit.add_invoke_item)


def unregister():
    bpy.types.TOPBAR_MT_file.remove(blendgit.add_invoke_item)
    for _cls in _classes_:
        bpy.utils.unregister_class(_cls)


def main_test():
    output = blendgit.do_git(("status", "--porcelain")).rstrip()
    print(not output)


if __name__ == "__main__":
    register()
    if not in_blender:
        main_test()
