# Graph Library

[![Build Status](https://travis-ci.org/bruth/graphlib.png?branch=master)](https://travis-ci.org/bruth/graphlib) [![Coverage Status](https://coveralls.io/repos/bruth/graphlib/badge.png)](https://coveralls.io/r/bruth/graphlib)

Graph API, serializer, and loader that conforms to the [JSON Graph Spec](https://github.com/bruth/json-graph-spec).

## Install

```
pip install graphlib
```

## Usage

### Create

The object API makes it simple to create nodes and relationships between them.

```python
from graphlib import Node

office = Node()
jane = Node()
john = Node()
bob = Node()

jane.relate(office, 'WORKS_IN')
john.relate(office, 'WORKS_IN')
bob.relate(office, 'WORKS_IN')

jane.relate([john, bob], 'MANAGES')
john.relate(bob, 'WORKS_WITH')
```

### Serialize

Serializes the object reprsentations into dicts and lists which can be encoded as JSON or loaded into a graph database.

```python
from graphlib import serialize

data = serialize(office)
```

### Load

Takes the serialized data and loads it into a database. This example loads it into Neo4j.

```python
from graphlib import neo4j

neo4j.load(data)
```
