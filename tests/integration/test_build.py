import os
import os.path
import tempfile

import dither.build

from common import (
        setup_test_environment,
        LATEST_BUILD_LINK_NAME,
        TEST_TEMPLATED_FILE_NAME,
        TEST_TEMPLATE_NAME)

def find_templated_file(build_output_dir):
    filepath = os.path.join(
            build_output_dir,
            LATEST_BUILD_LINK_NAME,
            TEST_TEMPLATED_FILE_NAME)
    if not os.path.exists(filepath):
        raise Exception("Can't find templated file at {!r}".format(filepath))
    return filepath

def is_templated_content_correct(build_output_dir):
    templated_filepath = find_templated_file(build_output_dir)
    contents = open(templated_filepath, 'r').read()
    stripped_contents = '\n'.join(
            line.strip()
            for line in
            contents.splitlines()
            if line.strip())
    return bool(
            stripped_contents == '''\
sample output
this line should appear
My variable is Test value.''')

def test_build():
    sandbox_dir, templates_dir, build_output_dir = setup_test_environment()
    print("Sandbox is {!r}".format(sandbox_dir))
    os.chdir(sandbox_dir)

    dither.build.build()

    assert is_templated_content_correct(build_output_dir)

if __name__ == '__main__':
    test_build()
