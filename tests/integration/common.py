import os

import unittest

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

def resolve_symlink(symlink_path, os_module=None):
    if os_module is None:
        import os as os_module
    raw_link_target = os_module.readlink(symlink_path)
    link_dir = os_module.path.dirname(symlink_path)
    return os_module.path.join(link_dir, raw_link_target)

class DitherIntegrationTestCase(unittest.TestCase):

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
