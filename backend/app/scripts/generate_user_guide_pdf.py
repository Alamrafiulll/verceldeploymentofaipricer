from __future__ import annotations

from pathlib import Path
import textwrap


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "docs" / "demo" / "Chin_Hin_AI_Pricing_Strategist_User_Guide.md"
OUTPUT = ROOT / "docs" / "demo" / "Chin_Hin_AI_Pricing_Strategist_User_Guide.pdf"

PAGE_WIDTH = 612
PAGE_HEIGHT = 792
LEFT_MARGIN = 50
TOP_MARGIN = 760
FONT_SIZE = 11
LINE_HEIGHT = 15
MAX_CHARS = 92
LINES_PER_PAGE = 46


def escape_pdf_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def normalize_markdown(text: str) -> list[str]:
    lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line:
            lines.append("")
            continue
        if line.startswith("```"):
            continue
        if line.startswith("### "):
            line = line[4:].upper()
        elif line.startswith("## "):
            line = line[3:].upper()
        elif line.startswith("# "):
            line = line[2:].upper()
        elif line.startswith("- "):
            line = "• " + line[2:]
        elif line[:2].isdigit() and line[1:3] == ". ":
            pass
        elif line[:3].isdigit() and line[2:4] == ". ":
            pass
        line = line.replace("`", "")
        wrapped = textwrap.wrap(line, width=MAX_CHARS) or [""]
        lines.extend(wrapped)
    return lines


def paginate(lines: list[str]) -> list[list[str]]:
    pages: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        current.append(line)
        if len(current) >= LINES_PER_PAGE:
            pages.append(current)
            current = []
    if current:
        pages.append(current)
    return pages or [[]]


def build_content_stream(page_lines: list[str]) -> bytes:
    commands = ["BT", f"/F1 {FONT_SIZE} Tf", f"{LEFT_MARGIN} {TOP_MARGIN} Td"]
    first = True
    for line in page_lines:
        escaped = escape_pdf_text(line)
        if first:
            commands.append(f"({escaped}) Tj")
            first = False
        else:
            commands.append(f"0 -{LINE_HEIGHT} Td")
            commands.append(f"({escaped}) Tj")
    commands.append("ET")
    return "\n".join(commands).encode("latin-1", errors="replace")


def add_object(objects: list[bytes], body: bytes) -> int:
    objects.append(body)
    return len(objects)


def generate_pdf(source_path: Path, output_path: Path) -> None:
    source_text = source_path.read_text(encoding="utf-8")
    lines = normalize_markdown(source_text)
    pages = paginate(lines)

    objects: list[bytes] = []

    catalog_id = add_object(objects, b"<< /Type /Catalog /Pages 2 0 R >>")
    _ = catalog_id
    pages_placeholder_id = add_object(objects, b"<< /Type /Pages /Count 0 /Kids [] >>")
    font_id = add_object(objects, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    page_ids: list[int] = []
    for page_lines in pages:
        content = build_content_stream(page_lines)
        content_id = add_object(
            objects,
            f"<< /Length {len(content)} >>\nstream\n".encode("latin-1")
            + content
            + b"\nendstream",
        )
        page_id = add_object(
            objects,
            (
                f"<< /Type /Page /Parent {pages_placeholder_id} 0 R "
                f"/MediaBox [0 0 {PAGE_WIDTH} {PAGE_HEIGHT}] "
                f"/Resources << /Font << /F1 {font_id} 0 R >> >> "
                f"/Contents {content_id} 0 R >>"
            ).encode("latin-1"),
        )
        page_ids.append(page_id)

    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    objects[pages_placeholder_id - 1] = (
        f"<< /Type /Pages /Count {len(page_ids)} /Kids [{kids}] >>"
    ).encode("latin-1")

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, body in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n".encode("latin-1"))
        pdf.extend(body)
        pdf.extend(b"\nendobj\n")

    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("latin-1"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))

    pdf.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("latin-1")
    )

    output_path.write_bytes(pdf)


if __name__ == "__main__":
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    generate_pdf(SOURCE, OUTPUT)
    print(f"Generated PDF: {OUTPUT}")
