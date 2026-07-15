#!/usr/bin/env python3
"""Turn an image (or a matplotlib figure) into a base64 `data:` URI.

Why this exists: the article is a single portable .html file, so every image —
a matplotlib chart, a fetched paper figure, an AI-generated illustration, a
rendered SVG — has to end up inlined as `data:image/...;base64,...`. This is the
one pipeline all four image sources funnel through. Bundling it means each run
doesn't reinvent the base64 dance.

Usage
-----
As a CLI (embed an existing image file):
    python fig_to_datauri.py path/to/figure.png
    python fig_to_datauri.py fig.png --html --alt "架構圖" --caption "圖 1：Transformer 架構" --src "Vaswani et al. 2017"
    # writes the <figure>…</figure> (or bare data URI) to stdout

As a library (from a plotting script):
    from fig_to_datauri import fig_to_datauri, figure_html
    uri = fig_to_datauri(plt.gcf())          # matplotlib Figure -> data URI
    print(figure_html(uri, caption="圖 2：loss 曲線"))

Notes
-----
- PNG is the safe default. SVG you author by hand goes straight into the HTML as
  an <svg> element — no need to base64 it, and it stays crisp and themeable.
- Downscale large photos before embedding; base64 inflates size ~33%.
"""
import argparse
import base64
import html
import io
import mimetypes
import sys
from pathlib import Path


def _b64(data: bytes, mime: str) -> str:
    return f"data:{mime};base64," + base64.b64encode(data).decode("ascii")


def file_to_datauri(path: str) -> str:
    """Read an image file and return a data URI."""
    p = Path(path)
    data = p.read_bytes()
    mime = mimetypes.guess_type(p.name)[0] or "image/png"
    return _b64(data, mime)


def fig_to_datauri(fig, dpi: int = 150, fmt: str = "png") -> str:
    """Serialize a matplotlib Figure to a data URI without touching disk."""
    buf = io.BytesIO()
    fig.savefig(buf, format=fmt, dpi=dpi, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    buf.seek(0)
    mime = "image/svg+xml" if fmt == "svg" else f"image/{fmt}"
    return _b64(buf.read(), mime)


def figure_html(uri: str, alt: str = "", caption: str = "",
                src: str = "", bordered: bool = False) -> str:
    """Wrap a data URI in the template's <figure> markup."""
    cls = ' class="bordered"' if bordered else ""
    cap = ""
    if caption or src:
        parts = []
        if caption:
            parts.append(html.escape(caption))
        if src:
            parts.append(f'<span class="src">來源：{html.escape(src)}</span>')
        cap = "\n  <figcaption>" + " ".join(parts) + "</figcaption>"
    return (f'<figure{cls}>\n'
            f'  <img src="{uri}" alt="{html.escape(alt)}">{cap}\n'
            f'</figure>')


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("image", help="path to an image file (png/jpg/gif/webp/svg)")
    ap.add_argument("--html", action="store_true",
                    help="emit a full <figure> block instead of a bare data URI")
    ap.add_argument("--alt", default="", help="alt text")
    ap.add_argument("--caption", default="", help="figcaption text")
    ap.add_argument("--src", default="", help="source attribution (shown as 來源：…)")
    ap.add_argument("--bordered", action="store_true",
                    help="white padding + border (good for figures on transparent bg)")
    args = ap.parse_args()

    uri = file_to_datauri(args.image)
    if args.html:
        sys.stdout.write(figure_html(uri, args.alt, args.caption, args.src, args.bordered))
    else:
        sys.stdout.write(uri)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
