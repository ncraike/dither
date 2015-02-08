import tempfile

import unittest

import dither.config.defaults
import dither.build.core
import dither.build.render
import dither.link
import dither.utils

from dither.di import di

from common import (
        DitherIntegrationTestCase,
        CreateDitherSandboxDirMixin,
        setup_test_dither_dir,
        create_test_template,
        create_test_context)

HOME_DIR_NAME = 'test_home_dir'
DITHER_DIR_NAME = 'test_dither_files'

BUILD_OUTPUT_SUBDIR_NAME = 'built_at_xxxx'
BUILD_OUTPUT_FILE_NAME = '.testfile'

LATEST_BUILD_SYMLINK_NAME = 'latest_build'
INSTALLED_BUILD_SYMLINK_NAME = 'installed_build'

def load_resource_providers():
    di.providers.clear()
    di.providers.load(
            dither.config.defaults.providers)
    di.providers.load(
            dither.utils.providers)
    di.providers.load(
            dither.build.core.providers)
    di.providers.load(
            dither.build.render.providers)

class TestLinkTestCase(
        CreateDitherSandboxDirMixin,
        DitherIntegrationTestCase):

    def setUp(self):
        load_resource_providers()

        self.create_dither_sandbox_dir()

        self._create_test_build_output()
        self._create_test_latest_build_symlink()

        self.installed_build_link_path = self.os.path.join(
            self.build_output_dir,
            INSTALLED_BUILD_SYMLINK_NAME)
        self.dot_dither_dotfiles_link_path = self.os.path.join(
                self.home_dir, ".dither_dotfiles")
        self.built_file_in_home_dir = self.os.path.join(
                self.home_dir, BUILD_OUTPUT_FILE_NAME)
        self.built_file_in_dither_dotfiles_dir = self.os.path.join(
                self.dot_dither_dotfiles_link_path, BUILD_OUTPUT_FILE_NAME)

        self.change_cwd_to_sandbox_dither_dir()

    def tearDown(self):
        di.providers.clear()

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
                home_dir=self.home_dir)

        self.assert_is_link_pointing_to(
                self.installed_build_link_path, self.build_output_subdir,
                "installed_build link doesn't point to latest build output")

class Test_dot_dither_dotfiles_link_created(TestLinkTestCase):

    def runTest(self):
        dither.link.link(
                base_build_dir=self.build_output_dir,
                home_dir=self.home_dir)

        self.assert_is_link_pointing_to(
                self.dot_dither_dotfiles_link_path, self.installed_build_link_path,
                "~/.dither_dotfiles link doesn't point to installed_build")

class Test_link_created_for_built_file(TestLinkTestCase):

    def runTest(self):
        dither.link.link(
                base_build_dir=self.build_output_dir,
                home_dir=self.home_dir)

        self.assert_is_link_pointing_to(
                self.built_file_in_home_dir, self.built_file_in_dither_dotfiles_dir,
                "~/{output_name!s} doesn't point to ~/.dither_dotfiles/"
                "{output_name!s}".format(output_name=BUILD_OUTPUT_FILE_NAME))

class Test_build_output_readable_in_home_dir(TestLinkTestCase):

    def runTest(self):
        dither.link.link(
                base_build_dir=self.build_output_dir,
                home_dir=self.home_dir)

        with open(self.built_file_in_home_dir, 'r') as f:
            build_output = f.read()
        self.assertEqual(build_output.strip(), 'Test build output',
                "Built file in home dir doesn't contain expected build output")

if __name__ == '__main__':
    unittest.main()
