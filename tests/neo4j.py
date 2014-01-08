from __future__ import absolute_import, unicode_literals

import os
import unittest
from graphlib import Node, serialize
from graphlib import neo4j

NEO4J_ENDPOINT = os.environ.get('NEO4J_ENDPOINT')


class Neo4jParserTestCase(unittest.TestCase):
    exporter_path = 'origins.io.neo4j'

    def setUp(self):
        n = Node({'foo': 'bar', 'baz': 10})

        # Add properties for coverage
        n.labels = ['Special']
        n.match_props = ['foo']
        n.update_props = ['baz']

        rels = []
        for i in range(5):
            rels.append(n.relate(Node({'index': i}), 'NEXT',
                        {'foo': i, 'bar': 2}))

        rels[0].match_props = ['foo']
        rels[0].update_props = ['bar']

        self.data = serialize(n)

    def test_parse_create_node(self):
        n = Node({'foo': None})
        s = 'CREATE (x0 )'
        self.assertEqual(neo4j.parse(serialize(n))[0], s)

        n['foo'] = 1
        n['bar'] = 'a'
        s = "CREATE (x0 {bar: 'a', foo: 1})"
        self.assertEqual(neo4j.parse(serialize(n))[0], s)

        n.labels = ['Special']
        s = "CREATE (x0:Special {bar: 'a', foo: 1})"
        self.assertEqual(neo4j.parse(serialize(n))[0], s)

    def test_parse_merge_node(self):
        n = Node({'foo': 1, 'bar': 'a', 'baz': None}, labels=['Special'],
                 match_props=['foo'])
        s = "MERGE (x0:Special {foo: 1}) " \
            "ON CREATE SET x0 = {bar: 'a', foo: 1} " \
            "ON MATCH SET x0.bar = 'a', x0.foo = 1"
        self.assertEqual(neo4j.parse(serialize(n))[0], s)

        # Replace properties on match
        d = serialize(n)
        d[0]['replace'] = True
        s = "MERGE (x0:Special {foo: 1}) " \
            "ON CREATE SET x0 = {bar: 'a', foo: 1} " \
            "ON MATCH SET x0 = {bar: 'a', foo: 1}"
        self.assertEqual(neo4j.parse(d)[0], s)

    def test_parse_create_rel(self):
        r = Node().relate(Node(), 'TO')
        s = 'CREATE (x0)-[:TO ]->(x1)'
        # Third statement.. after creating the nodes
        self.assertEqual(neo4j.parse(serialize(r))[2], s)

        r['foo'] = 1
        r['bar'] = 'a'
        s = "CREATE (x0)-[:TO {bar: 'a', foo: 1}]->(x1)"
        # Third statement.. after creating the nodes
        self.assertEqual(neo4j.parse(serialize(r))[2], s)

    def test_parse_merge_rel(self):
        n = Node()
        r = n.relate(Node(), 'TO', {'foo': 1, 'bar': 'a'}, match_props=['foo'])
        s = "MERGE (x0)-[x2:TO]->(x1) " \
            "ON CREATE SET x2 = {bar: 'a', foo: 1} " \
            "ON MATCH SET x2.bar = 'a', x2.foo = 1"
        # Third statement.. after creating the nodes
        self.assertEqual(neo4j.parse(serialize(r))[2], s)

    def test_parse(self):
        statements = neo4j.parse(self.data)
        self.assertTrue(statements)

    def test_load(self):
        output = neo4j.load(self.data, uri=NEO4J_ENDPOINT)
        self.assertFalse(output['errors'])
