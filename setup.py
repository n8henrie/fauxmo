import re
from setuptools import setup, find_packages

with open("README.md", encoding="utf-8") as readme_file, open(
    "CHANGELOG.md"
) as history_file:
    readme = readme_file.read()
    history = history_file.read()

with open("requirements-dev.txt") as dev_requirements_file:
    dev_requirements = [
        line
        for line in dev_requirements_file.read().splitlines()
        if not line.startswith("-i ")
    ]

version_regex = re.compile(r"__version__ = [\'\"]v((\d+\.?)+)[\'\"]")
with open("src/fauxmo/__init__.py") as f:
    vlines = f.readlines()
__version__ = next(
    re.match(version_regex, line).group(1)
    for line in vlines
    if re.match(version_regex, line)
)

setup(
    name="fauxmo",
    version=__version__,
    description="Emulated Belkin WeMo devices that work with the Amazon Echo",
    long_description=readme + "\n\n" + history,
    long_description_content_type="text/markdown",
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
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    extras_require={"dev": dev_requirements},
    test_suite="tests",
    tests_require=dev_requirements,
    entry_points={"console_scripts": ["fauxmo=fauxmo.cli:cli"]},
    python_requires=">=3.6",
)
