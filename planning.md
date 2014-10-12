
Add `dither link` command
=========================
Start link.py sub-module

Add link() function

Accept build output dir as an arg

Draft how we'd like linking to work
 - link `<output>/installed_build` to the _target_ of `<output>/latest_build`,
   which `dither build` should've updated on last build. If it doesn't exist,
   _then_ make assumption that we should use "newest" (last when sorted) of
   `<output>/built_at_*`
 - link from ~/.dither_dotfiles to `<output>/installed_build`
 - for each dotfile in `<output>/installed_build/`, check if it exists
   in home directory.
    - if it exists, check if it links to ~/.dither_dotfiles/<filename>
       - if it does, don't change it
       - if it doesn't, move it to 
         `~/<filename>.moved_by_dither_at_<timestamp>`, create link to
         `~/.dither_dotfiles/<filename>`
    - if it doesn't exist, create link to `~/.dither_dotfiles/<filename>`
 - in the ideal case, the above will just involve changing
   `<output>/installed_build` to point from some other `<output>/built_at_*` to newest of `<output>/built_at_*`.
/


Later tasks
===========
Move redundant constants to a common place
