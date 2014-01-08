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

city = Node({'location': 'Philadelphia'})
jane = Node({'name': 'Jane'})
john = Node({'name': 'John'})
bob = Node({'name': 'Bob'})

city.relate([jane, john, bob], 'LIVES_IN')
jane.relate(john, 'MARRIED_TO')
john.relate(bob, 'FRIENDS_WITH')
```

### Serialize

Serializes the object reprsentations into dicts and lists which can be encoded as JSON or loaded into a graph database.

```python
from graphlib import serialize

data = serialize(city)
```

### Load

Takes the serialized data and loads it into a database. This example loads it into Neo4j.

```python
from graphlib import neo4j

neo4j.load(data)
```

## CLI

The Neo4j module can be used directly via the command line:

```
python -m 'graphlib.neo4j' [path/to/file.json] [--load] [uri]
```

By default, `stdin` will be read which should be valid JSON that will be parsed and converted into Cypher statements and printed to stdout. If a path supplied, the file will be read instead of stdin. If the `--load` flag is present, the statements will be executed on the Neo4j server at the default URI unless a custom URI is provided.
