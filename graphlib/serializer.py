from __future__ import unicode_literals, absolute_import
from .graph import Node, Rel

# Alias str to unicode with unicode_literals imported
try:
    str = unicode
except NameError:
    pass


class Serializer(object):
    """Serializer to a data structure compatible with the JSON Graph
    Specification. Serialization is incremental and after each call the
    current output is returned from `serialize`.

    See https://github.com/bruth/json-graph-spec for more information.
    """
    def __init__(self):
        self.stack = []
        self.indexes = {}
        self.items = []
        self.index = 0

    def _add_node(self, node):
        data = {'props': node.serialize()}

        if node.labels:
            data['labels'] = list(node.labels)

        if node.match_props is not None:
            data['match'] = node.match_props

        if node.update_props is not None:
            data['update'] = node.update_props

        self.items.append(data)
        self.indexes[node] = self.index
        self.index += 1

    def _add_rel(self, rel):
        data = {
            'start': self.indexes[rel.start],
            'end': self.indexes[rel.end],
            'type': rel.type,
            'props': rel.serialize()
        }

        if rel.match_props is not None:
            data['match'] = rel.match_props

        if rel.update_props is not None:
            data['update'] = rel.update_props

        self.items.append(data)
        self.indexes[rel] = self.index
        self.index += 1

    def _serialize_rel(self, rel):
        if rel not in self.indexes:
            if rel.start not in self.indexes:
                self._add_node(rel.start)

            if rel.end not in self.indexes:
                self._add_node(rel.end)

            self._add_rel(rel)

    def _serialize_node(self, node, traverse):
        if node not in self.indexes:
            self._add_node(node)

        if traverse:
            for rel in node.rels():
                if rel.start not in self.indexes:
                    self.stack.append(rel.start)
                if rel.end not in self.indexes:
                    self.stack.append(rel.end)
                if rel not in self.indexes:
                    self.stack.append(rel)

    def _serialize(self, item, traverse):
        if isinstance(item, Node):
            self._serialize_node(item, traverse)
        else:
            self._serialize_rel(item)

    def serialize(self, item, traverse=True):
        "Prepares a node or relationship for export."
        if isinstance(item, (Node, Rel)):
            self.stack.append(item)
        elif isinstance(item, (tuple, list)):
            self.stack.extend(item)
        else:
            raise TypeError('unable to prepare objects with type "{}"'
                            .format(type(item)))

        while self.stack:
            item = self.stack.pop()
            self._serialize(item, traverse)

        return self.items


def serialize(*args, **kwargs):
    "Convenience method one-off serialization."
    serializer = Serializer()
    return serializer.serialize(*args, **kwargs)


def convert_array_to_dict(items):
    "Convert an array-based format to a dict."
    data = {
        'nodes': [],
        'rels': [],
    }

    nmap = {}
    nindex = 0

    for index, item in enumerate(items):
        if 'type' in item:
            data['rels'].append(item)
        else:
            data['nodes'].append(item)
            nmap[index] = nindex
            nindex += 1

    # Map index from flat array to local node array
    for rel in data['rels']:
        rel['start'] = nmap[rel['start']]
        rel['end'] = nmap[rel['end']]

    return data


def convert_dict_to_array(data):
    "Convert a dict-based format to an array."
    items = []

    nmap = {}
    index = 0

    nodes = data.get('nodes', ())
    rels = data.get('rels', ())

    for nindex, node in enumerate(nodes):
        items.append(node)
        nmap[nindex] = index
        index += 1

    # Map index from local node array to flat index
    for rel in enumerate(rels):
        items.append(rel)
        rel['start'] = nmap[rel['start']]
        rel['end'] = nmap[rel['end']]

    return data
