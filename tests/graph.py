from __future__ import unicode_literals, absolute_import

import sys
import unittest
from graphlib import Node, Nodes

if sys.version_info < (3, 0):
    unittest.TestCase.assertCountEqual = unittest.TestCase.assertItemsEqual


class GraphTestCase(unittest.TestCase):
    def test_init(self):
        self.assertEqual(Node([('one', 1)]).props, {'one': 1})
        self.assertEqual(Node({'one': 1}).props, {'one': 1})
        self.assertEqual(Node().props, {})

    def test_props(self):
        n = Node()
        n['one'] = 1
        self.assertEqual(n['one'], 1)
        del n['one']
        self.assertFalse('one' in n)

    def test_iter(self):
        self.assertEqual(list(Node({'key': 'value'})), ['key'])

    def test_parse_direction(self):
        s = Node()
        self.assertIsNone(s._parse_direction(incoming=True, outgoing=True))
        self.assertIsNone(s._parse_direction())

        self.assertEqual(s._parse_direction(direction=1), 1)
        self.assertEqual(s._parse_direction(outgoing=True), 1)
        self.assertEqual(s._parse_direction(outgoing=True), 1)
        self.assertEqual(s._parse_direction(incoming=True), -1)

    def test_degree(self):
        n0 = Node()
        n1 = Node()
        n2 = Node()
        n3 = Node()

        self.assertEqual(n0.degree, 0)

        n0.relate(n1, 'X')
        self.assertEqual(n0.degree, 1)
        self.assertEqual(n1.degree, 1)

        n0.relate(n2, 'X')
        self.assertEqual(n0.degree, 2)
        self.assertEqual(n1.degree, 1)
        self.assertEqual(n2.degree, 1)

        n2.relate(n3, 'X')
        self.assertEqual(n0.degree, 2)
        self.assertEqual(n1.degree, 1)
        self.assertEqual(n2.degree, 2)
        self.assertEqual(n3.degree, 1)

    def test_relate(self):
        s = Node()
        e = Node()

        r = s.relate(e, 'YES', direction=1)
        _r = e.relate(s, 'YES', direction=-1)
        self.assertEqual(r, _r)

        # Any relationship
        self.assertTrue(s.related(e))
        self.assertTrue(e.related(s))

        # Specific relationship
        self.assertTrue(s.related(e, 'YES'))
        self.assertTrue(e.related(s, 'YES'))

        self.assertFalse(s.related(e, 'NO'))
        self.assertFalse(e.related(s, 'NO'))

        # Specific direction
        self.assertTrue(s.related(e, 'YES', outgoing=True))
        self.assertTrue(e.related(s, 'YES', incoming=True))

        self.assertFalse(s.related(e, 'YES', incoming=True))
        self.assertFalse(e.related(s, 'YES', outgoing=True))

    def test_relate_multi(self):
        s = Node()
        o = Node()
        t = Node()
        s.relate([o, t], 'TRI')

    def test_relate_rev(self):
        s = Node()
        e = Node()

        r = e.relate(s, '-', direction=-1)
        _r = s.relate(e, '-', direction=1)
        self.assertEqual(r, _r)

    def test_relate_idempotent(self):
        s = Node()
        e = Node()

        r0 = s.relate(e, 'YES')
        r1 = s.relate(e, 'YES', {'one': 1})
        r2 = s.relate(e, 'YES')
        r3 = e.relate(s, 'YES', direction=-1)

        self.assertEqual(r1, r0)
        self.assertEqual(r2, r0)
        self.assertEqual(r3, r0)

        self.assertEqual(r0.props, {'one': 1})

    def test_unrelate(self):
        s = Node()
        e = Node()
        o = Node()

        s.relate(e, 'A')
        s.relate(e, 'B')
        s.relate(e, 'C')
        s.relate(o, 'B')
        s.relate(o, 'D')

        self.assertEqual(s.unrelate(e, 'A'), 1)
        self.assertEqual(s.unrelate(e), 2)
        self.assertEqual(s.unrelate(type='B'), 1)
        self.assertEqual(s.unrelate(), 1)

        e.relate(s, 'A')
        s.relate(e, 'A')

        self.assertEqual(s.unrelate(e, direction=1), 1)
        self.assertEqual(s.unrelate(e, direction=-1), 1)

    def test_rels(self):
        s = Node()
        e = Node()
        o = Node()

        r0 = s.relate(e, 'R')
        r1 = s.relate(e, 'A', direction=-1)
        r2 = s.relate(o, 'R')

        self.assertCountEqual(s.rels(e), [r0, r1])
        self.assertCountEqual(s.rels(e, direction=1), [r0])
        self.assertCountEqual(s.rels(e, direction=-1), [r1])

        self.assertCountEqual(s.rels(type='R'), [r0, r2])
        self.assertCountEqual(s.rels(type='R', direction=1), [r0, r2])
        self.assertCountEqual(s.rels(type='A', direction=-1), [r1])

        self.assertCountEqual(s.rels(e, type='R'), [r0])
        self.assertCountEqual(s.rels(e, type='R', direction=1), [r0])
        self.assertCountEqual(s.rels(e, type='A', direction=-1), [r1])

        self.assertCountEqual(s.rels(), [r0, r1, r2])
        self.assertCountEqual(s.rels(direction=1), [r0, r2])
        self.assertCountEqual(s.rels(direction=-1), [r1])


