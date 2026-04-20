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
    s = (
        "outfile:file:"
        "{{in.sobjfile | stem}}.annotated."
        "{{- ext0(in.sobjfile) if envs.outtype == 'input' else envs.outtype -}}"
    )
    out, blocks = replace_template_blocks(s)
    assert out == "outfile:file:<template#0>.annotated.<template#1>"
    assert blocks == {
        "<template#0>": "{{in.sobjfile | stem}}",
        "<template#1>": (
            "{{- ext0(in.sobjfile) if envs.outtype == 'input' else envs.outtype -}}"
        ),
    }
