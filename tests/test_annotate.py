import pytest

from pipen import Proc
from pipen_annotate import *

def test_basic():
    @annotate
    class Process1(Proc):
        ...

    assert Process1.annotated == {}

def test_summary():
    @annotate
    class Process1(Proc):
        """def

        ghi
        """
        desc = "abc"

    assert Process1.annotated.args is None
    assert Process1.annotated.input is None
    assert Process1.annotated.output is None
    assert Process1.annotated.short.lines == ['abc']
    assert Process1.annotated.long[0].lines == ['def']
    assert Process1.annotated.long[1].lines == ['ghi']

    @annotate
    class Process2(Proc):
        """
        a
        Input:
            input: An input
        """
        desc = "abc"

    assert Process2.annotated.args is None
    assert len(Process2.annotated.input) == 0
    assert Process2.annotated.output is None
    assert Process2.annotated.short.lines == ['abc']
    assert Process2.annotated.long[0].lines == ['a']


    @annotate
    class Process3(Proc):
        """short

        long
        """
    assert Process3.annotated.short.lines == ['short']
    assert Process3.annotated.long[0].lines == ['long']

def test_input():
    with pytest.warns(AnnotateMissingWarning):
        @annotate
        class Process1(Proc):
            """long

            Input:
                a: An input
            """
            desc = "abc"
            input_keys = 'a, b'

    assert Process1.annotated.input.a.name == 'a'
    assert Process1.annotated.input.a.type == 'var'
    assert Process1.annotated.input.a.desc == 'An input'
    assert Process1.annotated.input.a.more == []
    assert Process1.annotated.input.b.name == 'b'
    assert Process1.annotated.input.b.type == 'var'
    assert Process1.annotated.input.b.desc == None
    assert Process1.annotated.input.b.more == None

def test_output():
    with pytest.warns(AnnotateMissingWarning):
        @annotate
        class Process1(Proc):
            """long

            Output:
                a: An output
            """
            desc = "abc"
            output = 'a:file:1, b:2'

    assert Process1.annotated.output.a.name == 'a'
    assert Process1.annotated.output.a.type == 'file'
    assert Process1.annotated.output.a.desc == 'An output'
    assert Process1.annotated.output.a.more == [(['Default: 1'], )]
    assert Process1.annotated.output.b.name == 'b'
    assert Process1.annotated.output.b.type == 'var'
    assert Process1.annotated.output.b.desc == 'Undescribed.'
    assert Process1.annotated.output.b.more == [(['Default: 2'], )]

    @annotate
    class Process2(Proc):
        """long

        Output:
            a: An output
        """
        desc = "abc"
        output = '{{a:1}}'

    assert Process2.annotated.output == {}

def test_args():
    @annotate
    class Process1(Proc):
        """long

        Args:
            a: An arg
                More
        """
        args = {'a': 1, 'b': 2}

    assert Process1.annotated.args.a.name == 'a'
    assert Process1.annotated.args.a.type == None
    assert Process1.annotated.args.a.desc == 'An arg'
    assert Process1.annotated.args.a.more == [(['More'], ), (['Default: 1'], )]

    assert stringify(Process1.annotated.args.a) == 'a: An arg\n  More\n\n  Default: 1'
    assert stringify(None) == ''
    assert stringify('None') == 'None'
    assert stringify([Process1.annotated.args.a, Process1.annotated.args.b]) == 'a: An arg\n  More\n\n  Default: 1\nb: Undescribed.\n  Default: 2'