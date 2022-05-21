import bpy

from threading import Thread
from shutil import which
from os.path import exists, join as path_join, split as path_split


from .register import register_wrap
from ..common import ui_refresh, do_git

reloading = False
update_needed = True
lfs_installed = True
lfs_initialized = True


@register_wrap
class InitLfs(bpy.types.Operator):
    bl_idname = "blendgit.init_lfs"
    bl_label = "Initialize LFS"

    def execute(self, context: bpy.types.Context):
        initialize_lfs(context)

        self.report({"INFO"}, "Successfully initialized LFS!")

        return {"FINISHED"}


def check_lfs_installed() -> bool:
    """Check if git-lfs is installed"""
    print("Checking if LFS is installed...")
    return which("git-lfs")


def check_lfs_initialized() -> bool:
    """Checks if LFS is initialized"""
    # This will return a list of files tracked by LFS
    # OR it will return an empty string, which can be checked
    # with the 'not' operator
    work_dir = path_split(bpy.data.filepath)[0]
    gitattributes_path = path_join(work_dir, '.gitattributes')
    if not exists(gitattributes_path):
        return False
    with open(gitattributes_path) as f:
        for line in f.readlines():
            if 'lfs' in line:
                return True

    return False


def initialize_lfs(context, extra_filetypes=()):
    """Initializes LFS with default binary filetypes"""
    global lfs_initialized
    filetypes = {
        # Models
        "*.fbx", "*.obj", "*.max", "*.blend", "*.blender", "*.dae", "*.mb",
        "*.ma", "*.3ds", "*.dfx", "*.c4d", "*.lwo", "*.lwo2", "*.abc",
        "*.3dm", "*.bin", "*.glb",
        # Images
        "*.jpg", "*.jpeg", "*.png", "*.apng", "*.atsc", "*.gif", "*.bmp",
        "*.exr", "*.tga", "*.tiff", "*.tif", "*.iff", "*.pict", "*.dds",
        "*.xcf", "*.leo", "*.kra", "*.kpp", "*.clip", "*.webm", "*.webp",
        "*.svg", "*.svgz", "*.psd",
        # Archives
        "*.zip", "*.7z", "*.gz", "*.rar", "*.tar",
        # Unity
        "*.meta", "*.unity", "*.unitypackage", "*.asset", "*.prefab",
        "*.mat", "*.anim", "*.controller", "*.overrideController",
        "*.physicMaterial", "*.physicsMaterial2D", "*.playable",
        "*.mask", "*.brush", "*.flare", "*.fontsettings", "*.guiskin",
        "*.giparams", "*.renderTexture", "*.spriteatlas", "*.terrainlayer",
        "*.mixer", "*.shadervariants", "*.preset", "*.asmdef",
        # User specified
        *extra_filetypes
    }
    do_git("lfs", "track", *filetypes)

    lfs_data_update(force_update=True)
    lfs_initialized = True

    ui_refresh()


def initialize_lfs_async():
    """Initializes LFS asyncronously"""
    thread = Thread(target=initialize_lfs)
    thread.start()


def lfs_data_update(force_update=False):
    """Checks LFS installed/initialized status"""
    global lfs_installed, lfs_initialized, update_needed
    if not update_needed and not force_update:
        return

    if not check_lfs_installed():
        print("Please install git-lfs")
        lfs_installed = False
    elif not check_lfs_initialized():
        print("Need to initialize git-lfs")
        lfs_initialized = False

    update_needed = False


def lfs_data_update_async():
    """Performs LFS checks asyncronously"""
    global reloading
    if reloading:
        return

    reloading = True

    thread = Thread(target=lfs_data_update)
    thread.start()
