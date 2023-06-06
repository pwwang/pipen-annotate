import pytest
from pipen_annotate.utils import (
    dedent,
    indent,
    end_of_sentence,
    cleanup_empty_lines,
)


def test_dedent():
    lines = dedent(["    Abc", "    def", "    ", "    Ghi"])
    assert lines == ["Abc", "def", "", "Ghi"]


def test_indent():
    text = indent("Abc\ndef\n\nGhi", "    ")
    assert text == "Abc\n    def\n\n    Ghi\n"

    text = """Short summary

        Long summary

        Envs:
            arg2 (readonly;type=int;required): help21.
                help22
                more help
        """
    out = indent(text, "        ")
    assert text == """Short summary

        Long summary

        Envs:
            arg2 (readonly;type=int;required): help21.
                help22
                more help
        """


def test_end_of_sentence():
    assert end_of_sentence("Abc.")
    assert end_of_sentence("Abc?")
    assert end_of_sentence("Abc!")
    assert end_of_sentence("Abc:")
    assert not end_of_sentence("Abc")
    assert not end_of_sentence("Abc def")


def test_cleanup_empty_lines():
    lines = cleanup_empty_lines(["Abc", "", "def", "", "", "Ghi", ""])
    assert lines == ["Abc", "", "def", "", "Ghi"]

    lines = cleanup_empty_lines(["Abc", "", "def", "", "", "Ghi"])
    assert lines == ["Abc", "", "def", "", "Ghi"]
