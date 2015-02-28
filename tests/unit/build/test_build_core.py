
from collections import namedtuple
from functools import partial, update_wrapper

import pytest

from dither.di import di

# Module under test
import dither.build.core as build_core

@pytest.fixture(scope='function')
def di_providers():
    di.providers.clear()
    return di.providers

@pytest.fixture(scope='function')
def register_fake_config(di_providers):
    '''
    Configure DI with a small set of config values.

    The config values here are a little different to what are used in
    production, to ensure the code under test is actually asking the
    config system, instead of eg just using its own constants.
    '''
    di_providers.mass_register({
        'config.build.output.base_dir_name': 'build_output_dir',
        'config.build.output.subdir_name_format':
                'built_at_time_{timestamp}_by_dither',
    })

@pytest.fixture(scope='function')
def register_fake_run_timestamp(di_providers):
    '''
    Configure DI to give a fixed timestamp for utils.run_timestamp,
    rather than asking the system clock.
    '''
    di_providers.mass_register({
        'utils.run_timestamp': '2000-01-01_06.30.59',
    })

def fake_os_path_join(left, right):
    return left + '/' + right

def fake_ensure_dir_exists(dir_path):
    pass

def test_get_build_output_subdir__gives_expected_result(
        di_providers,
        register_fake_config,
        register_fake_run_timestamp):

    di_providers.register_instance(
            '.org.python.stdlib.os:path.join', fake_os_path_join)
    di_providers.register_instance(
            'utils.ensure_dir_exists', fake_ensure_dir_exists)

    assert di.resolver.are_all_dependencies_met_for(
            build_core.get_build_output_subdir)

    # Function under test
    result = build_core.get_build_output_subdir()

    assert (result ==
            'build_output_dir/built_at_time_2000-01-01_06.30.59_by_dither')

def test_get_build_output_subdir__calls_ensure_dir_exists_with_path(
        di_providers,
        register_fake_config,
        register_fake_run_timestamp,
        recorded_calls):

    di_providers.register_instance(
            '.org.python.stdlib.os:path.join', fake_os_path_join)
    di_providers.register_instance(
            'utils.ensure_dir_exists',
            recorded_calls.recorded(fake_ensure_dir_exists))

    assert di.resolver.are_all_dependencies_met_for(
            build_core.get_build_output_subdir)

    # Function under test
    result = build_core.get_build_output_subdir()

    # Test fake_ensure_dir_exists was called, and with expected args
    assert fake_ensure_dir_exists in recorded_calls.by_func
    calls_of_func = recorded_calls.by_func[fake_ensure_dir_exists]
    assert len(calls_of_func) == 1
    assert calls_of_func[0].args == (result,)
