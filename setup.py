import re
from setuptools import setup, find_packages

try:
    import pypandoc
    readme = pypandoc.convert('README.md', 'rst')
    history = pypandoc.convert('CHANGELOG.md', 'rst')
except ImportError:
    with open('README.md') as readme_file, \
            open('CHANGELOG.md') as history_file:
        readme = readme_file.read()
        history = history_file.read()

with open('requirements-dev.txt') as dev_requirements_file, \
        open('requirements-test.txt') as tests_requirements_file:
    test_requirements = tests_requirements_file.read().splitlines()
    dev_requirements = dev_requirements_file.read().splitlines()
    dev_requirements.extend(test_requirements)

version_regex = re.compile(r'__version__ = [\'\"]v((\d+\.?)+)[\'\"]')
with open('src/fauxmo/__init__.py') as f:
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
    packages=find_packages("src"),
    package_dir={"": "src"},
    include_package_data=True,
    license="MIT",
    zip_safe=False,
    keywords=["fauxmo", "alexa", "amazon echo"],
    classifiers=[
        "Natural Language :: English",
        "Programming Language :: Python :: 3.6"
    ],
    extras_require={
        "dev": dev_requirements
    },
    test_suite="tests",
    tests_require=test_requirements,
    entry_points={'console_scripts': ['fauxmo=fauxmo.cli:cli']},
    python_requires=">=3.6",
)
