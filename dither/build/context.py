import os
import sys
import importlib

from dither.di import di

# dependencies:
# - (config) TEMPLATES_DIR
# - (config) CONTEXT_PATH - depends on TEMPLATES_DIR
# - hostname - depends on os module (os.environ) or socket module
#   (socket.gethostname)
# - os_family - depends on sys module (sys.platform)
# - os_name - depends on os family and optionally on issue_file
# - 
#
# provides:
# - context_func:

TEMPLATES_DIR = 'dither_templates'
CONTEXT_PATH = os.path.join(TEMPLATES_DIR, 'template_context.py')

def hostname_from_env():
    return os.environ.get('HOSTNAME', None)

def hostname_from_socket():
    import socket
    return socket.gethostname()

def get_hostname():
    for get_func in [hostname_from_env, hostname_from_socket]:
        hostname = get_func()
        if hostname and hostname != 'localhost':
            return hostname
    else:
        return ''

def linux_parse_issue_file():
    try:
        with open('/etc/issue', 'r') as issue_file:
            issue = issue_file.read()
            first_bslash_pos = issue.find('\\')
            if first_bslash_pos > 0:
                return issue[:first_bslash_pos]
    except IOError as e:
        pass
            
    return None

def get_os():
    os_family = get_os_family()
    if os_family == 'linux':
        issue_name = linux_parse_issue_file()
        if issue_name:
            return issue_name
        return os_family
    else:
        return os_family

def get_os_family():
    py_platform = sys.platform
    if 'linux' in py_platform:
        return 'linux'
    elif 'darwin' in py_platform:
        return 'macosx'
    elif 'win' in py_platform:
        return 'windows'
    else:
        return ''

def get_context_func(context_path):
    context_subdir = os.path.dirname(os.path.abspath(CONTEXT_PATH))
    context_filename = os.path.basename(CONTEXT_PATH)
    context_module_name, context_ext = os.path.splitext(context_filename)

    if context_ext != '.py':
        raise ValueError("Context filename must end in .py")
    
    if context_subdir:
        sys.path.insert(0, context_subdir)

    context_module = importlib.import_module(context_module_name)
    return context_module.get_context


def get_context(
        os=None, os_family=None, hostname=None, context_path=None,
        log=None, **kwargs):

    context = {
        'os': os,
        'os_family': os_family,
        'hostname': hostname
    }

    if context_path:
        context_func = get_context_func(context_path)
        custom_context = context_func(
                os=os, os_family=os_family, hostname=hostname, **kwargs)

        context.update(custom_context)

    return context
