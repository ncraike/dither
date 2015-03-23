
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

FakeOsPathModule = namedtuple(
    'FakeOsPathModule', ['basename', 'islink', 'join', 'lexists'])

def fake_renderer_run(use_reloader='use_reloader default value'):
    pass

@pytest.fixture(scope='function')
def common_providers_for_testing_get_build_output_subdir(di_providers):
    '''
    Configure DI with a common set of resources suitable for testing
    get_build_output_subdir().

    Individual tests may override some of these resources explicitly by
    registering a new resource provider with allow_override=True. Often
    this is done to record how a resource is used.
    '''
    di_providers.mass_register({
        # The config values here are a little different to what are used
        # in production, to ensure the code under test is actually
        # asking the config system, instead of eg just using its own
        # constants.
        'config.build.output.base_dir_name': 'build_output_dir',
        'config.build.output.subdir_name_format':
                'built_at_time_{timestamp}_by_dither',
        # Give a fixed timestamp for utils.run_timestamp, instead of
        # asking the system clock.
        'utils.run_timestamp': '2000-01-01_06.30.59',
        # Give fake fucntion implementations
        '.org.python.stdlib.os:path.join': fake_os_path_join,
        'utils.ensure_dir_exists': fake_ensure_dir_exists,
    })

def test_get_build_output_subdir__returns_expected_result(
        di_providers,
        common_providers_for_testing_get_build_output_subdir):

    assert di.resolver.are_all_dependencies_met_for(
            build_core.get_build_output_subdir)

    # Function under test
    result = build_core.get_build_output_subdir()

    assert (result ==
            'build_output_dir/built_at_time_2000-01-01_06.30.59_by_dither')

def test_get_build_output_subdir__calls_ensure_dir_exists_with_path(
        di_providers,
        common_providers_for_testing_get_build_output_subdir,
        recorded_calls):

    di_providers.register_instance(
            'utils.ensure_dir_exists',
            recorded_calls.recorded(fake_ensure_dir_exists),
            allow_override=True)

    assert di.resolver.are_all_dependencies_met_for(
            build_core.get_build_output_subdir)

    # Function under test
    result = build_core.get_build_output_subdir()

    # Test fake_ensure_dir_exists was called, and with expected args
    assert fake_ensure_dir_exists in recorded_calls
    calls_of_func = recorded_calls[fake_ensure_dir_exists]
    assert len(calls_of_func) == 1
    assert calls_of_func[0].args == (result,)

@pytest.fixture(scope='function')
def common_providers_for_testing_create_latest_build_link(di_providers):
    '''
    Configure DI with a common set of resources suitable for testing
    create_latest_build_link().

    Individual tests may override some of these resources explicitly by
    registering a new resource provider with allow_override=True. Often
    this is done to record how a resource is used.
    '''
    di_providers.mass_register({
            'config.build.output.latest_build_link_name': 'newest_build',
            '.org.python.stdlib.os:remove': fake_os_remove,
            '.org.python.stdlib.os:symlink': fake_os_symlink,
    })

def test_create_latest_build_link__returns_none(
        di_providers,
        common_providers_for_testing_create_latest_build_link):

    di_providers.register_instance(
            '.org.python.stdlib.os:path',
            FakeOsPathModule(
                basename=fake_os_path_basename,
                join=fake_os_path_join,
                lexists=(lambda path: False),
                islink=(lambda path: False)))

    assert di.resolver.are_all_dependencies_met_for(
            build_core.create_latest_build_link)

    # Function under test
    result = build_core.create_latest_build_link(
            'some_dir/my_builds', 'built_a_moment_ago')
    assert result == None

def test_create_latest_build_link__calls_symlink_as_expected(
        di_providers,
        common_providers_for_testing_create_latest_build_link,
        recorded_calls):

    di_providers.register_instance(
            '.org.python.stdlib.os:path',
            FakeOsPathModule(
                basename=fake_os_path_basename,
                join=fake_os_path_join,
                lexists=(lambda path: False),
                islink=(lambda path: False)))
    di_providers.register_instance(
            '.org.python.stdlib.os:symlink',
            recorded_calls.recorded(fake_os_symlink),
            allow_override=True)

    assert di.resolver.are_all_dependencies_met_for(
            build_core.create_latest_build_link)

    # Function under test
    result = build_core.create_latest_build_link(
            'some_dir/my_builds', 'some_dir/built_a_moment_ago')

    # Test fake_os_symlink was called once, and with expected args
    assert fake_os_symlink in recorded_calls
    assert len(recorded_calls[fake_os_symlink]) == 1
    assert recorded_calls[fake_os_symlink][0].args == (
            'built_a_moment_ago', 'some_dir/my_builds/newest_build')

def test_create_latest_build_link__removes_if_path_exists_and_is_link(
        di_providers,
        common_providers_for_testing_create_latest_build_link,
        recorded_calls):

    di_providers.register_instance(
            '.org.python.stdlib.os:path',
            FakeOsPathModule(
                basename=fake_os_path_basename,
                join=fake_os_path_join,
                lexists=(lambda path: True),
                islink=(lambda path: True)))
    di_providers.register_instance(
            '.org.python.stdlib.os:remove',
            recorded_calls.recorded(fake_os_remove),
            allow_override=True)

    assert di.resolver.are_all_dependencies_met_for(
            build_core.create_latest_build_link)

    # Function under test
    result = build_core.create_latest_build_link(
            'some_dir/my_builds', 'some_dir/built_a_moment_ago')

    # Test fake_os_remove was called once, and with expected args
    assert fake_os_remove in recorded_calls, (
            "os:remove wasn't called")
    calls_of_func = recorded_calls[fake_os_remove]
    assert len(calls_of_func) == 1, (
            "os:remove should have been called exactly once")
    assert calls_of_func[0].args == ('some_dir/my_builds/newest_build',), (
            "os:remove wasn't called with expected args")

