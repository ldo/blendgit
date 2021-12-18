import os.path

import common

_, bpy = common.import_bpy()


def list_commits(self=None, context=None):
    # generates the menu items showing the commit history for the user to
    # pick from.
    # global last_commits_list  # docs say Python must keep ref to strings
    last_commits_list = []
    repo_name = common.get_repo_name()
    if os.path.isdir(repo_name):
        # Blender bug? Items in menu end up in reverse order from that in
        # my list
        last_commits_list = list(
            (entry[0], "%s: %s" %
             (common.format_compact_datetime(int(entry[1])), entry[2]), "")
            for line in common.do_git(("log", "--format=%H %ct %s"))
                              .split("\n")
            if len(line) != 0
            for entry in (line.split(" ", 2),)
        )
    else:
        last_commits_list = [("", "No repo found", ""), ]

    return last_commits_list


class LoadVersion(bpy.types.Operator):
    bl_idname = "file.version_control_load"
    bl_label = "Load Version..."

    commit: bpy.props.EnumProperty(
        items=list_commits,
        name="Commit",
        description="which previously-saved commit to restore",
    )

    def draw(self, context):
        self.layout.prop(self, "commit")

    def invoke(self, context, event):
        if common.doc_saved():
            result = context.window_manager.invoke_props_dialog(self)
        else:
            self.report({"ERROR"}, "Need to save the new document first")
            result = {"CANCELLED"}

        return result

    # def modal(self, context, event)
    # doesn’t seem to be needed

    def execute(self, context):
        if len(self.commit) != 0:
            common.do_git(("checkout", "-f", self.commit, "."))
            bpy.ops.wm.open_mainfile(
                "EXEC_DEFAULT", filepath=bpy.data.filepath)
            result = {"FINISHED"}
        else:
            result = {"CANCELLED"}

        return result
