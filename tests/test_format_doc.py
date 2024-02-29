import pytest  # noqa: F401
from pipen import Proc
from pipen_annotate import annotate


@pytest.fixture
def klass():

    @annotate.format_doc  # when no base, return the class itself
    class K:
        """Short summary

        Long summary

        Envs:
            arg1: help11
                >>> some code
                >>> some more code
                help12
                - subarg1: help111
                - subarg2: help112
            arg2 (type=int;required): help21.
                help22

        Text:
            A lazy dog jumps over a quick brown fox 1.
            A lazy dog jumps over a quick brown fox 2.
        """
        envs = {"arg": 1, "arg1": {"subarg1": 2, "subarg2": 3}}

    return K


def test_format_doc_inherits_whole_section(klass):

    @annotate.format_doc(indent=2)
    class K2(klass):
        """{{Summary}}

        {{* Envs }}

        {{* Text }}
        """

    annotated = annotate(K2)
    assert annotated["Summary"]["short"] == "Short summary"
    assert annotated["Summary"]["long"] == "Long summary"
    assert annotated["Envs"]["arg1"]["help"] == 'help11\n>>> some code\n>>> some more code\nhelp12'
    assert annotated["Envs"]["arg1"]["terms"]["subarg1"]["help"] == "help111"
    assert annotated["Envs"]["arg1"]["terms"]["subarg2"]["help"] == "help112"
    assert annotated["Envs"]["arg2"]["help"] == "help21.\nhelp22"
    assert annotated["Envs"]["arg2"]["attrs"]["type"] == "int"
    assert annotated["Envs"]["arg2"]["attrs"]["required"] is True
    assert annotated["Text"].lines == [
        "A lazy dog jumps over a quick brown fox 1.",
        "A lazy dog jumps over a quick brown fox 2.",
    ]


def test_format_doc_inherits_section_items(klass):

    @annotate.format_doc(indent=2)
    class K3(klass):
        """{{Summary.short}}

        {{Summary.long}}

        Envs:
            {{* Envs.arg1 }}
            {{* Envs.arg2 }}

        Text2:
            {{* Text.lines }}
        """

    annotated = annotate(K3)
    assert annotated["Summary"]["short"] == "Short summary"
    assert annotated["Summary"]["long"] == "Long summary"
    assert annotated["Envs"]["arg1"]["help"] == 'help11\n>>> some code\n>>> some more code\nhelp12'
    assert annotated["Envs"]["arg1"]["terms"]["subarg1"]["help"] == "help111"
    assert annotated["Envs"]["arg1"]["terms"]["subarg2"]["help"] == "help112"
    assert annotated["Envs"]["arg2"]["help"] == "help21.\nhelp22"
    assert annotated["Envs"]["arg2"]["attrs"]["type"] == "int"
    assert annotated["Envs"]["arg2"]["attrs"]["required"] is True
    assert annotated["Text2"].lines == [
        "A lazy dog jumps over a quick brown fox 1.",
        "A lazy dog jumps over a quick brown fox 2.",
    ]


def test_format_doc_update_section_items(klass):

    @annotate.format_doc(indent=2)
    class K4(klass):
        """{{Summary}}

        Envs:
            arg2 (readonly;{{Envs.arg2.attrs}}): {{Envs.arg2.help | indent: 16}}
                more help
        """
    assert K4.__doc__.startswith("Short summary")
    annotated = annotate(K4)
    assert annotated["Summary"]["short"] == "Short summary"
    assert annotated["Summary"]["long"] == "Long summary"
    assert annotated["Envs"]["arg2"]["help"] == "help21.\nhelp22 more help"
    assert annotated["Envs"]["arg2"]["attrs"]["type"] == "int"
    assert annotated["Envs"]["arg2"]["attrs"]["required"] is True
    assert annotated["Envs"]["arg2"]["attrs"]["readonly"] is True
    assert "arg1" in annotated["Envs"]


def test_format_doc_inherits_whole_summary(klass):

    @annotate.format_doc(indent=2)
    class K5(klass):
        """{{Summary}}"""

    annotated = annotate(K5)
    assert annotated["Summary"]["short"] == "Short summary"
    assert annotated["Summary"]["long"] == "Long summary"


def test_format_doc_works_when_both_classes_with_no_docs():

    # Test both None
    class L:
        ...

    @annotate.format_doc(indent=2)
    class L1(L):
        ...

    assert L1.__doc__ is None

    # Test base not None
    class M:
        """Summary"""

    @annotate.format_doc(indent=2)
    class M1(M):
        ...

    assert M1.__doc__ == "Summary\n"


def test_proc_format_doc():

    class P(Proc):
        """Short summary

        Long summary
        """
        envs = {"arg": 1}

    class P2(P):
        """Short summary2

        Long summary2

        Envs:
            arg: help1
        """
        envs = {"arg": 1}

    @annotate.format_doc(indent=2, vars={"a": 1})
    class P3(P2):
        """{{Summary}}

        Envs:
            arg (readonly): {{Envs.arg.help | indent: 16}}

        Vars:
            a: {{a}}
        """

    assert P2.__doc__.startswith("Short summary2")
    assert P3.__doc__.startswith("Short summary2")
    assert P3.__doc__.strip().endswith("a: 1")
