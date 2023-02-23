import pytest  # noqa: F401

from pipen_annotate.sections import (
    MissingAnnotationWarning,
    SectionEnvs,
    SectionInput,
    SectionItems,
    SectionOutput,
    SectionSummary,
    SectionText,
    _is_iterable,
)


def test_section_summary():
    section = SectionSummary(None)
    section.consume("Short summary.")
    section.consume("")
    section.consume("Long summary.")
    section.consume("Long long summary.")
    assert section.parse() == {
        "short": "Short summary.",
        "long": "Long summary.\nLong long summary.",
    }


def test_section_text():
    section = SectionText(None)
    section.consume("Text line 1.")
    section.consume("Text line 2.")
    assert section.parse() == "Text line 1.\nText line 2."


def test_section_items():
    section = SectionItems(None)
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
    assert parsed["item1"]["terms"]["subitem2"]["terms"]["subsubitem1"][
        "help"
    ] == "subsubhelp1 more help for subsubitem1"
    assert parsed["item1"]["terms"]["subitem2"]["terms"]["subsubitem1"][
        "attrs"
    ] == {}
    assert parsed["item1"]["terms"]["subitem2"]["terms"]["subsubitem1"][
        "terms"
    ] == {}
    assert parsed["item1"]["terms"]["subitem2"]["terms"]["subsubitem2"][
        "help"
    ] == "subsubhelp2"
    assert parsed["item1"]["terms"]["subitem2"]["terms"]["subsubitem2"][
        "attrs"
    ] == {}
    assert parsed["item1"]["terms"]["subitem2"]["terms"]["subsubitem2"][
        "terms"
    ] == {}
    assert parsed["item2"]["help"] == "help2 more help for item2"
    assert parsed["item2"]["attrs"] == {
        "attr1": "val1",
        "attr2": True,
        "attr3": "val3",
    }
    assert parsed["item2"]["terms"] == {}


def test_invalid_attr():
    section = SectionItems(None)
    section.consume("item1 (,): help1")
    with pytest.raises(ValueError, match="Invalid item attribute"):
        section.parse()


def test_invalid_item():
    section = SectionItems(None)
    section.consume("item1")
    with pytest.raises(ValueError, match="Invalid item line"):
        section.parse()


def test_input():
    class TestProc:
        input = "infile1:file, in2"

    section = SectionInput(TestProc)
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

    section = SectionInput(TestProc)
    section.consume("in2: help2")

    with pytest.warns(
        MissingAnnotationWarning,
        match="Missing annotation for input",
    ):
        section.parse()


def test_output():
    class TestProc:
        output = "outfile:file:{{a}}, outdir:dir:{{b}}, out:{{c}}"

    section = SectionOutput(TestProc)
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

    section = SectionOutput(TestProc)
    section.consume("outdir: help2")

    with pytest.warns(
        MissingAnnotationWarning,
        match="Missing annotation for output",
    ):
        section.parse()


def test_output_missing():
    class TestProc:
        output = None

    section = SectionOutput(TestProc)
    assert section.parse() == {}


def test_envs():
    class TestProc:
        envs = {"a": 1, "b": {"c": 3, "d": 4, "e": {"f": [6]}}}

    section = SectionEnvs(TestProc)
    section.consume("a: help1")
    section.consume("b: help2")
    section.consume("  - c: help3")
    section.consume("  - e: help5")
    section.consume("    - f: help6")

    with pytest.warns(
        MissingAnnotationWarning,
        match=r"Missing annotation for env: b\.d",
    ):
        parsed = section.parse()

    assert len(parsed) == 2
    assert parsed["a"]["help"] == "help1"
    assert parsed["a"]["attrs"]["default"] == 1
    assert parsed["b"]["help"] == "help2"
    assert parsed["b"]["terms"]["c"]["help"] == "help3"
    assert parsed["b"]["terms"]["c"]["attrs"]["default"] == 3
    assert parsed["b"]["terms"]["d"]["help"] == "Not annotated"
    assert parsed["b"]["terms"]["d"]["attrs"]["default"] == 4
    assert parsed["b"]["terms"]["e"]["help"] == "help5"
    assert parsed["b"]["terms"]["e"]["terms"]["f"]["help"] == "help6"
    assert parsed["b"]["terms"]["e"]["terms"]["f"]["attrs"]["default"] == [6]
    assert parsed["b"]["terms"]["e"]["terms"]["f"]["attrs"]["nargs"] == "+"
    assert parsed["b"]["terms"]["e"]["terms"]["f"]["attrs"]["action"] == "list"


def test_is_iterable():
    assert _is_iterable(1) is False
    assert _is_iterable("a") is False
    assert _is_iterable([1, 2, 3]) is True
    assert _is_iterable((1, 2, 3)) is True
    assert _is_iterable({"a": 1, "b": 2}) is True
