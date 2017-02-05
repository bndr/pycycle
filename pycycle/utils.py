import ast
import codecs
import os
import sys
import traceback
import click
import crayons
import re


if sys.version_info[0] > 2:
    open_func = open
else:
    open_func = codecs.open

REGEX_RELATIVE_PATTERN = re.compile('from \.')


class Node(object):

    def __init__(self, name, imports=None, full_path=None, line_no=None):
        self.name = name
        if not imports:
            self.imports = []
        else:
            self.imports = imports

        self.line_no = line_no
        self.full_path = full_path
        self.marked = 0
        self.func_imports = {}
        self.func_defs = {}
        self.is_in_context = False

    def __iter__(self):
        return iter(self.imports)

    def add(self, item):
        self.imports.append(item)

    def __repr__(self):
        return str(len(self.imports))


def read_project(root_path, verbose=False, ignore=None, encoding=None):
    """
    Reads project into an AST and transforms imports into Nodes
    :param root_path: String
    :return: Node
    """
    nodes = {}
    root_node = None
    errors = False
    ignore_files = set([".hg", ".svn", ".git", ".tox", "__pycache__", "env", "venv"]) # python 2.6 comp

    if ignore:
        for ignored_file in ignore:
            ignore_files.add(os.path.basename(os.path.realpath(ignored_file)))

    # traverse root directory, and list directories as dirs and files as files
    for root, dirs, files in os.walk(root_path):

        dirs[:] = [d for d in dirs if d not in ignore_files]

        files = [fn for fn in files if os.path.splitext(fn)[1] == ".py" and fn not in ignore_files]

        for file_name in files:
            full_path = os.path.join(root, file_name)
            with open_func(full_path, "r", encoding=encoding) as f:
                try:
                    # fails on empty files
                    file_data = f.read()
                    lines = file_data.splitlines()
                    tree = ast.parse(file_data)
                    if verbose:
                        click.echo(crayons.yellow('Trying to parse file: {}'.format(full_path)))

                    if full_path in nodes:
                        node = nodes[full_path]
                    else:
                        node = Node(file_name[:-3], full_path=full_path)
                        nodes[full_path] = node

                    if not root_node:
                        root_node = node

                    for ast_node in ast.walk(tree):
                        if isinstance(ast_node, ast.Import) and ast_node.names:
                            for subnode in ast_node.names:
                                if not subnode.name:
                                    continue

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

                        elif isinstance(ast_node, ast.ImportFrom) and ast_node.module:
                            current_path = root_path
                            if 0 <= ast_node.lineno - 1 < len(lines) and\
                                    REGEX_RELATIVE_PATTERN.findall(lines[ast_node.lineno - 1]):
                                current_path = root

                            path_to_module = get_path_from_package_name(
                                current_path, ast_node.module)

                            if path_to_module in nodes:
                                new_node = nodes[path_to_module]
                            else:
                                new_node = Node(
                                    ast_node.module, full_path=path_to_module)
                                nodes[path_to_module] = new_node

                            for obj_import in ast_node.names:
                                if ast_node.lineno not in node.func_imports:
                                    node.func_imports[ast_node.lineno] = [obj_import.name]
                                else:
                                    node.func_imports[ast_node.lineno].append(obj_import.name)

                            node.line_no = ast_node.lineno
                            node.add(new_node)
                        elif isinstance(ast_node, (ast.ClassDef, ast.FunctionDef)):
                            node.func_defs[ast_node.name] = ast_node.lineno

                except Exception as e:
                    errors = True
                    click.echo(crayons.yellow('Parsing of file failed: {}'.format(full_path)))
                    if verbose:
                        click.echo(crayons.red(traceback.format_exc(e)))

    if errors:
        click.echo(crayons.red('There were errors during the operation, perhaps you are trying to parse python 3 project, '
                               'with python 2 version of the script? (or vice versa)'))
    return root_node


def get_path_from_package_name(root, pkg):
    if not pkg or not root:
        return ''
    modules = pkg.split(".")
    return os.path.join(root, os.sep.join(modules) + '.py')


def check_if_cycles_exist(root):

    previous = None
    queue = [root]
    while queue:
        current_node = queue.pop()
        if current_node.marked > 1:
            return not current_node.is_in_context

        for item in current_node:
            if item.marked and previous:
                for lineno, imports in previous.func_imports.items():
                    for import_obj in imports:
                        if import_obj in item.func_defs\
                                and item.line_no > item.func_defs[import_obj]:
                            item.is_in_context = True
            previous = item
            queue.append(item)

        current_node.marked += 1

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
