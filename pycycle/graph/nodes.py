
class Node(object):

    def __init__(self, name, imports=None, full_path=None, line_no=None):
        self.name = name
        if not imports:
            self.imports = []
        else:
            self.imports = imports

        self.line_no = line_no
        self.full_path = full_path
        self.marked = False

    def __iter__(self):
        return iter(self.imports)

    def add(self, item):
        self.imports.append(item)

    def __repr__(self):
        return str(len(self.imports))
