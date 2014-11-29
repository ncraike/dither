import tempfile

import unittest

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

def resolve_symlink(symlink_path, os_module=None):
    if os_module is None:
        import os as os_module
    raw_link_target = os_module.readlink(symlink_path)
    link_dir = os_module.path.dirname(symlink_path)
    return os_module.path.join(link_dir, raw_link_target)

class TestLinkTestCase(unittest.TestCase):

    def __init__(self, *args, os_module=None, safe_repr_func=None, **kwargs):
        if os_module is None:
            import os as os_module
        self.os = os_module

        if safe_repr_func is None:
            from unittest.util import safe_repr as safe_repr_func
        self.safe_repr = safe_repr_func

        super().__init__(*args, **kwargs)

    def format_fail_msg(self, custom_msg, default_msg):
        return self._formatMessage(custom_msg, default_msg)

    def failure_exception_with_msg(self, custom_msg, default_msg):
        formatted_msg = self.format_fail_msg(custom_msg, default_msg)
        return self.failureException(formatted_msg)

    def assert_is_link_pointing_to(
            self, link_path, expected_link_target, custom_fail_msg=None):
        self.assert_is_link(link_path, custom_fail_msg)
        self.assert_link_points_to(
                link_path, expected_link_target, custom_fail_msg)

    def assert_is_link(self, link_path, custom_fail_msg=None):
        exists = self.os.path.exists(link_path)
        if not exists:
            raise self.failure_exception_with_msg(
                    custom_msg=custom_fail_msg,
                    default_msg="{} does not exist".format(
                        self.safe_repr(link_path)))

        is_link = self.os.path.islink(link_path)
        if not is_link:
            raise self.failure_exception_with_msg(
                    custom_msg=custom_fail_msg,
                    default_msg="{} is not a symbolic link".format(
                        self.safe_repr(link_path)))

    def assert_link_points_to(
            self, link_path, expected_link_target, custom_fail_msg=None):
        resolved_link_target = resolve_symlink(link_path, os_module=self.os)
        points_to = self.os.path.samefile(
                resolved_link_target, expected_link_target)
        if not points_to:
            raise self.failure_exception_with_msg(
                    custom_msg=custom_fail_msg,
                    default_msg="Link at {} doesn't point to {}".format(
                        self.safe_repr(link_path),
                        self.safe_repr(expected_link_target)))

    def setUp(self):
        self.sandbox_dir = tempfile.mkdtemp()
        self.home_path = self.os.path.join(self.sandbox_dir, HOME_DIR_NAME)
        self.os.mkdir(self.home_path)

        self.test_dither_path = self.os.path.join(self.home_path, DITHER_DIR_NAME)
        self.os.mkdir(self.test_dither_path)

        self.templates_dir, self.build_output_dir = setup_test_dither_dir(
                self.test_dither_path)

        self.build_output_subdir = self.os.path.join(
            self.build_output_dir,
            BUILD_OUTPUT_SUBDIR_NAME)
        self._create_test_build_output()
        self._create_test_latest_build_symlink()

        self.installed_build_link_path = self.os.path.join(
            self.build_output_dir,
            INSTALLED_BUILD_SYMLINK_NAME)
        self.dot_dither_dotfiles_link_path = self.os.path.join(
                self.home_path, ".dither_dotfiles")
        self.built_file_in_home_dir = self.os.path.join(
                self.home_path, BUILD_OUTPUT_FILE_NAME)
        self.built_file_in_dither_dotfiles_dir = self.os.path.join(
                self.dot_dither_dotfiles_link_path, BUILD_OUTPUT_FILE_NAME)

        self.os.chdir(self.test_dither_path)

    def _create_test_build_output(self):
        self.os.mkdir(self.build_output_subdir)
        self.build_output_file_path = self.os.path.join(
                self.build_output_subdir, BUILD_OUTPUT_FILE_NAME)
        with open(self.build_output_file_path, 'w') as f:
            f.write('Test build output\n')

    def _create_test_latest_build_symlink(self):
        symlink_path = self.os.path.join(
                self.build_output_dir, LATEST_BUILD_SYMLINK_NAME)
        self.os.symlink(BUILD_OUTPUT_SUBDIR_NAME, symlink_path)

class Test_installed_build_link_created(TestLinkTestCase):

    def runTest(self):
        dither.link.link(
                base_build_dir=self.build_output_dir,
                home_dir=self.home_path)

        self.assert_is_link_pointing_to(
                self.installed_build_link_path, self.build_output_subdir,
                "installed_build link doesn't point to latest build output")

class Test_dot_dither_dotfiles_link_created(TestLinkTestCase):

    def runTest(self):
        dither.link.link(
                base_build_dir=self.build_output_dir,
                home_dir=self.home_path)

        self.assert_is_link_pointing_to(
                self.dot_dither_dotfiles_link_path, self.installed_build_link_path,
                "~/.dither_dotfiles link doesn't point to installed_build")

class Test_link_created_for_built_file(TestLinkTestCase):

    def runTest(self):
        dither.link.link(
                base_build_dir=self.build_output_dir,
                home_dir=self.home_path)

        self.assert_is_link_pointing_to(
                self.built_file_in_home_dir, self.built_file_in_dither_dotfiles_dir,
                "~/{output_name!s} doesn't point to ~/.dither_dotfiles/"
                "{output_name!s}".format(output_name=BUILD_OUTPUT_FILE_NAME))

class Test_build_output_readable_in_home_dir(TestLinkTestCase):

    def runTest(self):
        dither.link.link(
                base_build_dir=self.build_output_dir,
                home_dir=self.home_path)

        with open(self.built_file_in_home_dir, 'r') as f:
            build_output = f.read()
        self.assertEqual(build_output.strip(), 'Test build output',
                "Built file in home dir doesn't contain expected build output")

if __name__ == '__main__':
    unittest.main()
