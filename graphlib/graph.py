from __future__ import unicode_literals, absolute_import
import re
import inspect
from collections import defaultdict

# Alias str to unicode with unicode_literals imported
try:
    str = unicode
except NameError:
    pass


OUTGOING = 1
INCOMING = -1


class Props(object):
    match_props = None
    update_props = None

    def __init__(self, props=None, match_props=None, update_props=None):
        if props is None:
            self.props = {}
        elif isinstance(props, dict):
            self.props = props
        else:
            self.props = dict(props)

        # Override class-defined properties
        if match_props:
            self.match_props = match_props
        if update_props:
            self.update_props = update_props

    def __getitem__(self, key):
        return self.props[key]

    def __setitem__(self, key, value):
        self.props[key] = value

    def __delitem__(self, key):
        del self.props[key]

    def __contains__(self, key):
        return key in self.props

    def __iter__(self):
        return iter(self.props)

    def update(self, props):
        self.props.update(props)

    def serialize(self, *args, **kwargs):
        "Returns a shallow copy of the properties."
        return self.props.copy()


class Rel(Props):
    def __init__(self, start, end, type, *args, **kwargs):
        self.start = start
        self.end = end
        self.type = type
        super(Rel, self).__init__(*args, **kwargs)

    def __repr__(self):
        return '{}({}-{}->{})'.format(self.__class__.__name__,
                                      repr(self.start), self.type,
                                      repr(self.end))


