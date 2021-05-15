#/!usr/bin/ python3
"""
np.py -- a small python script for creating and maintaining simple CMake projects.

Ideas:
  * Flag to add folder to root cmakelist if a CMakeLists.txt file is found in a sub directory
  * Expand to be less idiosyncratic (custom definitions of 'SRCS' and 'HDRS' would be a start)
  * Git integration?

This file is released into the public domain
"""

import os
import io
import argparse
from distutils import util

supported_languages = ['c', 'cxx']
language_extensions = ('.c', 'cpp', 'cxx', 'h', 'hpp', 'hxx')

# User-configurable settings
class NPSettings:
  def __init__ (self):
    self.use_tabs = False
    self.expanded_spaces = 2

  def bool_check (self, value):
    return util.strtobool(value)

  # Read project directory's np.txt settings
  def read (self):
    if os.path.exists('.np') and os.path.isfile('.np'):
      settings_txt = io.open('.np')

      lines = settings_txt.readlines()
      settings_txt.close()

      # Enumerate lines for error reporting purposes
      # TODO: Change the settings to use a dict, as this could all be done in
      # a single loop without the if/elifs.
      for index, line in enumerate(lines):
        if line.strip() and not line.strip().startswith('#'):
          tokens = line.split(':')

          if len(tokens) != 2:
            print('Invalid syntax at line {}: {}', index + 1, line)
          else:
            key = tokens[0].strip().lower()
            value = tokens[1].strip().lower()
            
            if key == 'use_tabs':
              self.use_tabs = self.bool_check(value)
            elif key == 'expanded_spaces':
              self.expanded_spaces = int(value)
            else:
              print('Invalid setting found at line {}: {}', index + 1, line)  

# Create new project directory with src and include sub directories
def make_project_folder (filepath):
  if os.path.exists(filepath):
    print('File path already exists, try again. :D')
    return False

  # Create path and useful sub directories
  os.mkdir(filepath)
  os.mkdir(filepath + '/src')
  os.mkdir(filepath + '/include')
  return True

# Create new CMakeLists.txt with some basic defaults
def create_project (name,filepath=None,languages='C/CXX'):
  default_project_template = """#
# %project_name% CMakeLists.txt
#

project ( %project_name% LANGUAGES %languages% )

cmake_minimum_required( VERSION 3.18 )

set ( SRCS 
  # project sources
)
set ( HDRS
  # project headers
)

add_executable( %project_name% ${SRCS} ${HDRS} )
target_include_directories( %project_name% PRIVATE include )
""" 

  if filepath is None:
    created_path = name
    make_project_folder(name)
  else:
    created_path = filepath
    make_project_folder(filepath)

  cmake_project = default_project_template.replace("%project_name%", name).replace("%languages%", languages)

  cmake_fd = io.open(created_path + '/CMakeLists.txt', 'w')
  cmake_fd.write(cmake_project)
  cmake_fd.flush()
  cmake_fd.close()

  print('Done! Use `cd ' + created_path + '` to navigate to ' + name + '.')


# Walks the defined subdirectory searching for compatible file extensions to add to the
# headers and sources list, returns a list of formatted paths from root directory
def seek_sources (subfolder, settings):
  resulting_paths = []

  for root, _, files in os.walk(subfolder):
    for file in files:
      if file.endswith(language_extensions):
        # even on Windows we want to keep foward slashes
        path = '\t{}/{}\n'.format(subfolder, os.path.relpath(os.path.join(root, file), subfolder).replace('\\', '/'))

        if not settings.use_tabs:
          path = path.expandtabs(settings.expanded_spaces)

        resulting_paths.append(path)

  # If there's no files to add, write a comment
  if len(resulting_paths) == 0:
    no_paths_comment = '\t# project {}'.format('sources' if subfolder == 'src' else 'headers')

    if not settings.use_tabs:
      no_paths_comment = no_paths_comment.expandtabs(settings.expanded_spaces)

    resulting_paths.append()

  return resulting_paths

# Reads in cmake list file, takes in current list of sources and headers, then checks
# the project directory for additional sources and headers (limited to include and src
# folder and sub directories)
def update_cmakelist_sources ():
  settings = NPSettings()
  settings.read()

  search_data = { 'src': ['set', 'SRCS'], 'include': ['set', 'HDR'] }

  # open and read entire cmake file, before closing
  cmake_fd = io.open('CMakeLists.txt', 'rt')
  lines = cmake_fd.readlines()
  cmake_fd.close()

  seek_end = False

  for update_section in search_data:
    for index, line in enumerate(lines):
      if not seek_end:
        if all(word in line for word in search_data[update_section]):
          start_index = index + 1
          seek_end = True
      else:
        if line.startswith(')'):
          seek_end = False
          end_index = index

    new_files = seek_sources(update_section, settings)
    del lines[start_index:end_index]
    lines[start_index:0] = new_files
    
  # rewrite entire file:
  cmake_fd = io.open('CMakeLists.txt', 'w')
  cmake_fd.writelines(lines)
  cmake_fd.flush()
  cmake_fd.close()


# Program start, parse command line args, and execute accordingly.
if __name__=="__main__":
  parser = argparse.ArgumentParser(description='Create a new project for specified directory.')
  parser.add_argument('-n', '--name')
  parser.add_argument('-u', '--update', help='Update current project with latest source tree.', action='store_true')
  parser.add_argument('-fp', '--filepath', help='Choose file path if name of project is not desired file path.')
  parser.add_argument('-l', '--language', help='Select language to use [C/CXX].')

  args = parser.parse_args()

  if args.name is None and not args.update:
    print('You must either set a name or update the current folder.')
    parser.print_help()
  else:
    if not args.update:
      if args.language is None:
        create_project(args.name, args.filepath)
      elif args.language.lower() in supported_languages:
        create_project(args.name, args.filepath, args.language.upper())
      else:
        print('Language ' + args.language + ' not supported, options are \'C\' or \'CXX\'');
    else:
      if os.path.exists('CMakeLists.txt'):
        update_cmakelist_sources()
      else:
        print('Current directory does not have a CMakeLists.txt')
