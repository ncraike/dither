
import unittest
from collections import namedtuple

from dither.di import di

# Module under test
import dither.build.core as build_core

def are_all_dependencies_met_for(dependent):
    di.resolver.resolve_all_dependencies(dependent)
    return True

class Test_get_build_output_subdir__gives_expected_output(
        unittest.TestCase):

    def setUp(self):
        di.providers.clear()
        self.expected_functions_called = []

        di.providers.mass_register({
            # The config values here are a little different to what we
            # use in production, to ensure we're actually asking the
            # config system and not just using our own constants which
            # happen to match the standard configured values.
            'config.build.output.base_dir_name': 'build_output_dir',
            'config.build.output.subdir_name_format':
                    'built_at_time_{timestamp}_by_dither',
            # We give a fixed timestamp here rather than asking the
            # system clock via the datetime module
            'utils.run_timestamp': '2000-01-01_06.30.59',
        })

        @di.providers.register('.org.python.stdlib.os.path')
        def give_fake_os_path():
            fake_os_path_module = namedtuple('fake_os_path', ['join'])
            def fake_join(left, right):
                return left + '/' + right

            return fake_os_path_module(
                    join=fake_join)

        @di.providers.register_instance('utils.ensure_dir_exists')
        def fake_ensure_dir_exists(dir_path):
            self.expected_functions_called.append(fake_ensure_dir_exists)
            return

    def runTest(self):
        self.assertTrue(are_all_dependencies_met_for(
                build_core.get_build_output_subdir))

        result = build_core.get_build_output_subdir()
        self.assertEqual(result,
                'build_output_dir/built_at_time_2000-01-01_06.30.59_by_dither')

        fake_ensure_dir_exists = (
                di.providers.resource_providers['utils.ensure_dir_exists'])()
        self.assertIn(fake_ensure_dir_exists, self.expected_functions_called)

    def tearDown(self):
        di.providers.clear()

if __name__ == '__main__':
    unittest.main()
