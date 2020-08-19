import re
import subprocess
from os.path import relpath
from pathlib import Path
from typing import Any, Dict, Union

from sphinx.application import Sphinx
from sphinx.builders import Builder
from sphinx.builders.dirhtml import DirectoryHTMLBuilder
from sphinx.builders.html import StandaloneHTMLBuilder
from sphinx.builders.linkcheck import CheckExternalLinksBuilder
from sphinx.errors import ExtensionError

from sphinx.util import logging
from sphinx.util.console import yellow, green, red  # pylint: disable=no-name-in-module


logger = logging.getLogger(__name__)


def create_graph(path: Path) -> Dict[str, str]:
    graph_edges = {}
    broken = False
    with open(path, "r") as file:
        for line in file:
            line = line.strip()
            if len(line) == 0:
                continue
            edge_from, edge_to, *_ = re.split(r"\s+", line)
            if edge_from in graph_edges:
                # Duplicate vertices not allowed / Vertices can only have 1 outgoing edge
                logger.error(
                    red(
                        f"rediraffe: {edge_from} is redirected multiple times in the rediraffe_redirects file!"
                    )
                )
                broken = True
            graph_edges[edge_from] = edge_to
    if broken:
        err_msg = f"rediraffe: Some links are redirected multiple times. They should only be redirected once."
        logger.error(err_msg)
        raise ExtensionError(err_msg)
    return graph_edges


def create_simple_redirects(graph_edges: dict) -> dict:
    redirects = {}
    broken_vertices = set()
    for vertex in graph_edges:
        if vertex in broken_vertices:
            continue

        visited = []
        while vertex in graph_edges:
            if vertex in visited:
                # Ensure graph is a DAG
                logger.error(
                    red(
                        "rediraffe: A circular redirect exists. Links involved: "
                        + " -> ".join(visited + [vertex])
                    )
                )
                broken_vertices.update(visited)
                break
            visited.append(vertex)
            vertex = graph_edges[vertex]

        # vertex is now a leaf
        for visited_vertex in visited:
            redirects[visited_vertex] = vertex

    if broken_vertices:
        err_msg = (
            f"rediraffe: At least 1 circular redirect detected. All involved links: "
            + ", ".join(broken_vertices)
        )
        logger.error(err_msg)
        raise ExtensionError(err_msg)

    return redirects


def build_redirects(app: Sphinx, exception: Union[Exception, None]) -> None:
    if exception != None:
        return

    if isinstance(app.builder, CheckExternalLinksBuilder):
        logger.info("rediraffe: Redirect generation skipped for linkcheck builders.")
        return

    if type(app.builder) not in (StandaloneHTMLBuilder, DirectoryHTMLBuilder):
        logger.info(
            "rediraffe: Redirect generation skipped for unsupported builders. Supported builders: html, dirhtml"
        )
        return

    graph_edges = {}

    rediraffe_redirects = app.config.rediraffe_redirects
    if isinstance(rediraffe_redirects, dict):
        # dict in conf.py
        graph_edges = rediraffe_redirects
    elif isinstance(rediraffe_redirects, str):
        # filename
        path = Path(app.srcdir) / rediraffe_redirects
        if not path.is_file():
            logger.error(
                red(
                    "rediraffe: rediraffe_redirects file does not exist. Redirects will not be generated."
                )
            )
            app.statuscode = 1
            return

        try:
            graph_edges = create_graph(path)
        except ExtensionError as e:
            app.statuscode = 1
            raise e
    else:
        logger.warning(
            "rediraffe: rediraffe was not given redirects to process. Redirects will not be generated."
        )
        return

    try:
        redirects = create_simple_redirects(graph_edges)
    except ExtensionError as e:
        app.statuscode = 1
        raise e

    logger.info("Writing redirects...")

    # write redirects
    for redirect_from, redirect_to in redirects.items():

        # relative paths from source dir (with source ext)
        redirect_from = Path(redirect_from)
        redirect_to = Path(redirect_to)

        if type(app.builder) == DirectoryHTMLBuilder:
            if redirect_from.with_suffix("") != Path(app.config.master_doc).with_suffix(
                ""
            ):
                redirect_from = redirect_from.with_suffix("") / "index"
            if redirect_to.with_suffix("") != Path(app.config.master_doc).with_suffix(
                ""
            ):
                redirect_to = redirect_to.with_suffix("") / "index"

        redirect_from = redirect_from.with_suffix(".html")
        redirect_to = redirect_to.with_suffix(".html")

        # absolute paths into the build dir
        build_redirect_from = Path(app.outdir) / redirect_from
        build_redirect_to = Path(app.outdir) / redirect_to

        if build_redirect_from.exists():
            logger.warning(
                f'{yellow("(broken)")} {redirect_from} redirects to {redirect_to} but {build_redirect_from} already exists!'
            )
            app.statuscode = 1

        if not build_redirect_to.exists():
            logger.warning(
                f'{yellow("(broken)")} {redirect_from} redirects to {redirect_to} but {build_redirect_to} does not exist!'
            )
            app.statuscode = 1

        build_redirect_from.parent.mkdir(parents=True, exist_ok=True)
        with build_redirect_from.open("w") as f:
            f.write(
                f'<html><head><meta http-equiv="refresh" content="0; url={relpath(build_redirect_to, build_redirect_from.parent)}"/></head></html>'
            )
            logger.info(
                f'{green("(good)")} {redirect_from} {green("-->")} {redirect_to}'
            )


