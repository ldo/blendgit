import os.path
import itertools

from .. import common

_, bpy = common.import_bpy()


def add_files(add_type=None, file=None) -> bool:
    """Adds files to staging"""
    if add_type not in ('all', 'category') and file is None:
        print("Type must be one of all/category, "
              + "or 'file' param must be set")
        return False
    if add_type == 'all':
        common.do_git(("add", "-A"))
    elif add_type == 'category':
        for category, match, mismatch in (
                ("fonts",     {},                (("filepath", "<builtin>"),)),
                ("images",    {"type": "IMAGE"}, ()),
                ("libraries", {},                ()),
                ("sounds",    {},                ())):
            for item in getattr(bpy.data, category):
                # not packed into .blend file
                if (item.packed_file is None
                        # must be relative to .blend file
                        and item.filepath.startswith("//")
                        # must not be at higher level than .blend file
                        and not item.filepath.startswith("//..")
                        # make sure there is no mismatch
                        and not any(getattr(item, k) == v
                                    for k, v in mismatch)
                        # make sure item has all match attributes
                        and all(getattr(item, k) == match[k]
                                for k in match)):
                    # We know the file is relative, remove prefix
                    relative_path = item.filepath[2:]
                    add_files(file=relative_path)
    elif file is not None:
        common.do_git(("add", "--", file))
    return True


# TODO: Offer to add LFS to repo
class SaveVersion(bpy.types.Operator):
    """Save a version"""
    bl_idname = "file.version_control_save"
    bl_label = "Save Version..."

    comment: bpy.props.StringProperty(name="Comment")
    add_lfs: bpy.props.BoolProperty(name="Add LFS")

    def draw(self, context):
        self.layout.prop(self, "add_lfs")
        self.layout.prop(self, "comment", text="")

    def invoke(self, context, event):
        if common.doc_saved():
            result = context.window_manager.invoke_props_dialog(self)
        else:
            self.report({"ERROR"}, "Need to save the new document first")
            result = {"CANCELLED"}

        return result

    def execute(self, context):
        if self.add_lfs:
            self.report({'INFO'}, "Adding LFS...")

        if self.comment.strip():
            repo_name = common.get_repo_name()
            if not os.path.isdir(repo_name):
                common.do_git(("init",))

            bpy.ops.wm.save_as_mainfile(
                "EXEC_DEFAULT", filepath=bpy.data.filepath)
            add_files(file=os.path.basename(bpy.data.filepath))
            add_files(add_type='category')

            common.do_git(("commit", "-m" + self.comment))
            result = {"FINISHED"}
        else:
            self.report({"ERROR"}, "Comment cannot be empty")
            result = {"CANCELLED"}

        return result
