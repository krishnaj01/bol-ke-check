import pytest
from fastapi.testclient import TestClient

from app import rules_engine as engine
from app.models import CATEGORIES, Segment


def seg(text: str, start: float = 0.0, end: float = 5.0, sid: str = "s1") -> Segment:
    return Segment(id=sid, start_sec=start, end_sec=end, text=text)


def families(text: str, category: str) -> set[str]:
    return {flag.family for flag in engine.scan([seg(text)], category, False, 30.0).flags}


@pytest.mark.parametrize(
    ("devanagari", "roman"),
    [
        ("दिन", "din"),
        ("में", "mein"),
        ("पक्का", "pakka"),
        ("पैसा", "paisa"),
        ("सिर्फ", "sirf"),
        ("सिर्फ़", "sirf"),
        ("आज", "aj"),
        ("करना", "karna"),
        ("सबसे", "sabse"),
        ("ख़त्म", "khatm"),
        ("ज़ीरो", "ziro"),
        ("रिस्क", "risk"),
        ("नंबर", "nambar"),
    ],
)
def test_devanagari_folds_to_roman_spelling(devanagari: str, roman: str) -> None:
    assert engine.fold_token(devanagari) == roman


def test_roman_spelling_variants_fold_together() -> None:
    assert engine.fold_token("Aaj,") == engine.fold_token("आज")
    assert engine.fold_token("Theek") == engine.fold_token("ठीक")
    assert engine.fold_token("jeet") == engine.fold_token("जीत")


@pytest.mark.parametrize(
    ("text", "category", "family"),
    [
        ("7 din mein guaranteed glow milega", "personal_care", "guaranteed_results"),
        ("सात दिन में glow मिलेगा", "personal_care", "guaranteed_results"),
        ("is cream ki गारंटी है", "personal_care", "guaranteed_results"),
        ("100% result milega", "personal_care", "guaranteed_results"),
        ("ye ek sau percent result deta hai", "personal_care", "guaranteed_results"),
        ("यह एक सौ percent result देता है", "personal_care", "guaranteed_results"),
        ("pakka fark dikhega", "personal_care", "guaranteed_results"),
        ("is stock mein paisa double pakka", "finance", "assured_returns"),
        ("पैसा डबल हो जाएगा", "finance", "assured_returns"),
        ("zero risk hai bhai", "finance", "assured_returns"),
        ("ज़ीरो रिस्क है", "finance", "assured_returns"),
        ("guaranteed return milega", "finance", "assured_returns"),
        ("main bata raha hoon ye stock kharido", "finance", "unqualified_advice"),
        ("ye dawai le lo", "health", "unqualified_advice"),
        ("diabetes theek ho jaayega", "health", "disease_cure"),
        ("is app pe paise lagao, jeet pakki", "betting", "betting_promotion"),
        ("India ka number one brand", "general", "superlatives"),
        ("ये सबसे best है", "general", "superlatives"),
        ("sirf aaj ke liye", "general", "fake_urgency"),
        ("सिर्फ आज का offer", "general", "fake_urgency"),
        ("offer khatam hone wala hai", "general", "fake_urgency"),
    ],
)
def test_spec_triggers_are_caught(text: str, category: str, family: str) -> None:
    assert family in families(text, category)


@pytest.mark.parametrize(
    ("text", "category"),
    [
        ("Main ye moisturizer teen hafte se use kar rahi hoon", "personal_care"),
        ("Mujhe skin thodi soft lagi, aapka experience alag ho sakta hai", "personal_care"),
        ("Investment mein risk hota hai, returns guaranteed nahi hain", "general"),
        ("Aaj hum market ke basics samjhenge", "finance"),
        ("Doctor se baat karna zaroori hai", "health"),
    ],
)
def test_clean_lines_are_not_flagged(text: str, category: str) -> None:
    assert families(text, category) == set()


def test_quote_is_exact_substring_of_transcript() -> None:
    text = "Dekho, is serum se 7 din mein GUARANTEED glow, milega!"
    flags = engine.scan([seg(text)], "personal_care", False, 30.0).flags
    assert flags and all(flag.quote in text for flag in flags)


def test_devanagari_quote_is_original_script() -> None:
    text = "दोस्तों ज़ीरो रिस्क है"
    flags = engine.scan([seg(text)], "finance", False, 30.0).flags
    assert flags[0].quote == "ज़ीरो रिस्क"


def test_flag_uses_segment_timestamps() -> None:
    flag = engine.scan([seg("zero risk", 14.1, 17.8)], "finance", False, 30.0).flags[0]
    assert (flag.start_sec, flag.end_sec) == (14.1, 17.8)


def test_common_rules_apply_to_every_category() -> None:
    for category in CATEGORIES:
        assert "fake_urgency" in families("sirf aaj", category)


def test_category_rules_do_not_leak() -> None:
    assert "assured_returns" not in families("zero risk", "food")


def test_disclosure_not_required_adds_no_flag() -> None:
    result = engine.scan([seg("hello doston")], "general", False, 30.0)
    assert result.flags == [] and not result.disclosure.required


def test_missing_disclosure_is_high_and_spans_video() -> None:
    result = engine.scan([seg("hello doston")], "general", True, 30.0)
    assert not result.disclosure.found
    flag = result.flags[0]
    assert (flag.rule_id, flag.severity) == ("DISC-MISSING-01", "high")
    assert (flag.start_sec, flag.end_sec) == (0.0, 30.0)


def test_early_disclosure_passes() -> None:
    result = engine.scan([seg("ye paid partnership hai", 2.0, 5.0)], "general", True, 30.0)
    assert result.flags == []
    assert (result.disclosure.found, result.disclosure.first_at_sec) == (True, 2.0)


def test_late_disclosure_is_medium() -> None:
    result = engine.scan([seg("ye sponsored video hai", 20.0, 25.0)], "general", True, 30.0)
    assert [(f.rule_id, f.severity) for f in result.flags] == [("DISC-LATE-01", "medium")]


def test_devanagari_disclosure_counts() -> None:
    assert engine.scan([seg("यह एक विज्ञापन है")], "general", True, 30.0).disclosure.found


@pytest.mark.parametrize("category", CATEGORIES)
def test_every_rule_cites_a_source_and_partial_ones_stay_unverified(category: str) -> None:
    for rule in engine.rules_for(category):
        assert rule.source and (rule.verified or rule.source.startswith("Partial:"))
        assert rule.family in engine.FAMILIES


def test_rules_endpoint(client: TestClient) -> None:
    body = client.get("/api/v1/rules", params={"category": "finance"}).json()
    ids = {rule["id"] for rule in body["rules"]}
    assert "FIN-RETURNS-01" in ids and "COM-SUPER-01" in ids
    assert client.get("/api/v1/rules", params={"category": "nope"}).status_code == 422
