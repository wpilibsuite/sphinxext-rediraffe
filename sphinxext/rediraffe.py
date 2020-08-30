from os import rename
import re
import subprocess
from os.path import relpath
from pathlib import Path, PurePath, PureWindowsPath, PurePosixPath
from typing import Any, Dict, List, Union

from jinja2 import Environment, FileSystemLoader, Template
from sphinx.application import Sphinx
from sphinx.builders import Builder
from sphinx.builders.dirhtml import DirectoryHTMLBuilder
from sphinx.builders.html import StandaloneHTMLBuilder
from sphinx.builders.linkcheck import CheckExternalLinksBuilder
from sphinx.errors import ExtensionError
from sphinx.util import logging
from sphinx.util.console import green, red, yellow  # pylint: disable=no-name-in-module

logger = logging.getLogger(__name__)

DEFAULT_REDIRAFFE_TEMPLATE = Template(
    """
<html>
    <head>
        <meta http-equiv="refresh" content="0; url={{rel_url}}"/>
    </head>
    <body>
        <p>You should have been redirected.</p>
        <a href="{{rel_url}}">If not, click here to continue.</a>
    </body>
</html>

"""
)

RE_OBJ = re.compile(r"(?:(\"|')(.*?)\1|(\S+))\s+(?:(\"|')(.*?)\4|(\S+))")


def create_graph(path: Path) -> Dict[str, str]:
    """
    Convert a file containing a whitespace delimited edge list (key value pairs) to a dict. Throws error on duplicate keys.
    """
    graph_edges = {}
    broken = False
    with open(path, "r") as file:
        for line_num, line in enumerate(file):
            line = line.strip()
            if len(line) == 0:
                continue
            match = RE_OBJ.fullmatch(line)

            if match == None:
                logger.error(
                    red(f"rediraffe: line {line_num} of the redirects is invalid!")
                )
                broken = True
                continue

            edge_from = match.group(2) or match.group(3)
            edge_to = match.group(5) or match.group(6)
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
        err_msg = f"rediraffe: Error(s) in parsing the redirects file."
        logger.error(err_msg)
        raise ExtensionError(err_msg)
    return graph_edges


