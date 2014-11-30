import os
import unittest

import dither.build

from common import (
        DitherIntegrationTestCase,
        CreateDitherSandboxDirMixin,
        create_test_template,
        create_test_context,
        LATEST_BUILD_LINK_NAME,
        TEST_TEMPLATED_FILE_NAME)


def find_templated_file(build_output_dir):
    filepath = os.path.join(
            build_output_dir,
            LATEST_BUILD_LINK_NAME,
            TEST_TEMPLATED_FILE_NAME)
    if not os.path.exists(filepath):
        raise Exception("Can't find templated file at {!r}".format(filepath))
    return filepath

class Test_build_output_is_as_expected(
        CreateDitherSandboxDirMixin,
        DitherIntegrationTestCase):

    def setUp(self):
        self.create_dither_sandbox_dir()

        create_test_template(self.templates_dir)
        create_test_context(self.templates_dir)

        self.change_cwd_to_sandbox_dither_dir()

    def runTest(self):
        dither.build.build()

        templated_filepath = find_templated_file(self.build_output_dir)
        with open(templated_filepath, 'r') as f:
            contents = f.read()
        stripped_contents = '\n'.join(
                line.strip()
                for line in contents.splitlines()
                if line.strip())
        self.assertEqual(stripped_contents, '''\
sample output
this line should appear
My variable is Test value.''')

if __name__ == '__main__':
    unittest.main()