class DictSeqTestCase(unittest.TestCase):
    def test_filter(self):
        items = Nodes([Node({'foo': 1}), Node({'foo': 2}), Node({'foo': 2})])

        self.assertCountEqual(items.filter('foo'), items)
        self.assertCountEqual(items.filter('foo', 1), items[:1])
        self.assertCountEqual(items.filter('foo', 2), items[1:])
        self.assertCountEqual(items.filter('foo', 3), [])
        self.assertCountEqual(items.filter('bar'), [])

        # Arbitrary filter function
        f = lambda n: n == items[2]
        self.assertCountEqual(items.filter(f), items[2:])

        # Only functions and strings
        self.assertRaises(TypeError, items.filter, 10)

    def test_sort(self):
        n0 = Node({'order': 0})
        n1 = Node({'order': 1})
        n2 = Node({'order': 2})
        items = Nodes([n1, n2, n0])

        self.assertCountEqual(items.sort('order'), [n0, n1, n2])

        f = lambda a, b: cmp(a['order'], b['order'])
        self.assertCountEqual(items.sort(f), [n0, n1, n2])

    def test_match(self):
        items = Nodes([1, 2, 13])
        self.assertCountEqual(items.match(r'1'), [1, 13])
        self.assertCountEqual(items.match(r'2'), [2])

    def test_getitem(self):
        items = Nodes([1, 2])
        # Index
        self.assertEqual(items[0], 1)
        # Key
        self.assertEqual(items['1'], 1)
        # Multiple
        self.assertCountEqual(items[0, 1], [1, 2])
        # Invalid key
        self.assertRaises(KeyError, items.__getitem__, None)

    def test_equality(self):
        self.assertEqual(Nodes([1]), [1])
        self.assertNotEqual(Nodes(), 1)
        self.assertNotEqual(Nodes([1, 2]), [1])
        self.assertNotEqual(Nodes([1, 2]), [1, 3])


class RelsTestCase(unittest.TestCase):
    def test(self):
        n0, n1, n2, n3 = Node(), Node(), Node(), Node()

        n0.relate([n1, n2, n3], 'CONTAINS')
        n0.relate([n1, n2], 'RELATED')

        # Get all relationships from n0
        rels = n0.rels()
        nodes = rels.nodes()

        # Gets distinct set of end nodes of rels
        self.assertCountEqual(nodes, [n1, n2, n3])
