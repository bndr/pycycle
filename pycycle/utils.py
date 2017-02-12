import ast
import codecs
from collections import defaultdict
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

        self.is_imported_from = defaultdict(list)
        self.full_path = full_path
        self.marked = 0
        self.parent = None
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

                                new_node.is_imported_from[full_path].append(ast_node.lineno)
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

                            new_node.is_imported_from[full_path].append(ast_node.lineno)
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


def get_import_context(node):
    """
    Go backs up the graph to the import that started this possible cycle,
    and gets the import line number
    :param node:
    :return: int
    """
    name = node.name
    seen = set()
    while node.parent and node.parent.parent:
        node = node.parent
        if node in seen or (node.parent and node.parent.name == name):
            break
        seen.add(node)

    # Should never fail because we take the full_path of the parent. And as the parent imports this child
    # there should at least be one number in the array
    return node.is_imported_from[node.parent.full_path][0]


def check_if_cycles_exist(root):
    """
    Goes through all nodes and looks for cycles, takes python import logic into account
    :param root:
    :return: bool
    """
    previous = None
    queue = [root]
    while queue:
        current_node = queue.pop()
        if current_node.marked > 1:
            return not current_node.is_in_context

        for item in current_node.imports:

            # Mark the current node as parent, so that we could trace the path from this node to the start node.
            item.parent = current_node
            if item.marked and previous:

                # This is a possible cycle, but maybe the import statement that started this all is under the function
                # definition that is required
                import_that_started = get_import_context(item)
                for lineno, imports in previous.func_imports.items():
                    for import_obj in imports:
                        # Compare the function definition line with the import line
                        if import_obj in item.func_defs\
                                and import_that_started > item.func_defs[import_obj]:
                            item.is_in_context = True
            previous = item
            queue.append(item)

        current_node.marked += 1

    return False


def format_path(path):
    """
    Format the cycle with colors
    :param path:
    :return: str
    """
    if len(path) > 1:
        result = [crayons.yellow(path[0].name)]

        previous = path[0]
        for item in path[1:]:
            result.append(' -> ')
            result.append(crayons.yellow(item.name))
            result.append(': Line ')
            result.append(crayons.cyan(str(item.is_imported_from[previous.full_path][0])))
            previous = item
        result.append(' =>> ')

        result.append(crayons.magenta(path[0].name))
        return ''.join(str(x) for x in result)
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
