import os
import tempfile

import dither.link

from common import (
        setup_test_dither_dir,
        create_test_template,
        create_test_context)

HOME_DIR_NAME = 'test_home_dir'
DITHER_DIR_NAME = 'test_dither_files'

BUILD_OUTPUT_SUBDIR_NAME = 'built_at_xxxx'
BUILD_OUTPUT_FILE_NAME = '.testfile'

LATEST_BUILD_SYMLINK_NAME = 'latest_build'
INSTALLED_BUILD_SYMLINK_NAME = 'installed_build'

def resolve_symlink(symlink_path):
    raw_link_target = os.readlink(symlink_path)
    link_dir = os.path.dirname(symlink_path)
    return os.path.join(link_dir, raw_link_target)

def get_build_output_subdir(build_output_dir):
    return os.path.join(
            build_output_dir,
            BUILD_OUTPUT_SUBDIR_NAME)

def get_installed_build_link_path(build_output_dir):
    return os.path.join(
            build_output_dir,
            INSTALLED_BUILD_SYMLINK_NAME)

def create_test_build_output(build_output_dir):
    build_output_subdir = get_build_output_subdir(build_output_dir)
    os.mkdir(build_output_subdir)
    
    build_output_file_path = os.path.join(
            build_output_subdir, BUILD_OUTPUT_FILE_NAME)
    with open(build_output_file_path, 'w') as f:
        f.write('''\
Test build output
''')

def create_test_latest_build_symlink(build_output_dir):
    symlink_path = os.path.join(
            build_output_dir, LATEST_BUILD_SYMLINK_NAME)
    os.symlink(BUILD_OUTPUT_SUBDIR_NAME, symlink_path)

def setup_test_environment():
    sandbox_dir = tempfile.mkdtemp()
    home_path = os.path.join(sandbox_dir, HOME_DIR_NAME)
    os.mkdir(home_path)

    test_dither_path = os.path.join(home_path, DITHER_DIR_NAME)
    os.mkdir(test_dither_path)

    templates_dir, build_output_dir = setup_test_dither_dir(test_dither_path)

    create_test_build_output(build_output_dir)
    create_test_latest_build_symlink(build_output_dir)

    return (sandbox_dir, home_path, test_dither_path, templates_dir,
            build_output_dir)

def test_link():
    (sandbox_dir, home_path, test_dither_path, templates_dir,
            build_output_dir) = setup_test_environment()
    build_output_subdir = get_build_output_subdir(build_output_dir)

    print("Sandbox is {!r}".format(sandbox_dir))
    os.chdir(test_dither_path)

    dither.link.link(
            base_build_dir=build_output_dir,
            home_dir=home_path)

    installed_build_link_path = get_installed_build_link_path(build_output_dir)
    dither_dotfiles_link_path = os.path.join(
            home_path, ".dither_dotfiles")
    built_file_in_home_dir = os.path.join(
            home_path, BUILD_OUTPUT_FILE_NAME)
    built_file_in_dither_dotfiles_dir = os.path.join(
            dither_dotfiles_link_path, BUILD_OUTPUT_FILE_NAME)

    assert_link_exists_and_points_to(
            installed_build_link_path, build_output_subdir,
            "installed_build link doesn't point to latest build output")

    assert_link_exists_and_points_to(
            dither_dotfiles_link_path, installed_build_link_path,
            "~/.dither_dotfiles link doesn't point to installed_build")

    assert_link_exists_and_points_to(
            built_file_in_home_dir, built_file_in_dither_dotfiles_dir,
            "~/{output_name!s} doesn't point to ~/.dither_dotfiles/"
            "{output_name!s}".format(output_name=BUILD_OUTPUT_FILE_NAME))

    assert_contents_of_built_file_in_home(built_file_in_home_dir)

def assert_link_exists_and_points_to(
        link_path, desired_target, message_on_link_not_exists):
    assert os.path.exists(link_path), "{!r} doesn't exist".format(link_path)
    assert os.path.islink(link_path), "{!r} isn't a symlink".format(link_path)
    assert_link_points_to(
            link_path, desired_target, message_on_link_not_exists)

def assert_link_points_to(
        link_path, desired_target, message_on_assert_failure):
    resolved_link_target = resolve_symlink(link_path)
    assert os.path.samefile(resolved_link_target, desired_target), (
            message_on_assert_failure)

def assert_contents_of_built_file_in_home(built_file_in_home_dir):
    build_output = open(built_file_in_home_dir, 'r').read()
    assert build_output.strip() == 'Test build output', (
            "Built file in home dir doesn't contain expected build output")

if __name__ == '__main__':
    test_link()
