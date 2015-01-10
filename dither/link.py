import os
import os.path
import re
import datetime

from dither.di import di

# Actual dependencies:
#  ...vary much more. Individual functions require and provide various
#  dependencies. Some satisfy each others.

# Dependencies include:
#  - prog_name and timestamp, or... a timestamped filename generator?
#  - build_output_base_dir: must exist, we'll search it for
#    latest_build_link_name
#  - installed_build_name, we'll use this with build_output_base_dir to
#    build a path where we create a symlink
#  - home_dir_link_name, we'll use this with the path to the user's home
#    directory

@di.dependsOn('config.build.output.latest_build_link_name')
def _get_latest_build_subdir_from_link(build_dir):
    latest_build_link_name = di.resolver.unpack(
            _get_latest_build_subdir_from_link)

    latest_build_link_path = os.path.join(
            build_dir, latest_build_link_name)
    if not (
            os.path.exists(latest_build_link_path) and
            os.path.islink(latest_build_link_path)):
        return None

    link_target = os.path.join(
            build_dir,
            os.readlink(latest_build_link_path))
    if not os.path.exists(link_target):
        return None

    return link_target

@di.dependsOn('config.build.output.subdir_name_prefix')
def _get_latest_build_subdir_by_file_sorting(build_dir):
    build_output_prefix = di.resolver.unpack(
            _get_latest_build_subdir_by_file_sorting)

    built_at_dirs = [
            name for name in os.listdir(build_dir)
            if name.startswith(build_output_prefix) and
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

@di.dependsOn('config.timestamp_format')
@di.dependsOn('config.moved_file_filename_format')
def move_to_timestamped_name(filepath):
    (timestamp_fmt, moved_file_filename_fmt
            ) = di.resolver.unpack(move_to_timestamped_name)

    timestamp = datetime.datetime.now().strftime(timestamp_fmt)
    new_filepath = moved_file_filename_fmt.format(
            original_name=filepath,
            timestamp=timestamp)
    os.rename(filepath, new_filepath)

def is_link_pointing_to_target(link_location, desired_target):
    if not os.path.exists(link_location):
        return False
    if not os.path.islink(link_location):
        return False

    raw_current_target = os.readlink(link_location)
    link_dir = os.path.dirname(link_location)
    abs_current_target = os.path.abspath(
            os.path.join(link_dir, raw_current_target))
    abs_desired_target = os.path.abspath(desired_target)

    return (abs_current_target == abs_desired_target)

def create_or_update_link(link_location, link_target, move_if_exists=False):
    # Test if link exists, even if it's broken
    if os.path.lexists(link_location):
        if is_link_pointing_to_target(link_location, link_target):
            # Nothing to do: link already exists and points to link_target
            return

        # Link exists. Either move it aside, or just delete it.
        if move_if_exists:
            move_to_timestamped_name(link_location)
        else:
            os.remove(link_location)

    # XXX TODO: Possible bug in that commonprefix works character-by-character,
    # and so may not always give valid directory names
    common_base_dir = os.path.commonprefix([link_location, link_target])
    relative_link_target = os.path.relpath(link_target, start=common_base_dir)

    os.symlink(relative_link_target, link_location)

def create_links_for_each_file_in_dir(
        dir_of_files_to_link_to, dir_to_make_links_in):

    for filename in os.listdir(dir_of_files_to_link_to):
        created_link_location = os.path.join(dir_to_make_links_in, filename)
        created_link_target = os.path.join(dir_of_files_to_link_to, filename)
        create_or_update_link(
                created_link_location,
                created_link_target,
                move_if_exists=True)

@di.dependsOn('config.link.installed_build_link_name')
@di.dependsOn('config.link.home_dir_link_name')
def link(base_build_dir=None, home_dir=None):
    (installed_build_link_name,
            home_dir_link_name
            ) = di.resolver.unpack(link)

    # Figure out what the latest build subdir is, usually by looking
    # for a "latest_build" symlink in build_dir
    latest_build_subdir = find_latest_build_subdir(base_build_dir)
    if latest_build_subdir is None:
        raise Exception(
                "Couldn't find latest build directory in {!r}".format(
                    base_build_dir))

    # Update "installed_build" link to point to latest build
    installed_build_link_path = os.path.join(
            base_build_dir, installed_build_link_name)
    create_or_update_link(installed_build_link_path, latest_build_subdir)

    # Update ~/.dither_dotfiles/ to point to installed_build
    home_dir_link_path = os.path.join(home_dir, home_dir_link_name)
    create_or_update_link(
            home_dir_link_path,
            os.path.abspath(installed_build_link_path),
            move_if_exists=True)

    # For each file in ~/.dither_dotfiles/, make a link from
    # ~/each_file to ~/.dither_dotfiles/eachfile
    create_links_for_each_file_in_dir(home_dir_link_path, home_dir)
