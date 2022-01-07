"""Functionality for storing special data in notebook code cells,
which can then be inserted into the document body.
"""
from logging import Logger
from typing import Any, Dict, List

import IPython
from IPython.display import display as ipy_display
from nbformat import NotebookNode

GLUE_PREFIX = "application/papermill.record/"


def glue(name: str, variable, display: bool = True) -> None:
    """Glue a variable into the notebook's cell metadata.

    Parameters
    ----------
    name: string
        A unique name for the variable. You can use this name to refer to the variable
        later on.
    variable: Python object
        A variable in Python for which you'd like to store its display value. This is
        not quite the same as storing the object itself - the stored information is
        what is *displayed* when you print or show the object in a Jupyter Notebook.
    display: bool
        Display the object you are gluing. This is helpful in sanity-checking the
        state of the object at glue-time.
    """
    mimebundle, metadata = IPython.core.formatters.format_display_data(variable)
    mime_prefix = "" if display else GLUE_PREFIX
    metadata["scrapbook"] = dict(name=name, mime_prefix=mime_prefix)
    ipy_display(
        {mime_prefix + k: v for k, v in mimebundle.items()}, raw=True, metadata=metadata
    )


def extract_glue_data(
    notebook: NotebookNode,
    resources: Dict[str, Any],
    source_map: List[int],
    logger: Logger,
) -> None:
    """Extract all the glue data from the notebook, into the resources dictionary."""
    data = resources.setdefault("glue", {})
    for index, cell in enumerate(notebook.cells):
        if cell.cell_type != "code":
            continue
        outputs = []
        for output in cell.get("outputs", []):
            meta = output.get("metadata", {})
            if "scrapbook" not in meta:
                outputs.append(output)
                continue
            key = meta["scrapbook"]["name"]
            mime_prefix = len(meta["scrapbook"].get("mime_prefix", ""))
            if key in data:
                logger.warning(
                    f"glue key {key!r} duplicate",
                    subtype="glue",
                    line=source_map[index],
                )
            output["data"] = {k[mime_prefix:]: v for k, v in output["data"].items()}
            data[key] = output
        cell.outputs = outputs
