from distutils.core import setup

version = __import__('graphlib').get_version()

kwargs = {
    'packages': ['graphlib'],
    'test_suite': 'test_suite',
    'name': 'graphlib',
    'version': version,
    'author': 'Byron Ruth',
    'author_email': 'b@devel.io',
    'description': 'Graph API',
    'license': 'BSD',
    'keywords': 'graph node relationship edge vertices neo4j',
    'url': 'https://github.com/bruth/graphlib/',
    'classifiers': [
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: BSD License',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
}

setup(**kwargs)
