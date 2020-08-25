extensions = ["sphinxext.rediraffe"]

master_doc = "index"
exclude_patterns = ["_build"]

html_theme = "basic"

rediraffe_redirects = "redirects.txt"

import subprocess
from pathlib import Path

rediraffe_branch = subprocess.check_output(
    f"git -C {Path(__file__).parent} rev-parse HEAD~1", shell=True
).decode("utf-8")
