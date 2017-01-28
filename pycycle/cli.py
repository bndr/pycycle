# -*- coding: utf-8 -*-
from __future__ import print_function

import click
import crayons
import os
import sys

# local imports
from .__version__ import __version__
from pycycle.utils import read_project, get_cycle_path


def format_help(_help):
    """Formats the help string."""
    additional_help = """
    Examples:
        Get the circular imports in current project:
        $ {0}
        Look for circular imports in another project
        $ {1}

Options:""".format(
        crayons.red('pycycle --here'),
        crayons.red('pycycle --source /home/user/workspace/awesome_project'))

    _help = _help.replace('Options:', additional_help)

    return _help


@click.group(invoke_without_command=True)
@click.option('--verbose', is_flag=True, default=False, help="Verbose output.")
@click.option('--here', is_flag=True, default=False, help="Try to find cycles in the current project")
@click.option('--source', default=False, help="Try to find cycles in the path provided")
@click.option('--help', is_flag=True, default=None, help="Show this message then exit.")
@click.version_option(prog_name=crayons.yellow('pycycle'), version=__version__)
@click.pass_context
def cli(ctx, verbose=False, help=False, source=None, here=False):
    if ctx.invoked_subcommand is None:

        if verbose:
            pass

        if source:
            source = os.path.abspath(source)
            click.echo(crayons.yellow(
                'Target source provided: {}'.format(source)))
        elif here:
            source = os.getcwd()
        else:
            # Display help to user, if no commands were passed.
            click.echo(format_help(ctx.get_help()))
            sys.exit(0)

        if not source:
            click.echo(crayons.red(
                'No project provided. Provide either --here or --source.'))

        root_node = read_project(source)

        click.echo(crayons.yellow(
            'Project successfully transformed to AST, checking imports for cycles..'))
        cycle_path = get_cycle_path(root_node)
        if cycle_path:
            click.echo(crayons.red('Cycle Found :('))
            click.echo(crayons.red(cycle_path))
            click.echo(crayons.green("Finished."))
            sys.exit(1)
        else:
            click.echo(crayons.green(('No worries, no cycles here!')))
            click.echo(crayons.green(
                'If you think some cycle was missed, please open an Issue on Github.'))
            click.echo(crayons.green("Finished."))
            sys.exit(0)
