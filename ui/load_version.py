import os
import os.path

import bpy

from . import ToolPanel

from .. import common


def get_main_branch() -> str:
    """Returns the main branch of the repo"""
    branches = common.do_git("branch").split('\n')
    branches = [branch.strip() for branch in branches]
    if 'main' in branches:
        return 'main'
    return 'master'


def list_commits(self=None, context=None):
    """Generates the menu items showing the commit history for the user to
    pick from."""
    last_commits_list = []
    repo_name = common.get_repo_name()
    main_branch = get_main_branch()
    if os.path.isdir(repo_name):
        # Blender bug? Items in menu end up in reverse order from that in
        # my list
        last_commits_list = [(main_branch, "(main branch)", "")]
        for line in common.do_git(
                "log",
                "--format=%H %ct %s",
                main_branch).split("\n"):
            if not line:
                continue
            for commit_entry in (line.split(" ", 2),):
                blender_list_entry = (
                    commit_entry[0],  # Commit hash
                    "%s: %s" % (common.format_compact_datetime(
                        int(commit_entry[1])),  # Commit time
                        commit_entry[2]),  # Commit description
                    ""  # Blender expects something here
                )
                last_commits_list.append(blender_list_entry)
    else:
        last_commits_list = [("", "No repo found", ""), ]

    return last_commits_list


class LoadCommit(bpy.types.Operator):
    bl_idname = "blendgit.commit"
    bl_label = "Load Commit"

    def execute(self, context):
        if len(context.scene.commit) != 0:
            if not common.working_dir_clean():
                self.report({"ERROR"}, "Working directory not clean")
                return {"CANCELLED"}
            common.do_git("checkout", context.scene.commit)
            bpy.ops.wm.open_mainfile(
                "EXEC_DEFAULT", filepath=bpy.data.filepath)
            result = {"FINISHED"}
        else:
            result = {"CANCELLED"}

        return result


class LoadVersion(bpy.types.Panel, ToolPanel):
    """Load a version"""
    bl_idname = "BLENDGIT_PT_load_version"
    bl_label = "Load Version"

    bpy.types.Scene.commit = bpy.props.EnumProperty(
        items=list_commits,
        name="LoadCommit",
        description="which previously-saved commit to restore",
    )

    def draw(self, context):
        layout = self.layout
        box = layout.box()

        row = box.row(align=True)
        row.prop(context.scene, "commit", text="")
        row = box.row(align=True)
        row.operator(LoadCommit.bl_idname)

    # def invoke(self, context, event):
    #     if common.doc_saved():
    #         result = context.window_manager.invoke_props_dialog(self)
    #     else:
    #         self.report({"ERROR"}, "Need to save the new document first")
    #         result = {"CANCELLED"}

    #     return result
