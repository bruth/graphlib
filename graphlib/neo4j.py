#!/usr/bin/env python

from __future__ import unicode_literals, absolute_import

try:
    import requests
except ImportError:
    raise ImportError('The requests library is required to use the '
                      'Neo4j exporter module.')

# Alias str to unicode with unicode_literals imported
try:
    str = unicode
except NameError:
    pass


import json


# Default URI to Neo4j REST endpoint
DEFAULT_URI = 'http://localhost:7474/db/data/'

# Endpoint for the single transaction
TRANSACTION_URI_TMPL = '{}transaction/commit'

# Cypher statement template for a node
CREATE_NODE_STMT = 'CREATE ({ref}{labels}{props})'
MERGE_NODE_STMT = 'MERGE ({ref}{labels}{props}){oncreate}{onmatch}'

# Cypher statement template for a relationship
CREATE_REL_STMT = 'CREATE ({start})-[:{rtype}{props}]->({end})'
MERGE_REL_STMT = 'MERGE ({start})-[{ref}:{rtype}{props}]->({end}){oncreate}{onmatch}'  # noqa

# Supported property value types:
# http://docs.neo4j.org/chunked/2.0.0/graphdb-neo4j-properties.html
VALID_TYPES = (bool, int, float, str, bytes)


def cref(index):
    "Returns a Cypher reference name based on a positional index."
    return 'x{}'.format(index)


def stringify(value):
    if isinstance(value, list):
        return '[' + ', '.join([stringify(v) for v in value]) + ']'
    if isinstance(value, (str, bytes)):
        return repr(value).lstrip('u')
    if isinstance(value, bool):
        return 'true' if True else 'false'
    return repr(value)


def dict_props(props):
    "Converts a dict into a valid properties object in Cypher syntax."
    if not props:
        return ''

    toks = []

    for key, value in sorted(props.items()):
        toks.append("{}: {}".format(key, stringify(value)))

    return ' {{{}}}'.format(', '.join(toks))


def keyword_props(ref, props):
    "Converts a dict into an array of valid assignments in Cypher syntax."
    if not props:
        return ''

    toks = []

    for key, value in sorted(props.items()):
        toks.append('{}.{} = {}'.format(ref, key, stringify(value)))

    return ' ' + ', '.join(toks)


def labels_suffix(labels):
    "Returns the suffix of node labels."
    if not labels:
        return ''
    return ':' + ':'.join(labels)


def oncreate_stmt(ref, props):
    if not props:
        return ''
    props = dict_props(props)
    return ' ON CREATE SET {} ={}'.format(ref, props)


def onmatch_stmt(ref, props, replace):
    if not props:
        return ''

    if replace:
        props = dict_props(props)
        return ' ON MATCH SET {} ={}'.format(ref, props)

    props = keyword_props(ref, props)
    return ' ON MATCH SET{}'.format(props)


def create_node_stmt(index, props, labels=None):
    ref = cref(index)
    labels = labels_suffix(labels)
    props = dict_props(props)

    return CREATE_NODE_STMT.format(ref=ref, labels=labels, props=props)


def merge_node_stmt(index, props, cprops=None, uprops=None, labels=None,
                    replace=False):
    ref = cref(index)
    labels = labels_suffix(labels)
    props = dict_props(props)
    oncreate = oncreate_stmt(ref, cprops)
    onmatch = onmatch_stmt(ref, uprops, replace)

    return MERGE_NODE_STMT.format(ref=ref, labels=labels, props=props,
                                  oncreate=oncreate, onmatch=onmatch)


def create_rel_stmt(index, n1, rtype, n2, props=None):
    ref = cref(index)
    start = cref(n1)
    end = cref(n2)
    props = dict_props(props)

    return CREATE_REL_STMT.format(ref=ref, start=start, end=end, rtype=rtype,
                                  props=props)


def merge_rel_stmt(index, n1, rtype, n2, props=None, cprops=None, uprops=None,
                   replace=False):
    ref = cref(index)
    start = cref(n1)
    end = cref(n2)
    props = dict_props(props)
    oncreate = oncreate_stmt(ref, cprops)
    onmatch = onmatch_stmt(ref, uprops, replace)

    return MERGE_REL_STMT.format(ref=ref, start=start, end=end, rtype=rtype,
                                 props=props, oncreate=oncreate,
                                 onmatch=onmatch)


def send_request(uri, statements):
    "Sends a request to the transaction endpoint."
    if not uri:
        uri = DEFAULT_URI
    url = TRANSACTION_URI_TMPL.format(uri)

    data = json.dumps({
        'statements': [{'statement': ' '.join(statements)}]
    })

    headers = {
        'accept': 'application/json; charset=utf-8',
        'content-type': 'application/json',
    }

    resp = requests.post(url, data=data, headers=headers)
    resp.raise_for_status()
    return resp.json()


def pick(props, keys):
    "Returns a subset of properties given keys."
    picked = {}

    for key in keys:
        if key not in props:
            raise KeyError('{} does not exist in properties'.format(repr(key)))
        picked[key] = props[key]

    return picked


