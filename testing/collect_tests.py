from __future__ import print_function  # Only Python 2.x
import glob
import subprocess
import os
import sys
import datetime
import time
import docopt
import colorama

from parse import extract_menu_file
from env import get_ci_environment, get_generator, get_buildflags, get_topdir, verbose_output


def run_command(step, command, expect_failure):
    """
    step: string (e.g. 'configuring', 'building', ...); only used in printing
    command: string; this is the command to be run
    expect_failure: bool; if True we do not panic if the command fails
    """
    child = subprocess.Popen(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    stdout_coded, stderr_coded = child.communicate()
    stdout = stdout_coded.decode('UTF-8')
    stderr = stderr_coded.decode('UTF-8')

    child_return_code = child.returncode

    return_code = 0
    sys.stdout.write(colorama.Fore.BLUE + colorama.Style.BRIGHT +
                     '  {0} ... '.format(step))
    if child_return_code == 0:
        sys.stdout.write(colorama.Fore.GREEN + colorama.Style.BRIGHT +
                         'OK\n')
        if verbose_output():
            sys.stdout.write(stdout + stderr + '\n')
    else:
        if expect_failure:
            sys.stdout.write(colorama.Fore.YELLOW + colorama.Style.BRIGHT +
                             'EXPECTED TO FAIL\n')
        else:
            sys.stdout.write(colorama.Fore.RED + colorama.Style.BRIGHT +
                             'FAILED\n')
            sys.stderr.write(stdout + stderr + '\n')
            return_code = child_return_code
    sys.stdout.flush()
    sys.stderr.flush()

    return return_code


def run_example(topdir, generator, ci_environment, buildflags, recipe, example):

    # extract global menu
    menu_file = os.path.join(topdir, 'testing', 'menu.yml')
    expect_failure_global, env_global, definitions_global, targets_global = extract_menu_file(
        menu_file, generator, ci_environment)

    sys.stdout.write('\n  {}\n'.format(example))

    # extract local menu
    menu_file = os.path.join(recipe, example, 'menu.yml')
    expect_failure_local, env_local, definitions_local, targets_local = extract_menu_file(
        menu_file, generator, ci_environment)

    expect_failure = expect_failure_global or expect_failure_local

    # local env vars override global ones
    env = env_global.copy()
    for entry in env_local:
        env[entry] = env_local[entry]

    # local definitions override global ones
    definitions = definitions_global.copy()
    for entry in definitions_local:
        definitions[entry] = definitions_local[entry]

    # local targets extend global targets
    targets = targets_global + targets_local

    env_string = ' '.join('{0}={1}'.format(entry, env[entry])
                          for entry in env)
    definitions_string = ' '.join('-D{0}={1}'.format(
        entry, definitions[entry]) for entry in definitions)

    # we append a time stamp to the build directory
    # to avoid it being re-used when running tests multiple times
    # when debugging on a laptop
    time_stamp = datetime.datetime.fromtimestamp(
        time.time()).strftime('%Y-%m-%d-%H-%M-%S')
    build_directory = os.path.join(recipe, example,
                                   'build-{0}'.format(time_stamp))
    cmakelists_path = os.path.join(recipe, example)

    return_code = 0

    # configure step
    step = 'configuring'
    command = '{0} cmake -H{1} -B{2} -G"{3}" {4}'.format(
        env_string, cmakelists_path, build_directory, generator,
        definitions_string)
    return_code += run_command(
        step=step,
        command=command,
        expect_failure=expect_failure)

    # build step
    step = 'building'
    command = 'cmake --build {0} -- {1}'.format(build_directory, buildflags)
    return_code += run_command(
        step=step,
        command=command,
        expect_failure=expect_failure)

    # extra targets
    for target in targets:
        step = target
        command = 'cmake --build {0} --target {1}'.format(build_directory, target)
        return_code += run_command(
            step=step,
            command=command,
            expect_failure=expect_failure)

    return return_code


def main(arguments):
    topdir = get_topdir()
    buildflags = get_buildflags()
    generator = get_generator()
    ci_environment = get_ci_environment()

    # glob recipes
    recipes = [
        r
        for r in sorted(glob.glob(os.path.join(topdir, arguments['<regex>'])))
    ]

    # Set NINJA_STATUS environment variable
    os.environ['NINJA_STATUS'] = '[Built edge %f of %t in %e sec]'

    colorama.init(autoreset=True)
    return_code = 0
    for recipe in recipes:

        # extract title from README.md
        with open(os.path.join(recipe, 'README.md'), 'r') as f:
            for line in f.read().splitlines():
                if line[0:2] == '# ':
                    print(colorama.Back.BLUE +
                          '\nrecipe: {0}'.format(line[2:]))

        # Glob examples
        examples = [
            e for e in sorted(glob.glob(os.path.join(recipe, '*example')))
        ]

        for example in examples:
            return_code += run_example(topdir, generator, ci_environment, buildflags, recipe, example)


    colorama.deinit()
    sys.exit(return_code)


if __name__ == '__main__':
    options = """Run continuous integration

    Usage:
        collect_tests.py <regex>
        collect_tests.py (-h | --help)

    Options:
        -h --help     Show this screen.

    """
    # parse command line args
    try:
        arguments = docopt.docopt(options, argv=None)
    except docopt.DocoptExit:
        sys.stderr.write('ERROR: bad input to {0}\n'.format(sys.argv[0]))
        sys.stderr.write(options)
        sys.exit(-1)
    main(arguments)
