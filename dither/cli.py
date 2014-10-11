import click

@click.group(
        name='dither',
)
def cli():
    pass

@cli.command()
def update():
    pass

@cli.command()
def build():
    from . import build
    build.build()

@cli.command()
def link():
    pass
