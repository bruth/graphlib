from __future__ import unicode_literals, absolute_import

import unittest
from graphlib import Node, Serializer, serialize


class SerializeTestCase(unittest.TestCase):
    def test(self):
        s = Serializer()
        n = Node({'foo': 'bar', 'bar': 1})

        # Add properties for coverage
        n.labels = ['Special']
        n.match_props = ['foo']
        n.update_props = ['bar']

        rels = n.relate([Node() for _ in range(5)], 'NEXT')

        o = Node()
        n.relate(o, 'OTHER')

        # Add properties for coverage
        rels[0].match_props = ['foo']
        rels[0].update_props = ['bar']

        # Single relationship (and start and end node)
        s.serialize(rels[0])

        # Remaining rels
        s.serialize(rels[1:])

        s.serialize(n)

        # No effect
        s.serialize(n, traverse=False)
        s.serialize(rels[0])

        self.assertRaises(TypeError, s.serialize, None)

        self.assertEqual(len(s.items), 13)
        self.assertEqual(len(s.batches), 2)

    def test_serialize(self):
        self.assertTrue(serialize(Node()))
