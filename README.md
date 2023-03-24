# pipen-annotate

Use docstring to annotate [pipen](https://github.com/pwwang/pipen) processes

## Installation

```shell
pip install -U pipen-annotate
```

## Usage

```python
from pprint import pprint
from pipen import Proc
from pipen_annotate import annotate


class Process(Proc):
    """Short description

    Long description

    Input:
        infile: An input file
        invar: An input variable

    Output:
        outfile: The output file

    Envs:
        ncores: Number of cores
    """
    input = "infile:file, invar"
    output = "outfile:file:output.txt"
    args = {'ncores': 1}

annotated = annotate(Process)
# prints:
{'Envs': {'ncores': {'attrs': OrderedDiot([('default', 1)]),
                     'help': 'Number of cores',
                     'terms': OrderedDiot([])}},
 'Input': {'infile': {'attrs': {'action': 'extend',
                                'itype': 'file',
                                'nargs': '+'},
                      'help': 'An input file',
                      'terms': OrderedDiot([])},
           'invar': {'attrs': {'action': 'extend',
                               'itype': 'var',
                               'nargs': '+'},
                     'help': 'An input variable',
                     'terms': OrderedDiot([])}},
 'Output': {'outfile': {'attrs': {'default': 'output.txt',
                                  'otype': 'file'},
                        'help': 'The output file',
                        'terms': OrderedDiot([])}},
 'Summary': {'long': 'Long description\n',
             'short': 'Short description'}}
```
