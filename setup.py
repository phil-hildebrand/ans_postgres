#!/usr/bin/env python

from setuptools import setup, Command, Extension
import unittest
from os.path import splitext, basename, join as pjoin
import os, sys

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(name = 'playbook_tests',
      version = '1.0.0',
      description = 'PostgreSQL laybook tests',
      url = 'http://github.com/phil-hildebrand/ans_postgres',
      author = 'Phil Hildebrand',
      author_email = 'phil.hildebrand@gmail.com',
      license = 'mit',
      packages = ['tests'],
      install_requires = [ requirements ],
      test_suite="tests",
      use_2to3=True
)
