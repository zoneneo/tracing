#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re

from setuptools import setup, find_packages

version = None
with open('algotracing/__init__.py', 'r') as f:
    for line in f:
        m = re.match(r'^__version__\s*=\s*(["\'])([^"\']+)\1', line)
        if m:
            version = m.group(2)
            break

assert version is not None, \
    'Could not determine version number from algotracing/__init__.py'


setup(name='algotracing',
    version=version,
    description='Algohub Tracing',
    author='Ander Sun',
    author_email='zhaohui.sun@genetalks.com',
    install_requires=['opentracing==1.3.0','future==0.16.0','six==1.11.0','tornado==4.5.3'],
    url='https://www.genetalks.com/',
    packages=['algotracing'])
