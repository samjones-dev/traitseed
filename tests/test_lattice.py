"""Lattice draws, serialisation, and bundled data integrity."""

import json
import random

import pytest

from traitseed import Lattice, Position, list_bundled

BUNDLED = ("claude-traits", "gpt41-traits", "human-taxonomies")


def small_lattice() -> Lattice:
    return Lattice(
        name="test",
        positions=(
            Position("worldview", "Worldview/disposition", ("a", "b", "c"), "taken to excess"),
            Position("concern", "Primary concern/focus", ("x", "y", "z"), None),
        ),
    )


def test_seeded_draws_are_reproducible():
    lat = small_lattice()
    assert lat.draw(rng=random.Random(7)) == lat.draw(rng=random.Random(7))


def test_different_seeds_differ():
    lat = Lattice.default()
    assert lat.draw(rng=random.Random(1)) != lat.draw(rng=random.Random(2))


def test_draw_one_item_per_position():
    seed = small_lattice().draw(rng=random.Random(3))
    assert [i.position for i in seed.items] == ["worldview", "concern"]
    assert seed.lattice == "test"


def test_intensity_suffix_applies_only_where_configured():
    lat = small_lattice()
    seeds = [lat.draw(rng=random.Random(i), intensity_probability=1.0) for i in range(5)]
    for seed in seeds:
        worldview, concern = seed.items
        assert worldview.intensified and worldview.text.endswith("(taken to excess)")
        assert not concern.intensified  # no suffix configured


def test_zero_intensity_probability():
    seed = small_lattice().draw(rng=random.Random(1), intensity_probability=0.0)
    assert not any(i.intensified for i in seed.items)


def test_block_format():
    seed = small_lattice().draw(rng=random.Random(1), intensity_probability=0.0)
    lines = seed.block().splitlines()
    assert lines[0].startswith("1. Worldview/disposition: ")
    assert lines[1].startswith("2. Primary concern/focus: ")


def test_seed_provenance_round_trip():
    seed = small_lattice().draw(rng=random.Random(9))
    record = seed.to_dict()
    assert record["lattice"] == "test"
    assert all({"position", "base", "intensified", "text"} <= set(i) for i in record["items"])
    json.dumps(record)  # serialisable


def test_lattice_save_load_round_trip(tmp_path):
    lat = small_lattice()
    lat.save(tmp_path / "lat.json")
    assert Lattice.load(tmp_path / "lat.json") == lat


def test_duplicate_items_rejected():
    with pytest.raises(ValueError, match="duplicate"):
        Position("p", "P", ("a", "a"))


def test_bundled_list_and_integrity():
    assert set(BUNDLED) <= set(list_bundled())
    for name in BUNDLED:
        lat = Lattice.bundled(name)
        assert [p.name for p in lat.positions] == ["worldview", "concern", "blind_spot"]
        assert all(len(p.items) == 78 for p in lat.positions)
        assert lat.provenance


def test_default_is_claude_traits():
    assert Lattice.default().name == "claude-traits"


def test_unknown_bundled_name():
    with pytest.raises(ValueError, match="available"):
        Lattice.bundled("nope")
