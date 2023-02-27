from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, List

import re
import textwrap
import warnings

from diot import Diot, OrderedDiot
from pipen.defaults import ProcInputType

__all__ = (
    "SectionSummary",
    "SectionInput",
    "SectionOutput",
    "SectionEnvs",
    "SectionItems",
    "SectionText",
)

ITEM_LINE_REGEX = re.compile(
    r"(?P<name>^[\w-]+)\s*(?:\((?P<attrs>.+?)\))?:(?P<help>.+)?$"
)
ITEM_ATTR_REGEX = re.compile(r"(?P<name>[\w-]+)(?:\s*:\s*(?P<value>.+))?")


def _is_iterable(obj: Any) -> bool:
    """Check if an object is iterable.
    """
    try:
        iter(obj)
    except TypeError:
        return False
    if isinstance(obj, str):
        return False
    return True


def _dedent(lines: List[str]) -> List[str]:
    """Dedent a list of lines.
    """
    return textwrap.dedent("\n".join(lines)).splitlines()


def _parse_terms(lines: List[str], prefix: str | None = None) -> Diot:
    """Parse a list of lines as terms.
    """
    terms = OrderedDiot()
    lines = _dedent(lines)
    sublines = []
    item = None
    just_matched = False
    for line in lines:
        if prefix:
            matched = ITEM_LINE_REGEX.match(line[len(prefix):])
        else:
            matched = ITEM_LINE_REGEX.match(line)

        if matched:
            if item:
                # See if we have sub-terms
                item.terms = _parse_terms(sublines, prefix="- ")
                sublines.clear()

            # Create a new item
            name = matched.group("name")
            attrs = matched.group("attrs")
            help = matched.group("help")
            terms[name] = Diot(attrs={}, terms={}, help="")

            if attrs:
                for attr in attrs.split(";"):
                    attr = attr.strip()
                    attr_matched = ITEM_ATTR_REGEX.match(attr)
                    if not attr_matched:
                        raise ValueError(f"Invalid item attribute: {attr}")
                    attr_name = attr_matched.group("name")
                    attr_value = attr_matched.group("value")

                    terms[name].attrs[attr_name] = (
                        True if attr_value is None else attr_value
                    )
            terms[name].help = help.lstrip()
            item = terms[name]
            just_matched = True
        elif item is None:
            raise ValueError(f"Invalid item line: {line}")
        elif just_matched and not line.lstrip().startswith("- "):
            item.help += f" {line.lstrip()}"
        elif line.lstrip().startswith("- "):
            sublines.append(line)
            just_matched = False
        else:
            sublines.append(line)

    if item:
        # See if we have sub-terms
        item.terms = _parse_terms(sublines, prefix="- ")

    return terms


def _parse_one_output(out: str) -> List[str] | None:
    """Parse one output item, such as `out:file:<outfile>`"""
    parts = out.split(":")
    if not parts[0].isidentifier():
        return None
    if len(parts) < 3:
        return [parts[0], ProcInputType.VAR, parts[1]]
    return parts


def _update_attrs_with_cls(
    parsed: Diot,
    envs: dict | None,
    prev_key: str | None = None,
    cls_name: str | None = None,
) -> None:
    """Update the attrs of parsed terms with the class envs."""
    envs = envs or {}
    for key, value in envs.items():
        whole_key = f"{prev_key}.{key}" if prev_key else key

        if key not in parsed:
            warnings.warn(
                f"Missing annotation for env: {whole_key} ({cls_name})",
                MissingAnnotationWarning,
            )
            parsed[key] = Diot(attrs={}, terms={}, help="Not annotated")

        if isinstance(value, dict):
            parsed[key].attrs.setdefault("action", "namespace")
            _update_attrs_with_cls(
                parsed[key].terms,
                value,
                whole_key,
                cls_name,
            )
            continue

        if "default" not in parsed[key].attrs:
            parsed[key].attrs["default"] = value

        if "atype" not in parsed[key].attrs:
            if value is not None and not _is_iterable(value):
                parsed[key].attrs["atype"] = type(value).__name__

        if isinstance(value, list):
            if "action" not in parsed[key].attrs:
                parsed[key].attrs["action"] = "clear_extend"
            if "nargs" not in parsed[key].attrs:
                parsed[key].attrs["nargs"] = "+"


class MissingAnnotationWarning(Warning):
    """Warns when a Proc class has a missing annotation (input/output)."""


class Section(ABC):

    def __init__(self, cls) -> None:
        self._cls = cls
        self._lines: List[str] = []

    def consume(self, line: str) -> None:
        self._lines.append(line)

    @abstractmethod
    def parse(self) -> str | Diot | List[str]:  # pragma: no cover
        pass


class SectionSummary(Section):

    def parse(self) -> str | Diot | List[str]:
        return Diot(
            short=self._lines[0],
            long="\n".join(self._lines[1:]).lstrip(),
        )


class SectionItems(Section):

    def parse(self) -> str | Diot | List[str]:
        return _parse_terms(self._lines)


class SectionInput(SectionItems):

    def parse(self) -> str | Diot | List[str]:
        parsed = _parse_terms(self._lines)
        input_keys = self._cls.input

        if isinstance(input_keys, str):
            input_keys = [
                input_key.strip() for input_key in input_keys.split(",")
            ]

        for input_key_type in input_keys or []:
            if ":" not in input_key_type:
                input_key_type = f"{input_key_type}:{ProcInputType.VAR}"

            input_key, input_type = input_key_type.split(":", 1)
            if input_key not in parsed:
                warnings.warn(
                    f"Missing annotation for input: {input_key} "
                    f"({self._cls.__name__})",
                    MissingAnnotationWarning,
                )
                parsed[input_key] = Diot(
                    attrs={"itype": input_type},
                    terms={},
                    help="Not annotated",
                )
            else:
                parsed[input_key].attrs["itype"] = input_type

            parsed[input_key].attrs["nargs"] = "+"
            if input_type in (ProcInputType.FILES, ProcInputType.DIRS):
                parsed[input_key].attrs["action"] = "append"
            else:
                parsed[input_key].attrs["action"] = "extend"

        return parsed


class SectionOutput(SectionItems):

    def parse(self) -> str | Diot | List[str]:
        output = self._cls.output
        if not output:
            return Diot()

        parsed = _parse_terms(self._lines)

        if not isinstance(output, (list, tuple)):
            output = [out.strip() for out in output.split(",")]

        for out in output:
            parts = _parse_one_output(out)
            if not parts:
                continue

            if parts[0] not in parsed:
                warnings.warn(
                    f"Missing annotation for output: {parts[0]} "
                    f"({self._cls.__name__})",
                    MissingAnnotationWarning,
                )
                parsed[parts[0]] = Diot(
                    attrs={"otype": parts[1], "default": parts[2]},
                    terms={},
                    help="Not annotated",
                )
            else:
                parsed[parts[0]].attrs["otype"] = parts[1]
                parsed[parts[0]].attrs["default"] = parts[2]

        return parsed


class SectionEnvs(SectionItems):

    def parse(self) -> str | Diot | List[str]:
        parsed = _parse_terms(self._lines)
        _update_attrs_with_cls(
            parsed,
            self._cls.envs,
            cls_name=self._cls.__name__,
        )
        return parsed


class SectionText(Section):

    def parse(self) -> str | Diot | List[str]:
        return "\n".join(_dedent(self._lines))
