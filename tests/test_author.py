"""Lattice authoring with a fake LLM callable."""

import pytest

from traitseed import AuthoringError, author_lattice


def fake_llm_factory(n: int, fail_first: int = 0):
    """Returns valid n-item lists after fail_first garbage responses."""
    calls = {"count": 0}

    def llm(prompt: str) -> str:
        calls["count"] += 1
        if calls["count"] <= fail_first:
            return "too\nfew\nitems"
        return "\n".join(f"- item {calls['count']}-{i}" for i in range(n + 2))

    return llm, calls


def test_author_produces_valid_lattice():
    llm, _ = fake_llm_factory(10)
    lat = author_lattice("test domain", llm, name="t", items_per_position=10)
    assert lat.name == "t"
    assert [p.name for p in lat.positions] == ["worldview", "concern", "blind_spot"]
    for p in lat.positions:
        assert len(p.items) == 10
        assert len(set(p.items)) == 10
    assert "test domain" in lat.provenance


def test_author_strips_bullets_and_dedupes():
    def llm(prompt: str) -> str:
        return "\n".join(["1. alpha", "- beta", "* gamma", "beta", "  delta  ", "epsilon"])

    lat = author_lattice("d", llm, name="t", items_per_position=5)
    assert lat.positions[0].items == ("alpha", "beta", "gamma", "delta", "epsilon")


def test_author_retries_then_succeeds():
    llm, calls = fake_llm_factory(5, fail_first=2)
    lat = author_lattice("d", llm, name="t", items_per_position=5)
    assert len(lat.positions[0].items) == 5
    assert calls["count"] >= 3


def test_author_fails_after_max_attempts():
    def llm(prompt: str) -> str:
        return "never\nenough"

    with pytest.raises(AuthoringError, match="worldview"):
        author_lattice("d", llm, name="t", items_per_position=5, max_attempts=2)


def test_drawn_seed_from_authored_lattice():
    import random

    llm, _ = fake_llm_factory(8)
    lat = author_lattice("d", llm, name="authored", items_per_position=8)
    seed = lat.draw(rng=random.Random(1))
    assert seed.lattice == "authored"
    assert len(seed.items) == 3