class CheckRedirectsDiffBuilder(Builder):
    name = "rediraffecheckdiff"

    def init(self) -> None:
        super().init()

        source_suffixes = set(self.app.config.source_suffix)
        src_path = Path(self.app.srcdir)

        rediraffe_redirects = self.app.config.rediraffe_redirects
        if isinstance(rediraffe_redirects, dict):
            pass
        elif isinstance(rediraffe_redirects, str):
            path = Path(src_path) / rediraffe_redirects
            if not path.is_file():
                logger.error(red("rediraffe: rediraffe_redirects file does not exist."))
                self.app.statuscode = 1
                return
            try:
                rediraffe_redirects = create_graph(path)
            except ExtensionError as e:
                self.app.statuscode = 1
                return
        else:
            logger.error("rediraffe: rediraffe was not given redirects to process.")
            self.app.statuscode = 1
            return

        absolute_redirects = {
            (src_path / redirect_from).resolve(): (src_path / redirect_to).resolve()
            for redirect_from, redirect_to in rediraffe_redirects.items()
        }

        path_to_git_repo = subprocess.check_output(
            f"git -C {self.app.srcdir} rev-parse --show-toplevel", shell=True
        ).decode("utf-8")

        # run git diff
        deleted_files = subprocess.check_output(
            f"git -C {self.app.srcdir} diff --diff-filter=AR --name-only HEAD {self.app.config.rediraffe_branch}",
            shell=True,
        )

        # splitlines
        deleted_files = deleted_files.splitlines()
        # convert to utf-8
        deleted_files = [filename.decode("utf-8") for filename in deleted_files]
        # convert to path
        deleted_files = [Path(filename.strip()) for filename in deleted_files]
        # to absolute path
        deleted_files = [
            Path(path_to_git_repo.strip()) / filename for filename in deleted_files
        ]
        # in source dir
        deleted_files = [
            filename
            for filename in deleted_files
            if str(filename).startswith(str(src_path))
        ]
        # with source suffix
        deleted_files = [
            filename for filename in deleted_files if filename.suffix in source_suffixes
        ]

        for deleted_file in deleted_files:
            if deleted_file in absolute_redirects:
                logger.info(
                    f"deleted file {deleted_file} redirects to {absolute_redirects[deleted_file]}."
                )
            else:
                logger.error(
                    f'{red("(broken)")} {deleted_file} was deleted but is not redirected!'
                )
                self.app.statuscode = 1

    def get_outdated_docs(self):
        return []

    def prepare_writing(self, docnames):
        pass

    def write_doc(self, docname, doctree):
        pass


def setup(app: Sphinx) -> Dict[str, Any]:
    app.add_config_value("rediraffe_redirects", "", None)
    app.add_config_value("rediraffe_branch", "", None)

    app.add_builder(CheckRedirectsDiffBuilder)
    app.connect("build-finished", build_redirects)

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
