import time
import os
import subprocess
import logging

import bpy

# from .tools.register import register_wrap


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


def ui_refresh():
    # A way to refresh the ui
    refreshed = False
    while not refreshed:
        if hasattr(bpy.data, 'window_managers'):
            for windowManager in bpy.data.window_managers:
                for window in windowManager.windows:
                    for area in window.screen.areas:
                        area.tag_redraw()
            refreshed = True
            print('Refreshed UI')
        else:
            time.sleep(0.1)


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
        ).decode('utf-8').strip()
