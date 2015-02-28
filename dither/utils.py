from functools import lru_cache

from fang import ResourceProviderRegister

from dither.di import di

providers = ResourceProviderRegister(
        '.com.ncraike.dither')

@providers.register('.org.python.stdlib.os')
def python_os_module():
    import os
    return os

@di.dependsOn('.org.python.stdlib.os')
@providers.register('.org.python.stdlib.os:makedirs')
def python_os_makedirs():
    os = di.resolver.unpack(python_os_makedirs)
    return os.makedirs

@di.dependsOn('.org.python.stdlib.os')
@providers.register('.org.python.stdlib.os:remove')
def python_os_remove():
    os = di.resolver.unpack(python_os_remove)
    return os.remove

@di.dependsOn('.org.python.stdlib.os')
@providers.register('.org.python.stdlib.os:symlink')
def python_os_symlink():
    os = di.resolver.unpack(python_os_symlink)
    return os.symlink

@di.dependsOn('.org.python.stdlib.os')
@providers.register('.org.python.stdlib.os:path')
def python_os_path_module():
    os = di.resolver.unpack(python_os_path_module)
    return os.path

@di.dependsOn('.org.python.stdlib.os')
@providers.register('.org.python.stdlib.os:path.exists')
def python_os_path_exists():
    os = di.resolver.unpack(python_os_path_exists)
    return os.path.exists

@di.dependsOn('.org.python.stdlib.os')
@providers.register('.org.python.stdlib.os:path.join')
def python_os_path_join():
    os = di.resolver.unpack(python_os_path_join)
    return os.path.join

@providers.register('.org.python.stdlib.datetime')
def python_datetime_module():
    import datetime
    return datetime

@di.dependsOn('.org.python.stdlib.datetime')
@providers.register('.org.python.stdlib.datetime:datetime.now')
def python_datetime_now():
    datetime = di.resolver.unpack(python_datetime_now)
    return datetime.datetime.now

@di.dependsOn('.org.python.stdlib.datetime:datetime.now')
@di.dependsOn('config.timestamp_format')
@providers.register('utils.run_timestamp')
@lru_cache(maxsize=None)
def give_run_timestamp():
    '''
    Give a timestamp which is generated the first time it's requested,
    then re-used for the rest of the program execution.
    '''
    (
            datetime_now,
            timestamp_format,
            ) = di.resolver.unpack(give_run_timestamp) 

    return datetime_now().strftime(timestamp_format)

@di.dependsOn('.org.python.stdlib.os:path.exists')
@di.dependsOn('.org.python.stdlib.os:makedirs')
@providers.register_instance('utils.ensure_dir_exists')
def ensure_dir_exists(dir_path):
    path_exists, makedirs = di.resolver.unpack(ensure_dir_exists)
    if not path_exists(dir_path):
        makedirs(dir_path)
