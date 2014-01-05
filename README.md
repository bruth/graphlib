# Graph Library

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
