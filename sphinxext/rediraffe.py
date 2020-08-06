from typing import Any, Dict, List, Set, Tuple, Union, overload
import sphinx.builders.linkcheck
from sphinx.application import Sphinx
from docutils.nodes import Node
import subprocess
from pathlib import Path
from sphinx.errors import ExtensionError
import re
from sphinx.builders.linkcheck import CheckExternalLinksBuilder
from sphinx.builders import Builder
from sphinx.builders.html import StandaloneHTMLBuilder, DirectoryHTMLBuilder
from os.path import relpath


def create_graph(path: Path) -> Dict[str, str]:
    graph_edges = {}
    if not path.exists():
        raise ExtensionError("rediraffe: rediraffe_redirects file does not exist.")

    with open(path, "r") as file:
        for line in file:
            edge_from, edge_to, *_ = re.split(r"\s+", line)
            if edge_from in graph_edges:
                # Duplicate vertices not allowed / Vertices can only have 1 outgoing edge
                raise ExtensionError(f"rediraffe: {edge_from} is redirected multiple times in the rediraffe_redirects file.")
            graph_edges[edge_from] = edge_to
    return graph_edges

def create_simple_redirects(graph_edges: dict) -> dict:
    redirects = {}
    for vertex in graph_edges:
        visited = set()

        while vertex in graph_edges:
            if vertex in visited:
                # Ensure graph is a DAG
                raise ExtensionError(f"rediraffe: A circular redirect exists. Links involved: {str(visited)}.")
            visited.add(vertex)
            vertex = graph_edges[vertex]

        # vertex is now a leaf
        for visited_vertex in visited:
            redirects[visited_vertex] = vertex

    return redirects

def build_redirects(app: Sphinx, exception: Union[Exception, None]) -> None:
    if exception != None:
        return

    if isinstance(app.builder, CheckExternalLinksBuilder):
        app.info("rediraffe: Redirect generation skipped for linkcheck builders.")
        return
    
    if type(app.builder) not in (StandaloneHTMLBuilder, DirectoryHTMLBuilder):
        app.info("rediraffe: Redirect generation skipped for unsupported builders. Supported builders: html, dirhtml")
        return

    graph_edges = {}

    rediraffe_redirects = app.config.rediraffe_redirects
    if isinstance(rediraffe_redirects, dict):
        # dict in conf.py
        graph_edges = rediraffe_redirects
    elif isinstance(rediraffe_redirects, str):
        # filename
        graph_edges = create_graph(Path(app.srcdir) / rediraffe_redirects)
    
    redirects = create_simple_redirects(graph_edges)

    # write redirects
    for redirect_from, redirect_to in redirects.items():
        
        redirect_from = Path(redirect_from)
        redirect_to = Path(redirect_to)
        
        if type(app.builder) == DirectoryHTMLBuilder:
            redirect_from = redirect_from.with_suffix("") / "index"
            redirect_to = redirect_to.with_suffix("") / "index"
        
        redirect_from = redirect_from.with_suffix("html")
        redirect_to = redirect_to.with_suffix("html")

        build_redirect_from = Path(app.outdir) / redirect_from
        build_redirect_to = Path(app.outdir) / redirect_to

        if build_redirect_from.exists():
            raise ExtensionError(f'rediraffe: {redirect_from} redirects to {redirect_to} but {build_redirect_from} exists!')

        if not build_redirect_to.exists():
            raise ExtensionError(f'rediraffe: {redirect_from} redirects to {redirect_to} but {build_redirect_to} does not exist!')

        
        build_redirect_from.parent.mkdir(exist_ok=True)
        with build_redirect_from.open("w") as f:
            f.write(f'<html><head><meta http-equiv="refresh" content="0; url={relpath(redirect_to, redirect_from)}"/></head></html>')

class CheckRedirectsDiffBuilder(Builder):
    name = "rediraffecheckdiff"

    def init(self) -> None:
        super().init()

        path_to_git_repo = subprocess.check_output(
            f"git -C {self.app.srcdir} rev-parse --show-toplevel", shell=True
        ).decode("utf-8")

        # run git diff
        deleted_files = subprocess.check_output(
            f"git -C {self.app.srcdir} diff --diff-filter=D --name-only  {self.app.config.rediraffe_branch}",
            shell=True,
        )

        # splitlines
        deleted_files = deleted_files.splitlines()
        # convert to utf-8
        deleted_files = [
            filename.decode("utf-8") for filename in deleted_files
        ]
        # convert to path
        deleted_files = [Path(filename.strip()) for filename in deleted_files]
        # to absolute path
        deleted_files = [
            Path(self.path_to_git_repo.strip()) / filename
            for filename in deleted_files
        ]

        src_path = Path(self.app.srcdir)

        rediraffe_redirects = self.app.config.rediraffe_redirects
        if isinstance(rediraffe_redirects, dict):
            pass
        elif isinstance(rediraffe_redirects, str):
            rediraffe_redirects = create_graph(src_path / rediraffe_redirects)

        absolute_redirects = {
            (src_path / redirect_from).resolve() : (src_path / redirect_to).resolve()
            for redirect_from, redirect_to in rediraffe_redirects.items()
        }

        for deleted_file in deleted_files:
            try:
                deleted_file.relative_to(src_path)
            except ValueError:
                # deleted_file is not in source dir
                continue

            if deleted_file.suffix in {".rst", ".md"}:
                if deleted_file not in absolute_redirects:
                    raise ExtensionError(f"OOPSIE! WPISIE! {deleted_file} was deleted but is not redirected!")



def setup(app: Sphinx) -> Dict[str, Any]:
    app.add_config_value("rediraffe_redirects", "", None)
    app.add_config_value("rediraffe_branch", "", None)

    app.add_builder(CheckRedirectsDiffBuilder)
    app.connect("build-finished", build_redirects)

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
