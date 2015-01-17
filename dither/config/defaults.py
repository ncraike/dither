
from fang import ResourceProviderRegister

from dither.di import di

providers = ResourceProviderRegister(
        '.com.ncraike.dither')

#
# General config:
#

providers.mass_register({
        'config.program_name': 'dither',
        'config.timestamp_format': '%Y-%m-%d_%H-%M-%S',
})

@di.dependsOn('config.program_name')
@providers.register('config.moved_file_filename_format')
def moved_file_filename_format():
    program_name = di.resolver.unpack(templates_context_path)
    return '{original_name}.moved_by_{program_name}_at_{timestamp}'.format(
            program_name=program_name)

#
# build config:
#

providers.mass_register({
        'config.build.templates.dir_name': 'dither_templates',
        'config.build.templates.extensions': ('.template', '.tpl'),
        'config.build.templates.context_module_name': 'template_context',

        'config.build.output.base_dir_name': 'built_dotfiles',
        'config.build.output.subdir_name_prefix': 'built_at',
        'config.build.output.subdir_name_format': 'built_at_{timestamp}',
        'config.build.output.latest_build_link_name': 'latest_build',
})

@di.dependsOn('config.build.templates.dir_name')
@di.dependsOn('config.build.templates.context_module_name')
@providers.register('config.build.templates.context_path')
def templates_context_path():
    templates_dir_name, context_module_name = di.resolver.unpack(
            templates_context_path)
    # FIXME: Make os.path a resource
    import os.path

    return os.path.join(
            templates_dir_name, context_module_name + '.py')

#
# link config:
#

providers.mass_register({
        'config.link.installed_build_link_name': 'installed_build',
        'config.link.home_dir_link_name': '.dither_dotfiles',
})
