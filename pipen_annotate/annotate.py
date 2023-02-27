from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING, Type, MutableMapping
from diot import OrderedDiot

from . import sections

if TYPE_CHECKING:  # pragma: no cover
    from pipen import Proc

SECTION_TYPES: MutableMapping[str, Type[sections.Section] | str] = {
    "Summary": "summary",
    "Input": "input",
    "Output": "output",
    "Envs": "envs",
    "Args": "items",
    "Returns": "items",
    "Raises": "items",
    "Warns": "items",
    "See Also": "text",
    "Notes": "text",
    "References": "text",
    "Examples": "text",
    "Todo": "text",
}


def annotate(cls: Type[Proc]):
    """Annotate a Proc class with docstring.

    Args:
        cls: The class to be annotated.

    Returns:
        The annotated class.
    """
    if hasattr(cls, "annotated"):
        return cls

    cls.annotated = OrderedDiot()
    docstring = cls.__doc__

    if not docstring:
        return cls

    if docstring[0] in (" ", "\t"):
        docstring = textwrap.dedent(docstring)
    else:
        parts = docstring.split("\n", 1)
        if len(parts) == 1:
            first, rest = parts[0], ""
        else:
            first, rest = parts
        docstring = f"{first}\n{textwrap.dedent(rest)}"

    section = sections.SectionSummary(cls)
    section_name = "Summary"
    for line in docstring.splitlines():
        line = line.rstrip()
        if line and line[-1] == ":" and line[:-1] in SECTION_TYPES:
            cls.annotated[section_name] = section.parse()
            section_name = line[:-1]
            if isinstance(SECTION_TYPES[section_name], str):
                section_class = getattr(
                    sections,
                    f"Section{SECTION_TYPES[section_name].title()}",
                )
            else:
                section_class = SECTION_TYPES[section_name]

            section = section_class(cls)
        else:
            section.consume(line)

    cls.annotated[section_name] = section.parse()

    if "Input" not in cls.annotated:
        cls.annotated.Input = sections.SectionInput(cls).parse()
    if "Output" not in cls.annotated:
        cls.annotated.Output = sections.SectionOutput(cls).parse()
    if "Envs" not in cls.annotated:
        cls.annotated.Envs = sections.SectionEnvs(cls).parse()

    return cls


def _register_section(
    section: str,
    section_class: Type[sections.Section],
) -> None:
    """Register a section to be parsed.

    Args:
        section: The section name.
        section_class: The section class or a shortcut string to
            builtin section class.
            summary: SectionSummary
            input: SectionInput
            output: SectionOutput
            envs: SectionEnvs
            items: SectionItems
            text: SectionText
    """
    if isinstance(section_class, str):
        try:
            section_class = getattr(
                sections,
                f"Section{section_class.title()}",
            )
        except AttributeError:
            raise ValueError(
                f"Invalid section class shortcut: {section_class}\n"
                f"Valid shortcuts: {', '.join(sections.__all__)}",
            ) from None

    SECTION_TYPES[section] = section_class


def _unregister_section(section: str) -> None:
    """Unregister a section.

    Args:
        section: The section name.
    """
    SECTION_TYPES.pop(section, None)


annotate.register_section = _register_section
annotate.unregister_section = _unregister_section
