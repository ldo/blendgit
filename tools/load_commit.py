import os.path
from threading import Thread

import bpy

from .register import register_wrap
from ..common import (do_git,
                      working_dir_clean,
                      get_repo_name,
                      format_compact_datetime,
                      ui_refresh)

commits_list = []


def get_main_branch() -> str:
    """Returns the main branch of the repo"""
    branches = do_git("branch").split('\n')
    branches = [branch.strip() for branch in branches]
    if 'main' in branches:
        return 'main'
    return 'master'


def which_branch() -> str:
    branch = None
    for line in do_git("branch").split("\n"):
        if "*" in line and "(" not in line:
            branch = line[2:].rstrip()
            break

    return branch


def list_commits(self=None, context=None):
    """Generates the menu items showing the commit history for the user to
    pick from."""
    last_commits_list = []
    repo_name = get_repo_name()
    main_branch = get_main_branch()
    current_branch = which_branch()
    if current_branch is None:
        current_branch = main_branch
    if os.path.isdir(repo_name):
        # Blender bug? Items in menu end up in reverse order from that in
        # my list
        last_commits_list = []
        for line in do_git(
                "log",
                "--format=%H %ct %s",
                "-n", "5",
                current_branch).split("\n"):
            if not line:
                continue
            for commit_entry in (line.split(" ", 2),):
                blender_list_entry = (
                    commit_entry[0],  # Commit hash
                    "%s: %s" % (format_compact_datetime(
                        int(commit_entry[1])),  # Commit time
                        commit_entry[2]),  # Commit description
                    ""  # Blender expects something here
                )
                last_commits_list.append(blender_list_entry)
    else:
        last_commits_list = [("", "No repo found", ""), ]

    return last_commits_list


def get_commits(self=None, context=None) -> list:
    global commits_list
    if not commits_list:
        commits_list = list_commits(self, context)
    return commits_list


def refresh_commit_list():
    global commits_list
    commits_list = list_commits()
    ui_refresh()


def refresh_commit_list_async():
    thread = Thread(target=refresh_commit_list)
    thread.start()


@register_wrap
class LoadCommit(bpy.types.Operator):
    bl_idname = "blendgit.load_commit"
    bl_label = "Load Commit"

    def execute(self, context: bpy.types.Context):
        if len(context.window_manager.commit) != 0:
            if not working_dir_clean():
                self.report({"ERROR"}, "Working directory not clean")
                return {"CANCELLED"}
            do_git("checkout", context.window_manager.commit)
            bpy.ops.wm.open_mainfile(
                "EXEC_DEFAULT", filepath=bpy.data.filepath)
            result = {"FINISHED"}
        else:
            result = {"CANCELLED"}

        return result
