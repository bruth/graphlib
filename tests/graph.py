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
        self.assertEqual(list(Node()), [])

    def test_relate(self):
        n0, n1, n2, n3 = Node(), Node(), Node(), Node()

        r0, r2 = n0.relate([n1, n2], 'CONTAINS')
        r1, r3 = n0.relate([n1, n3], 'RELATED')

        self.assertTrue(n0.related(n1))
        self.assertTrue(n0.related(n2))
        self.assertTrue(n0.related(n3, 'RELATED'))

        self.assertCountEqual(n0.rels(), [r0, r1, r2, r3])
        self.assertCountEqual(n0.rels(node=n1), [r0, r1])
        self.assertCountEqual(n0.rels(type='CONTAINS'), [r0, r2])
        self.assertCountEqual(n0.rels(node=n1, type='RELATED'), [r1])
        self.assertCountEqual(n0.rels(node=n0, type='FOO'), [])

    def test_relate_type_once(self):
        n0, n1 = Node(), Node()

        r0 = n0.relate(n1, 'CONTAINS')
        r0p = n0.relate(n1, 'CONTAINS', {'one': 1})
        r0d = n0.relate(n1, 'CONTAINS')
        self.assertEqual(r0p, r0)
        self.assertEqual(r0d, r0)
        self.assertEqual(r0p.props, {'one': 1})
        self.assertEqual(r0d.props, {'one': 1})

    def test_unrelate_node(self):
        n0, n1, n2, n3 = Node(), Node(), Node(), Node()

        n0.relate([n1, n2, n3], 'CONTAINS')
        n0.relate([n1, n2], 'RELATED')

        # Node
        self.assertEqual(n0.unrelate(n1), 2)
        # Type
        self.assertEqual(n0.unrelate(type='RELATED'), 1)
        # Node and Type
        self.assertEqual(n0.unrelate(n3, type='CONTAINS'), 1)
        # All
        self.assertEqual(n0.unrelate(), 1)
        # None left
        self.assertEqual(n0.unrelate(n1, type='RELATED'), 0)

        self.assertFalse(n0.related(n1))
        self.assertFalse(n0.related(n2))
        self.assertFalse(n0.related(n3))

        self.assertEqual(n0.rels(), [])


class RelTestCase(unittest.TestCase):
    def test(self):
        n0, n1 = Node(), Node()
        r = n0.relate(n1, 'CONTAINS')
        self.assertTrue(r.related())
        r.unrelate()
        self.assertFalse(r.related())
        r.relate()
        self.assertTrue(r.related())


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
