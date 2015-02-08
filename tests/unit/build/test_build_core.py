
from collections import namedtuple

import pytest

from dither.di import di

# Module under test
import dither.build.core as build_core

def are_all_dependencies_met_for(dependent):
    di.resolver.resolve_all_dependencies(dependent)
    return True

@pytest.fixture(scope='function')
def di_providers(request):
    di.providers.clear()
    return di.providers

@pytest.fixture
def functions_called():
    return []

def test_get_build_output_subdir__gives_expected_output(
        di_providers, functions_called):

    di_providers.mass_register({
        # The config values here are a little different to what are
        # used in production, to ensure the code under test is
        # actually asking the config system, and not just using its
        # own constants which happen to match the normal configured
        # values.
        'config.build.output.base_dir_name': 'build_output_dir',
        'config.build.output.subdir_name_format':
                'built_at_time_{timestamp}_by_dither',
        # We give a fixed timestamp here rather than asking the
        # system clock via the datetime module
        'utils.run_timestamp': '2000-01-01_06.30.59',
    })

    @di_providers.register('.org.python.stdlib.os.path')
    def give_fake_os_path():
        fake_os_path_module = namedtuple('fake_os_path', ['join'])
        def fake_join(left, right):
            return left + '/' + right

        return fake_os_path_module(
                join=fake_join)

    @di_providers.register_instance('utils.ensure_dir_exists')
    def fake_ensure_dir_exists(dir_path):
        functions_called.append(fake_ensure_dir_exists)
        return

    #
    # Test body
    #
    assert are_all_dependencies_met_for(
            build_core.get_build_output_subdir)

    result = build_core.get_build_output_subdir()
    assert (result ==
            'build_output_dir/built_at_time_2000-01-01_06.30.59_by_dither')

    assert fake_ensure_dir_exists in functions_called
