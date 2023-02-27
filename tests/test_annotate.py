import pytest  # noqa: F401

from pipen_annotate import annotate
from pipen_annotate.annotate import SECTION_TYPES
from pipen_annotate.sections import MissingAnnotationWarning, SectionItems


def test_annotate():

    @annotate
    @annotate
    class TestClass:
        """Summary

        Input:
            infile: Input file
            infiles: Input files

        Output:
            outfile: Output file

        Envs:
            arg1: help1
            arg2: help2
        """
        input = "infile:file, infiles:files"
        output = "outfile:file:{{in.infile | basename}}"
        envs = {"arg1": 1, "arg2": 2}

    annotated = TestClass.annotated
    assert annotated["Summary"]["short"] == "Summary"
    assert annotated["Summary"]["long"] == ""
    assert annotated["Input"]["infile"]["help"] == "Input file"
    assert annotated["Input"]["infile"]["attrs"]["itype"] == "file"
    assert annotated["Input"]["infile"]["attrs"]["action"] == "extend"
    assert annotated["Input"]["infile"]["attrs"]["nargs"] == "+"
    assert annotated["Input"]["infiles"]["help"] == "Input files"
    assert annotated["Input"]["infiles"]["attrs"]["itype"] == "files"
    assert annotated["Input"]["infiles"]["attrs"]["action"] == "append"
    assert annotated["Input"]["infiles"]["attrs"]["nargs"] == "+"
    assert annotated["Output"]["outfile"]["help"] == "Output file"
    assert annotated["Output"]["outfile"]["attrs"]["otype"] == "file"
    assert annotated["Output"]["outfile"]["attrs"][
        "default"
    ] == "{{in.infile | basename}}"
    assert annotated["Envs"]["arg1"]["help"] == "help1"
    assert annotated["Envs"]["arg2"]["help"] == "help2"


def test_annotate_with_no_docstring():
    @annotate
    class TestClass:
        ...

    assert TestClass.annotated == {}


def test_annotate_with_leading_space():
    with pytest.warns(MissingAnnotationWarning):
        @annotate
        class TestClass:
            """\
            Summary
            """
            input = "infile:file"
            output = "outfile:file:{{in.infile | basename}}"
            envs = {"arg1": 1, "arg2": 2}

    assert TestClass.annotated["Summary"]["short"] == "Summary"
    assert TestClass.annotated["Summary"]["long"] == ""


def test_annotate_with_single_docline():
    with pytest.warns(MissingAnnotationWarning):
        @annotate
        class TestClass:
            """Summary"""
            input = "infile:file"
            output = "outfile:file:{{in.infile | basename}}"
            envs = {"arg1": 1, "arg2": 2}

    assert TestClass.annotated["Summary"]["short"] == "Summary"
    assert TestClass.annotated["Summary"]["long"] == ""


def test_register_section():
    class TestSection(SectionItems):
        def parse(self):
            parsed = super().parse()
            for key, value in parsed.items():
                value.attrs["test"] = True
            return parsed

    annotate.register_section("Test", TestSection)

    with pytest.warns(MissingAnnotationWarning):
        @annotate
        class TestClass:
            """Summary

            Test:
                a: help1
                b: help2
            """
            input = "infile:file"
            output = "outfile:file:{{in.infile | basename}}"
            envs = {"arg1": 1, "arg2": 2}

    assert TestClass.annotated["Test"]["a"]["attrs"]["test"] is True
    assert TestClass.annotated["Test"]["b"]["attrs"]["test"] is True

    annotate.unregister_section("Test")
    assert "Test" not in SECTION_TYPES


def test_register_section_with_shotcut():
    annotate.register_section("Test", "text")

    with pytest.warns(MissingAnnotationWarning):
        @annotate
        class TestClass:
            """Summary

            Test:
                a: help1
                b: help2
            """
            input = "infile:file"
            output = "outfile:file:{{in.infile | basename}}"
            envs = {"arg1": 1, "arg2": 2}

    assert TestClass.annotated["Test"] == "a: help1\nb: help2"
    annotate.unregister_section("Test")


def test_register_section_with_invalid_type():
    with pytest.raises(ValueError):
        annotate.register_section("Test", "invalid")
