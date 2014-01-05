from __future__ import unicode_literals, absolute_import
from .graph import Node, Rel


class Serializer(object):
    """Serializer to a data structure compatible with the JSON Graph
    Specification. Serialization is incremental and after each call the
    current output is returned from `serialize`.

    See https://github.com/bruth/json-graph-spec for more information.
    """
    def __init__(self):
        self.indexes = {}
        self.data = {
            'nodes': [],
            'rels': [],
        }
        self.node_index = 0
        self.rel_index = 0

    def _add_node(self, node):
        data = {'props': node.serialize()}
        if node.labels:
            data['labels'] = list(node.labels)
        if node.match_props is not None:
            data['match'] = node.match_props
        if node.update_props is not None:
            data['update'] = node.update_props
        self.data['nodes'].append(data)
        self.indexes[node.id] = self.node_index
        self.node_index += 1

    def _add_rel(self, rel):
        data = {
            'start': self.indexes[rel.start.id],
            'end': self.indexes[rel.end.id],
            'type': rel.type,
            'props': rel.serialize()
        }
        if rel.match_props is not None:
            data['match'] = rel.match_props
        if rel.update_props is not None:
            data['update'] = rel.update_props
        self.data['rels'].append(data)
        self.indexes[rel.id] = self.rel_index
        self.rel_index += 1

    def _serialize_rel(self, rel):
        if rel.id not in self.indexes:
            if rel.start.id not in self.indexes:
                self._add_node(rel.start)

            if rel.end.id not in self.indexes:
                self._add_node(rel.end)

            self._add_rel(rel)

    def _serialize_node(self, node, traverse=True):
        if node.id not in self.indexes:
            self._add_node(node)

        if traverse:
            for rel in node.rels():
                self._serialize_node(rel.end, traverse=traverse)
                self._serialize_rel(rel)

    def serialize(self, node, traverse=True):
        "Prepares a node or relationship for export."
        if isinstance(node, Node):
            self._serialize_node(node, traverse=traverse)
        elif isinstance(node, Rel):
            self._serialize_rel(node)
        elif isinstance(node, (tuple, list)):
            for item in node:
                self.serialize(item, traverse=traverse)
        else:
            raise TypeError('unable to prepare objects with type "{}"'
                            .format(type(node)))
        return self.data


def serialize(*args, **kwargs):
    "Convenience method one-off serialization."
    serializer = Serializer()
    return serializer.serialize(*args, **kwargs)
