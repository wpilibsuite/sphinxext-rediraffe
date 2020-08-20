# sphinxext-rediraffe
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Sphinx Extension to redirect files

![Rediraffe](assets/rediraffe_logo.svg)

## Installation

`python -m pip install git+https://github.com/wpilibsuite/sphinxext-rediraffe.git`


## Usage
Add `sphinxext.rediraffe` to your extensions list in your `conf.py`

```python
extensions = [
   sphinxext.rediraffe,
]
```
## Options
These values are placed in the conf.py of your sphinx project.

* `rediraffe_branch`
    * Required for rediraffecheckdiff builder. The branch to diff against.

* `rediraffe_redirects`
    * Required. The filename or dict containing redirects

* `rediraffe_template`
    * Optional. The jinja template to use to render the inserted redirecting files.


## Example Config

```python
rediraffe_branch = "master"
```

tests/roots/ext/