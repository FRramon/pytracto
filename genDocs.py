"""Program to generate `Docs` using `pdoc3` and crate a central `index.html`"""

import inspect
import os
from pathlib import Path

from pdoc import _render_template, import_module


def generate_docs_and_central_index(modules_to_process: list[str]) -> None:
    """Method to generate `docs` folder with central `index.html`

    Args:
        modules_to_process (list[str]): List of modules to process
    """

    modules = [import_module(module, reload=True) for module in modules_to_process]

    # Generate the docs for each module under docs folder
    command = f'pdoc --html --skip-errors --force --output-dir docs {" ".join(modules_to_process)}'
    os.system(command=command)

    # Create a single base `index.html`
    with open(Path("docs", "index.html"), "w", encoding="utf-8") as index:
        index.write(_render_template("/html.mako", modules=sorted((module.__name__, inspect.getdoc(module)) for module in modules)))


if __name__ == "__main__":
    # Update this as per your source
    module_list = ["tractography", "matrixescreation"]
    generate_docs_and_central_index(module_list)
