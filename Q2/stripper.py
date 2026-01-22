# stripper.py
# Gebruik:
# python stripper.py test.ipynb

import sys
import nbformat as nbf
from pathlib import Path

# Dé folder waar de schone notebooks heen moeten
OUTPUT_DIR = Path("./studentenversie")   # mag ook absoluut pad zijn

MARK_START = "### begin-solution"
MARK_END   = "### end-solution"
PLACEHOLDER = "#your code/answer\n"

def strip_and_replace(src: str) -> str:
    out_lines = []
    in_block = False

    for line in src.splitlines(keepends=True):
        if not in_block and MARK_START in line:
            in_block = True
            out_lines.append(PLACEHOLDER)
            continue

        if in_block and MARK_END in line:
            in_block = False
            continue

        if not in_block:
            out_lines.append(line)

    return "".join(out_lines)

def process_notebook(inp_path: Path, output_dir: Path) -> Path:
    nb = nbf.read(str(inp_path), as_version=4)

    for cell in nb.cells:
        if cell.cell_type in {"code", "markdown", "raw"}:
            if isinstance(cell.get("source", ""), str):
                cell["source"] = strip_and_replace(cell["source"])

    # Output-pad: zelfde naam, andere map
    output_file = output_dir / inp_path.name

    # Zorg dat de folder bestaat
    output_file.parent.mkdir(parents=True, exist_ok=True)

    nbf.write(nb, str(output_file))
    return output_file

def main():
    if len(sys.argv) != 2:
        print("Gebruik: python stripper.py input.ipynb")
        sys.exit(1)

    inp = Path(sys.argv[1]).expanduser().resolve()
    out_path = process_notebook(inp, OUTPUT_DIR)

    print(f"Geschreven naar: {out_path}")

if __name__ == "__main__":
    main()
