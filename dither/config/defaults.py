
from fang import ResourceProviderRegister

from dither.di import di

providers = ResourceProviderRegister(
        '.com.ncraike.dither')

providers.register_instance(
        'config.program_name', 'dither')

providers.register_instance(
        'config.timestamp_format', '%Y-%m-%d_%H-%M-%S')

providers.register_instance(
        'config.build.templates.dir_name', 'dither_templates')

providers.register_instance(
        'config.build.templates.extensions',
        ['.template', '.tpl'])

providers.register_instance(
        'config.build.templates.context_module_name',
        'template_context')

@di.dependsOn('config.build.templates.dir_name')
@di.dependsOn('config.build.templates.context_module_name')
def templates_context_path():
    templates_dir_name, context_module_name = di.resolver.unpack(
            templates_context_path)
    # FIXME: Make os.path a resource
    import os.path

    return os.path.join(templates_dir, context_module_name, '.py')

# FIXME: Use decorators
providers.register_callable(
        'config.build.templates.context_path',
        templates_context_path)

providers.register_instance(
        'config.build.output.base_dir_name', 'built_dotfiles')

providers.register_instance(
        'config.build.output.subdir_name_format',
        'built_at_{timestamp}')

providers.register_instance(
        'config.build.output.latest_build_link_name',
        'latest_build')

providers.register_instance(
        'config.link.installed_build_link_name',
        'installed_build')

providers.register_instance(
        'config.link.home_dir_link_name',
        '.dither_dotfiles')

@di.dependsOn('config.program_name')
def moved_file_filename_format():
    program_name = di.resolver.unpack(templates_context_path)
    return '{original_name}.moved_by_{program_name}_at_{timestamp}'.format(
            program_name=program_name)
providers.register_callable(
        'config.moved_file_filename_format',
        moved_file_filename_format)
