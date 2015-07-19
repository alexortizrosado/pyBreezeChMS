#!/usr/bin/env python
import os

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    long_description = readme.read()


setup(name='pyBreezeChMS',
      version='1.0.0',
      description="Python interface to BreezeChMS REST API.",
      long_description=long_description,
      classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: Console',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: Apache Software License',
          'Operating System :: OS Independent',
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7',
          'Natural Language :: English',
      ],
      keywords='breezechms breezeapi python breeze',
      author='Alex Ortiz-Rosado',
      author_email='alex@rohichurch.org',
      maintainer='Alex Ortiz-Rosado',
      maintainer_email='alex@rohichurch.org',
      url='http://www.github.com/aortiz32/pyBreezeChMS/',
      license='Apache 2.0',
      packages=['breeze'],
      test_suite='tests.all_tests',
      install_requires=['requests>=1.1.0'],
      zip_safe=False,
)
