import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Parameter:
    name: str
    default: str | None


@dataclass
class Template:
    name: str
    path: Path
    params: list[Parameter]
    content: ET.Element


@dataclass
class State:
    templates: list[Template]
    dirtree: dict[str, dict | None]


def process_template(content: str, path: Path) -> Template:
    xml = ET.fromstring(content)
    if xml.tag != "templatedef":
        raise Exception("File does not contain a template.")

    params: list[Parameter] = []

    for child in xml:
        if child.tag == "paramdef":
            if child.text is None:
                raise Exception("Empty parameter definition.")
            keys = child.attrib.keys()
            if len(keys) >= 2 or len(keys) != 0 and "default" not in keys:
                raise Exception(f"Unexpected attribute(s) in parameter: {keys}.")

            default = child.attrib["default"] if len(keys) > 0 else None
            params.append(Parameter(child.text, default))
            xml.remove(child)
        else:
            break

    # done reading parameters
    seen: set[str] = set()
    for i in params:
        if i.name in seen:
            raise Exception(f"Duplicate definition of parameter {i.name}.")
        seen.add(i.name)

    # more sanity checks
    for child in xml.iter():
        if child.tag == "paramdef":
            raise Exception(f"Definition of parameter {child.text} after end of parameter list.")

        if child.tag == "param":
            param = child.text
            if not any((i.name == param for i in params)):
                raise Exception(f"Use of undeclared parameter {param}.")

    return Template(path.name, path, params, xml)


# process one file
def process_file(content: str, state: State) -> str:
    return ""
