import pytest
from sphinx.testing.path import path


@pytest.fixture(scope="module")
def rootdir():
    return path(__file__).parent.abspath() / "roots" / "builder"


@pytest.mark.sphinx("rediraffewritediff", testroot="renamed_write_file_not_redirected")
def test_builder_renamed_file_write_not_redirected(app_init_repo):
    app_init_repo.build()
    valid_string = '"another.rst" "another2.rst"'
    with open(path(app_init_repo.srcdir).joinpath("redirects.txt"), "r") as file:
        assert valid_string in file.readline()


@pytest.mark.sphinx("rediraffewritediff", testroot="renamed_write_file_perc_low_fail")
def test_builder_renamed_file_write_perc_low_fail(app_init_repo):
    app_init_repo.build()
    valid_string = '"another.rst" "another2.rst"'
    with open(path(app_init_repo.srcdir).joinpath("redirects.txt"), "r") as file:
        assert valid_string not in file.readline()


@pytest.mark.sphinx("rediraffewritediff", testroot="renamed_write_file_perc_low_pass")
def test_builder_renamed_file_write_perc_low_pass(app_init_repo):
    app_init_repo.build()
    valid_string = '"another.rst" "another2.rst"'
    with open(path(app_init_repo.srcdir).joinpath("redirects.txt"), "r") as file:
        assert valid_string in file.readline()
