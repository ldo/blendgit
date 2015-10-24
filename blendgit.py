#+
# This add-on script for Blender 2.7x manages revisions of a Blender document
# and associated files using a Git repository. It adds a “Version Control”
# submenu to the File menu, with “Load Version...” and “Save Version...”
# menu items; the latter can be used in place of the standard “Save” action,
# popping up a dialog asking the user for a commit message and saving the
# file as a new commit in the Git repo. (You can still use the normal “Save”
# action to save a new working copy of the .blend file without committing it
# to the repo.) The “Load Version...” action displays a popup menu listing all
# the versions of the file you previously saved to the repo, and lets you choose
# one to replace the current working copy.
#
# I’d love to use the Dulwich library <http://www.samba.org/~jelmer/dulwich/> to
# interface to Git, but unfortunately that doesn’t seem to be available for
# Python 3.x yet. So for now all interfacing to Git is done by spawning
# the command-line programs.
#
# Copyright 2012, 2015 Lawrence D’Oliveiro <ldo@geek-central.gen.nz>.
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#-

import os
import time
import subprocess
import errno
import shutil
import bpy

bl_info = \
    {
        "name" : "Blendgit",
        "author" : "Lawrence D’Oliveiro <ldo@geek-central.gen.nz>",
        "version" : (0, 5, 0),
        "blender" : (2, 7, 4),
        "location" : "File > Version Control",
        "description" : "manage versions of a .blend file using Git",
        "warning" : "",
        "wiki_url" : "",
        "tracker_url" : "",
        "category" : "System",
    }

def format_compact_datetime(timestamp) :
    # returns as brief as possible a human-readable display of the specified date/time.
    then_items = time.localtime(timestamp)
    now = time.time()
    now_items = time.localtime(now)
    if abs(now - timestamp) < 86400 :
        format = "%H:%M:%S"
    else :
        format = "%b-%d %H:%M"
        if then_items.tm_year != now_items.tm_year :
            format = "%Y " + format
        #end if
    #end if
    return \
        time.strftime(format, then_items)
#end format_compact_datetime

def doc_saved() :
    # has the current doc been saved at least once
    return len(bpy.data.filepath) != 0
#end doc_saved

def get_repo_name() :
    # name to use for the repo associated with this doc
    return bpy.data.filepath + ".git"
#end get_repo_name

def get_workdir_name() :
    # name to use for a temporary source tree directory for making commits to the repo
    return bpy.data.filepath + ".work"
#end get_workdir_name

def setup_workdir() :
    # creates a temporary work directory in which .git points to the actual
    # repo directory.
    work_dir = get_workdir_name()
    try :
        os.mkdir(work_dir)
    except OSError as why :
        if why.errno != errno.EEXIST :
            raise
        #end if
    #end try
    os.symlink("../" + os.path.basename(get_repo_name()), os.path.join(work_dir, ".git"))
      # must be a symlink because it might not initially exist
#end setup_workdir

def cleanup_workdir() :
    # gets rid of the temporary work directory.
    shutil.rmtree(get_workdir_name())
#end cleanup_workdir

def do_git(args, saving = False) :
    # common routine for invoking various Git functions.
    env = dict(os.environ)
    if saving :
        # assume setup_workdir has been called
        env.pop("GIT_DIR", None)
        # Cannot use GIT_DIR, as that creates a bare repo, which cannot be committed to.
        work_dir = get_workdir_name()
        env = None
    else :
        # assume repo already exists, use parent directory of .blend file as work dir
        work_dir = os.path.split(bpy.data.filepath)[0]
        env["GIT_DIR"] = get_repo_name()
    #end if
    return \
        subprocess.check_output \
          (
            args = ("git",) + args,
            stdin = subprocess.DEVNULL,
            shell = False,
            cwd = work_dir,
            env = env
          )
#end do_git

def list_commits(self, context) :
    # generates the menu items showing the commit history for the user to pick from.
    global last_commits_list # docs say Python must keep ref to strings
    repo_name = get_repo_name()
    if os.path.isdir(repo_name) :
        # Blender bug? Items in menu end up in reverse order from that in my list
        last_commits_list = list \
          (
            (entry[0], "%s: %s" % (format_compact_datetime(int(entry[1])), entry[2]), "")
                for line in do_git(("log", "--format=%H %ct %s")).decode("utf-8").split("\n")
                if len(line) != 0
                for entry in (line.split(" ", 2),)
          )
    else :
        last_commits_list = [("", "No repo found", ""),]
    #end if
    return last_commits_list
#end list_commits

