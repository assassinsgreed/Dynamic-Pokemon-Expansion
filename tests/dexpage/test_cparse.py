import pytest

from tools.dexpage.cparse import (
    UnresolvedConditional,
    parse_designated_array,
    parse_int_defines,
    parse_string_table,
    parse_struct_fields,
    resolve_conditionals,
)


def test_resolve_ifdef_else():
    src = "#ifdef A\nx\n#else\ny\n#endif\n"
    assert resolve_conditionals(src, {"A": ""}).split() == ["x"]
    assert resolve_conditionals(src, {}).split() == ["y"]


def test_resolve_if_expression():
    src = "#if (N > 64) && defined(B)\nhit\n#endif\n"
    assert "hit" in resolve_conditionals(src, {"N": "96", "B": ""})
    assert "hit" not in resolve_conditionals(src, {"N": "32", "B": ""})


def test_unresolvable_raises():
    with pytest.raises(UnresolvedConditional):
        resolve_conditionals("#if FOO(1)\nx\n#endif\n", {})


def test_designated_array_and_fields():
    src = "const T gX[] = {\n [SPECIES_A] = { .hp = 1, .type1 = TYPE_FIRE, },\n [SPECIES_B] = { .hp = 2 },\n};"
    arr = parse_designated_array(src, "gX")
    assert list(arr) == ["SPECIES_A", "SPECIES_B"]
    assert parse_struct_fields(arr["SPECIES_A"]) == {"hp": "1", "type1": "TYPE_FIRE"}


def test_real_string_table(paths):
    rows = parse_string_table(paths.cfru / "strings/attack_name_table.string")
    assert rows[0] == ("NAME_MOVE_NONE", "-")
    assert ("NAME_CEASELESS_EDGE", "Endless Edge") in rows


def test_real_item_constants(paths):
    assert parse_int_defines(paths.cfru / "include/constants/items.h", "ITEM_")["ITEM_LINK_STONE"] == 0x5B