def create_simple_redirects(graph_edges: dict) -> dict:
    """
    Ensures that a graph is a acyclic and reconnects every vertex to its leaf vertex.
    """
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
    """
    Build amd write redirects
    """

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

    rediraffe_template = app.config.rediraffe_template
    if isinstance(rediraffe_template, str):
        # path
        template_path = Path(app.srcdir) / rediraffe_template
        if template_path.exists():
            file_loader = FileSystemLoader(template_path.parent)
            env = Environment(loader=file_loader)
            rediraffe_template = env.get_template(template_path.name)
        else:
            logger.warning(
                "rediraffe: rediraffe_template does not exist. The default will be used."
            )
            rediraffe_template = DEFAULT_REDIRAFFE_TEMPLATE
    else:
        rediraffe_template = DEFAULT_REDIRAFFE_TEMPLATE

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
    for src_redirect_from, src_redirect_to in redirects.items():
        # Normalize path - src_redirect_.* is relative so drive letters aren't an issue.
        src_redirect_from = Path(PureWindowsPath(src_redirect_from))
        src_redirect_to = Path(PureWindowsPath(src_redirect_to))

        # relative paths from source dir (without ext)
        redirect_from = src_redirect_from.with_suffix("")
        redirect_to = src_redirect_to.with_suffix("")

        if type(app.builder) == DirectoryHTMLBuilder:
            master_doc = Path(app.config.master_doc).with_suffix("")
            if redirect_from != master_doc:
                redirect_from = redirect_from / "index"
            if redirect_to != master_doc:
                redirect_to = redirect_to / "index"

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
                rediraffe_template.render(
                    rel_url=str(
                        PurePosixPath(
                            PureWindowsPath(
                                relpath(build_redirect_to, build_redirect_from.parent)
                            )
                        )
                    ),
                    from_file=src_redirect_from,
                    to_file=src_redirect_to,
                    from_url=redirect_from,
                    to_url=redirect_to,
                )
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
        redirects_path = None
        if isinstance(rediraffe_redirects, dict):
            pass
        elif isinstance(rediraffe_redirects, str):
            redirects_path = Path(src_path) / rediraffe_redirects
            if not redirects_path.is_file():
                logger.error(red("rediraffe: rediraffe_redirects file does not exist."))
                self.app.statuscode = 1
                return
            try:
                rediraffe_redirects = create_graph(redirects_path)
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

        def abs_path_in_src_dir_w_src_suffix(filename: str) -> Union[Path, None]:
            abs_path = (Path(path_to_git_repo.strip()) / filename.strip()).resolve()
            if not str(abs_path).startswith(str(src_path)):
                return None
            if abs_path.suffix not in source_suffixes:
                return None
            return abs_path

        # run git diff
        renamed_files_out = (
            subprocess.check_output(
                f"git -C {self.app.srcdir} diff --name-status --diff-filter=R {self.app.config.rediraffe_branch}",
                shell=True,
            )
            .decode("utf-8")
            .splitlines()
        )

        rename_hints = {}
        for line in renamed_files_out:
            line = line.strip()
            r_perc, rename_from, rename_to = re.split(r"\s+", line)
            perc = int(r_perc[1:])
            path_rename_from = abs_path_in_src_dir_w_src_suffix(rename_from)
            path_rename_to = abs_path_in_src_dir_w_src_suffix(rename_to)

            if path_rename_from == None:
                continue
            if path_rename_to == None:
                continue
            rename_hints[path_rename_from] = (path_rename_to, perc)

        # run git diff
        deleted_files = (
            subprocess.check_output(
                f"git -C {self.app.srcdir} diff --diff-filter=D --name-only {self.app.config.rediraffe_branch}",
                shell=True,
            )
            .decode("utf-8")
            .splitlines()
        )

        # to absolute path + filter out
        deleted_files = [
            abs_path_in_src_dir_w_src_suffix(filename) for filename in deleted_files
        ]
        deleted_files = list(filter(lambda x: x != None, deleted_files))

        for deleted_file in deleted_files:
            if deleted_file in absolute_redirects:
                logger.info(
                    f"deleted file {deleted_file} redirects to {absolute_redirects[deleted_file]}."
                )
            else:
                err_msg = f'{red("(broken)")} {deleted_file} was deleted but is not redirected!'
                logger.error(err_msg)
                self.app.statuscode = 1

        with redirects_path.open("a") as redirects_file:

            for renamed_file in rename_hints:
                hint_to, perc = rename_hints[renamed_file]

                if renamed_file in absolute_redirects:
                    logger.info(
                        f"renamed file {renamed_file} redirects to {absolute_redirects[renamed_file]}."
                    )
                    continue

                if self.name == "rediraffewritediff":
                    if perc >= self.app.config.rediraffe_auto_redirect_perc:
                        rel_rename_from = f'"{str(PurePosixPath(renamed_file.relative_to(src_path)))}"'
                        rel_rename_to = (
                            f'"{str(PurePosixPath(hint_to.relative_to(src_path)))}"'
                        )
                        redirects_file.write(f"{rel_rename_from} {rel_rename_to}\n")
                        logger.info(
                            f"{green('(okay)')} Renamed file {rel_rename_from} has been redirected to {rel_rename_to} in your redirects file!"
                        )
                        continue

                err_msg = (
                    f"{red('(broken)')} {renamed_file} was deleted but is not redirected!"
                    f" Hint: This file was renamed to {hint_to} with a similarity of {perc}%."
                )
                logger.error(err_msg)
                self.app.statuscode = 1

    def get_outdated_docs(self):
        return []

    def prepare_writing(self=None, docnames=None):
        pass

    def write_doc(self, docname=None, doctree=None):
        pass

    def get_target_uri(self, docname=None, typ=None):
        return ""

    def read(self):
        return []


class WriteRedirectsDiffBuilder(CheckRedirectsDiffBuilder):
    name = "rediraffewritediff"

    def init(self) -> None:
        rediraffe_redirects = self.app.config.rediraffe_redirects
        if not isinstance(rediraffe_redirects, str):
            logger.error(
                f"{red('(broken)')} Automatic redirects is only available with a redirects file."
            )
            self.app.statuscode = 1
            return

        super().init()


def setup(app: Sphinx) -> Dict[str, Any]:
    app.add_config_value("rediraffe_redirects", None, None)
    app.add_config_value("rediraffe_branch", "", None)
    app.add_config_value("rediraffe_template", None, None)
    app.add_config_value("rediraffe_auto_redirect_perc", 100, None)

    app.add_builder(CheckRedirectsDiffBuilder)
    app.add_builder(WriteRedirectsDiffBuilder)
    app.connect("build-finished", build_redirects)

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
