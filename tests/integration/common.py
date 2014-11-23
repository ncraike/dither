import os
import os.path

TEMPLATES_DIR = 'dither_templates'
BUILD_OUTPUT_DIR = 'built_dotfiles'
CONTEXT_NAME = 'template_context.py'
LATEST_BUILD_LINK_NAME = 'latest_build'

TEST_TEMPLATED_FILE_NAME = '.test'
TEST_TEMPLATE_NAME = TEST_TEMPLATED_FILE_NAME + '.template'

def setup_test_dither_dir(base_dir):
    templates_dir = os.path.join(base_dir, TEMPLATES_DIR)
    build_output_dir = os.path.join(base_dir, BUILD_OUTPUT_DIR)

    os.mkdir(templates_dir)
    os.mkdir(build_output_dir)

    return templates_dir, build_output_dir

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