class Node(Props):
    """Node class which support properties and creating directed relationships
    with other nodes.
    """
    labels = None
    relclass = Rel

    def __init__(self, *args, **kwargs):
        labels = kwargs.pop('labels', None)

        # Override class-defined labels
        if labels:
            self.labels = labels

        # Nested hash of relationships by node then type. Currently a
        # only a single relationship of the same type can be defined between
        # the same two nodes.
        # { nref : { type: rref } }
        self._outgoing = defaultdict(dict)
        self._incoming = defaultdict(dict)

        # Hash of relationship types with a set of nodes regardless of
        # direction. { type: { nref0, nref1, ... } }
        self._types = defaultdict(set)

        super(Node, self).__init__(*args, **kwargs)

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, id(self))

    def _rels_for_type(self, type, direction=None):
        rels = set()

        for node in self._types[type]:
            if not direction or direction == OUTGOING:
                if type in self._outgoing[node]:
                    rels.add(self._outgoing[node][type])

            if not direction or direction == INCOMING:
                if type in self._incoming[node]:
                    rels.add(self._incoming[node][type])

        return rels

    def _rels_for_node(self, node, direction=None):
        rels = set()

        if not direction or direction == OUTGOING:
            for type in self._outgoing[node]:
                rels.add(self._outgoing[node][type])

        if not direction or direction == INCOMING:
            for type in self._incoming[node]:
                rels.add(self._incoming[node][type])

        return rels

    def _rels_for_node_and_type(self, node, type, direction=None):
        rels = set()

        if not direction or direction == OUTGOING:
            if type in self._outgoing[node]:
                rels.add(self._outgoing[node][type])

        if not direction or direction == INCOMING:
            if type in self._incoming[node]:
                rels.add(self._incoming[node][type])

        return rels

    def _rels(self, direction=None):
        "Returns a set of rels for this node."
        rels = set()

        if not direction or direction == OUTGOING:
            for node in self._outgoing:
                rels.update(self._outgoing[node].values())

        if not direction or direction == INCOMING:
            for node in self._incoming:
                rels.update(self._incoming[node].values())

        return rels

    def _add_rel(self, rel):
        "Adds a relation to the start and end node."
        rel.start._outgoing[rel.end][rel.type] = rel
        rel.start._types[rel.type].add(rel.end)
        rel.end._incoming[rel.start][rel.type] = rel
        rel.end._types[rel.type].add(rel.start)

    def _remove_rel(sel, rel):
        del rel.start._outgoing[rel.end][rel.type]
        rel.start._types[rel.type].discard(rel.end)
        del rel.end._incoming[rel.start][rel.type]
        rel.end._types[rel.type].discard(rel.start)

    def _del_rel(self, node, type, direction=None):
        "Deletes a relationship for a node and a type."
        count = 0
        total = 0

        if type in self._outgoing[node]:
            if not direction or direction == OUTGOING:
                rel = self._outgoing[node][type]
                self._remove_rel(rel)
                count += 1
            else:
                total += 1

        if type in self._incoming[node]:
            if not direction or direction == INCOMING:
                rel = self._incoming[node][type]
                self._remove_rel(rel)
                count += 1
            else:
                total += 1

        # None left in either direction.
        if total == 0:
            self._types[type].discard(node)

        return count

    def _del_rels_for_node_and_type(self, node, type, direction=None):
        "Deletes all relationships of type."
        return self._del_rel(node, type, direction=direction)

    def _del_rels_for_type(self, type, direction=None):
        "Deletes all relationships of type."
        count = 0

        for node in tuple(self._types[type]):
            count += self._del_rel(node, type, direction=direction)

        return count

    def _del_rels_for_node(self, node, direction=None):
        "Deletes all relationships for node."
        count = 0

        if not direction or direction == OUTGOING:
            for type in list(self._outgoing[node]):
                count += self._del_rel(node, type, direction=OUTGOING)

        if not direction or direction == INCOMING:
            for type in list(self._incoming[node]):
                count += self._del_rel(node, type, direction=INCOMING)

        return count

    def _del_rels(self, direction=None):
        "Deletes all relationships."
        count = 0

        if not direction or direction == OUTGOING:
            for node in list(self._outgoing):
                for type in list(self._outgoing[node]):
                    count += self._del_rel(node, type, direction=OUTGOING)

        if not direction or direction == INCOMING:
            for node in list(self._incoming):
                for type in list(self._incoming[node]):
                    count += self._del_rel(node, type, direction=INCOMING)

        return count

    def _parse_direction(self, **kwargs):
        direction = kwargs.get('direction')

        if direction:
            assert direction == INCOMING or direction == OUTGOING, \
                'A direction must be defined for the relationship'
        else:
            incoming = kwargs.get('incoming')
            outgoing = kwargs.get('outgoing')

            if incoming and outgoing:
                direction = None
            elif incoming:
                direction = INCOMING
            elif outgoing:
                direction = OUTGOING
            else:
                direction = None

        return direction

    @property
    def degree(self):
        "Returns the number of neighboring nodes."
        return len(self.neighbors)

    @property
    def neighbors(self):
        "Returns the neighboring nodes."
        s = set()
        for type in self._types:
            s |= self._types[type]
        return Nodes(s)

    def relate(self, node, type, props=None, direction=OUTGOING, **kwargs):
        "Adds a relationship to node if it does not already exist."
        if isinstance(node, (list, tuple)):
            rels = []

            for _node in node:
                rel = self.relate(_node, type, props, direction, **kwargs)
                rels.append(rel)

            return Rels(rels)

        relclass = kwargs.pop('relclass', self.relclass)

        assert isinstance(node, Node), 'End node must be a Node instance'
        assert isinstance(type, (str, bytes)), 'Type must be a string'
        assert direction == OUTGOING or direction == INCOMING, \
            'A direction must be defined for the relationship'

        rel = None

        # Update the relationship if it already exists
        if direction == OUTGOING:
            if type in self._outgoing[node]:
                rel = self._outgoing[node][type]
        else:
            if type in self._incoming[node]:
                rel = self._incoming[node][type]

        if rel:
            if props:
                rel.update(props)
        else:
            if direction == OUTGOING:
                rel = relclass(self, node, type, props=props, **kwargs)
            else:
                rel = relclass(node, self, type, props=props, **kwargs)
            self._add_rel(rel)

        return rel

    def unrelate(self, node=None, type=None, **kwargs):
        "Deletes a relationship."
        direction = self._parse_direction(**kwargs)

        if node and type:
            count = self._del_rels_for_node_and_type(node, type,
                                                     direction=direction)
        elif node:
            count = self._del_rels_for_node(node, direction=direction)
        elif type:
            count = self._del_rels_for_type(type, direction=direction)
        else:
            count = self._del_rels(direction=direction)

        return count

    def related(self, node, type=None, **kwargs):
        "Returns true if the node is related, optionally by a type."
        direction = self._parse_direction(**kwargs)

        if not direction or direction == OUTGOING:
            if self._outgoing[node]:
                if type:
                    if type in self._outgoing[node]:
                        return True
                else:
                    return True

        if not direction or direction == INCOMING:
            if self._incoming[node]:
                if type:
                    if type in self._incoming[node]:
                        return True
                else:
                    return True

        return False

    def rels(self, node=None, type=None, **kwargs):
        "Returns relations for the node, optionally filtered by type."
        direction = self._parse_direction(**kwargs)

        if node and type:
            rels = self._rels_for_node_and_type(node, type, direction)
        elif node:
            rels = self._rels_for_node(node, direction)
        elif type:
            rels = self._rels_for_type(type, direction)
        else:
            rels = self._rels(direction)

        return Rels(rels)


