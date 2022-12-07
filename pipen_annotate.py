"""Use docstring to annotate pipen processes"""
import warnings

from diot import Diot, OrderedDiot
from pipen.defaults import ProcInputType
from pardoc import google_parser
from pardoc.default import SUMMARY
from pardoc.parsed import ParsedItem, ParsedPara, ParsedTodo, ParsedCode

__version__ = "0.0.3"
__all__ = ("annotate", "stringify", "AnnotateMissingWarning")


def stringify(parsed, indent: str = "", indent_base: str = "  ") -> str:
    if parsed is None:
        return ""

    if isinstance(parsed, list):
        return "\n".join(stringify(par, indent, indent_base) for par in parsed)

    if not isinstance(
        parsed, (ParsedItem, ParsedPara, ParsedTodo, ParsedCode)
    ):
        return str(parsed)

    return "\n".join(
        google_parser._format_element(
            parsed,
            indent=indent,
            leading_empty_line=False,
            indent_base=indent_base,
        )
    )


class AnnotateMissingWarning(Warning):
    """Missing items in annotation"""


def annotate(cls=None, *, warn_missing=True):
    if cls is not None:
        return annotate(warn_missing=warn_missing)(cls)

    def wrapper(cls):

        cls.annotated = Diot(diot_nest=False)

        try:
            doc = cls.__doc__
        except AttributeError:  # pragma: no cover
            return cls
        if not doc:
            return cls

        parsed = google_parser.parse(doc)

        annotate_summary(cls, parsed.get(SUMMARY))
        annotate_input(cls, parsed.get("Input"), warn_missing)
        annotate_output(cls, parsed.get("Output"), warn_missing)
        annotate_args(cls, parsed.get("Args"), warn_missing)

        for key in parsed:
            if key not in (SUMMARY, "Input", "Output", "Args"):
                cls.annotated[key.lower()] = parsed[key]

        return cls

    return wrapper


def annotate_summary(cls, summary):
    if cls.desc:
        cls.annotated.short = ParsedPara([cls.desc])
        cls.annotated.long = summary.section
    else:
        cls.annotated.short = summary.section[0]
        cls.annotated.long = summary.section[1:]


def annotate_input(cls, input, warn_missing):
    if not input:
        cls.annotated.input = None
        return

    cls.annotated.input = OrderedDiot(diot_nest=False)
    parsed_items = {
        parsed_item.name: parsed_item for parsed_item in input.section
    }

    input_keys = cls.input
    if isinstance(input_keys, str):
        input_keys = [input_key.strip() for input_key in input_keys.split(",")]

    for input_key_type in input_keys or []:
        if ":" not in input_key_type:
            input_key_type = f"{input_key_type}:{ProcInputType.VAR}"
        input_key, input_type = input_key_type.split(":", 1)
        if input_key not in parsed_items and warn_missing:
            warnings.warn(
                f"Missing annotation for input: {input_key}",
                AnnotateMissingWarning,
            )
            cls.annotated.input[input_key] = ParsedItem(
                name=input_key, type=input_type, desc=None, more=None
            )
        else:
            item = parsed_items[input_key]
            cls.annotated.input[input_key] = ParsedItem(
                name=item.name, type=input_type, desc=item.desc, more=item.more
            )


def annotate_output(cls, output, warn_missing):
    if not output:
        cls.annotated.output = None
        return

    cls.annotated.output = OrderedDiot(diot_nest=False)
    parsed_items = {
        parsed_item.name: parsed_item for parsed_item in output.section
    }

    # output can be arbitrary template string.
    # its structure is resolved after its rendered.
    # here we are trying to parse the output if it's just single strings
    # For example:
    # >>> output = "afile:file:..., bfile:file:..."
    # or
    # >>> output = ["afile:file:...", "bfile:file:..."]
    # give up parsing if any error happens
    output = cls.output

    def parse_one_output(out):
        parts = out.split(":")
        if not parts[0].isidentifier():
            return None
        if len(parts) < 3:
            return parts[0], ProcInputType.VAR, parts[1]
        return parts

    if not isinstance(output, (list, tuple)):
        output = [out.strip() for out in output.split(",")]

    for out in output:
        parsed = parse_one_output(out)
        if not parsed:
            continue
        if parsed[0] not in parsed_items and warn_missing:
            warnings.warn(
                f"Missing annotation for output: {parsed[0]}",
                AnnotateMissingWarning,
            )
            cls.annotated.output[parsed[0]] = ParsedItem(
                name=parsed[0],
                type=parsed[1],
                desc="Undescribed.",
                more=[ParsedPara([f"Default: {parsed[2]}"])],
            )
        else:
            cls.annotated.output[parsed[0]] = ParsedItem(
                name=parsed[0],
                type=parsed[1],
                desc=parsed_items[parsed[0]].desc,
                more=(parsed_items[parsed[0]].more or [])
                + [ParsedPara([f"Default: {parsed[2]}"])],
            )


def annotate_args(cls, args, warn_missing):
    if not args:
        cls.annotated.args = None
        return

    cls.annotated.args = OrderedDiot(diot_nest=False)
    parsed_items = {
        parsed_item.name: parsed_item for parsed_item in args.section
    }

    for key, val in cls.args.items():
        if key not in parsed_items and warn_missing:
            warnings.warn(
                f"Missing annotation for args: {key}", AnnotateMissingWarning
            )
            cls.annotated.args[key] = ParsedItem(
                name=key,
                type=None,
                desc="Undescribed.",
                more=[
                    ParsedPara([f'Default: {repr(val) if val == "" else val}'])
                ],
            )
        else:
            item = parsed_items[key]
            cls.annotated.args[key] = ParsedItem(
                name=key,
                type=item.type,
                desc=item.desc,
                more=(item.more or [])
                + [
                    ParsedPara([f'Default: {repr(val) if val == "" else val}'])
                ],
            )
