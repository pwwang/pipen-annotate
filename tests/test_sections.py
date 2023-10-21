import pytest  # noqa: F401

from pipen_annotate.sections import (
    SectionEnvs,
    SectionInput,
    SectionItems,
    SectionOutput,
    SectionSummary,
    SectionText,
    MalFormattedAnnotationError,
    _ipython_to_markdown,
)


def test_section_summary():
    section = SectionSummary(None, "Summary")
    section.consume("")
    assert section.parse() == {"short": "", "long": ""}
    assert section.parse().to_markdown() == "\n\n"

    section = SectionSummary(None, "Summary")
    section.consume("    Abc")
    section.consume("    def")
    section.consume("")
    section.consume("    Ghi")
    assert section.parse() == {"short": "Abc def", "long": "Ghi"}

    section = SectionSummary(None, "Summary")
    section.consume("Abc")
    section.consume("    def")
    section.consume("    ")
    section.consume("    Ghi")
    assert section.parse() == {"short": "Abc def", "long": "Ghi"}

    section = SectionSummary(None, "Summary")
    section.consume("Short summary.")
    section.consume("")
    section.consume("Long summary.")
    section.consume("Long long summary.")
    assert section.parse() == {
        "short": "Short summary.",
        "long": "Long summary.\nLong long summary.",
    }

    section = SectionSummary(None, "Summary")
    section.consume("Short summary,")
    section.consume("short summary continued.")
    section.consume("")
    section.consume("Long summary.")
    section.consume("Long long summary.")
    assert section.parse() == {
        "short": "Short summary, short summary continued.",
        "long": "Long summary.\nLong long summary.",
    }


def test_section_text():
    section = SectionText(None, "Text")
    section.consume("Text line 1.")
    section.consume("Text line 2.")
    parsed = section.parse()
    assert parsed.lines == ["Text line 1.", "Text line 2."]
    assert parsed.to_markdown() == "    Text line 1.<br />\n    Text line 2.<br />"


def test_section_items():
    section = SectionItems(None, "Items")
    text = """\
    item1: help1
        more help for item1
        - subitem1: subhelp1
            more help for subitem1
        - subitem2: subhelp2
            more help for subitem2
            - subsubitem1: subsubhelp1
                more help for subsubitem1
            - subsubitem2: subsubhelp2
    item2 (attr1:val1; attr2; attr3:val3): help2
        more help for item2
    """
    for line in text.splitlines():
        section.consume(line)

    parsed = section.parse()
    assert len(parsed) == 2
    assert parsed["item1"]["help"] == "help1 more help for item1"
    assert parsed["item1"]["attrs"] == {}
    assert len(parsed["item1"]["terms"]) == 2
    assert parsed["item1"]["terms"]["subitem1"]["help"] == (
        "subhelp1 more help for subitem1"
    )
    assert parsed["item1"]["terms"]["subitem1"]["attrs"] == {}
    assert parsed["item1"]["terms"]["subitem1"]["terms"] == {}
    assert parsed["item1"]["terms"]["subitem2"]["help"] == (
        "subhelp2 more help for subitem2"
    )
    assert parsed["item1"]["terms"]["subitem2"]["attrs"] == {}
    assert len(parsed["item1"]["terms"]["subitem2"]["terms"]) == 2
    assert (
        parsed["item1"]["terms"]["subitem2"]["terms"]["subsubitem1"]["help"]
        == "subsubhelp1 more help for subsubitem1"
    )
    assert (
        parsed["item1"]["terms"]["subitem2"]["terms"]["subsubitem1"]["attrs"]
        == {}
    )
    assert (
        parsed["item1"]["terms"]["subitem2"]["terms"]["subsubitem1"]["terms"]
        == {}
    )
    assert (
        parsed["item1"]["terms"]["subitem2"]["terms"]["subsubitem2"]["help"]
        == "subsubhelp2"
    )
    assert (
        parsed["item1"]["terms"]["subitem2"]["terms"]["subsubitem2"]["attrs"]
        == {}
    )
    assert (
        parsed["item1"]["terms"]["subitem2"]["terms"]["subsubitem2"]["terms"]
        == {}
    )
    assert parsed["item2"]["help"] == "help2 more help for item2"
    assert parsed["item2"]["attrs"] == {
        "attr1": "val1",
        "attr2": True,
        "attr3": "val3",
    }
    assert parsed["item2"]["terms"] == {}


def test_invalid_attr():
    section = SectionItems(int, "Items")
    section.consume("item1 (,): help1")
    with pytest.raises(
        MalFormattedAnnotationError,
        match="Invalid item attribute",
    ):
        section.parse()


def test_invalid_item():
    section = SectionItems(int, "Items")
    section.consume("item1")
    with pytest.raises(MalFormattedAnnotationError, match="Invalid item line"):
        section.parse()


def test_input():
    class TestProc:
        input = "infile1:file, in2"

    section = SectionInput(TestProc, "Input")
    section.consume("infile1: help1")
    section.consume("in2: help2")

    parsed = section.parse()
    assert len(parsed) == 2
    assert parsed["infile1"]["help"] == "help1"
    assert parsed["infile1"]["attrs"]["itype"] == "file"
    assert parsed["in2"]["help"] == "help2"
    assert parsed["in2"]["attrs"]["itype"] == "var"


