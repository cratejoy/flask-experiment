#!/usr/bin/env python

import re
from setuptools import setup

DESCRIPTION = 'Flask multvariate experiment testing extension'


def parse_requirements(file_name):
    requirements = []
    for line in open(file_name, 'r').read().split('\n'):
        if re.match(r'(\s*#)|(\s*$)', line):
            continue
        if re.match(r'\s*-e\s+', line):
            # TODO support version numbers
            requirements.append(re.sub(r'\s*-e\s+.*#egg=(.*)$', r'\1', line))
        elif re.match(r'\s*-f\s+', line):
            pass
        else:
            requirements.append(line)

    return requirements


def parse_dependency_links(file_name):
    dependency_links = []
    for line in open(file_name, 'r').read().split('\n'):
        if re.match(r'\s*-[ef]\s+', line):
            dependency_links.append(re.sub(r'\s*-[ef]\s+', '', line))

    return dependency_links

setup(
    packages=['flask-experiment'],
    name='flask-experiment',
    url='git@github.com:larkio/flask-experiment.git',
    description=DESCRIPTION,

    version="HEAD",
    author="Amir Elaguizy",
    author_email="amir@lark.io",

    include_package_data=True,

    test_suite="test",
    keywords="",
    install_requires=parse_requirements('requirements.txt'),
    dependency_links=parse_dependency_links('requirements.txt')
)
