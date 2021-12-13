#!/usr/bin/env python3

"""
TODO: Separate into modules
"""

import os
import time
import itertools
import subprocess
import errno
import shutil

from . import common

_, bpy = common.import_bpy()


def format_compact_datetime(timestamp):
    # returns as brief as possible a human-readable display of the specified
    # date/time.
    then_items = time.localtime(timestamp)
    now = time.time()
    now_items = time.localtime(now)
    if abs(now - timestamp) < 86400:
        format = "%H:%M:%S"
    else:
        format = "%b-%d %H:%M"
        if then_items.tm_year != now_items.tm_year:
            format = "%Y " + format

    return \
        time.strftime(format, then_items)


def doc_saved():
    # has the current doc been saved at least once
    return len(bpy.data.filepath) != 0


def add_files(files=None):
    if files is None:
        do_git(("add", "-A"), saving=True)
        return True
    elif type(files) is not list:
        print("'files' must refer to a list (None for '-A')")
        return False
    do_git(("add", "--", *files), saving=True)
    return True


def working_dir_clean():
    return not do_git(("status", "--porcelain")).rstrip()


def get_repo_name():
    # name to use for the repo associated with this doc
    return ".git"


def get_workdir_name():
    # name to use for a temporary source tree directory for making commits
    # to the repo
    return ".work"


def setup_workdir():
    # creates a temporary work directory in which .git points to the actual
    # repo directory.
    work_dir = get_workdir_name()
    try:
        os.mkdir(work_dir)
    except OSError as why:
        if why.errno != errno.EEXIST:
            raise

    os.symlink(os.path.basename(get_repo_name()),
               os.path.join(work_dir, ".git"))
    # must be a symlink because it might not initially exist


def cleanup_workdir():
    # gets rid of the temporary work directory.
    shutil.rmtree(get_workdir_name())


def do_git(args, saving=False):
    # common routine for invoking various Git functions.
    env = dict(os.environ)
    if saving:
        # assume setup_workdir has been called
        env.pop("GIT_DIR", None)
        # Cannot use GIT_DIR, as that creates a bare repo, which cannot be
        # committed to.
        work_dir = get_workdir_name()
    else:
        # assume repo already exists, use parent directory of .blend file
        # as work dir
        work_dir = os.path.split(bpy.data.filepath)[0]
        env["GIT_DIR"] = get_repo_name()

    return \
        subprocess.check_output(
            args=("git",) + args,
            stdin=subprocess.DEVNULL,
            shell=False,
            cwd=work_dir,
            env=env
        ).decode('utf-8')


def list_commits(self=None, context=None):
    # generates the menu items showing the commit history for the user to
    # pick from.
    # global last_commits_list  # docs say Python must keep ref to strings
    last_commits_list = []
    repo_name = get_repo_name()
    if os.path.isdir(repo_name):
        # Blender bug? Items in menu end up in reverse order from that in
        # my list
        last_commits_list = list(
            (entry[0], "%s: %s" %
             (format_compact_datetime(int(entry[1])), entry[2]), "")
            for line in do_git(("log", "--format=%H %ct %s")).split("\n")
            if len(line) != 0
            for entry in (line.split(" ", 2),)
        )
    else:
        last_commits_list = [("", "No repo found", ""), ]

    return last_commits_list


def list_branches(self=None, context=None):
    branches_list = []
    repo_name = get_repo_name()
    if os.path.isdir(repo_name):
        current_branch = do_git(('rev-parse', '--abbrev-ref', 'HEAD')).rstrip()
        branches_list.append((current_branch, current_branch, ""))
        for branch in do_git(("branch", "--format=%(refname:short)")) \
                .split("\n"):
            if not branch:
                break
            elif branch == current_branch:
                continue
            branches_list.append((branch, branch, ""))
    else:
        branches_list = [("", "No repo found", ""), ]

    return branches_list


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
        if doc_saved():
            result = context.window_manager.invoke_props_dialog(self)
        else:
            self.report({"ERROR"}, "Need to save the new document first")
            result = {"CANCELLED"}

        return result

    # def modal(self, context, event)
    # doesn’t seem to be needed

    def execute(self, context):
        if len(self.commit) != 0:
            do_git(("checkout", "-f", self.commit, "."))
            bpy.ops.wm.open_mainfile(
                "EXEC_DEFAULT", filepath=bpy.data.filepath)
            result = {"FINISHED"}
        else:
            result = {"CANCELLED"}

        return result


class SaveVersion(bpy.types.Operator):
    bl_idname = "file.version_control_save"
    bl_label = "Save Version..."

    comment: bpy.props.StringProperty(name="Comment")

    def draw(self, context):
        self.layout.prop(self, "comment", text="")

    def invoke(self, context, event):
        if doc_saved():
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

                add_files(files=[dst_path])
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
            repo_name = get_repo_name()
            setup_workdir()
            if not os.path.isdir(repo_name):
                do_git(("init",), saving=True)
                do_git(("config", "--unset", "core.worktree"),
                       saving=True)  # can get set for some reason

            bpy.ops.wm.save_as_mainfile(
                "EXEC_DEFAULT", filepath=bpy.data.filepath)
            parent_dir = os.path.split(bpy.data.filepath)[0]
            work_dir = get_workdir_name()
            os.link(bpy.data.filepath, os.path.join(
                work_dir, os.path.basename(bpy.data.filepath)))
            # must be a hard link, else git commits the symlink
            add_files(files=[os.path.basename(bpy.data.filepath)])
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

            do_git(("commit", "-m" + self.comment), saving=True)
            cleanup_workdir()
            result = {"FINISHED"}
        else:
            self.report({"ERROR"}, "Comment cannot be empty")
            result = {"CANCELLED"}

        return result


class SelectBranch(bpy.types.Operator):
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
        is_saved = doc_saved()
        working_dir_is_clean = working_dir_clean()
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
            do_git(("checkout", self.branch))
            bpy.ops.wm.open_mainfile(
                "EXEC_DEFAULT", filepath=bpy.data.filepath)
            result = {"FINISHED"}
        else:
            result = {"CANCELLED"}

        return result


class VersionControlMenu(bpy.types.Menu):
    bl_idname = "file.version_control_menu"
    bl_label = "Version Control"

    def draw(self, context):
        for op in (LoadVersion, SaveVersion, SelectBranch):
            self.layout.operator(op.bl_idname, text=op.bl_label)


def add_invoke_item(self, context):
    self.layout.menu(VersionControlMenu.bl_idname)
