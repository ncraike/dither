import os
import os.path
import tempfile

import dither.build

TEMPLATES_DIR = 'dither_templates'
BUILD_OUTPUT_DIR = 'built_dotfiles'
CONTEXT_NAME = 'template_context.py'
LATEST_BUILD_LINK_NAME = 'latest_build'

TEST_TEMPLATED_FILE_NAME = '.test'
TEST_TEMPLATE_NAME = TEST_TEMPLATED_FILE_NAME + '.template'

def create_test_sandbox_dir():
    sandbox_dir = tempfile.mkdtemp()
    templates_dir = os.path.join(sandbox_dir, TEMPLATES_DIR)
    build_output_dir = os.path.join(sandbox_dir, BUILD_OUTPUT_DIR)

    os.mkdir(templates_dir)
    os.mkdir(build_output_dir)

    return sandbox_dir, templates_dir, build_output_dir

def create_test_template(templates_dir):
    test_template_path = os.path.join(templates_dir, TEST_TEMPLATE_NAME)
    with open(test_template_path, 'w') as f:
        f.write('''\
sample output
{% if test_true %}
this line should appear
{% else %}
this line should not appear
{% endif %}

My variable is {{ test_var }}.

''')
    return test_template_path

def create_test_context(templates_dir):
    test_context_path = os.path.join(templates_dir, CONTEXT_NAME)
    with open(test_context_path, 'w') as f:
        f.write('''\
def get_context(**kwargs):
    return {
        'test_true': True,
        'test_var': 'Test value',
    }
''')
    return test_context_path


def setup_test_environment():
    sandbox_dir, templates_dir, build_output_dir = create_test_sandbox_dir()
    create_test_template(templates_dir)
    create_test_context(templates_dir)

    return sandbox_dir, templates_dir, build_output_dir

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
