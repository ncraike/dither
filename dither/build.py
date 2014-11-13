import logging
import os
import sys
import datetime

import staticjinja
import jinja2

from . import context

TEMPLATES_DIR = 'dither_templates'
BUILD_OUTPUT_DIR = 'built_dotfiles'
OUTPUT_SUBDIR_FMT = 'built_at_{timestamp}'
TIMESTAMP_FMT = '%Y-%m-%d_%H-%M-%S'
TEMPLATE_EXTENSIONS = ('.template', '.tpl')
CONTEXT_PATH = os.path.join(TEMPLATES_DIR, 'template_context.py')
LATEST_BUILD_LINK_NAME = 'latest_build'

# Actual dependencies:
#  - template_dir: given to staticjinja, must exist, be readable
#  - context_module: usually found within template_dir, given to
#    staticjinja, must exist, be importable
#  - build_output_subdir: parent dirs must exist, may not exist, must
#    be writeable
#  - latest_build_link_path: may already exist, must be over-writeable
#
#  Just for context building (maybe move context to other module?):
#  - hostname: may be derived in various ways (env vars, socket module)
#  - os_family: based on sys.platform
#  - os_name: based partly on os_family
#
#  If we did move context building to another module, build module's
#  dependencies would include instead of context_module:
#  - context_func: usually provided by context_builder module, given
#    to staticjinja
#
#  ...and context_builder module's would be:
#  - context_module: user-defined, usually found within template_dir,
#    must exist and be importable, used along with hostname, os_family
#    and os_name to provide context_func

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
        return context.get_context(
                os=context.get_os(),
                os_family=context.get_os_family(),
                hostname=context.get_hostname(),
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
