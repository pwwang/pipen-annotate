import pytest
from pipen_annotate.utils import (
    dedent,
    indent,
    end_of_sentence,
    cleanup_empty_lines,
    strip_template_syntax,
    replace_template_blocks,
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


def test_strip_template_syntax():
    s = "This is a {{template}} string with {#comments#} and {% blocks %}."
    assert strip_template_syntax(s) == "This is a  string with  and ."


def test_replace_template_blocks():
    s = "This is a {{template}} string with {#comments#} and {% blocks %}."
    out, blocks = replace_template_blocks(s)
    assert out == "This is a <template#0> string with <template#1> and <template#2>."
    assert blocks == {
        "<template#0>": "{{template}}",
        "<template#1>": "{#comments#}",
        "<template#2>": "{% blocks %}",
    }
