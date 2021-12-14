import os.path
import itertools

import common as cmn

_, bpy = cmn.import_bpy()


class SaveVersion(bpy.types.Operator):
    bl_idname = "file.version_control_save"
    bl_label = "Save Version..."

    comment: bpy.props.StringProperty(name="Comment")

    def draw(self, context):
        self.layout.prop(self, "comment", text="")

    def invoke(self, context, event):
        if cmn.doc_saved():
            result = context.window_manager.invoke_props_dialog(self)
        else:
            self.report({"ERROR"}, "Need to save the new document first")
            result = {"CANCELLED"}

        return result

    def execute(self, context):

        seen_filepaths = set()

        def process_item(item):
            # common processing for all externally-referenceable item types
            # other than nodes.
            if item.filepath not in seen_filepaths:
                seen_filepaths.add(item.filepath)
                filepath = item.filepath[2:]  # relative to .blend file
                subparent_dir = os.path.split(filepath)[0]
                if len(subparent_dir) != 0:
                    os.makedirs(os.path.join(
                        work_dir, subparent_dir), exist_ok=True)

                dst_path = os.path.join(work_dir, filepath)
                # keep relative path within work dir
                try:
                    os.link(os.path.join(parent_dir, filepath), dst_path)
                    # must be a hard link, else git commits the symlink
                except FileExistsError:
                    # in case of multiple references to file
                    pass

                cmn.add_files(files=[dst_path])
                # Git will quietly ignore this if file hasn’t changed

        def process_node(node):
            # looks for externally-referenced OSL scripts and IES parameters.
            if node.node_tree is not None:
                for subnode in node.node_tree.nodes:
                    if subnode.type == "GROUP":
                        # multiple references to a node group don’t matter,
                        # since process_item (above) automatically skips
                        # filepaths it has already seen.
                        process_node(subnode)
                    elif (isinstance
                          (subnode,
                            (bpy.types.ShaderNodeScript,
                             bpy.types.ShaderNodeTexIES)
                           )
                          and subnode.mode == "EXTERNAL"
                          ):
                        process_item(subnode)

        if self.comment.strip():
            repo_name = cmn.get_repo_name()
            cmn.setup_workdir()
            if not os.path.isdir(repo_name):
                cmn.do_git(("init",), saving=True)
                cmn.do_git(("config", "--unset", "core.worktree"),
                           saving=True)  # can get set for some reason

            bpy.ops.wm.save_as_mainfile(
                "EXEC_DEFAULT", filepath=bpy.data.filepath)
            parent_dir = os.path.split(bpy.data.filepath)[0]
            work_dir = cmn.get_workdir_name()
            os.link(bpy.data.filepath, os.path.join(
                work_dir, os.path.basename(bpy.data.filepath)))
            # must be a hard link, else git commits the symlink
            cmn.add_files(files=[os.path.basename(bpy.data.filepath)])
            for category, match, mismatch in (
                    ("fonts", {}, (("filepath", "<builtin>"),)),
                    ("images", {"type": "IMAGE"}, ()),
                    ("libraries", {}, ()),
                    ("sounds", {}, ())):
                for item in getattr(bpy.data, category):
                    if (item.packed_file is None
                        # not packed into .blend file
                        and item.filepath.startswith("//")
                        # must be relative to .blend file
                        and not item.filepath.startswith("//..")
                        # must not be at higher level than .blend file
                        and not any(getattr(item, k) == v
                                    for k, v in mismatch)
                            and all(getattr(item, k) == match[k]
                                    for k in match)):
                        process_item(item)

            for item in itertools.chain(bpy.data.materials, bpy.data.lights):
                process_node(item)

            for light in bpy.data.lights:
                process_node(light)

            cmn.do_git(("commit", "-m" + self.comment), saving=True)
            cmn.cleanup_workdir()
            result = {"FINISHED"}
        else:
            self.report({"ERROR"}, "Comment cannot be empty")
            result = {"CANCELLED"}

        return result