class LoadVersion(bpy.types.Operator) :
    bl_idname = "file.version_control_load"
    bl_label = "Load Version..."

    commit = bpy.props.EnumProperty \
      (
        items = list_commits,
        name = "Commit",
        description = "which previously-saved commit to restore",
      )

    def draw(self, context) :
        self.layout.prop(self, "commit")
    #end draw

    def invoke(self, context, event):
        if doc_saved() :
            result = context.window_manager.invoke_props_dialog(self)
        else :
            self.report({"ERROR"}, "Need to save the new document first")
            result = {"CANCELLED"}
        #end if
        return result
    #end invoke

    # def modal(self, context, event)
      # doesn’t seem to be needed

    def execute(self, context) :
        if len(self.commit) != 0 :
            basename = os.path.basename(bpy.data.filepath)
            do_git(("checkout", "-f", self.commit, "."))
            bpy.ops.wm.open_mainfile("EXEC_DEFAULT", filepath = bpy.data.filepath)
            result = {"FINISHED"}
        else :
            result = {"CANCELLED"}
        #end if
        return result
    #end execute

#end LoadVersion

class SaveVersion(bpy.types.Operator) :
    bl_idname = "file.version_control_save"
    bl_label = "Save Version..."

    comment = bpy.props.StringProperty(name = "Comment")

    def draw(self, context) :
        self.layout.prop(self, "comment", "")
    #end draw

    def invoke(self, context, event):
        if doc_saved() :
            result = context.window_manager.invoke_props_dialog(self)
        else :
            self.report({"ERROR"}, "Need to save the new document first")
            result = {"CANCELLED"}
        #end if
        return result
    #end invoke

    def execute(self, context) :
        if len(self.comment.strip()) != 0 :
            repo_name = get_repo_name()
            setup_workdir()
            if not os.path.isdir(repo_name) :
                do_git(("init",), saving = True)
                do_git(("config", "--unset", "core.worktree"), saving = True) # can get set for some reason
            #end if
            bpy.ops.wm.save_as_mainfile("EXEC_DEFAULT", filepath = bpy.data.filepath)
            parent_dir = os.path.split(bpy.data.filepath)[0]
            work_dir = get_workdir_name()
            os.link(bpy.data.filepath, os.path.join(work_dir, os.path.basename(bpy.data.filepath)))
              # must be a hard link, else git commits the symlink
            do_git(("add", "--", os.path.basename(bpy.data.filepath)), saving = True)
            for \
                category, match, mismatch \
            in \
                (
                    ("images", {"type" : "IMAGE"}, ()),
                    ("libraries", {}, ()),
                    ("fonts", {}, (("filepath" , "<builtin>"),)),
                    ("sounds", {}, ()),
                ) \
            :
                for item in getattr(bpy.data, category) :
                    if (
                            item.packed_file == None
                              # not packed into .blend file
                        and
                            item.filepath.startswith("//")
                              # must be relative to .blend file
                        and
                            not item.filepath.startswith("//..")
                              # must not be at higher level than .blend file
                        and
                            not any(getattr(item, k) == v for k, v in mismatch)
                        and
                            all(getattr(item, k) == match[k] for k in match)
                    ) :
                        filepath = item.filepath[2:] # relative to .blend file
                        subparent_dir = os.path.split(filepath)[0]
                        if len(subparent_dir) != 0 :
                            os.makedirs(os.path.join(work_dir, subparent_dir), exist_ok = True)
                        #end if
                        dst_path = os.path.join(work_dir, filepath)
                          # keep relative path within work dir
                        os.link(os.path.join(parent_dir, filepath), dst_path)
                          # must be a hard link, else git commits the symlink
                        do_git(("add", "--", dst_path), saving = True)
                          # Git will quietly ignore this if file hasn’t changed
                    #end if
                #end for
            #end if
            do_git(("commit", "-m" + self.comment), saving = True)
            cleanup_workdir()
            result = {"FINISHED"}
        else :
            self.report({"ERROR"}, "Comment cannot be empty")
            result = {"CANCELLED"}
        #end if
        return result
    #end execute

#end SaveVersion

class VersionControlMenu(bpy.types.Menu) :
    bl_idname = "file.version_control_menu"
    bl_label = "Version Control"

    def draw(self, context) :
        for op in (LoadVersion, SaveVersion) :
            self.layout.operator(op.bl_idname, text = op.bl_label)
        #end for
    #end draw

#end VersionControlMenu

def add_invoke_item(self, context) :
    self.layout.menu(VersionControlMenu.bl_idname)
#end add_invoke_item

def register() :
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_file.append(add_invoke_item)
#end register

def unregister() :
    bpy.types.INFO_MT_file.remove(add_invoke_item)
    bpy.utils.unregister_module(__name__)
#end unregister

if __name__ == "__main__" :
    register()
#end if
