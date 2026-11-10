#! /usr/bin/env python3
from pathlib import Path
import dir
import file
import logging


def check_templates(state: file.State):
    templates: dict[str, file.Template] = {}
    for i in state.templates:
        if i.name in templates:
            raise Exception(f"Duplicate definition of template {i.name} at {i.path} and {templates[i.name].path}.")
        else:
            templates[i.name] = i


logging.basicConfig(level=logging.INFO)

src = Path("site")
dest = Path("build")

state = dir.scan_dir(src)
check_templates(state)
logging.info(f"Finished loading templates ({len(state.templates)} found).")

dir.process_dir(src, dest, state)
logging.info("Finished!")
