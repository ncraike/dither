from collections import namedtuple
import functools

CallRecord = namedtuple('CallRecord', [
        'func_name',
        'func',
        'args',
        'kwargs'])

class RecordedCalls:

    def __init__(self):
        self.in_order = []
        self.by_func = {}
        self.by_func_name = {}

    def __contains__(self, item):
        if isinstance(item, str):
            return item in self.by_func_name
        else:
            return item in self.by_func

    def __getitem__(self, item):
        if isinstance(item, str):
            return self.by_func_name[item]
        else:
            return self.by_func[item]

    def add_call(self, func, func_name, args, kwargs):
        call_record = CallRecord(func_name, func, args, kwargs)
        self.in_order.append(call_record)
        self.by_func.setdefault(func, []).append(call_record)
        self.by_func_name.setdefault(func_name, []).append(call_record)

    def recorded(self, func_to_record, with_name=None):
        if with_name is None:
            with_name = func_to_record.__name__
        
        def call_proxy(*args, **kwargs):
            self.add_call(func_to_record, with_name, args, kwargs)
            return func_to_record(*args, **kwargs)

        functools.update_wrapper(call_proxy, func_to_record)
        return call_proxy
