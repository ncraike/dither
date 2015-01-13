from functools import lru_cache

from fang import ResourceProviderRegister

from dither.di import di

providers = ResourceProviderRegister(
        '.com.ncraike.dither')

def provide_python_datetime():
    import datetime
    return datetime

providers.register_callable(
        '.org.python.stdlib.datetime',
        provide_python_datetime)

@di.dependsOn('.org.python.stdlib.datetime')
def provide_python_datetime_now():
    datetime = di.resolver.unpack(provide_python_datetime_now)
    return datetime.datetime.now

providers.register_callable(
        '.org.python.stdlib.datetime:datetime.now',
        provide_python_datetime_now)

@di.dependsOn('.org.python.stdlib.datetime:datetime.now')
@di.dependsOn('config.timestamp_format')
@lru_cache(maxsize=None)
def give_run_timestamp():
    (
            datetime_now,
            timestamp_format,
            ) = di.resolver.unpack(give_run_timestamp) 

    return datetime_now().strftime(timestamp_format)

providers.register_callable(
        'utils.run_timestamp',
        give_run_timestamp)
