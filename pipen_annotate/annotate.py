from __future__ import annotations

import re
import textwrap
from typing import Any, Callable, Type, MutableMapping

from diot import OrderedDiot
from pipen import Proc

from .sections import (
    Section,
    SectionSummary,
    SectionInput,
    SectionOutput,
    SectionEnvs,
    SectionItems,
    SectionText,
)

SECTION_TYPES: MutableMapping[str, Type[Section]] = {
    "Summary": SectionSummary,
    "Input": SectionInput,
    "Output": SectionOutput,
    "Envs": SectionEnvs,
    "Args": SectionItems,
    "Returns": SectionItems,
    "Raises": SectionItems,
    "Warns": SectionItems,
    "See Also": SectionText,
    "Notes": SectionText,
    "References": SectionText,
    "Examples": SectionText,
    "Todo": SectionText,
    "Text": SectionText,
    "Items": SectionItems,
}

META_CONTAINER = "__meta__"


def _annotate_uninherited(cls: Type[Proc]) -> OrderedDiot:
    """Annotate a Proc class with docstring, without inheriting from base.

    Args:
        cls: The class to be annotated.

    Returns:
        The annotated dict.
    """
    annotated = OrderedDiot()
    docstring = cls.__doc__

    if docstring:
        if docstring[0] in (" ", "\t"):
            docstring = textwrap.dedent(docstring)
        else:
            parts = docstring.split("\n", 1)
            if len(parts) == 1:
                first, rest = parts[0], ""
            else:
                first, rest = parts
            docstring = f"{first}\n{textwrap.dedent(rest)}"

        section_name = "Summary"
        section = SectionSummary(cls, section_name)
        for line in docstring.splitlines():
            line = line.rstrip()
            if line and line[-1] == ":":
                if line[:-1] in SECTION_TYPES:
                    annotated[section_name] = section.parse()
                    section_name = line[:-1]
                    section = SECTION_TYPES[section_name](
                        cls,
                        section_name,
                    )
                elif re.sub(r"(?!^) ", "", line[:-1]).isidentifier():
                    annotated[section_name] = section.parse()
                    section_name = line[:-1]
                    section = SectionText(cls, section_name)
                else:
                    section.consume(line)
            else:
                section.consume(line)

        annotated[section_name] = section.parse()

    if issubclass(cls, Proc):
        if "Input" not in annotated:
            annotated.Input = SectionInput(cls, "Input").parse()
        if "Output" not in annotated:
            annotated.Output = SectionOutput(cls, "Output").parse()
        if "Envs" not in annotated:
            annotated.Envs = SectionEnvs(cls, "Envs").parse()

    return annotated


def _update_annotation(base: OrderedDiot, other: OrderedDiot) -> OrderedDiot:
    """Update the annotation with another annotation."""
    base = base.copy()
    for key, value in other.items():
        section_class = SECTION_TYPES.get(key)
        if key not in base or section_class is None:
            base[key] = value
        else:
            base[key] = section_class.update_parsed(base[key], value)
    return base


def annotate(cls: Type[Any]) -> OrderedDiot:
    """Annotate a Proc class with docstring.

    Args:
        cls: The class to be annotated.

    Returns:
        The annotated dict.
    """
    if not getattr(cls, META_CONTAINER, None):
        setattr(cls, META_CONTAINER, {})

    meta = getattr(cls, META_CONTAINER)

    if not meta.get("annotate_annotated", False):
        base = [
            mro
            for mro in cls.__mro__
            if issubclass(mro, Proc) and mro is not Proc and mro is not cls
        ]
        annotated = _annotate_uninherited(cls)
        if (
            not meta.get("annotate_doc_inherit", True)
            or not base
        ):
            meta["annotate_annotated"] = annotated
        else:
            meta["annotate_annotated"] = _update_annotation(
                annotate(base[0]),
                annotated,
            )

    return meta["annotate_annotated"]


def _register_section(
    section: str,
    section_class: Type[Section] | str | None = None,
) -> Callable[[Type[Section]], Type[Section]] | Type[Section]:
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
    # When used as a decorator
    if section_class is None:
        return lambda cls: _register_section(section, cls)

    if isinstance(section_class, str):
        section_class = section_class.title()
        if section_class not in SECTION_TYPES:
            raise ValueError(
                f"Invalid section class shortcut: {section_class}\n"
                f"Valid shortcuts: {', '.join(SECTION_TYPES)}",
            ) from None
        section_class = SECTION_TYPES[section_class]

    SECTION_TYPES[section] = section_class
    return section_class


def _unregister_section(section: str) -> None:
    """Unregister a section.

    Args:
        section: The section name.
    """
    SECTION_TYPES.pop(section, None)


def _no_doc_inherit(proc: Type[Proc]) -> Type[Proc]:
    """A decorator to disable docstring inheritance for a Proc class"""
    if not hasattr(proc, META_CONTAINER):
        setattr(proc, META_CONTAINER, {})

    getattr(proc, META_CONTAINER)["annotate_doc_inherit"] = False
    return proc


annotate.register_section = _register_section
annotate.unregister_section = _unregister_section
annotate.no_doc_inherit = _no_doc_inherit