def check_prop_type(value):
    "Checks if value is a valid Neo4j primitive and raises an error if not."
    if not isinstance(value, VALID_TYPES):
        raise TypeError('{value} is not supported by Neo4j'
                        .format(repr(value)))
    return value


def clean_props(props):
    """Cleans a dict of property values. This removes keys with None values
    and ensure the values are primitives or a list of primitives supported by
    Neo4j.
    """
    if not props:
        return

    copy = {}

    for key, value in props.items():
        if value is None:
            continue

        if not isinstance(key, (str, bytes)):
            raise TypeError('property key {} must be a string'.format(key))

        # Handle lists
        if isinstance(value, (list, tuple)):
            value = [check_prop_type(v) for v in value]
        else:
            value = check_prop_type(value)

        copy[key] = value

    return copy


def parse_match_props(match, props):
    if not match:
        return {}
    elif isinstance(match, (list, tuple)):
        return pick(props, match)
    raise ValueError('match must be None, False, or a list of keys')


def parse_update_props(update, props):
    if not update:
        return props
    elif isinstance(update, (list, tuple)):
        return pick(props, update)
    raise ValueError('update must be None or a list of keys')


def parse_node(index, node):
    props = node.get('props', {})
    match = node.get('match')
    update = node.get('update')
    replace = node.get('replace', False)
    labels = node.get('labels')

    assert type(replace) is bool, 'replace must be a boolean'

    # Clean the properties and ensure the values are valid
    props = clean_props(props)

    mprops = parse_match_props(match, props)

    # Force create the node if matching is disabled or no
    # properties exist to match on.
    if match is False or not mprops:
        return create_node_stmt(index, props, labels=labels)

    uprops = parse_update_props(update, props)

    return merge_node_stmt(index, mprops, cprops=props, uprops=uprops,
                           labels=labels, replace=replace)


def parse_rel(index, rel, bound):
    start = int(rel.get('start'))
    end = int(rel.get('end'))
    rtype = rel.get('type')
    props = rel.get('props', {})
    match = rel.get('match')
    update = rel.get('update')
    replace = rel.get('replace', False)

    # Ensure the references are within bounds
    assert 0 <= start <= bound, 'start node index not bounds'
    assert 0 <= end <= bound, 'end node index not in bounds'
    assert rtype, 'relationships must have a non-empty type'

    assert type(replace) is bool, 'replace must be a boolean'

    # Clean the properties and ensure the values are valid
    props = clean_props(props)

    # Force create the relationship is match is disabled
    if match is False:
        return create_rel_stmt(index, start, rtype, end, props)

    if match:
        mprops = parse_match_props(match, props)
    else:
        mprops = None

    uprops = parse_update_props(update, props)

    return merge_rel_stmt(index, start, rtype, end, mprops, cprops=props,
                          uprops=uprops, replace=replace)


def _parse_dict_schema(data, stream):
    "Parses a dict-based format with `nodes` and `rels` arrays."
    statements = []

    nodes = data.get('nodes', ())
    rels = data.get('rels', ())

    for index, node in enumerate(nodes):
        stmt = parse_node(index, node)
        if stream:
            print(stmt)
        else:
            statements.append(stmt)

    # References to nodes in relationships cannot exceed
    # this upper bound, offset if for generating references
    offset = len(nodes)
    bound = offset - 1

    for index, rel in enumerate(rels):
        stmt = parse_rel(offset + index, rel, bound)
        if stream:
            print(stmt)
        else:
            statements.append(stmt)

    return statements


def _parse_array_schema(data, stream):
    """Parses the array-based format where nodes and relationships are
    interleaved.
    """
    statements = []

    for index, item in enumerate(data):
        if 'type' in item:
            stmt = parse_rel(index, item, index)
        else:
            stmt = parse_node(index, item)
        if stream:
            print(stmt)
        else:
            statements.append(stmt)

    return statements


def parse(data, stream=False):
    if isinstance(data, dict):
        return _parse_dict_schema(data, stream)
    elif isinstance(data, (list, tuple)):
        return _parse_array_schema(data, stream)
    raise ValueError('Invalid format. Must be a dict or list/tuple')


def load(data, uri=DEFAULT_URI):
    statements = parse(data)
    return send_request(uri, statements)


if __name__ == '__main__':
    import sys

    args = sys.argv[1:]

    if '--load' in args:
        args.remove('--load')
        _load = True
    else:
        _load = False

    # Path to JSON file, otherwise assume stdin
    if args:
        with open(args.pop(0)) as f:
            data = json.load(f)
    else:
        data = json.load(sys.stdin)

    if _load:
        # Args remaining, this should be a custom URI
        if args:
            uri = args[0]
        else:
            uri = None

        output = load(data, uri=uri)

        # Print errors if any were returned
        if output['errors']:
            print(output['errors'])
            sys.exit(1)
    else:
        parse(data, stream=True)
