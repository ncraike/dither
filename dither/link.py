import os
import os.path

OUTPUT_DIR = 'built_dotfiles'
LATEST_BUILD_NAME = 'latest_build'

def _get_latest_build_subdir_from_link(build_dir):
    latest_build_link_path = os.path.join(OUTPUT_DIR, LATEST_BUILD_NAME)
    if (os.path.lexists(latest_build_link_path) and
            os.path.islink(latest_build_link_path)):
        link_target = os.rea


def find_latest_build_subdir(build_dir):
    # Latest `dither build` _should_ have created a symlink from `
    # `<build_dir>/latest_build` to the last
    # `<build_dir>/built_at_<timestamp>` subdirectory it made.
    # If this does exist, return its target
    # Otherwise, try to guess what the newest built `built_at_*` dir is
    # by sorting all of the `built_at_*` subdirs and using the last one.

def link(build_dir=None, home_dir=None):
    pass
