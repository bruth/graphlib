from __future__ import unicode_literals, absolute_import
from collections import deque
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
        self.queue = deque()
        self.indexes = {}
        self.items = []
        self.batches = []
        self.index = 0

        # 1 - node, 2 - rel
        self._batch = None
        self._batch_type = None

    def _queue(self, item):
        if item not in self.indexes and item not in self.queue:
            if isinstance(item, Node):
                self.queue.append(item)
            elif isinstance(item, Rel):
                self._queue(item.start)
                self._queue(item.end)
                self.queue.append(item)

    def _batch_item(self, item, data):
        item_type = 'type' in data and 2 or 1

        # Append and reset the batch
        if item_type != self._batch_type:
            # Reset and append the reference
            self._batch = []
            self.batches.append(self._batch)
            self._batch_type = item_type

        self._batch.append(data)

    def _add_item(self, item, data):
        self.items.append(data)
        self.indexes[item] = self.index
        self.index += 1
        self._batch_item(item, data)

    def _add_node(self, node):
        data = {'props': node.serialize()}

        if node.labels:
            data['labels'] = list(node.labels)

        if node.match_props is not None:
            data['match'] = node.match_props

        if node.update_props is not None:
            data['update'] = node.update_props

        self._add_item(node, data)

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

        self._add_item(rel, data)

    def _serialize_rel(self, rel):
        self._add_rel(rel)

    def _serialize_node(self, node, traverse):
        # Add the node to the items
        self._add_node(node)

        if traverse:
            # Queue neighbors for traversal
            for node in node.neighbors:
                self._queue(node)

            # Queue relationships to neighbors. The start and end
            # nodes are guaranteed to be queued first, so there is
            # not need to queue them here.
            for rel in node.rels():
                self._queue(rel)

    def _serialize(self, item, traverse):
        if isinstance(item, Node):
            self._serialize_node(item, traverse)
        else:
            self._serialize_rel(item)

    def serialize(self, item, traverse=True):
        "Prepares a node or relationship for export."
        if isinstance(item, (Node, Rel)):
            self._queue(item)
        elif isinstance(item, (tuple, list)):
            for _item in item:
                self._queue(_item)
        else:
            raise TypeError('unable to prepare objects with type "{}"'
                            .format(type(item)))

        while self.queue:
            item = self.queue.popleft()
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
