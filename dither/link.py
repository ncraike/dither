import os
import os.path
import re

BASE_BUILD_DIR = 'built_dotfiles'
LATEST_BUILD_NAME = 'latest_build'
BUILT_AT_PREFIX = 'built_at_'
INSTALLED_BUILD_NAME = 'installed_build'

def _get_latest_build_subdir_from_link(build_dir):
    latest_build_link_path = os.path.join(build_dir, LATEST_BUILD_NAME)
    if not (
            os.path.lexists(latest_build_link_path) and
            os.path.islink(latest_build_link_path)):
        print("Returning because latest_build link can't be found")
        import IPython; IPython.embed()
        return None

    link_target = os.path.join(
            build_dir,
            os.readlink(latest_build_link_path))
    if not os.path.lexists(link_target):
        print("Returning because latest_build link target doesn't exist")
        import IPython; IPython.embed()
        return None

    return link_target

def _get_latest_build_subdir_by_file_sorting(build_dir):
    built_at_dirs = [
            name for name in os.listdir(build_dir)
            if name.startswith(BUILT_AT_PREFIX) and
                os.path.isdir(os.path.join(build_dir, name))]
    if not built_at_dirs:
        return None

    built_at_dirs.sort()
    return os.path.join(build_dir, built_at_dirs[-1])

def find_latest_build_subdir(build_dir):
    # Latest `dither build` _should_ have created a symlink from `
    # `<build_dir>/latest_build` to the last
    # `<build_dir>/built_at_<timestamp>` subdirectory it made.
    # If this does exist, return its target
    # Otherwise, try to guess what the newest built `built_at_*` dir is
    # by sorting all of the `built_at_*` subdirs and using the last one.
    for strategy in (
            _get_latest_build_subdir_from_link,
            _get_latest_build_subdir_by_file_sorting):
        result = strategy(build_dir)
        if result is not None:
            return result
    else:
        return None

def create_or_update_link(link_location, link_target):
    if os.path.exists(link_location):
        os.remove(link_location)

    common_base_dir = os.path.commonprefix([link_location, link_target])
    relative_link_target = os.path.relpath(link_target, start=common_base_dir)

    os.symlink(relative_link_target, link_location)

def link(base_build_dir=None, home_dir=None):
    latest_build_subdir = find_latest_build_subdir(base_build_dir)
    if latest_build_subdir is None:
        raise Exception(
                "Couldn't find latest build directory in {!r}".format(
                    base_build_dir))

    # Update "installed_build" link to point to latest build
    create_or_update_link(
            os.path.join(base_build_dir, INSTALLED_BUILD_NAME),
            latest_build_subdir)