class DictSeq(tuple):
    """Immutable sequence of items which supports dict-like access. Items are
    ordered in the order they were provided. They can be accessed by index
    or by key, where the key is the `str` representation of the item.

    Key-based accessed is case-insensitive.
    """
    def __init__(self, *args):
        self._map = {str(n).lower(): i for i, n in enumerate(self)}

    def __eq__(self, other):
        "Equality based on the items contained."
        if not hasattr(other, '__iter__'):
            return False

        if len(self) != len(other):
            return False

        for i, x in enumerate(self):
            if other[i] != x:
                return False

        return True

    def __ne__(self, other):
        "Equality based on the items contained."
        return not self == other

    def __getitem__(self, key):
        """Supports standard index/slice access, key-based access by name
        and multi-item access via passing an non-string iterable.
        """
        if isinstance(key, (int, slice)):
            return tuple.__getitem__(self, key)
        elif isinstance(key, (str, bytes)):
            key = str(key).lower()
        elif hasattr(key, '__iter__'):
            return Nodes(self[_key] for _key in key)

        key = self._map[key]

        return tuple.__getitem__(self, key)

    def filter(self, key, value=None):
        """Filters the items in this container and returns a new container.
        The most common filtering is by property, so a key and value can be
        supplied as a shorthand, otherwise a filter function must be passed.
        """
        if isinstance(key, (str, bytes)):
            def func(item):
                if key in item:
                    if value is not None:
                        return item[str(key)] == value
                    return True
                return False
        else:
            func = key
            if not inspect.isfunction(func):
                raise TypeError('filter requires key/value or function')

        return self.__class__(filter(func, self))

    def sort(self, key):
        """Sorts the items in this container and returns a new container.
        The most common sorting is by property, so a key can be supplied
        as a shorthand, otherwise a sort function must be passed.
        """
        if isinstance(key, (str, bytes)):
            func = lambda n: n.props.get(str(key))
        else:
            func = key
            if not inspect.isfunction(func):
                raise TypeError('sort requires key or function')

        return self.__class__(sorted(self, key=func))

    def match(self, regexp, flags=re.I):
        "Returns one or more items that match the regexp on the key."
        r = re.compile(regexp, flags)
        return self.__class__(self[key] for key in self._map if r.match(key))


class Rels(DictSeq):
    "Tuple of relationships."
    def nodes(self):
        return Nodes({rel.end for rel in self})


class Nodes(DictSeq):
    "Tuple of nodes."
