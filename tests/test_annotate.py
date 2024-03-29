import pytest  # noqa: F401

import json
from pipen import Proc, ProcGroup
from pipen.utils import mark
from pipen_annotate import annotate
from pipen_annotate.annotate import SECTION_TYPES
from pipen_annotate.sections import SectionItems, Section, UnknownAnnotationItemWarning, dedent


def test_annotate():

    class TestClass:
        """Summary

        Input:
            infile: Input file
            infiles: Input files
            x: help1

        Output:
            outfile: Output file

        Envs:
            arg1: help1
            arg2: help2
        """
        input = "infile:file, infiles:files"
        output = "outfile:file:{{in.infile | basename}}"
        envs = {"arg1": 1, "arg2": 2}

    with pytest.warns(UnknownAnnotationItemWarning):
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

    class TestClass2(Proc):
        ...

    anno = annotate(TestClass2)
    assert anno["Summary"]["short"] == ""
    assert anno["Summary"]["long"] == ""
    assert anno["Input"] == {}
    assert anno["Output"] == {}
    assert anno["Envs"] == {}


def test_annotate_with_leading_space():

    class TestClass:
        """\
        Summary

        Output:
            outfile: Output file
            y: help2
        """
        input = "infile:file"
        output = "outfile:file:{{in.infile | basename}}"
        envs = {"arg1": 1, "arg2": 2}

    with pytest.warns(UnknownAnnotationItemWarning):
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
    @annotate.register_section("Test")
    class TestSection(SectionItems):
        def parse(self):
            parsed = super().parse()
            for key, value in parsed.items():
                value.attrs["test"] = True
            return parsed

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

    class TestClass(Proc):
        """Summary

        Test:
            a: help1
            b: help2
        """
        input = "infile:file"
        output = "outfile:file:{{in.infile | basename}}"
        envs = {"arg1": 1, "arg2": 2}

    annotated = annotate(TestClass)

    assert annotated.Test.lines == ["a: help1", "b: help2"]
    annotate.unregister_section("Test")


def test_register_section_with_invalid_type():
    with pytest.raises(ValueError):
        annotate.register_section("Test", "invalid")


def test_inherit():
    class SectionList(Section):
        def parse(self):
            return dedent(self._lines)

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
            arg3 (hidden): help3

        Text:
            def

        List:
            c
            d

        Dict:
            {"c": 3, "b": 4}
        """
        envs = {"arg3": 3}

    annotated = annotate(Inherited1)
    assert annotated["Text"].lines == ["def"]
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
    assert annotated.Envs.to_markdown() == """- `arg1` *(`type=int;choices`)*: *Default: `1`*. <br />
    help11
- `arg2`: *Default: `2`*. <br />
    help2"""


def test_inherit_no_doc_inherit():

    class Base(Proc):
        """Summary

        Input:
            infile: Input file

        Output:
            outfile: Output file

        Envs:
            arg1 (type:int): help1
            arg2: help2

        List:
            a
            b

        Dict:
            {"a": 1, "b": 2}
        """
        input = "infile:file"
        output = "outfile:file:{{in.infile | basename}}"
        envs = {"arg1": 1, "arg2": 2}

    @mark(annotate_inherit=False)
    class Inherited2(Base):
        """Short

        Envs:
            arg1 (choices): help11
            arg3: help3
        """
        envs = {"arg3": 3}

    annotated = annotate(Inherited2)
    assert annotated["Summary"]["short"] == "Short"
    assert annotated["Summary"]["long"].strip() == ""
    assert annotated["Envs"]["arg1"]["help"] == "help11"
    assert annotated["Envs"]["arg1"]["attrs"]["choices"] is True
    assert "type" not in annotated["Envs"]["arg1"]["attrs"]
    assert annotated["Envs"]["arg3"]["help"] == "help3"


def test_procgroup():
    class MyGroup(ProcGroup):
        """Summary

        Args:
            arg1:
            arg2 (ns): help2
                - subarg1: help21
        """
        DEFAULTS = {"arg1": 1, "arg2": {"subarg1": 2}}

    annotated = annotate(MyGroup)
    assert annotated["Summary"]["short"] == "Summary"
    assert annotated["Summary"]["long"] == ""
    assert annotated["Args"]["arg1"]["help"] == ""
    assert annotated["Args"]["arg1"]["attrs"]["default"] == 1
    assert annotated["Args"]["arg2"]["help"] == "help2"
    assert annotated["Args"]["arg2"]["attrs"]["default"] == {"subarg1": 2}
    assert annotated["Args"]["arg2"]["attrs"]["ns"] is True
    assert annotated["Args"]["arg2"]["terms"]["subarg1"]["help"] == "help21"
    assert annotated["Args"]["arg2"]["terms"]["subarg1"]["attrs"][
        "default"
    ] == 2

    class MyGroup2(ProcGroup):
        """Summary"""

    annotated = annotate(MyGroup2)
    assert annotated["Summary"]["short"] == "Summary"
    assert annotated["Summary"]["long"] == ""
    assert annotated["Args"] == {}


def test_unknown_section():
    @mark(annotate_inherit=False)
    class TestClass:
        """Summary

        Un known:
            help1
            help2
        """
        input = "infile:file"
        output = "outfile:file:{{in.infile | basename}}"
        envs = {"arg1": 1, "arg2": 2}

    annotated = annotate(TestClass)
    assert annotated["Un known"].lines == ["help1", "help2"]


def test_help_newline():
    class TestClass:
        """Summary

        Envs:
            arg: help1.
                help2
        """
        input = "infile:file"
        output = "outfile:file:{{in.infile | basename}}"
        envs = {"arg": 1}

    annotated = annotate(TestClass)
    assert annotated.Envs.arg.help == "help1.\nhelp2"


def test_code():
    class TestClass:
        """Summary

        Envs:
            arg: help1
                >>> some code
                >>> some more code
                help2
        """
        input = "infile:file"
        output = "outfile:file:{{in.infile | basename}}"
        envs = {"arg": 1}

    annotated = annotate(TestClass)
    assert annotated.Envs.arg.help == 'help1\n>>> some code\n>>> some more code\nhelp2'
