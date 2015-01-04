import os

import click

from dither.di import di
import dither.config.defaults

@click.group(
        name='dither',
)
def cli():
    pass

def load_config_resource_providers():
    di.providers.load(
            dither.config.defaults.providers)

@cli.command()
def build():
    '''Builds new dotfiles from ./dither_templates.'''
    load_config_resource_providers()

    from . import build
    build.build()

@cli.command()
def link():
    '''Symlinks latest build into home directory.'''
    from . import link
    link.link(
            base_build_dir=link.BASE_BUILD_DIR,
            home_dir=os.path.expanduser('~'))

@cli.command()
@click.pass_context
def update(context):
    '''Performs the "build" and "link" steps.'''
    context.forward(build)
    context.forward(link)

