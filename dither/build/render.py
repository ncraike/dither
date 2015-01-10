import os
import logging

import staticjinja
import jinja2

from dither.di import di

from . import context

def get_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())
    return logger


@di.dependsOn('config.build.templates.extensions')
@di.dependsOn('config.build.templates.context_path')
class CustomRenderer(staticjinja.Renderer):

    def __init__(self, *args, **kwargs):
        (self.template_extensions,
                self.context_path) = di.resolver.unpack(CustomRenderer)
        super().__init__(*args, **kwargs)

    def transform_template_path(self, template_path):
        for extension in self.template_extensions:
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

        return not filename.endswith(self.template_extensions)

    def is_partial(self, filename):
        '''Prevent files prefixed with '_' being considered partials.
        '''
        return False

    def is_ignored(self, filename):
        '''Prevent dotfiles being ignored as templates
        '''
        if '__pycache__' in filename:
            return True
        if filename == os.path.basename(self.context_path):
            return True
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

@di.dependsOn('config.build.templates.context_path')
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

    context_path = di.resolver.unpack(make_renderer)

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
                context_path=context_path,
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
