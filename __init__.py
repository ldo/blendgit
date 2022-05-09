#!/usr/bin/env python3
import logging

# import bpy

from . import common
# from .common import log

# from .ui.select_branch import SelectBranch
# from .ui.save_version import SaveVersion
from .ui.load_version import LoadVersion, LoadCommit

bl_info = {
    "name": "Blendgit",
    "author": "Nat Osaka",
    "version": (0, 8, 0),
    "blender": (3, 0, 0),
    "description": "Manage versions of a .blend file using Git",
    "warning": "",
    "wiki_url": "",
    "category": "System",
}


# class VersionControlMenu(bpy.types.Menu):
#     bl_idname = "file.version_control_menu"
#     bl_label = "Version Control"

#     def draw(self, context):
#         for op in (LoadVersion, SaveVersion, SelectBranch):
#             self.layout.operator(op.bl_idname, text=op.bl_label)


_classes = {
    LoadVersion,
    LoadCommit,
    # SaveVersion,
    # SelectBranch,
    # VersionControlMenu,
}

# def add_invoke_item(self, context):
#     self.layout.menu(VersionControlMenu.bl_idname)


logging.basicConfig(level=logging.INFO)
logging.getLogger('blender_id').setLevel(logging.DEBUG)
logging.getLogger('blender_cloud').setLevel(logging.DEBUG)


def register():
    common.register()


def unregister():
    common.unregister()
