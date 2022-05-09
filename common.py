import time
import os
import subprocess
import logging


def log(msg):
    logging.info(msg)


def import_bpy():
    """
    Import bpy if in Blender or mock if not
    """
    try:
        import bpy
    except ImportError:
        from unittest.mock import MagicMock
        bpy = MagicMock()
        attrs = {'data.filepath': "./test.blend"}
        bpy.configure_mock(**attrs)

    return bpy


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


def working_dir_clean():
    """Checks if working dir is clean"""
    return not do_git("status",
                      "--porcelain",
                      "--untracked-files=no").rstrip()


def get_repo_name():
    """Gets name to use for the repo associated with this doc"""
    return ".git"


def register(to_register=None):
    if to_register is None:
        from . import _classes
        to_register = _classes
    try:
        for _cls in to_register:
            log(f"Registering {_cls.__name__}")
            if _cls not in _classes:
                _classes.add(_cls)
            bpy.utils.register_class(_cls)
    except Exception:
        unregister()


def unregister():
    from . import _classes
    for _cls in _classes:
        try:
            bpy.utils.unregister_class(_cls)
        except Exception:
            pass


def do_git(*args):
    """Common routine for invoking various Git functions."""
    env = dict(os.environ)
    work_dir = os.path.split(bpy.data.filepath)[0]
    env["GIT_DIR"] = get_repo_name()

    return \
        subprocess.check_output(
            args=("git", *args),
            stdin=subprocess.DEVNULL,
            shell=False,
            cwd=work_dir,
            env=env
        ).decode('utf-8')


bpy = import_bpy()
