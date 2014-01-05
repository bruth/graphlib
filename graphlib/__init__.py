from __future__ import unicode_literals, absolute_import

__version_info__ = {
    'major': 0,
    'minor': 9,
    'micro': 0,
    'releaselevel': 'final',
    'serial': 1
}


def get_version(short=False):
    assert __version_info__['releaselevel'] in ('alpha', 'beta', 'final')
    vers = ['{major}.{minor}.{micro}'.format(**__version_info__)]
    if __version_info__['releaselevel'] != 'final' and not short:
        vers.append('{}{}'.format(__version_info__['releaselevel'][0],
                    __version_info__['serial']))
    return ''.join(vers)


__version__ = get_version()


from .graph import Node, Nodes, Rel, Rels  # noqa
from .serialize import serialize, Serializer  # noqa
