# -*- coding: utf-8 -*-
from __future__ import print_function

import click
import crayons
import codecs
import os
import ast
import sys
import traceback

# local imports
from graph.nodes import Node
from .__version__ import __version__


if sys.version_info[0] > 2:
    open_func = open
else:
    open_func = codecs.open


def read_project(root_path):
    nodes = {}
    root_node = None
    # traverse root directory, and list directories as dirs and files as files
    for root, dirs, files in os.walk(root_path):
        for file_name in files:
            _, extname = os.path.splitext(file_name)

            if extname == ".py":
                full_path = os.path.join(root, file_name)
                with open_func(full_path, "r", encoding=None) as f:
                    try:
                        # fails on empty files
                        tree = ast.parse(f.read())
                        if full_path in nodes:
                            node = nodes[full_path]
                        else:
                            node = Node(file_name[:-3], full_path=full_path)
                            nodes[full_path] = node

                        if not root_node:
                            root_node = node

                        for ast_node in ast.walk(tree):
                            if isinstance(ast_node, ast.Import):
                                for subnode in ast_node.names:
                                    path_to_module = get_path_from_package_name(
                                        root_path, subnode.name)

                                    if path_to_module in nodes:
                                        new_node = nodes[path_to_module]
                                    else:
                                        new_node = Node(
                                            subnode.name, full_path=path_to_module)
                                        nodes[path_to_module] = new_node
                                    node.line_no = ast_node.lineno
                                    node.add(new_node)

                            elif isinstance(ast_node, ast.ImportFrom):
                                path_to_module = get_path_from_package_name(
                                    root_path, ast_node.module)

                                if path_to_module in nodes:
                                    new_node = nodes[path_to_module]
                                else:
                                    new_node = Node(
                                        ast_node.module, full_path=path_to_module)
                                    nodes[path_to_module] = new_node
                                node.line_no = ast_node.lineno
                                node.add(new_node)

                    except Exception as e:
                        click.echo(crayons.red(traceback.print_exc(e)))

    return root_node


def get_path_from_package_name(root, pkg):
    modules = pkg.split(".")
    return os.path.join(root, os.sep.join(modules) + '.py')


def check_if_cycles_exist(root):

    for item in root:
        if item.marked:
            return True
        item.marked = True
        if item.imports:
            return check_if_cycles_exist(item)

    return False


def format_path(path):
    return ' -> '.join([crayons.yellow(x.name) + ': Line ' + crayons.cyan(x.line_no) for x in path])\
           + ' =>> ' + crayons.magenta(path[0].name)


def get_cycle_path(root, acc=[], seen=set()):
    for item in root:
        if item.full_path in seen:
            return acc
        seen.add(item.full_path)
        if item.imports:
            acc.append(item)
            get_cycle_path(item)
            return format_path(acc) if len(acc) > 1 else ''
    return acc


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
            click.echo(crayons.yellow('Target source provided: {}'.format(source)))
        elif here:
            source = os.getcwd()
        else:
            # Display help to user, if no commands were passed.
            click.echo(format_help(ctx.get_help()))
            sys.exit(0)

        if not source:
            click.echo(crayons.red('No project provided. Provide either --here or --source.'))

        root_node = read_project(source)

        click.echo(crayons.yellow('Project successfully transformed to AST, checking imports for cycles..'))
        cycle_path = get_cycle_path(root_node)
        if cycle_path:
            click.echo(crayons.red('Cycle Found :('))
            click.echo(crayons.red(cycle_path))
            click.echo(crayons.green("Finished."))
            sys.exit(1)
        else:
            click.echo(crayons.green(('No worries, no cycles here!')))
            click.echo(crayons.green('If you think some cycle was missed, please open an Issue on Github.'))
            click.echo(crayons.green("Finished."))
            sys.exit(0)


