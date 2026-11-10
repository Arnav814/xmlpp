import file
from pathlib import Path


# scan one directory recursively
def scan_dir(directory: Path) -> file.State:
    state = file.State([], {})
    for path in directory.iterdir():
        if path.is_file():
            state.dirtree[path.name] = None
            if path.name[0] == '@':  # this file is a template
                try:
                    content = path.read_text()
                    template = file.process_template(content, path)
                    state.templates.append(template)
                except Exception as e:
                    raise Exception(f'Error while processing template "{path}".') from e

        elif path.is_dir():
            substate = scan_dir(path)
            state.templates += substate.templates
            state.dirtree[path.name] = substate.dirtree

        else:
            raise Exception()
    return state


def process_dir(in_dir: Path, out_dir: Path, state: file.State):
    out_dir.mkdir(mode=0o770, parents=True, exist_ok=True)
    if list(out_dir.iterdir()) != []:
        raise Exception(f'Output directory "{out_dir}" is not empty.')

    for path in in_dir.iterdir():
        if path.is_file():
            if path.name[0] != '@':
                try:
                    content = path.read_text()
                    processed = file.process_file(content, state)
                    out_file = out_dir / path.name
                    out_file.write_text(processed, encoding="utf-8")
                except Exception as e:
                    raise Exception(f'Error while processing file "{path}".') from e

        elif path.is_dir():
            process_dir(path, out_dir / path.name, state)

        else:
            raise Exception()

