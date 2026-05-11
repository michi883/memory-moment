"""compress_v5.py — Deterministic survey-to-Context-block compressor.

This is the canonical Python implementation of the v5 spec
(see context_spec_v5.md). It must produce byte-identical output to
compressSurvey() in survey_form.html. Parity is enforced by
parity_test.py.
"""

MASCULINE = {"father", "grandfather", "uncle", "brother", "husband",
             "son", "nephew"}

REL_PHRASING = {
    "mother": "Your mother",
    "father": "Your father",
    "spouse": "Your spouse",
    "wife": "Your wife",
    "husband": "Your husband",
    "grandmother": "Your grandmother",
    "grandfather": "Your grandfather",
    "aunt": "Your aunt",
    "uncle": "Your uncle",
    "sibling": "Your sibling",
    "sister": "Your sister",
    "brother": "Your brother",
    "friend": "Your friend",
    "other": "Someone you care for",
}

CALM_LABEL = {
    "tea_or_coffee": "tea",
    "music": "music",
    "photos": "photos",
    "a_walk": "a walk",
    "holding_hands": "a hand to hold",
    "sitting_quietly": "sitting quietly",
    "a_familiar_show": "a familiar show",
    "a_specific_person_visiting": "a familiar visit",
    "prayer": "prayer",
    "food": "food",
    "the_outdoors": "being outside",
    "a_blanket_or_cushion": "a blanket",
}

HARD_TIME_LABEL = {
    "morning": "mornings",
    "midday": "middays",
    "late_afternoon": "late afternoons",
    "evening": "evenings",
    "night": "nights",
}

# v5: new resists section. Keys mirror the form's snake_case enum;
# values are the natural-English labels emitted into the Context block.
RESISTS_LABEL = {
    "medication": "medication",
    "bathing": "bathing",
    "dressing": "dressing",
    "eating": "eating",
    "doctor_visits": "doctor visits",
    "going_outside": "going outside",
}


def _pronouns(rel: str):
    """Return (Subject_Cap, subject_lower, object) for the relationship."""
    if rel in MASCULINE:
        return ("He", "he", "him")
    return ("She", "she", "her")


def _select_phrases(phrases, k=3):
    """One from each length bucket (short/medium/long); fill empties shortest-first.

    See spec section 3 for the exact rule. Determinism matters here —
    parity with the JS implementation depends on identical sort orders.
    """
    if not phrases:
        return []
    short = sorted([p for p in phrases if len(p.split()) < 3], key=len)
    medium = sorted([p for p in phrases if 3 <= len(p.split()) <= 7], key=len)
    long_ = sorted([p for p in phrases if len(p.split()) >= 8], key=len)
    chosen = []
    for bucket in (short, medium, long_):
        if bucket:
            chosen.append(bucket[0])
    used = set(chosen)
    leftovers = sorted([p for p in phrases if p not in used], key=len)
    while len(chosen) < k and leftovers:
        chosen.append(leftovers.pop(0))
    return sorted(chosen, key=len)


def compress_survey(survey: dict) -> str:
    """Survey JSON → Context block string. Pure, deterministic, v5."""
    lines = []
    Cap, _, obj = _pronouns(survey.get("relationship", ""))

    # 1. Relationship + name
    if survey.get("relationship") and survey.get("name_used"):
        who = REL_PHRASING.get(survey["relationship"], "Someone you care for")
        lines.append(f"{who}. You call {obj} {survey['name_used']}.")

    # 2. Voice
    if survey.get("voice_tags"):
        lines.append(f"Voice: {', '.join(survey['voice_tags'])}.")

    # 3. Often says
    chosen = _select_phrases(survey.get("phrases_she_says", []))
    if chosen:
        quoted = " / ".join(f'"{p}"' for p in chosen)
        lines.append(f"{Cap} often says: {quoted}")

    # 4. Calms / hard times (combined)
    pieces = []
    calms = survey.get("what_calms_her", [])
    if calms and calms[0] in CALM_LABEL:
        pieces.append(f"calms with {CALM_LABEL[calms[0]]}")
    hard = survey.get("hard_times_of_day", [])
    if hard and hard[0] in HARD_TIME_LABEL:
        pieces.append(f"{HARD_TIME_LABEL[hard[0]]} are harder")
    if pieces:
        lines.append(f"{Cap} " + ", ".join(pieces) + ".")

    # 5. Repeats
    repeats = survey.get("repeats_she_makes", [])
    if repeats:
        lines.append(f"{Cap} sometimes asks: " + " / ".join(repeats[:2]))

    # 6. Avoid
    avoid = survey.get("topics_to_avoid", [])
    if avoid:
        lines.append("Avoid: " + "; ".join(e["topic_or_name"] for e in avoid) + ".")

    # 7. Resists — NEW IN v5
    # Filter unknown keys silently rather than raising; the form should
    # already constrain to valid enum values, but defensive parsing here
    # keeps the compressor robust against future enum drift.
    resists = survey.get("things_she_resists", [])
    valid_resists = [RESISTS_LABEL[k] for k in resists if k in RESISTS_LABEL]
    if valid_resists:
        lines.append("Resists: " + ", ".join(valid_resists) + ".")

    return "\n".join(lines)
