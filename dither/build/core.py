import logging

from fang import ResourceProviderRegister

from . import render

from dither.di import di

providers = ResourceProviderRegister(
        '.com.ncraike.dither')

# Actual dependencies:
#  - template_dir: given to staticjinja, must exist, be readable
#  - context_module: usually found within template_dir, given to
#    staticjinja, must exist, be importable
#  - build_output_subdir: parent dirs must exist, may not exist, must
#    be writeable
#  - latest_build_link_path: may already exist, must be over-writeable
#  - staticjinja module, particularly staticjinja.Renderer
#  - jinja2 module, particularly jinja2.Environment and
#    jinja2.FileSystemLoader
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

@di.dependsOn('config.build.output.base_dir_name')
@di.dependsOn('config.build.output.subdir_name_format')
@di.dependsOn('utils.run_timestamp')
@di.dependsOn('.org.python.stdlib.os:path.join')
@di.dependsOn('utils.ensure_dir_exists')
@providers.register('build.output.path')
def get_build_output_subdir():
    (output_base_dir_name,
            subdir_name_format,
            run_timestamp,
            os_path_join,
            ensure_dir_exists
            ) = di.resolver.unpack(get_build_output_subdir)

    subdir_name = subdir_name_format.format(timestamp=run_timestamp)
    # TODO Replace os.path use with pathlib
    outpath = os_path_join(output_base_dir_name, subdir_name)
    ensure_dir_exists(outpath)
    return outpath

@di.dependsOn('config.build.output.latest_build_link_name')
@di.dependsOn('.org.python.stdlib.os:path')
@di.dependsOn('.org.python.stdlib.os:remove')
@di.dependsOn('.org.python.stdlib.os:symlink')
@providers.register_instance('build.output.create_latest_build_link')
def create_latest_build_link(build_output_dir, latest_build_path):
    (latest_build_link_name,
            os_path,
            remove,
            symlink) = di.resolver.unpack(create_latest_build_link)

    # TODO Replace os.path use with pathlib
    link_location = os_path.join(build_output_dir, latest_build_link_name)
    if os_path.lexists(link_location):
        if not os_path.islink(link_location):
            raise Exception(
                    "{!r} already exists, but isn't a symlink. Cautiously not "
                    "removing it.".format(link_location))
        remove(link_location)

    # TODO Clean this up, maybe use functions from link module
    symlink(
            os_path.basename(latest_build_path),
            link_location)

@di.dependsOn('build.renderer')
@di.dependsOn('config.build.output.base_dir_name')
@di.dependsOn('build.output.path')
@di.dependsOn('build.output.create_latest_build_link')
def build():
    (renderer,
            output_base_dir_name,
            latest_build_path,
            create_latest_build_link) = di.resolver.unpack(build)

    renderer.run(use_reloader=False)
    create_latest_build_link(output_base_dir_name, latest_build_path)
