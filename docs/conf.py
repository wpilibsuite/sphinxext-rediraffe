master_doc = "index"
project = "sphinxext-rediraffe"

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

extensions = ["myst_parser", "sphinxext.rediraffe"]

rediraffe_redirects = {"other.md": "index.md"}
