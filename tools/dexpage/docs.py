"""The Docs tab: topics from the Pokémon Amethyst feature list (Google Doc).

`python -m tools.dexpage.docs <feature-list.docx>` writes docs.json and doc_images/ from a File → Download → .docx
export. Heading 1 groups topics; each Heading 2 is a topic. Topics the other tabs already cover are skipped.
The importer needs python-docx; building the page does not."""

import html
import json
import sys
from pathlib import Path

DOCS_JSON = Path(__file__).with_name("docs.json")
DOC_IMAGES = Path(__file__).with_name("doc_images")

SKIP_GROUPS = {"Locations", "Dungeon Maps"}  # the page itself is the locations reference; maps don't export
SKIP_TOPICS = {"TMs and HMs", "Move Tutors", "Trades", "Gifts", "Secondary Shops", "Pokedex and Wild Encounters"}


def load_docs(path: Path = DOCS_JSON) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- rendering (build time)

def _block_html(block: dict, images: dict[str, str]) -> str:
    kind = block["t"]
    if kind == "p":
        return f"<p>{block['html']}</p>"
    if kind == "h":
        return f"<h4>{block['html']}</h4>"
    if kind == "img":
        src = images.get(block["src"])
        return f'<img src="{src}" alt="" loading="lazy">' if src else ""
    if kind == "list":
        out, depth = [], -1
        for level, item in block["items"]:
            while depth < level:
                out.append("<ul>")
                depth += 1
            while depth > level:
                out.append("</ul>")
                depth -= 1
            out.append(f"<li>{item}</li>")
        out.append("</ul>" * (depth + 1))
        return "".join(out)
    if kind == "table":
        rows = block["rows"]
        head = "".join(f"<th>{c}</th>" for c in rows[0])
        body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows[1:])
        return f'<div class="doctable"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'
    raise ValueError(f"unknown doc block {kind!r}")


def render_topic(topic: dict, images: dict[str, str]) -> str:
    return "".join(_block_html(b, images) for b in topic["blocks"])


def topic_text(topic: dict) -> str:
    """Plain text of a topic, for search."""
    import re
    parts = []
    for b in topic["blocks"]:
        if b["t"] in ("p", "h"):
            parts.append(b["html"])
        elif b["t"] == "list":
            parts += [i for _, i in b["items"]]
        elif b["t"] == "table":
            parts += [c for r in b["rows"] for c in r]
    return html.unescape(re.sub(r"<[^>]+>", " ", " ".join(parts)))


# ---------------------------------------------------------------- import (docx → docs.json)

def import_docx(docx_path: Path) -> None:
    import docx  # optional dependency, only for re-importing the feature list
    from docx.oxml.ns import qn

    document = docx.Document(str(docx_path))
    rels = document.part.rels

    def inline(el) -> str:
        """Runs and hyperlinks of a paragraph as escaped HTML with <b>, <i> and <a>."""
        out = []
        for child in el:
            if child.tag == qn("w:hyperlink"):
                rid = child.get(qn("r:id"))
                target = rels[rid].target_ref if rid in rels else None
                text = inline(child)
                out.append(f'<a href="{html.escape(target)}" target="_blank" rel="noopener">{text}</a>' if target and text else text)
            elif child.tag == qn("w:r"):
                text = "".join((t.text or "") if t.tag == qn("w:t") else "\n" if t.tag in (qn("w:br"), qn("w:cr")) else "\t" if t.tag == qn("w:tab") else ""
                               for t in child)
                if not text:
                    continue
                text = html.escape(text).replace("\n", "<br>").replace("\t", " ")
                props = child.find(qn("w:rPr"))
                on = lambda tag: props is not None and props.find(qn(tag)) is not None and props.find(qn(tag)).get(qn("w:val")) not in ("0", "false")
                if on("w:b"):
                    text = f"<b>{text}</b>"
                if on("w:i"):
                    text = f"<i>{text}</i>"
                out.append(text)
        return "".join(out).replace("</b><b>", "").replace("</i><i>", "")

    def images_in(el) -> list[str]:
        names = []
        for blip in el.iter(qn("a:blip")):
            rid = blip.get(qn("r:embed"))
            if rid in rels:
                part = rels[rid].target_part
                name = Path(part.partname).name
                DOC_IMAGES.mkdir(exist_ok=True)
                (DOC_IMAGES / name).write_bytes(part.blob)
                names.append(name)
        return names

    def cell_html(cell_el) -> str:
        lines = [inline(p) for p in cell_el.iter(qn("w:p"))]
        return "<br>".join(line for line in lines if line.strip())

    groups: list[dict] = []
    group = topic = None
    table_index = 0
    for el in document.element.body.iterchildren():
        if el.tag == qn("w:tbl"):
            table = document.tables[table_index]
            table_index += 1
            if topic is None:
                continue
            rows = [[cell_html(c._tc) for c in r.cells] for r in table.rows]
            rows = [r for r in rows if any(c.strip() for c in r)]
            if rows:
                topic["blocks"].append({"t": "table", "rows": rows})
            continue
        if el.tag != qn("w:p"):
            continue
        style_el = el.find(".//" + qn("w:pStyle"))
        style = style_el.get(qn("w:val")) if style_el is not None else ""
        text = "".join(t.text or "" for t in el.iter(qn("w:t"))).strip()
        if style == "Heading1":
            if text:
                group = None if text in SKIP_GROUPS else {"title": text, "topics": []}
                if group:
                    groups.append(group)
                topic = None
            continue
        if group is None:
            continue
        if style == "Heading2":
            if not text:
                continue  # an empty heading: keep adding to the current topic
            topic = None if text in SKIP_TOPICS else {"title": text, "blocks": []}
            if topic:
                group["topics"].append(topic)
            continue
        if topic is None:
            continue
        for name in images_in(el):
            topic["blocks"].append({"t": "img", "src": name})
        if style.startswith("Heading"):
            if text:
                topic["blocks"].append({"t": "h", "html": inline(el)})
            continue
        if not text:
            continue
        numbered = el.find(".//" + qn("w:numPr"))
        if numbered is not None:
            level_el = numbered.find(qn("w:ilvl"))
            level = int(level_el.get(qn("w:val"))) if level_el is not None else 0
            last = topic["blocks"][-1] if topic["blocks"] else None
            if not last or last["t"] != "list":
                last = {"t": "list", "items": []}
                topic["blocks"].append(last)
            last["items"].append([level, inline(el)])
        else:
            topic["blocks"].append({"t": "p", "html": inline(el)})

    groups = [g for g in groups if g["topics"]]
    for g in groups:
        g["topics"] = [t for t in g["topics"] if t["blocks"]]
    DOCS_JSON.write_text(json.dumps(groups, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Wrote {sum(len(g['topics']) for g in groups)} topics in {len(groups)} groups")


if __name__ == "__main__":
    import_docx(Path(sys.argv[1]))
