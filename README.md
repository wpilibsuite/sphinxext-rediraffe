# sphinxext-rediraffe
![ci](https://github.com/wpilibsuite/sphinxext-rediraffe/workflows/ci/badge.svg)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Sphinx Extension to redirect files

![Rediraffe](assets/rediraffe_logo.svg)

This sphinx extension redirects non-existent pages to working pages.
Additionally, a builder is provided to check that deleted/renamed files in your git repo are redirected. 

Rediraffe supports the html and dirhtml builders.

Note: Chained redirects will be resolved. For example, if a config has 6 chained redirects, all 6 links will redirect directly to the final link. The end user will never experience more than 1 redirection.

## Installation

`python -m pip install sphinxext-rediraffe`


## Usage
Add `sphinxext.rediraffe` to your extensions list in your `conf.py`

```python
extensions = [
   sphinxext.rediraffe,
]
```

To check that deleted/renamed files in your git repo are in your redirects,
1. Make sure `rediraffe_branch` and `rediraffe_redirects` are set in conf.py.
2. Run the `rediraffecheckdiff` builder.

## Options
These values are placed in the conf.py of your sphinx project.

* `rediraffe_branch`
    * Required for rediraffecheckdiff builder. The branch or commit to diff against.

* `rediraffe_redirects`
    * Required. A filename or dict containing redirects

* `rediraffe_template`
    * Optional. A jinja template to use to render the inserted redirecting files. If not specified, a default template will be used. This template will only be accessed after the html/htmldir builder is finished; Therefore, this file may be generated as part of your build.
    * variables available to rediraffe_template:
        * `from_file` - the file being redirected as written in rediraffe_redirects.
        * `to_file` - the destination file that from_file is redirected to as written in rediraffe_redirects.
        * `from_url` - the path to from_url's html file (built by rediraffe) relative to the outdir.
        * `to_url` - the path to to_url's built html file relative to the outdir.
        * `rel_url` - the relative path from from_url to to_url.


## Example Config

### redirects only (file)

conf.py:
```python
rediraffe_redirects = "redirects.txt"
```

redirects.txt:
```
another.rst index.rst
another2.rst another.rst
```

### redirects only (dict)

conf.py:
```python
rediraffe_redirects = {
    "another.rst": "index.rst",
    "another2.rst": "another.rst",
}
```

### redirects + diff checker

conf.py:
```python
rediraffe_redirects = "redirects.txt"
rediraffe_branch = "master~1"
```

### redirects with jinja template

conf.py:
```python
rediraffe_redirects = "redirects.txt"
rediraffe_template = "template.html"
```

template.html:
```html
<html>
    <body>
        <p>Your destination is {{to_url}}</p>
    </body>
</html>
```

A complex example can be found at tests/roots/ext/.

## Testing

Rediraffe uses pytest for testing.
To run tests:
1. Install this package
2. Install test dependencies
    ```bash
    python -m pip install -r test-requirements.txt
    ```
3. Navigate to the tests directory and run
    ```bash
    python -m pytest --headless
    ```

The `--headless` flag ensures that a browser window does not open during browser backed selenium testing.
