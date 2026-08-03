# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License").
# See the LICENSE file in the project root for the full license text.

"""Unit tests for the domain rules (no network, no model calls)."""

from app.models import Claim, ClaimKind, Disposition, RevisionEntry, Scene, Verdict
from app.services import parallel_client
from app.services.ledger import InMemoryLedger


def _claim(**kw):
    base = {"id": "c1", "kind": ClaimKind.FACTUAL, "text": "a claim"}
    base.update(kw)
    return Claim(**base)


def test_contradicted_claim_needs_attention_until_decided():
    c = _claim(verdict=Verdict.CONTRADICTED)
    assert c.needs_attention
    c.disposition = Disposition.KEEP_DELIBERATE
    assert not c.needs_attention, "a decided claim must stop demanding attention"


def test_verified_claim_never_needs_attention():
    assert not _claim(verdict=Verdict.VERIFIED).needs_attention


def test_keep_deliberate_clears_the_flag_without_changing_the_scene():
    """Artistic licence: the scene text is untouched, but it is on the record."""
    scene = Scene(id="s1", intent="x", text="original text",
                  claims=[_claim(verdict=Verdict.CONTRADICTED)])
    assert scene.open_flags
    scene.claims[0].disposition = Disposition.KEEP_DELIBERATE
    scene.claims[0].rationale = "stylised on purpose"
    assert not scene.open_flags
    assert scene.text == "original text"
    assert scene.is_signed_off


def test_scene_with_no_claims_is_not_signed_off():
    """Nothing checked is not the same as everything cleared."""
    assert not Scene(id="s1", intent="x", text="t").is_signed_off


def test_ledger_revisions_are_scoped_and_append_only():
    led = InMemoryLedger()
    led.append_revision(RevisionEntry(revision=1, scene_id="a", what_changed="x", why="y"))
    led.append_revision(RevisionEntry(revision=2, scene_id="b", what_changed="x", why="y"))
    led.append_revision(RevisionEntry(revision=2, scene_id="a", what_changed="z", why="w"))
    a = led.revisions("a")
    assert [r.revision for r in a] == [1, 2]
    assert len(led.revisions("b")) == 1


def test_offline_search_returns_fixture_and_empty_for_unknown():
    hits = parallel_client._offline("was the motorola handheld available", 5)
    assert hits and "1969" in hits[0].snippet
    assert parallel_client._offline("something nobody canned", 5) == []


def test_parse_tolerates_field_name_drift():
    parsed = parallel_client._parse(
        {"search_results": [{"url": "http://x", "excerpts": ["hello"]}]}, 5)
    assert parsed[0].url == "http://x" and parsed[0].snippet == "hello"
