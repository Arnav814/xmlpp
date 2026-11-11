import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from copy import deepcopy


@dataclass
class Template:
    name: str
    path: Path
    params: list[str]
    content: ET.Element


@dataclass
class TemplateInit:
    template: Template
    args: list[ET.Element]


@dataclass
class State:
    templates: list[Template]
    dirtree: dict[str, dict | None]


def process_template(content: str, path: Path) -> Template:
    xml = ET.fromstring(content)
    if xml.tag != "templatedef":
        raise Exception("File does not contain a template.")

    params: set[str] = set()

    for child in xml.iter("param"):
        if "name" not in child.attrib.keys():
            raise Exception("Parameter has no name.")
        param = child.attrib["name"]
        if param is None:
            raise Exception("Empty parameter name.")
        params.add(param)

    return Template(path.stem.lstrip('@'), path, list(params), xml)


# replaces an element with the children of *another* element
# keeps track of text and concats where needed
# needs the parent of the element to be replaced
def replace_element_with_children(
        parent: ET.Element, target: ET.Element, replacement: ET.Element):
    replacement = deepcopy(replacement)

    # needed if we need to concat text at the start
    prev: ET.Element | None = None
    index = 0
    for elem in parent:
        if elem is target:
            break
        prev = elem
        index += 1

    tail = target.tail if target.tail is not None else ""
    parent.remove(target)
    if replacement.text is not None:
        if prev is not None:
            if prev.tail is None:
                prev.tail = replacement.text
            else:
                prev.tail += replacement.text
        else:
            if parent.text is None:
                parent.text = replacement.text
            else:
                parent.text += replacement.text

    for i, elem in enumerate(replacement):
        if i == len(replacement) - 1:
            if elem.tail is None:
                elem.tail = tail
            else:
                elem.tail += tail
        parent.insert(index + i, elem)


def expand_params(tree: ET.Element, state: State,
                  expanding_template: TemplateInit | None = None) -> ET.Element:
    # reverse to allow modification
    for child in reversed(tree):
        # TODO: check for links and ensure they're valid

        if child.tag == "param":
            # already checked that the param has a name
            param_name = child.attrib["name"]
            if expanding_template is None:
                raise Exception(f'Parameter "{param_name}" referenced outside of a template.')
            print(f"expanding param {param_name} for {expanding_template.template.name}")

            for index, p in enumerate(expanding_template.template.params):
                if param_name == p:
                    replacement = expanding_template.args[index]
                    replace_element_with_children(tree, child, replacement)
                    break
            else:
                raise Exception(f'Parameter "{param_name} referenced without being defined in expansion of template "{expanding_template.template.name}".');

        if len(child) > 0:
            expand_params(child, state, expanding_template)

    return tree


def expand_templates(tree: ET.Element, state: State) -> ET.Element:
    for child in reversed(tree):
        # expand templates
        if child.tag == "template":
            if "name" not in child.attrib.keys():
                raise Exception("No template specified to instantiate.")
            template_name = child.attrib["name"]
            template: Template | None = None
            for i in state.templates:
                if i.name == template_name:
                    template = i
                    break
            if template is None:
                raise Exception(f'Couldn\'t find template "{template_name}".')

            args: list[ET.Element] = \
                [ET.Element("argument") for i in template.params]
            for arg in child:
                if arg.tag != "argument":
                    raise Exception(f'Unexpected tag "{arg.tag}" in instantiation of template "{template.name}".')
                if "name" not in arg.attrib.keys():
                    raise Exception(f'Argument with missing name in instantiation of template "{template.name}".')
                param = arg.attrib["name"]

                for index, p in enumerate(template.params):
                    if p == param:
                        # could remove the attributes, but why bother
                        args[index] = arg
                        break
                else:
                    raise Exception(f'Argument refers to undeclared parameter "{param}" in instantiation of template "{template.name}".')

            # mmm, recursion
            expanded = process_tree(deepcopy(template.content), state,
                                    TemplateInit(template, args))
            replace_element_with_children(tree, child, expanded)

        if len(child) > 0:
            expand_templates(child, state)

    return tree


# recursively process the tree
def process_tree(tree: ET.Element, state: State,
                 expanding_template: TemplateInit | None = None) -> ET.Element:
    # expand parameters first so that template instantiations that contain
    # paramters are handled correctly
    tree = expand_params(tree, state, expanding_template)
    tree = expand_templates(tree, state)
    return tree


# process one file
def process_file(content: str, state: State) -> str:
    xml = ET.fromstring(content)

    if xml.tag == "template":
        raise Exception("Root tag cannot be a template.")

    processed = process_tree(xml, state, None)
    return ET.tostring(processed, encoding="unicode")
