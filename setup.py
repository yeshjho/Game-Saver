from cx_Freeze import setup, Executable
# Dependencies are automatically detected, but it might need
# fine tuning.
buildOptions = dict(packages = [], excludes = [], includes = ["PyQt5"], include_files = ["locations.txt", 'options.txt', 'constants.py'])
import sys
base = 'Console' if sys.platform=='win32' else None
executables = [
    Executable('main.py', base=base)
]
setup(
    name='Game Saver',
    version = '1.0',
    description = 'A Game Saver',
    options = dict(build_exe = buildOptions),
    executables = executables, requires=[]
)