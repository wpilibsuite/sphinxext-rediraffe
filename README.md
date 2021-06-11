# sphinxext-rediraffe
![ci](https://github.com/wpilibsuite/sphinxext-rediraffe/workflows/ci/badge.svg)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Sphinx Extension to redirect files

![Rediraffe](assets/rediraffe_logo.svg)

This sphinx extension redirects non-existent pages to working pages.
Rediraffe can also check that deleted/renamed files in your git repo are redirected.

Rediraffe creates a graph of all specified redirects and traverses it to point all internal urls to leaf urls. This means that chained redirects will be resolved. For example, if a config has 6 chained redirects, all 6 links will redirect directly to the final link. The end user will never experience more than 1 redirection.

Note: Rediraffe supports the html and dirhtml builders.

## Installationqqq

`python -m pip install sphinxext-rediraffe`


## Usage
Add `sphinxext.rediraffe` to your extensions list in your `conf.py`

```python
extensions = [
   "sphinxext.rediraffe",
]
```

Set `rediraffe_redirects` to a dict or file of redirects in your `conf.py`

### Diff Checker
The diff checker ensures that deleted/renamed files in your git repo are in your redirects.

To run the diff checker,
1. Set `rediraffe_branch` and `rediraffe_redirects` in conf.py.
2. Run the `rediraffecheckdiff` builder.

### Auto Redirect builder
The auto redirect builder can be used to automatically add renamed files to your redirects file. Simply run the `rediraffewritediff` builder.

To run the auto redirecter:
1. Set `rediraffe_branch` and `rediraffe_redirects` in conf.py.
2. Run the `rediraffewritediff` builder.

Note: The auto redirect builder only works with a configuration file.
Note: Deleted files cannot be added to your redirects file automatically.

## Options
These values are placed in the conf.py of your sphinx project.

* `rediraffe_branch`
    * Required for the `rediraffecheckdiff` and `rediraffewritediff` builders. The branch or commit to diff against.

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

* `rediraffe_auto_redirect_perc`
    * Optional. Only used by the `rediraffewritediff` builder. The percentage as an integer representing the accuracy required before auto redirecting with the `rediraffewritediff` builder. The default is 100.

## Example Config

### redirects only (file)

conf.py:
```python
rediraffe_redirects = "redirects.txt"
```

redirects.txt:
```
# comments start with "#"
"another file.rst" index.rst
another2.rst 'another file.rst'
```

Note: Filepaths can be wrapped in quotes (single or double).
This is especially useful for filepaths containing spaces.

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
rediraffe_branch = "main~1"
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
