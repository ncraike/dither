
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
        'config.build.output.latest_build_link_name': 'newest_build',
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

#
# XXX Not sure if the fake_os_path_* funcs should do so much
#
def fake_os_path_join(left, right):
    return left + '/' + right

def fake_os_path_basename(path):
    if '/' in path:
        last_slash_pos = path.rfind('/')
        return path[last_slash_pos+1:]
    else:
        return path

def fake_os_remove(filename):
    pass

def fake_os_symlink(link_target_path, link_name):
    pass

def fake_ensure_dir_exists(dir_path):
    pass

FakeOsPathModule = namedtuple('FakeOsPathModule', [
    'basename',
    'islink',
    'join',
    'lexists',
    ])

def test_get_build_output_subdir__returns_expected_result(
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

def test_create_latest_build_link__returns_none(
        di_providers,
        register_fake_config):

    fake_os_path = FakeOsPathModule(
            basename=fake_os_path_basename,
            join=fake_os_path_join,
            lexists=lambda path: False,
            islink=lambda path: False)
    di_providers.register_instance(
            '.org.python.stdlib.os:path', fake_os_path)
    di_providers.register_instance(
            '.org.python.stdlib.os:remove', fake_os_remove)
    di_providers.register_instance(
            '.org.python.stdlib.os:symlink', fake_os_symlink)

    assert di.resolver.are_all_dependencies_met_for(
            build_core.create_latest_build_link)

    # Function under test
    result = build_core.create_latest_build_link(
            'some_dir/my_builds', 'built_a_moment_ago')
    assert result == None

def test_create_latest_build_link__calls_symlink_as_expected(
        di_providers,
        register_fake_config,
        recorded_calls):

    fake_os_path = FakeOsPathModule(
            basename=fake_os_path_basename,
            join=fake_os_path_join,
            lexists=lambda path: False,
            islink=lambda path: False)
    di_providers.register_instance(
            '.org.python.stdlib.os:path', fake_os_path)
    di_providers.register_instance(
            '.org.python.stdlib.os:remove', fake_os_remove)
    di_providers.register_instance(
            '.org.python.stdlib.os:symlink',
            recorded_calls.recorded(fake_os_symlink))

    assert di.resolver.are_all_dependencies_met_for(
            build_core.create_latest_build_link)

    # Function under test
    result = build_core.create_latest_build_link(
            'some_dir/my_builds', 'some_dir/built_a_moment_ago')

    # Test fake_os_symlink was called once, and with expected args
    assert fake_os_symlink in recorded_calls.by_func
    calls_of_func = recorded_calls.by_func[fake_os_symlink]
    assert len(calls_of_func) == 1
    assert calls_of_func[0].args == (
            'built_a_moment_ago', 'some_dir/my_builds/newest_build')

def test_create_latest_build_link__removes_if_path_exists_and_is_link(
        di_providers,
        register_fake_config,
        recorded_calls):

    fake_os_path = FakeOsPathModule(
            basename=fake_os_path_basename,
            join=fake_os_path_join,
            lexists=lambda path: True,
            islink=lambda path: True)
    di_providers.register_instance(
            '.org.python.stdlib.os:path', fake_os_path)
    di_providers.register_instance(
            '.org.python.stdlib.os:remove',
            recorded_calls.recorded(fake_os_remove))
    di_providers.register_instance(
            '.org.python.stdlib.os:symlink', fake_os_symlink)

    assert di.resolver.are_all_dependencies_met_for(
            build_core.create_latest_build_link)

    # Function under test
    result = build_core.create_latest_build_link(
            'some_dir/my_builds', 'some_dir/built_a_moment_ago')

    # Test fake_os_remove was called once, and with expected args
    assert fake_os_remove in recorded_calls.by_func, (
            "os:remove wasn't called")
    calls_of_func = recorded_calls.by_func[fake_os_remove]
    assert len(calls_of_func) == 1, (
            "os:remove should have been called exactly once")
    assert calls_of_func[0].args == ('some_dir/my_builds/newest_build',), (
            "os:remove wasn't called with expected args")

def test_create_latest_build_link__raises_if_path_exists_and_is_not_link(
        di_providers,
        register_fake_config,
        recorded_calls):

    fake_os_path = FakeOsPathModule(
            basename=fake_os_path_basename,
            join=fake_os_path_join,
            lexists=lambda path: True,
            islink=lambda path: False)
    di_providers.register_instance(
            '.org.python.stdlib.os:path', fake_os_path)
    di_providers.register_instance(
            '.org.python.stdlib.os:remove',
            fake_os_remove)
    di_providers.register_instance(
            '.org.python.stdlib.os:symlink', fake_os_symlink)

    assert di.resolver.are_all_dependencies_met_for(
            build_core.create_latest_build_link)

    # Function under test
    with pytest.raises(Exception):
        result = build_core.create_latest_build_link(
                'some_dir/my_builds', 'some_dir/built_a_moment_ago')
