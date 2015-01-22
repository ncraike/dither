from functools import lru_cache

from fang import ResourceProviderRegister

from dither.di import di

providers = ResourceProviderRegister(
        '.com.ncraike.dither')

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
