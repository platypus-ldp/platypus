from setuptools import setup

from platypus import __version__

setup(name='platypus',
      version=__version__,
      description='A Python LDP client',
      url='http://github.com/platypus-ldp/platypus',
      author='rlskoeser, barmintor, cmh2166, jrhoads',
      author_email='platypus-ldp@googlegroups.com',
      license='MIT',
      packages=['platypus'],
      install_requires=[
        'requests',
        'rdflib'
      ],
      setup_requires=['pytest-runner'],
      tests_require=['pytest'],
      zip_safe=False)
