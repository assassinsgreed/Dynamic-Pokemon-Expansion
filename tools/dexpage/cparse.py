"""Just enough C-source parsing to read the repo's data tables."""

import re
from pathlib import Path

DEFINE_RE = re.compile(r"^\s*#\s*define\s+(\w+)(?:\s+(.*?))?\s*(?://.*)?$")


class UnresolvedConditional(Exception):
    def __init__(self, line_no: int, expr: str):
        super().__init__(f"line {line_no}: cannot evaluate #if {expr!r}")
        self.line_no = line_no
        self.expr = expr


def read(path: Path) -> str:
    data = path.read_bytes()
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("cp1252")  # some hand-edited files are saved as Windows-1252


def collect_defines(*files: Path) -> dict[str, str]:
    """Every uncommented #define in the given files, in order (later wins)."""
    defines: dict[str, str] = {}
    for f in files:
        text = strip_comments(read(f))
        for line in text.splitlines():
            m = DEFINE_RE.match(line)
            if m and "(" not in line.split(m.group(1), 1)[1][:1]:
                defines[m.group(1)] = (m.group(2) or "").strip()
    return defines


def strip_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.S)
    # keep // inside string literals intact
    return re.sub(r'("(?:\\.|[^"\\])*")|//[^\n]*', lambda m: m.group(1) or "", text)


def _int_value(value: str, defines: dict[str, str], depth: int = 0) -> int | None:
    value = value.strip().strip("()").strip()
    if re.fullmatch(r"0[xX][0-9a-fA-F]+|\d+", value):
        return int(value, 0)
    if depth < 8 and value in defines:
        return _int_value(defines[value], defines, depth + 1)
    return None


def _eval_if(expr: str, defines: dict[str, str], line_no: int) -> bool:
    e = re.sub(r"defined\s*\(\s*(\w+)\s*\)|defined\s+(\w+)",
               lambda m: "1" if (m.group(1) or m.group(2)) in defines else "0", expr)

    def ident(m):
        v = _int_value(m.group(0), defines)
        if v is None:
            raise UnresolvedConditional(line_no, expr)
        return str(v)

    e = re.sub(r"\b[A-Za-z_]\w*\b", ident, e)
    if not re.fullmatch(r"[\d\s()!&|<>=xXa-fA-F]*", e):
        raise UnresolvedConditional(line_no, expr)
    e = e.replace("&&", " and ").replace("||", " or ")
    e = re.sub(r"!(?!=)", " not ", e)
    try:
        return bool(eval(e, {"__builtins__": {}}))
    except Exception:
        raise UnresolvedConditional(line_no, expr) from None


def resolve_conditionals(text: str, defines: dict[str, str]) -> str:
    out: list[str] = []
    # stack of (parent_active, this_branch_active, any_branch_taken)
    stack: list[tuple[bool, bool, bool]] = []
    active = True
    for no, line in enumerate(text.splitlines(), 1):
        m = re.match(r"\s*#\s*(ifdef|ifndef|if|elif|else|endif)\b(.*)", line)
        if not m:
            out.append(line if active else "")
            continue
        kind, rest = m.group(1), strip_comments(m.group(2)).strip()
        if kind in ("ifdef", "ifndef", "if"):
            if not active:
                cond = False
            elif kind == "ifdef":
                cond = rest in defines
            elif kind == "ifndef":
                cond = rest not in defines
            else:
                cond = _eval_if(rest, defines, no)
            stack.append((active, cond, cond))
            active = active and cond
        elif kind == "elif":
            parent, _, taken = stack[-1]
            cond = parent and not taken and _eval_if(rest, defines, no)
            stack[-1] = (parent, cond, taken or cond)
            active = parent and cond
        elif kind == "else":
            parent, _, taken = stack[-1]
            stack[-1] = (parent, not taken, True)
            active = parent and not taken
        else:
            parent, _, _ = stack.pop()
            active = parent
        out.append("")
    return "\n".join(out)


def match_brace(text: str, open_idx: int) -> int:
    """Index of the bracket closing the one at open_idx."""
    pairs = {"{": "}", "(": ")", "[": "]"}
    opener, closer = text[open_idx], pairs[text[open_idx]]
    depth = 0
    i = open_idx
    while i < len(text):
        c = text[i]
        if c == '"':
            i = text.index('"', i + 1)
        elif c == opener:
            depth += 1
        elif c == closer:
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise ValueError("unbalanced bracket")


def array_body(text: str, array_name: str) -> str:
    m = re.search(rf"\b{re.escape(array_name)}\s*(?:\[[^\]]*\]\s*)+=\s*{{", text)
    if not m:
        raise KeyError(array_name)
    start = m.end() - 1
    return text[start + 1:match_brace(text, start)]


def split_top_level(body: str, sep: str = ",") -> list[str]:
    parts, depth, cur = [], 0, []
    for c in body:
        if c in "{([":
            depth += 1
        elif c in "})]":
            depth -= 1
        if c == sep and depth == 0:
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(c)
    parts.append("".join(cur))
    return [p.strip() for p in parts if p.strip()]


def parse_designated_array(text: str, array_name: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in split_top_level(array_body(text, array_name)):
        m = re.match(r"\[\s*(\w+)\s*\]\s*=\s*(.*)", item, flags=re.S)
        if m:
            value = m.group(2).strip()
            if value.startswith("{") and value.endswith("}"):
                value = value[1:-1]
            result[m.group(1)] = value.strip()
    return result


def parse_struct_fields(body: str) -> dict[str, str]:
    fields = {}
    for item in split_top_level(body):
        m = re.match(r"\.(\w+)\s*=\s*(.*)", item, flags=re.S)
        if m:
            fields[m.group(1)] = " ".join(m.group(2).split())
    return fields


def parse_string_table(path: Path) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    label = None
    for line in read(path).splitlines():
        if line.startswith("#org"):
            label = line.split("@", 1)[1].strip()
            if not label.startswith("NAME_"):
                label = None
            continue
        if label and line.strip():
            rows.append((label, line.strip()))
            label = None
    return rows


def parse_int_defines(path: Path, prefix: str) -> dict[str, int]:
    values = {}
    for m in re.finditer(rf"^\s*#\s*define\s+({re.escape(prefix)}\w+)\s+(0[xX][0-9a-fA-F]+|\d+)\b",
                         read(path), flags=re.M):
        values[m.group(1)] = int(m.group(2), 0)
    return values
