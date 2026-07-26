"""
build_notebook.py
====================
Converts a jupytext "percent format" .py script into a genuine, EXECUTED
.ipynb file -- without requiring the `nbformat` or `jupyter` packages
(unavailable in this offline sandbox).

Cell markers in the source .py:
    # %% [markdown]
    # any markdown text, one '#' prefixed line per markdown line
    # %%
    python_code_here()

Each code cell is executed in a persistent namespace; stdout and any
matplotlib figures created during that cell are captured as real cell
outputs, exactly like a normal Jupyter run.
"""
import sys
import io
import base64
import json
import contextlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def parse_cells(py_path):
    with open(py_path) as f:
        text = f.read()
    raw_cells = text.split("# %%")[1:]  # first split chunk is empty/header
    cells = []
    for raw in raw_cells:
        lines = raw.split("\n")
        first = lines[0].strip()
        if first == "[markdown]":
            body = "\n".join(lines[1:])
            md_lines = []
            for ln in body.split("\n"):
                if ln.startswith("# "):
                    md_lines.append(ln[2:])
                elif ln.strip() == "#":
                    md_lines.append("")
                else:
                    md_lines.append(ln)
            cells.append(("markdown", "\n".join(md_lines).strip("\n")))
        else:
            body = "\n".join(lines[1:]) if first == "" else "\n".join(lines)
            cells.append(("code", body.strip("\n")))
    return cells


def run_notebook(py_path, ipynb_path):
    cells_src = parse_cells(py_path)
    namespace = {}
    nb_cells = []
    exec_count = 0

    for cell_type, source in cells_src:
        if not source.strip():
            continue
        if cell_type == "markdown":
            nb_cells.append({
                "cell_type": "markdown",
                "metadata": {},
                "source": source.splitlines(keepends=True),
            })
            continue

        exec_count += 1
        outputs = []
        buf = io.StringIO()
        plt.close("all")
        try:
            with contextlib.redirect_stdout(buf):
                exec(compile(source, py_path, "exec"), namespace)
        except Exception as e:
            outputs.append({
                "output_type": "error",
                "ename": type(e).__name__,
                "evalue": str(e),
                "traceback": [f"{type(e).__name__}: {e}"],
            })

        stdout_text = buf.getvalue()
        if stdout_text:
            outputs.append({
                "output_type": "stream",
                "name": "stdout",
                "text": stdout_text.splitlines(keepends=True),
            })

        # capture any open matplotlib figures as PNG outputs
        fignums = plt.get_fignums()
        for fn in fignums:
            fig = plt.figure(fn)
            imgbuf = io.BytesIO()
            fig.savefig(imgbuf, format="png", bbox_inches="tight", dpi=110)
            imgbuf.seek(0)
            b64 = base64.b64encode(imgbuf.read()).decode("ascii")
            outputs.append({
                "output_type": "execute_result",
                "execution_count": exec_count,
                "data": {"image/png": b64, "text/plain": ["<Figure>"]},
                "metadata": {},
            })
        plt.close("all")

        nb_cells.append({
            "cell_type": "code",
            "execution_count": exec_count,
            "metadata": {},
            "outputs": outputs,
            "source": source.splitlines(keepends=True),
        })

    notebook = {
        "cells": nb_cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": sys.version.split()[0]},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    with open(ipynb_path, "w") as f:
        json.dump(notebook, f, indent=1)
    print(f"Wrote executed notebook: {ipynb_path}  ({len(nb_cells)} cells, {exec_count} code cells run)")


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    run_notebook(src, dst)
