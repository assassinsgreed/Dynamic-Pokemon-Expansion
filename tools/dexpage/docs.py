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


# ---------------------------------------------------------------- cleanup (build time)
# The page describes the latest release only, so the doc's version history is edited out at build time
# (docs.json keeps the doc's own words).

V = r"v\d+(?:\.\d+)+"
_VERSION_RULES = [
    # "Sand Spit (v1.3) or Aeriliate (v1.4+)" → the newer one
    (rf"[^,;:<>()]*?\s*\({V}\)\s+or\s+([^()<>]+?)\s*\({V}\+?\)", r"\1"),
    # "Land in v1.3.<br>Surf or good/super rod in v1.4." → the newer line
    (rf"[^<>]*?\s+in\s+{V}\.?<br>([^<>]*?)\s+in\s+{V}\.?", r"\1"),
    # whole sentences that only describe history (the capitalised note only, not "are introduced in")
    (rf"(?-i:Introduced|Removed from pool) in {V}\.?", ""),
    (rf"Note: this is fully supported as of {V}\.\s*", ""),
    (rf"Prior to {V},[^.<]*\.?", ""),
    (rf"The layout described below references {V}’s layout;[^.<]*\.\s*", ""),
    (rf"\*+\s*In v1\.1\.5,[^<]*", ""),
    # "In v1.3’s Divergent mode" → "In Divergent mode"
    (rf"\bIn\s+{V}’s\s+", "In "),
    # lead-ins: "In v1.3, …", "Starting in v1.4 …", "As of v1.4.3 …"
    (rf"\b(?:Starting in|In|As of|Since)\s+{V},?\s+", ""),
    # tags and asides: "(v1.4+)", "(introduced in v1.4)", "(in v1.4)", ", as of v1.3", "v1.4+ Ditto trade"
    (rf"\s*\((?:(?:introduced|available)\s+)?(?:in\s+)?{V}\+?\)", ""),
    (rf",?\s+as of {V}", ""),
    (rf"\b{V}\+\s+", ""),
    (rf"\s+(?:in|from) {V}\b", ""),
]


def clean_versions(text: str) -> str:
    import re
    for pattern, repl in _VERSION_RULES:
        text = re.sub(pattern, repl, text, flags=re.I)
    # A removed lead-in leaves a lower-case sentence start
    text = re.sub(r"(^|<br>|[.!?]\s+)([a-z])", lambda m: m.group(1) + m.group(2).upper(), text)
    text = re.sub(r"\(\s*\)|<(b|i)>\s*</\1>", "", text)  # what an emptied aside leaves behind
    text = re.sub(r"\s+([,.])", r"\1", text)
    text = re.sub(r",\s*,", ",", text)
    text = re.sub(r"(<br>\s*){2,}", "<br>", text)
    return re.sub(r"^(\s*<br>)+|(<br>\s*)+$", "", text).strip()


TYPES = ["Normal", "Fire", "Water", "Grass", "Electric", "Ice", "Fighting", "Poison", "Ground", "Flying", "Psychic",
         "Bug", "Rock", "Ghost", "Dragon", "Dark", "Steel", "Fairy"]
_T = "|".join(TYPES)


def _chip(name: str) -> str:
    t = name.capitalize()
    return f'<span class="type t-{t.upper()}">{t}</span>'


def type_chips(text: str, whole_cell: bool = False) -> str:
    """Type names as the Pokédex's type chips: a cell that is just types ("Water/Steel"), or "<type> type" in text.
    Other uses (Fire Stone, Rock Smash, Psychic Terrain) stay plain."""
    import re
    if whole_cell:
        inner = re.sub(r"^\s*<(b|i)>(.*)</\1>\s*$", r"\2", text)  # a bold "<b>Grass</b>" cell is still just a type
        if re.fullmatch(rf"\s*(?:{_T})(?:\s*/\s*(?:<br>)?\s*(?:{_T}))*\s*", inner, flags=re.I):
            return re.sub(r"\s*/\s*(?:<br>)?\s*", "/", re.sub(rf"\b({_T})\b", lambda m: _chip(m.group(1)), inner.strip(), flags=re.I))
    # "flying or water type", "Any fire type", "Dragon-type"
    return re.sub(rf"\b({_T})(\s+or\s+)({_T})(?=[\s-]types?\b)|\b({_T})(?=[\s-]types?\b)",
                  lambda m: (_chip(m.group(1)) + m.group(2) + _chip(m.group(3))) if m.group(1) else _chip(m.group(4)),
                  text, flags=re.I)


def ability_link(cell: str, ability_names: set[str]) -> str:
    """A table cell that is exactly an ability name ("Triage") links to the Abilities tab."""
    import re
    plain = html.unescape(re.sub(r"<[^>]+>", "", cell)).strip()
    if plain in ability_names:
        return f'<button class="mvname" data-ability="{html.escape(plain)}">{cell}</button>'
    return cell


def _cleaned(topic: dict, ability_names: set[str] = frozenset()) -> list[dict]:
    blocks = []
    for b in topic["blocks"]:
        if b["t"] in ("p", "h"):
            text = type_chips(clean_versions(b["html"]))
            if text:
                blocks.append({**b, "html": text})
        elif b["t"] == "list":
            items = [[lvl, type_chips(clean_versions(i))] for lvl, i in b["items"]]
            items = [i for i in items if i[1]]
            if items:
                blocks.append({**b, "items": items})
        elif b["t"] == "table":
            rows = [r for r in b["rows"] if not any("removed from pool" in c.lower() for c in r)]  # no longer in the game
            rows = [[ability_link(type_chips(clean_versions(c), whole_cell=True), ability_names) for c in r] for r in rows]
            if len(rows) > 1:
                blocks.append({**b, "rows": rows})
        else:
            blocks.append(b)
    return blocks


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
        import re
        rows = block["rows"]
        # Right-align columns whose filled cells are all numbers ("80", "1,000", "20%", "5-10") so digits line up
        number = re.compile(r"[$¥]?\d[\d,.]*\s*(?:%|x|×)?(?:\s*[-–]\s*\d[\d,.]*\s*%?)?")
        width = max(len(r) for r in rows)
        numeric = [bool(cells) and all(number.fullmatch(c) for c in cells)
                   for cells in ([re.sub(r"<[^>]+>", "", r[i]).strip() for r in rows[1:] if i < len(r) and re.sub(r"<[^>]+>", "", r[i]).strip()]
                                 for i in range(width))]
        cls = lambda i: ' class="n"' if i < width and numeric[i] else ""
        head = "".join(f"<th{cls(i)}>{c}</th>" for i, c in enumerate(rows[0]))
        body = "".join("<tr>" + "".join(f"<td{cls(i)}>{c}</td>" for i, c in enumerate(r)) + "</tr>" for r in rows[1:])
        return f'<div class="doctable"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'
    raise ValueError(f"unknown doc block {kind!r}")


def render_topic(topic: dict, images: dict[str, str], ability_names: set[str] = frozenset()) -> str:
    return "".join(_block_html(b, images) for b in _cleaned(topic, ability_names))


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
