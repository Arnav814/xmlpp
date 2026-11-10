#! /usr/bin/env python3
from pathlib import Path
import dir
import file
import logging
import argparse


def check_templates(state: file.State):
    templates: dict[str, file.Template] = {}
    for i in state.templates:
        if i.name in templates:
            raise Exception(f"Duplicate definition of template {i.name} at {i.path} and {templates[i.name].path}.")
        else:
            templates[i.name] = i


parser = argparse.ArgumentParser(
        prog="xmlpp",
        description="A simple XML preprocessor")
parser.add_argument("--loglevel", default="info")
parser.add_argument("--src", default="site")
parser.add_argument("--dest", default="build")
args = parser.parse_args()

logging.basicConfig(level=logging.getLevelNamesMapping()[args.loglevel.upper()])

src = Path(args.src)
dest = Path(args.dest)

state = dir.scan_dir(src)
check_templates(state)
logging.info(f"Finished loading templates ({len(state.templates)} found).")

dir.process_dir(src, dest, state)
logging.info("Finished!")
