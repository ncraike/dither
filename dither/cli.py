import os

import click

from dither.di import di

@click.group(
        name='dither',
)
def cli():
    pass

def load_resource_providers():
    import dither.config.defaults
    import dither.utils
    import dither.build.core
    import dither.build.render
    di.providers.load(
            dither.config.defaults.providers)
    di.providers.load(
            dither.utils.providers)
    di.providers.load(
            dither.build.core.providers)
    di.providers.load(
            dither.build.render.providers)

@cli.command()
def build():
    '''Builds new dotfiles from ./dither_templates.'''
    load_resource_providers()

    from . import build
    build.build()

@cli.command()
def link():
    '''Symlinks latest build into home directory.'''
    load_resource_providers()

    from . import link
    # TODO: Take these arguments from di's 'config.*' space
    link.link(
            base_build_dir='built_dotfiles',
            home_dir=os.path.expanduser('~'))

@cli.command()
@click.pass_context
def update(context):
    '''Performs the "build" and "link" steps.'''
    context.forward(build)
    context.forward(link)
