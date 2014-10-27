import inspect
import logging
import os
import sys
import re
import datetime
import importlib

import staticjinja
import jinja2

TEMPLATES_DIR = 'dither_templates'
BUILD_OUTPUT_DIR = 'built_dotfiles'
OUTPUT_SUBDIR_FMT = 'built_at_{timestamp}'
TIMESTAMP_FMT = '%Y-%m-%d_%H-%M-%S'
TEMPLATE_EXTENSIONS = ('.template', '.tpl')
CONTEXT_PATH = os.path.join(TEMPLATES_DIR, 'template_context.py')
LATEST_BUILD_LINK_NAME = 'latest_build'

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
        return 'mac'
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

def get_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())
    return logger

def ensure_dir_exists(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

def get_build_output_subdir():
    timestamp = datetime.datetime.now().strftime(TIMESTAMP_FMT)
    subdir_name = OUTPUT_SUBDIR_FMT.format(timestamp=timestamp)
    outpath = os.path.join(BUILD_OUTPUT_DIR, subdir_name)
    ensure_dir_exists(outpath)
    return outpath

class CustomRenderer(staticjinja.Renderer):

    TEMPLATE_EXTENSIONS = ('.template', '.tpl')

    def transform_template_path(self, template_path):
        for extension in TEMPLATE_EXTENSIONS:
            if template_path.endswith(extension):
                # Strip extension from the end of the template_path
                before, _unused, _unused = template_path.rpartition(extension)
                return before
        else:
            return template_path

    def is_static(self, filename):
        '''Only files ending in .tpl or .template are considered templates
        '''
        if self.is_ignored(filename):
            return False

        return not filename.endswith(self.TEMPLATE_EXTENSIONS)

    def is_partial(self, filename):
        '''Prevent files prefixed with '_' being considered partials.
        '''
        return False

    def is_ignored(self, filename):
        '''Prevent dotfiles being ignored as templates
        '''
        if '__pycache__' in filename:
            return True
        if filename == os.path.basename(CONTEXT_PATH):
            return True
        if 'context' in filename:
            raise Exception("filename is: {!r}".format(filename))
        return False

    def render_template(self, template, context=None, filepath=None):
        '''Render a template.

        This wraps the parent class implementation to strip template
        extensions (eg '.template') from filepath, so
        'my_subdir/my_file.conf.template' becomes
        'my_subdir/my_file.conf'.
        '''
        if filepath is None:
            filepath = os.path.join(self.outpath, template.name)
        filepath = self.transform_template_path(filepath)

        return super(CustomRenderer, self).render_template(
                template, context=context, filepath=filepath)

def make_renderer(searchpath=None,
                  outpath=None,
                  contexts=None,
                  rules=None,
                  encoding="utf8",
                  extensions=None,
                  staticpath=None):
    """Get a Renderer object.

    :param searchpath: the name of the directory to search for templates.
                       Defaults to ``'templates'``.

    :param outpath: the name of the directory to store the rendered files in.
                    Defaults to ``'.'``.

    :param contexts: list of *(regex, function)* pairs. When rendering, if a
                     template's name matches *regex*, *function* will be
                     invoked and expected to provide a context. *function*
                     should optionally take a Template as a parameter and
                     return a dictionary context when invoked. Defaults to
                     ``[]``.

    :param rules: list of *(regex, function)* pairs. When rendering, if a
                  template's name matches *regex*, rendering will delegate to
                  *function*. *function* should take a jinja2 Environment, a
                  filename, and a context and render the template. Defaults to
                  ``[]``.

    :param encoding: the encoding of templates to use. Defaults to ``'utf8'``.

    :param extensions: list of extensions to add to the Environment. Defaults
                       to ``[]``.

    :param staticpath: the name of the directory to get static files from
                       (relative to searchpath). Defaults to ``None``.


    """
    if searchpath is None:
        raise ValueError("searchpath must be given")
    if outpath is None:
        raise ValueError("outpath must be given")

    # Coerce search to an absolute path if it is not already
    searchpath = os.path.abspath(searchpath)

    loader = jinja2.FileSystemLoader(
            searchpath=searchpath, encoding=encoding)
    environment = jinja2.Environment(
            loader=loader, extensions=extensions or [])

    logger = get_logger()

    def _get_context(template=None):
        return get_context(
                os=get_os(),
                os_family=get_os_family(),
                hostname=get_hostname(),
                context_path=CONTEXT_PATH,
                log=logger
        )

    context_mappings = [
            ('.*', _get_context)
    ]

    return CustomRenderer(environment,
                    searchpath=searchpath,
                    outpath=outpath,
                    encoding=encoding,
                    logger=logger,
                    rules=rules,
                    contexts=context_mappings,
                    staticpath=staticpath,
                    )

def create_latest_build_link(build_output_dir, latest_build_path):
    link_location = os.path.join(build_output_dir, LATEST_BUILD_LINK_NAME)
    if os.path.lexists(link_location):
        if not os.path.islink(link_location):
            raise Exception(
                    "{!r} already exists, but isn't a symlink. Cautiously not "
                    "removing it.".format(link_location))
        os.remove(link_location)

    # XXX TODO Clean this up, maybe use functions from link module
    os.symlink(
            os.path.basename(latest_build_path),
            link_location)

def build():
    latest_build_path = get_build_output_subdir()

    renderer = make_renderer(
            searchpath=TEMPLATES_DIR,
            outpath=latest_build_path)

    renderer.run(use_reloader=False)

    create_latest_build_link(BUILD_OUTPUT_DIR, latest_build_path)

    # enable automatic reloading
    renderer.run(use_reloader=False)
