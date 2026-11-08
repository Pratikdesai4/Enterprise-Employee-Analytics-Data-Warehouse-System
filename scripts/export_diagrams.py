'''\
export_diagrams.py – Export .drawio diagram files to PNG/SVG for documentation.
\
The project stores the source diagrams as Draw.io ``.drawio`` XML files under
``docs/diagrams``.  For a quick visual preview in the README we generate PNG
images that can be rendered by GitHub markdown.  The script attempts to call the
official Draw.io CLI (``drawio``) which is available on most developer machines.
If the CLI is not installed we fall back to creating a tiny placeholder PNG so
that the documentation still builds without error.
\
Usage::
\
    python scripts/export_diagrams.py
\
The script will write the following files next to the source ``.drawio`` files:
\
    docs/diagrams/oltp_er_diagram.png
    docs/diagrams/olap_star_schema.png
\
These images can then be referenced in ``README.md``.
'''
import os
import subprocess
import sys
from pathlib import Path

# Pillow is a lightweight dependency already present via requirements (via pandas)
try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = None  # type: ignore

DIAGRAM_DIR = Path(__file__).resolve().parents[1] / "docs" / "diagrams"
DRAWIO_CLI = "drawio"  # assumed to be on PATH

def _run_drawio(input_path: Path, output_path: Path, fmt: str = "png") -> bool:
    """Run the drawio CLI to export *input_path* to *output_path*.

    Returns ``True`` if the command succeeded, else ``False``.
    """
    try:
        subprocess.check_call([
            DRAWIO_CLI,
            "-x",  # export mode
            "-f", fmt,
            "-o", str(output_path),
            str(input_path),
        ])
        return True
    except Exception as e:
        print(f"[export_diagrams] Draw.io export failed ({e}); using placeholder.")
        return False

def _placeholder_png(output_path: Path, title: str) -> None:
    """Create a minimal placeholder PNG with the diagram *title*.
    This ensures the README can display an image even when the real export is not
    possible.  The image is 800×600 with a light‑gray background and the title
    rendered in the centre.
    """
    if Image is None:
        # If Pillow is not available we write a raw 1×1 pixel PNG binary.
        # This tiny PNG will still render as an image placeholder.
        raw_png = (b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
                   b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
                   b"\x00\x00\x00\x0cIDATx\x9cc``\x00\x00\x00\x02\x00\x01"
                   b"\xe2!\xbc3\x00\x00\x00\x00IEND\xaeB`\x82")
        with open(output_path, "wb") as f:
            f.write(raw_png)
        return
    img = Image.new("RGB", (800, 600), color="#f0f0f0")
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except Exception:
        font = ImageFont.load_default()
    bbox = d.textbbox((0, 0), title, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    d.text(((800 - w) / 2, (600 - h) / 2), title, fill="#333333", font=font)
    img.save(output_path)

def export_diagram(drawio_name: str, title: str) -> None:
    src = DIAGRAM_DIR / f"{drawio_name}.drawio"
    out_png = DIAGRAM_DIR / f"{drawio_name}.png"
    if not src.exists():
        print(f"[export_diagrams] Source {src} not found – skipping.")
        return
    success = _run_drawio(src, out_png)
    if not success:
        _placeholder_png(out_png, title)
    else:
        print(f"[export_diagrams] Exported {src} → {out_png}")

def main() -> None:
    export_diagram("oltp_er_diagram", "OLTP ER Diagram")
    export_diagram("olap_star_schema", "OLAP Star Schema Diagram")

if __name__ == "__main__":
    main()
