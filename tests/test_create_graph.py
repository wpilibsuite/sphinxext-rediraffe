from sphinxext.rediraffe import create_graph
import pytest
from sphinx.errors import ExtensionError

def test_create_graph(tmp_path):
    path = tmp_path / "rediraffe.txt"
    path.write_text(
        """
        a b
        c d
        d e
        """
    )
    graph = create_graph(path)
    assert graph == {
        "a":"b",
        "c":"d",
        "d":"e",
    }

def test_create_graph_spacing(tmp_path):
    path = tmp_path / "rediraffe.txt"
    path.write_text(
        """
        a  b
        c d
        d            e
        """
    )
    graph = create_graph(path)
    assert graph == {
        "a":"b",
        "c":"d",
        "d":"e",
    }

def test_create_graph_link_redirected_twice(tmp_path):
    path = tmp_path / "rediraffe.txt"
    path.write_text(
        """
        a b
        a c
        """
    )
    with pytest.raises(ExtensionError):
        graph = create_graph(path)

def test_create_graph_link_redirected_lots(tmp_path):
    path = tmp_path / "rediraffe.txt"
    path.write_text(
        """
        a b
        c d
        a c
        d e
        a q
        """
    )
    with pytest.raises(ExtensionError):
        graph = create_graph(path)
