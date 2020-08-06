# sphinxext-rediraffe
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Sphinx Extension to redirect files

## Installation

`python -m pip install https://github.com/TheTripleV/sphinxext-rediraffe`

## Usage
Add `sphinxext.rediraffe` to your extensions list in your `conf.py`

```python
extensions = [
   sphinxext.rediraffe,
]
```
<!-- ## Options
These values are placed in the conf.py of your sphinx project.

* `linkcheckdiff_branch`
    * Required. The branch to diff against.

Note: linkcheckdiff is an extension of the linkcheck builder that ships with Sphinx. linkcheckdiff respects all of linkcheck's configuration options.


## Example Config

```python
linkcheckdiff_branch = "master"
``` -->