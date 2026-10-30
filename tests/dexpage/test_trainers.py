import pytest

from tools.dexpage import trainers as T


@pytest.fixture(scope="module")
def loaded(paths, source_data):
    return T.load_trainers(paths, source_data.stats, source_data.levelup, source_data.moves,
                           lambda a, s: source_data.abilities.get(a, a))


def by_const(loaded, const):
    return next(t for t in loaded[0] if t["const"] == const)


def test_default_moves_are_last_four_without_repeats():
    learnset = [(1, "A"), (1, "B"), (5, "C"), (9, "B"), (12, "D"), (20, "E")]
    assert T.default_moves(learnset, 12) == ["B", "C", "D"]  # last four entries are B C B D; the second B is skipped
    assert T.default_moves(learnset, 4) == ["A", "B"]


def test_best_two_stats_breaks_ties_toward_earlier_stats():
    stats = {"hp": 50, "atk": 100, "def": 100, "spe": 60, "spa": 100, "spd": 50}
    assert T.best_two_stats(stats) == ["atk", "def"]


def test_nature_lowers_the_unused_attacking_stat():
    stats = {"hp": 80, "atk": 120, "def": 80, "spe": 90, "spa": 60, "spd": 80}
    moves = {"MOVE_X": {"split": "physical", "power": 80, "effect": "EFFECT_HIT"}}
    assert T.best_stat_nature(stats, ["MOVE_X"], moves) == "Adamant"


def test_trick_room_lowers_speed():
    stats = {"hp": 80, "atk": 60, "def": 80, "spe": 30, "spa": 120, "spd": 80}
    moves = {"MOVE_PSYCHIC": {"split": "special", "power": 90, "effect": "EFFECT_HIT"},
             "MOVE_TRICKROOM": {"split": "status", "power": 0, "effect": "EFFECT_TRICK_ROOM"}}
    assert T.best_stat_nature(stats, ["MOVE_PSYCHIC", "MOVE_TRICKROOM"], moves) == "Quiet"


def test_missing_hard_entry_falls_back_to_standard(loaded):
    rival1 = by_const(loaded, "TRAINER_RIVAL1")
    assert rival1["teams"]["hard"] == rival1["teams"]["std"]


def test_class_ivs(loaded):
    assert by_const(loaded, "TRAINER_RIVAL1")["iv"] == 25           # not in the table: STANDARD_IV would be 10
    assert by_const(loaded, "TRAINER_ROUTE_1_YOUNGSTER_PETER")["iv"] == 5


def test_variant_notes(loaded):
    assert "Squirtle" in by_const(loaded, "TRAINER_BRUCCIE_VILLAGE_RIVAL_V")["note"]
    assert "Sobble" in by_const(loaded, "TRAINER_BRUCCIE_VILLAGE_RIVAL_S")["note"]
    assert "1 of 4" in by_const(loaded, "TRAINER_LEADER_RAINE_REMATCH_1")["note"]
    assert "3 badges" in by_const(loaded, "TRAINER_HELEO_CITY_GYM_LEADER_RAINE_2")["note"]


def test_important_trainers_get_a_place(loaded):
    assert by_const(loaded, "TRAINER_TORMA_CAVE_CASEY_F")["place"] == "Torma Cave"
    assert all(t["place"] != "Important trainers" for t in loaded[0])


def test_class_names_read_from_rom(paths):
    names = T.class_names(paths)
    assert names[0] == "PKMN Trainer"
    assert "Rival" in names


def test_rom_trainer_table_matches_source(paths):
    # The trainerPic read relies on gTrainers' ROM address; the class byte beside it must match the source table
    import re, struct
    from tools.dexpage.cparse import collect_defines, read
    from tools.dexpage.rom import _rom_bytes
    base = int(re.search(r"^gTrainers:\s+([0-9A-Fa-f]{8})", read(paths.cfru / "offsets.ini"), flags=re.M).group(1), 16) - 0x08000000
    rom = _rom_bytes(paths.rom)
    ids = {k: int(v) for k, v in collect_defines(paths.cfru / "include/constants/opponents.h").items() if (v or "").isdigit()}
    classes = T._class_ids(paths)
    std = T.load_tables(paths)["std"]
    for const, entry in std.items():
        assert rom[base + T.TRAINER_STRUCT_SIZE * ids[const] + 1] == classes[entry["trainerClass"]], const


def test_rival_uses_rival_pic(paths):
    assert T._rom_pics(paths, {"TRAINER_RIVAL1": 1})["TRAINER_RIVAL1"] == 0x6A


def test_pokemon_gender_from_trainer_gender():
    g = lambda pct, female: T._gender({"gender": pct}, female)
    assert g(50.0, True) == "F" and g(50.0, False) == "M"            # low byte 0x0F / 0x88 against ratio 127
    assert g(12.5, True) == "F" and g(87.5, False) == "F"            # 31 > 15; 223 > 136
    assert g(75.0, False) == "F" and g(25.0, False) == "M"           # 191 > 136 (Galarian Corsola); 63 < 136
    assert g(0.0, True) == "M" and g(100.0, False) == "F" and g(None, True) is None


def test_unnamed_ability_follows_trainer_gender():
    s = {"abilities": ["ABILITY_A", "ABILITY_B"], "hidden_ability": "ABILITY_H"}
    assert T._ability(None, s) == "ABILITY_A"                        # male trainer: personality 0x88, low bit 0
    assert T._ability(None, s, female=True) == "ABILITY_B"           # female trainer: 0x0F, low bit 1
    assert T._ability(None, {"abilities": ["ABILITY_A"], "hidden_ability": None}, female=True) == "ABILITY_A"
    assert T._ability("Ability_Random_1_2", s) == "ABILITY_A or ABILITY_B"   # rolled in battle
    assert T._ability("Ability_RandomAll", s) == "ABILITY_A or ABILITY_B or ABILITY_H"
    assert T._ability("Ability_Hidden", s) == "ABILITY_H"


def test_class_poke_balls(paths, loaded):
    balls = T.class_balls(paths)
    assert balls["CLASS_RICH_BOY"] == "ITEM_LUXURY_BALL"
    assert all(t["ball"].startswith("ITEM_") for t in loaded[0])


def test_every_trainer_pic_decodes(loaded):
    assert all(img.size == (64, 64) for img in loaded[2].values())


def test_gym_and_trainer_house_places(loaded):
    assert by_const(loaded, "TRAINER_RHODANZI_GYM_ALONSO")["place"] == "Rhodanzi City Gym"
    assert by_const(loaded, "TRAINER_LAPLAZ_TRAINER_HOUSE_COLLECTOR_DIRK")["place"] == "Laplaz Town Trainer House"
    assert by_const(loaded, "TRAINER_BRUCCIE_VILLAGE_GYM_LEADER_ABBY")["place"] == "Bruccie Village Gym"
    assert by_const(loaded, "TRAINER_TSARVOSA_CITY_GYM_TRAINEE_NOAM")["place"] == "Tsarvosa City"


def test_ferrox_library(loaded):
    assert by_const(loaded, "TRAINER_FERROX_LIBRARY_LAURENA")["place"] == "Ferrox Library"
