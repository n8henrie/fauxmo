# -*- coding: utf-8 -*-

import re
try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup

try:
    import pypandoc
    readme = pypandoc.convert('README.md', 'rst')
    history = pypandoc.convert('HISTORY.md', 'rst')
except ImportError:
    with open('README.md') as readme_file, open('HISTORY.md') as history_file:
        readme = readme_file.read()
        history = history_file.read()

with open('requirements.txt') as requirements_file:
    requirements = requirements_file.read().splitlines()

test_requirements = [
    'pytest>=2.6.4'
]

version_regex = re.compile(r'__version__ = [\'\"]((\d+\.?)+)[\'\"]')
with open('fauxmo/__init__.py') as f:
    vlines = f.readlines()
__version__ = next(re.match(version_regex, line).group(1) for line in vlines
               if re.match(version_regex, line))

setup(
    name="fauxmo",
    version=__version__,
    description="Emulated Belkin WeMo devices that work with the Amazon Echo",
    long_description=readme + "\n\n" + history,
    author="Nathan Henrie",
    author_email="nate@n8henrie.com",
    url="https://github.com/n8henrie/fauxmo",
    packages=find_packages(),
    package_dir={"fauxmo":
                 "fauxmo"},
    include_package_data=True,
    install_requires=requirements,
    license="MIT",
    zip_safe=False,
    keywords=["fauxmo", "alexa", "amazon echo"],
    classifiers=[
        "Natural Language :: English",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5"
    ],
    test_suite="tests",
    tests_require=test_requirements,
    entry_points={'console_scripts': ['fauxmo=fauxmo.cli:cli']}
)
