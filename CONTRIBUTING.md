# Contributing

Contributions are welcome, and they are greatly appreciated! Every
little bit helps, and credit will always be given.

You can contribute in many ways:

## Types of Contributions

### Report Bugs

Report bugs at <https://github.com/n8henrie/fauxmo/issues>.

If you are reporting a bug, please include:

-   Your operating system name and version.
-   Any details about your local setup that might be helpful in
    troubleshooting.
-   Detailed steps to reproduce the bug.

### Fix Bugs

Look through the GitHub issues for bugs. Anything tagged with "bug" is
open to whoever wants to work on it.

### Implement Features

Look through the GitHub issues for features. Anything tagged with
"feature" is open to whoever wants to implement it.

### Write Documentation

Fauxmo could always use more documentation, whether as part of the official
fauxmo docs, in docstrings, or even on the web in blog posts, articles, and
such.

### Submit Feedback

The best way to send feedback is to file an issue at
<https://github.com/n8henrie/fauxmo/issues>.

If you are proposing a feature:

-   Explain in detail how it would work.
-   Keep the scope as narrow as possible, to make it easier to
    implement.
-   Remember that this is a volunteer-driven project, and that
    contributions are welcome :)

### Create a new Plugin

Please refer to <https://github.com/n8henrie/fauxmo-plugins>

## Get Started!

Ready to contribute? Here's how to set up fauxmo
for local development.

1.  Start by making an issue to serve as a reference point for discussion
    regarding the change being proposed.
1.  Fork the fauxmo repo on GitHub.
1.  Clone your fork locally:

        ```shell_session
        $ git clone git@github.com:your_name_here/fauxmo.git
        ```

1.  Install your local copy into a virtualenv. Assuming you have
    python >= 3.6 installed, this is how you set up your fork for
    local development:

        ```shell_session
        $ cd fauxmo
        $ python3 -m venv venv
        $ source venv/bin/activate
        $ pip install -e .[dev]
        ```

1.  Create a branch for local development:

        ```shell_session
        $ git checkout -b name-of-your-bugfix-or-feature
        ```

    Now you can make your changes locally.

1.  When you're done making changes, check that your changes pass all tests
    configured for each Python version with tox:

        ```shell_session
        $ tox
        ```

1.  Commit your changes and push your branch to GitHub:

        ```shell_session
        $ git add .
        $ git commit -m "Your detailed description of your changes."
        $ git push origin name-of-your-bugfix-or-feature
        ```

1.  Submit a pull request through the GitHub website.

## Pull Request Guidelines

Before you submit a pull request, check that it meets these guidelines:

1.  Pull requests of any substance should reference an issue used for
    discussion regarding the change being considered.
1.  The style should pass `tox -e lint`, including docstrings, type hints, and
    `black --line-length=79 --target-version=py37` for overall formatting.
1.  The pull request should include tests if I am using tests in the repo.
1.  If the pull request adds functionality, the docs should be updated.
    Put your new functionality into a function with a docstring, and add
    the feature to the list in README.md
1.  The pull request should work for Python 3.7. If I have included a
    `.travis.yml` file in the repo, check
    <https://travis-ci.org/n8henrie/fauxmo/pull_requests> and make sure that
    the tests pass for all supported Python versions.

## Tips

To run a subset of tests: `pytest tests/test_your_test.py`
