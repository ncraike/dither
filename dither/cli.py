import os

import click

@click.group(
        name='dither',
)
def cli():
    pass

@cli.command()
@click.pass_context
def update(context):
    context.forward(build)
    context.forward(link)

@cli.command()
def build():
    from . import build
    build.build()

@cli.command()
def link():
    from . import link
    link.link(
            base_build_dir=link.BASE_BUILD_DIR,
            home_dir=os.path.expanduser('~'))