def test_input_missing_annotation():
    class TestProc:
        input = "infile1:file, in2"

    section = SectionInput(TestProc, "Input")
    section.consume("in2: help2")

    parsed = section.parse()
    assert len(parsed) == 2
    assert parsed["infile1"]["help"] == ""
    assert parsed["infile1"]["attrs"]["itype"] == "file"
    assert parsed["in2"]["help"] == "help2"
    assert parsed["in2"]["attrs"]["itype"] == "var"


def test_output():
    class TestProc:
        output = "outfile:file:{{a}}, outdir:dir:{{b}}, out:{{c}}"

    section = SectionOutput(TestProc, "Output")
    section.consume("outfile: help1")
    section.consume("outdir: help2")
    section.consume("out: help3")

    parsed = section.parse()
    assert len(parsed) == 3
    assert parsed["outfile"]["help"] == "help1"
    assert parsed["outfile"]["attrs"]["otype"] == "file"
    assert parsed["outfile"]["attrs"]["default"] == "{{a}}"
    assert parsed["outdir"]["help"] == "help2"
    assert parsed["outdir"]["attrs"]["otype"] == "dir"
    assert parsed["outdir"]["attrs"]["default"] == "{{b}}"
    assert parsed["out"]["help"] == "help3"
    assert parsed["out"]["attrs"]["otype"] == "var"
    assert parsed["out"]["attrs"]["default"] == "{{c}}"


def test_output_missing_annotation():
    class TestProc:
        output = "outfile:file:{{a}}, outdir:dir:{{b}}, 1"

    section = SectionOutput(TestProc, "Output")
    section.consume("outdir: help2")

    parsed = section.parse()
    assert len(parsed) == 2
    assert parsed["outfile"]["help"] == ""
    assert parsed["outfile"]["attrs"]["otype"] == "file"
    assert parsed["outfile"]["attrs"]["default"] == "{{a}}"
    assert parsed["outdir"]["help"] == "help2"
    assert parsed["outdir"]["attrs"]["otype"] == "dir"
    assert parsed["outdir"]["attrs"]["default"] == "{{b}}"


def test_output_missing():
    class TestProc:
        output = None

    section = SectionOutput(TestProc, "Output")
    assert section.parse() == {}


def test_envs():
    class TestProc:
        envs = {"a": 1, "b": {"c": 3, "d": 4, "e": {"f": [6]}}}

    section = SectionEnvs(TestProc, "Envs")
    section.consume("a: help1")
    section.consume("b: help2")
    section.consume("  - c: help3")
    section.consume("  - e: help5")
    section.consume("    - f: help6")

    parsed = section.parse()

    assert len(parsed) == 2
    assert parsed["a"]["help"] == "help1"
    assert parsed["a"]["attrs"]["default"] == 1
    assert parsed["b"]["help"] == "help2"
    # assert parsed["b"]["attrs"]["action"] == "namespace"
    assert parsed["b"]["terms"]["c"]["help"] == "help3"
    assert parsed["b"]["terms"]["c"]["attrs"]["default"] == 3
    assert parsed["b"]["terms"]["d"]["help"] == ""
    assert parsed["b"]["terms"]["d"]["attrs"]["default"] == 4
    assert parsed["b"]["terms"]["e"]["help"] == "help5"
    assert parsed["b"]["terms"]["e"]["terms"]["f"]["help"] == "help6"
    assert parsed["b"]["terms"]["e"]["terms"]["f"]["attrs"]["default"] == [6]
    # assert parsed["b"]["terms"]["e"]["terms"]["f"]["attrs"]["nargs"] == "+"
    # assert (
    #     parsed["b"]["terms"]["e"]["terms"]["f"]["attrs"]["action"]
    #     == "clear_extend"
    # )
    assert parsed.to_markdown() == """- `a`: *Default: `1`*. <br />
    help1
- `b`:
    help2
    - `c`: *Default: `3`*. <br />
        help3
    - `e`:
        help5
        - `f`: *Default: `[6]`*. <br />
            help6
    - `d`: *Default: `4`*. <br />"""


def test_envs_help_continuing():
    class TestProc:
        envs = {"a": 1}

    section = SectionEnvs(TestProc, "Envs")
    section.consume("a: |")
    section.consume("  help1")
    section.consume("  help1 continued")

    parsed = section.parse()

    assert len(parsed) == 1
    assert parsed["a"]["help"] == "help1\nhelp1 continued"
    assert parsed.to_markdown() == """- `a`: *Default: `1`*. <br />
    help1
    help1 continued"""


def test_ipython_to_markdown():
    lines = [
        "a",
        ">>> print(123)",
        ">>> print(345)",
        "b.",
        "c",
        ">>> print('hello')",
    ]
    out = _ipython_to_markdown(lines)
    assert len(out) == 14
    assert out == [
        "a",
        "",
        "```python",
        "print(123)",
        "print(345)",
        "```",
        "",
        "b.<br />",
        "c",
        "",
        "```python",
        "print('hello')",
        "```",
        "",
    ]
