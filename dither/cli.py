import os

import click

@click.group(
        name='dither',
)
def cli():
    pass

@cli.command()
def build():
    '''Builds new dotfiles from ./dither_templates.'''
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

