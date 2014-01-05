# Graph Library

[![Build Status](https://travis-ci.org/bruth/graphlib.png?branch=master)](https://travis-ci.org/bruth/graphlib) [![Coverage Status](https://coveralls.io/repos/bruth/graphlib/badge.png)](https://coveralls.io/r/bruth/graphlib)

Graph API and serializer for the [JSON Graph Spec](https://github.com/bruth/json-graph-spec)

## Install

```
pip install graphlib
```

## Usage

### Create

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

```python
from graphlib import serialize

data = serialize(office)
```
