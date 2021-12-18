import time
import os
import shutil
import subprocess
import errno


def import_bpy():
    """
    Import bpy if in Blender or mock if not
    """
    try:
        import bpy
        in_blender = True
    except ImportError:
        from unittest.mock import MagicMock
        bpy = MagicMock()
        attrs = {'data.filepath': "./test.blend"}
        bpy.configure_mock(**attrs)
        in_blender = False

    return in_blender, bpy


def format_compact_datetime(timestamp):
    """
    Returns as brief as possible a human-readable display of the specified
    date/time.
    """
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
    """Checks if the current doc been saved at least once"""
    return len(bpy.data.filepath) != 0


def add_files(files=None):
    """Adds files to staging"""
    if files is None:
        do_git(("add", "-A"), saving=True)
        return True
    elif type(files) is not list:
        print("'files' must refer to a list (None for '-A')")
        return False
    do_git(("add", "--", *files), saving=True)
    return True


def working_dir_clean():
    """Checks if working dir is clean"""
    return not do_git(("status", "--porcelain")).rstrip()


def get_repo_name():
    """Gets name to use for the repo associated with this doc"""
    return ".git"


def get_workdir_name():
    """
    Name to use for a temporary source tree directory for making commits
    to the repo
    """
    return ".work"


def setup_workdir():
    """
    Creates a temporary work directory in which .git points to the actual
    repo directory.
    """
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
    """Gets rid of the temporary work directory."""
    shutil.rmtree(get_workdir_name())


def do_git(args, saving=False):
    """Common routine for invoking various Git functions."""
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


_, bpy = import_bpy()