def test_create_latest_build_link__raises_if_path_exists_and_is_not_link(
        di_providers,
        common_providers_for_testing_create_latest_build_link,
        recorded_calls):

    di_providers.register_instance(
            '.org.python.stdlib.os:path',
            FakeOsPathModule(
                basename=fake_os_path_basename,
                join=fake_os_path_join,
                lexists=(lambda path: True),
                islink=(lambda path: False)))

    assert di.resolver.are_all_dependencies_met_for(
            build_core.create_latest_build_link)

    # Function under test
    with pytest.raises(Exception):
        result = build_core.create_latest_build_link(
                'some_dir/my_builds', 'some_dir/built_a_moment_ago')

def test_create_latest_build_link__doesnt_remove_if_path_exists_and_is_not_link(
        di_providers,
        common_providers_for_testing_create_latest_build_link,
        recorded_calls):

    di_providers.register_instance(
            '.org.python.stdlib.os:path',
            FakeOsPathModule(
                basename=fake_os_path_basename,
                join=fake_os_path_join,
                lexists=(lambda path: True),
                islink=(lambda path: False)))
    di_providers.register_instance(
            '.org.python.stdlib.os:remove',
            recorded_calls.recorded(fake_os_remove),
            allow_override=True)

    assert di.resolver.are_all_dependencies_met_for(
            build_core.create_latest_build_link)

    # Function under test
    try:
        result = build_core.create_latest_build_link(
                'some_dir/my_builds', 'some_dir/built_a_moment_ago')
    # We expect an exception to be thrown, but that's not we're testing
    except:
        pass

    # Test fake_os_remove was _not called_
    assert fake_os_remove not in recorded_calls, (
            'os:remove was called')

def test_create_latest_build_link__doesnt_symlink_if_path_exists_and_is_not_link(
        di_providers,
        common_providers_for_testing_create_latest_build_link,
        recorded_calls):

    di_providers.register_instance(
            '.org.python.stdlib.os:path',
            FakeOsPathModule(
                basename=fake_os_path_basename,
                join=fake_os_path_join,
                lexists=(lambda path: True),
                islink=(lambda path: False)))
    di_providers.register_instance(
            '.org.python.stdlib.os:symlink',
            recorded_calls.recorded(fake_os_symlink),
            allow_override=True)

    assert di.resolver.are_all_dependencies_met_for(
            build_core.create_latest_build_link)

    # Function under test
    try:
        result = build_core.create_latest_build_link(
                'some_dir/my_builds', 'some_dir/built_a_moment_ago')
    except:
        pass

    # Test fake_os_symlink was _not called_
    assert fake_os_symlink not in recorded_calls, (
            'os:symlink was called')

FakeRenderer = namedtuple('FakeRenderer', [
    'run'])

def fake_create_latest_build_link(
        output_base_dir_name, latest_build_link_path):
    pass

@pytest.fixture(scope='function')
def common_providers_for_testing_build(di_providers):
    '''
    Configure DI with a common set of resources suitable for testing
    build().

    Individual tests may override some of these resources explicitly by
    registering a new resource provider with allow_override=True. Often
    this is done to record how a resource is used.
    '''
    di.providers.mass_register({
        'config.build.output.base_dir_name': 'build_output_dir',
        'build.output.path': 'build_output_dir/my_build_just_now',
        'build.renderer':
                FakeRenderer(run=fake_renderer_run),
        'build.output.create_latest_build_link':
                fake_create_latest_build_link,
    })

def test_build__returns_None(
        di_providers, common_providers_for_testing_build):

    assert di.resolver.are_all_dependencies_met_for(
            build_core.build)

    # Function under test
    result = build_core.build()

    assert result == None

def test_build__calls_renderer_run(
        di_providers,
        common_providers_for_testing_build,
        recorded_calls):

    di.providers.register_instance(
            'build.renderer',
            FakeRenderer(
                run=recorded_calls.recorded(fake_renderer_run)),
            allow_override=True)

    assert di.resolver.are_all_dependencies_met_for(
            build_core.build)

    # Function under test
    result = build_core.build()

    # Test fake_renderer_run was called once, and with expected args
    assert fake_renderer_run in recorded_calls
    calls_of_func = recorded_calls[fake_renderer_run]
    assert len(calls_of_func) == 1
    assert calls_of_func[0].args == ()
    assert calls_of_func[0].kwargs == {'use_reloader': False}

def test_build__calls_create_latest_build_link(
        di_providers,
        common_providers_for_testing_build,
        recorded_calls):

    di.providers.register_instance(
            'build.output.create_latest_build_link',
            recorded_calls.recorded(fake_create_latest_build_link),
            allow_override=True)

    assert di.resolver.are_all_dependencies_met_for(
            build_core.build)

    # Function under test
    result = build_core.build()

    # Test fake_create_latest_build_link was called once, and with
    # expected args
    assert fake_create_latest_build_link in recorded_calls
    calls_of_func = recorded_calls[fake_create_latest_build_link]
    assert len(calls_of_func) == 1
    assert calls_of_func[0].args == (
            'build_output_dir', 'build_output_dir/my_build_just_now')
