#!/usr/bin/env python3
import sys
import os.path

from . import common as cmn

from .menu.select_branch import SelectBranch
from .menu.save_version import SaveVersion
from .menu.load_version import LoadVersion

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

# main_dir = os.path.join('..', os.path.dirname(__file__))

# if main_dir not in sys.path:
#     sys.path.append(main_dir)

in_blender, bpy = cmn.import_bpy()


class VersionControlMenu(bpy.types.Menu):
    bl_idname = "file.version_control_menu"
    bl_label = "Version Control"

    def draw(self, context):
        for op in (LoadVersion, SaveVersion, SelectBranch):
            self.layout.operator(op.bl_idname, text=op.bl_label)


_classes_ = (
    LoadVersion,
    SaveVersion,
    SelectBranch,
    VersionControlMenu,
)


def add_invoke_item(self, context):
    self.layout.menu(VersionControlMenu.bl_idname)


def register():
    for _cls in _classes_:
        bpy.utils.register_class(_cls)

    bpy.types.TOPBAR_MT_file.append(add_invoke_item)


def unregister():
    bpy.types.TOPBAR_MT_file.remove(add_invoke_item)
    for _cls in _classes_:
        bpy.utils.unregister_class(_cls)


def main_test():
    # output = cmn.do_git(("status", "--porcelain")).rstrip()
    print("Test")


if __name__ == "__main__":
    register()
    if not in_blender:
        main_test()
