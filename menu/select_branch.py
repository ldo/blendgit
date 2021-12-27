import os.path

from .. import common

bpy = common.import_bpy()


def list_branches(self=None, context=None):
    """Returns a list of branches to be passed to SelectBranch"""
    branches_list = []
    repo_name = common.get_repo_name()
    if os.path.isdir(repo_name):
        current_branch = common.do_git(
            ('rev-parse', '--abbrev-ref', 'HEAD')).rstrip()
        branches_list.append((current_branch, current_branch, ""))
        for branch in common.do_git(("branch", "--format=%(refname:short)")) \
                .split("\n"):
            if not branch:
                break
            elif branch == current_branch:
                continue
            branches_list.append((branch, branch, ""))
    else:
        branches_list = [("", "No repo found", ""), ]

    return branches_list


class SelectBranch(bpy.types.Operator):
    """Select branch"""
    bl_idname = "file.version_control_select_branch"
    bl_label = "Select branch..."

    branch: bpy.props.EnumProperty(
        items=list_branches,
        name="Branch",
        description="the local branches of the repo",
    )

    def draw(self, context):
        self.layout.prop(self, "branch")

    def invoke(self, context, event):
        is_saved = common.doc_saved()
        working_dir_is_clean = common.working_dir_clean()
        if not is_saved or not working_dir_is_clean:
            if not is_saved:
                err = "Need to save first"
            else:
                err = "Working directory must be clean (try saving)"
            self.report({"ERROR"}, err)
            return {"CANCELLED"}

        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        if len(self.branch) != 0:
            common.do_git(("checkout", self.branch))
            bpy.ops.wm.open_mainfile(
                "EXEC_DEFAULT", filepath=bpy.data.filepath)
            result = {"FINISHED"}
        else:
            result = {"CANCELLED"}

        return result
