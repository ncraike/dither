
prog_name = 'dither'

templates_dir = 'dither_templates'
build_output_base_dir = 'built_dotfiles'
build_output_subdir_prefix = 'built_at'
timestamp_format = '%Y-%m-%d_%H-%M-%S'
template_extensions = ['.template', '.tpl']

context_module_name = 'template_context'
latest_build_link_name = 'latest_build'
installed_build_name_link_name = 'installed_build'
home_dir_link_name = '.dither_dotfiles'

# Depending on the above:

# `prefix` comes from `build_output_subdir_prefix`
# `timestamp` is made with `timestamp_format`, but should also probably be singleton-like - made at the start of a run, and re-used throughout
build_output_subdir_format = '{prefix}_{timestamp}'

# `templates_dir` is defined above
context_path = os.path.join(templates_dir, 'template_context.py')

# `original_name` is given each call, `prog_name` is defined above, `timestamp` is as described above
move_timestamped_format = '{original_name}.moved_by_{prog_name}_at_{timestamp}'
