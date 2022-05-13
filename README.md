# pipen-annotate

Use docstring to annotate [pipen](https://github.com/pwwang/pipen) processes

## Installation

```shell
pip install pipen-annotate
```

## Usage

```python
from pipen import Proc
from pipen_annotate import annotate

@annotate
class Process(Proc):
    """Short description

    Long description

    Input:
        infile: An input file
        invar: An input variable

    Output:
        outfile: The output file

    Args:
        ncores: Number of cores
    """
    input = "infile:file, invar"
    output = "outfile:file:output.txt"
    args = {'ncores': 1}

print(Process.annotated)
# prints:
{'args': {'ncores': ParsedItem(name='ncores',
                               type=None,
                               desc='Number of cores',
                               more=[ParsedPara(lines=['Default: 1'])])},
 'input': {'infile': ParsedItem(name='infile',
                                type='file',
                                desc='An input file',
                                more=[]),
           'invar': ParsedItem(name='invar',
                               type='var',
                               desc='An input variable',
                               more=[])},
 'long': [ParsedPara(lines=['Long description'])],
 'output': {'outfile': ParsedItem(name='outfile',
                                  type='file',
                                  desc='The output file',
                                  more=[ParsedPara(lines=['Default: output.txt'])])},
 'short': ParsedPara(lines=['Short description'])}
```
