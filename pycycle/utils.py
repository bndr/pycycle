import ast
import codecs
import os
import sys
import traceback
import click
import crayons
from pycycle.graph.nodes import Node

if sys.version_info[0] > 2:
    open_func = open
else:
    open_func = codecs.open


def read_project(root_path):
    """
    Reads project into an AST and transforms imports into Nodes
    :param root_path: String
    :return: Node
    """
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
    if len(path) > 1:
        return ' -> '.join([crayons.yellow(x.name) + ': Line ' + crayons.cyan(x.line_no) for x in path])\
               + ' =>> ' + crayons.magenta(path[0].name)
    else:
        return ''


def get_cycle_path(root, acc=[], seen=set()):
    for item in root:
        if item.full_path in seen:
            return format_path(acc)
        seen.add(item.full_path)
        if item.imports:
            acc.append(item)
            return get_cycle_path(item, acc, seen)

    return ''
