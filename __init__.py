#!/usr/bin/env python3
import logging

from bpy.utils import register_class, unregister_class
from bpy.types import Scene

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


from . import tools, extensions, ui


logging.basicConfig(level=logging.INFO)
logging.getLogger('blender_id').setLevel(logging.DEBUG)
logging.getLogger('blender_cloud').setLevel(logging.DEBUG)


def register():
    tools.register.order_classes()
    for cls in tools.register.__bl_classes:
        try:
            register_class(cls)
            print("Registered", cls.__name__)
        except ValueError:
            pass
    extensions.register()


def unregister():
    for cls in reversed(tools.register.__bl_ordered_classes):
        try:
            unregister_class(cls)
        except ValueError:
            pass
        except RuntimeError:
            pass


if __name__ == '__main__':
    register()
