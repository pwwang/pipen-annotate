import pytest  # noqa: F401

import json
from pipen import Proc
from pipen_annotate import annotate
from pipen_annotate.annotate import SECTION_TYPES
from pipen_annotate.sections import SectionItems, Section, _dedent


def test_annotate():

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

    annotated = annotate(TestClass)
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
    class TestClass:
        ...

    assert annotate(TestClass) == {}


def test_annotate_with_leading_space():

    class TestClass:
        """\
        Summary
        """
        input = "infile:file"
        output = "outfile:file:{{in.infile | basename}}"
        envs = {"arg1": 1, "arg2": 2}

    annotated = annotate(TestClass)

    assert annotated["Summary"]["short"] == "Summary"
    assert annotated["Summary"]["long"] == ""


def test_annotate_with_single_docline():

    class TestClass:
        """Summary"""
        input = "infile:file"
        output = "outfile:file:{{in.infile | basename}}"
        envs = {"arg1": 1, "arg2": 2}

    annotated = annotate(TestClass)

    assert annotated["Summary"]["short"] == "Summary"
    assert annotated["Summary"]["long"] == ""


def test_register_section():
    class TestSection(SectionItems):
        def parse(self):
            parsed = super().parse()
            for key, value in parsed.items():
                value.attrs["test"] = True
            return parsed

    annotate.register_section("Test", TestSection)

    class TestClass:
        """Summary

        Test:
            a: help1
            b: help2
        """
        input = "infile:file"
        output = "outfile:file:{{in.infile | basename}}"
        envs = {"arg1": 1, "arg2": 2}

    annotated = annotate(TestClass)

    assert annotated["Test"]["a"]["attrs"]["test"] is True
    assert annotated["Test"]["b"]["attrs"]["test"] is True

    annotate.unregister_section("Test")
    assert "Test" not in SECTION_TYPES


def test_register_section_with_shotcut():
    annotate.register_section("Test", "text")

    class TestClass:
        """Summary

        Test:
            a: help1
            b: help2
        """
        input = "infile:file"
        output = "outfile:file:{{in.infile | basename}}"
        envs = {"arg1": 1, "arg2": 2}

    annotated = annotate(TestClass)

    assert annotated["Test"] == "a: help1\nb: help2"
    annotate.unregister_section("Test")


def test_register_section_with_invalid_type():
    with pytest.raises(ValueError):
        annotate.register_section("Test", "invalid")


def test_inherit():
    class SectionList(Section):
        def parse(self):
            return _dedent(self._lines)

    class SectionDict(Section):
        def parse(self):
            return json.loads(self._lines[0].strip())

    annotate.register_section("List", SectionList)
    annotate.register_section("Dict", SectionDict)

    class Base(Proc):
        """Summary

        Input:
            infile: Input file

        Output:
            outfile: Output file

        Envs:
            arg1 (type:int): help1
            arg2: help2

        Text:
            abc

        List:
            a
            b

        Dict:
            {"a": 1, "b": 2}
        """
        input = "infile:file"
        output = "outfile:file:{{in.infile | basename}}"
        envs = {"arg1": 1, "arg2": 2}

    class Inherited1(Base):
        """Short

        Long

        Envs:
            arg1 (choices): help11
            arg3: help3

        Text:
            def

        List:
            c
            d

        Dict:
            {"c": 3, "b": 4}
        """
        envs = {"arg3": 3}

    annotated = annotate(Inherited1, inherit=True)
    assert annotated["Text"] == "def"
    assert annotated["List"] == ["a", "b", "c", "d"]
    assert annotated["Dict"] == {"a": 1, "b": 4, "c": 3}
    assert annotated["Summary"]["short"] == "Short"
    assert annotated["Summary"]["long"].strip() == "Long"
    assert annotated["Input"]["infile"]["help"] == "Input file"
    assert annotated["Input"]["infile"]["attrs"]["itype"] == "file"
    assert annotated["Input"]["infile"]["attrs"][
        "action"
    ] == "extend"
    assert annotated["Input"]["infile"]["attrs"]["nargs"] == "+"
    assert annotated["Output"]["outfile"]["help"] == "Output file"
    assert annotated["Output"]["outfile"]["attrs"]["otype"] == "file"
    assert annotated["Output"]["outfile"]["attrs"][
        "default"
    ] == "{{in.infile | basename}}"
    assert annotated["Envs"]["arg1"]["help"] == "help11"
    assert annotated["Envs"]["arg1"]["attrs"]["type"] == "int"
    assert annotated["Envs"]["arg1"]["attrs"]["choices"] is True
    assert annotated["Envs"]["arg2"]["help"] == "help2"
    assert annotated["Envs"]["arg3"]["help"] == "help3"
