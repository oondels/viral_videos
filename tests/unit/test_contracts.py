import re

import pytest
from pydantic import ValidationError

from app.core.contracts import ValidatedJob, validate_job

JOB_ID_RE = re.compile(r"^job_\d{4}_\d{2}_\d{2}_\d{3}$")


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_minimal_payload_materializes_defaults():
    job = validate_job({"topic": "explain inflation"})
    assert job.topic == "explain inflation"
    assert job.duration_target_sec == 30
    assert job.characters == ["char_a", "char_b"]
    assert job.background_style == "auto"
    assert job.output_preset == "shorts_default"


def test_job_id_is_generated_and_well_formed():
    job = validate_job({"topic": "test topic"})
    assert JOB_ID_RE.match(job.job_id), f"bad job_id: {job.job_id}"


def test_job_id_not_accepted_from_payload():
    with pytest.raises(ValidationError):
        validate_job({"topic": "test", "job_id": "job_2026_01_01_001"})


def test_topic_is_trimmed():
    job = validate_job({"topic": "  hello world  "})
    assert job.topic == "hello world"


def test_full_valid_payload():
    job = validate_job(
        {
            "topic": "crypto crash explained",
            "duration_target_sec": 25,
            "background_style": "minecraft_parkour",
            "characters": ["char_a", "char_b"],
            "output_preset": "shorts_default",
        }
    )
    assert job.duration_target_sec == 25
    assert job.background_style == "minecraft_parkour"


def test_returns_validated_job_instance():
    job = validate_job({"topic": "anything"})
    assert isinstance(job, ValidatedJob)


# ---------------------------------------------------------------------------
# topic validation
# ---------------------------------------------------------------------------


def test_missing_topic_fails():
    with pytest.raises(ValidationError):
        validate_job({})


def test_empty_topic_fails():
    with pytest.raises(ValidationError):
        validate_job({"topic": ""})


def test_whitespace_only_topic_fails():
    with pytest.raises(ValidationError):
        validate_job({"topic": "   "})


# ---------------------------------------------------------------------------
# duration_target_sec validation
# ---------------------------------------------------------------------------


def test_duration_too_low_fails():
    with pytest.raises(ValidationError):
        validate_job({"topic": "t", "duration_target_sec": 19})


def test_duration_too_high_fails():
    with pytest.raises(ValidationError):
        validate_job({"topic": "t", "duration_target_sec": 46})


def test_duration_boundary_low_passes():
    job = validate_job({"topic": "t", "duration_target_sec": 20})
    assert job.duration_target_sec == 20


def test_duration_boundary_high_passes():
    job = validate_job({"topic": "t", "duration_target_sec": 45})
    assert job.duration_target_sec == 45


# ---------------------------------------------------------------------------
# characters validation
# ---------------------------------------------------------------------------


def test_one_character_fails():
    with pytest.raises(ValidationError):
        validate_job({"topic": "t", "characters": ["char_a"]})


def test_three_characters_fails():
    with pytest.raises(ValidationError):
        validate_job({"topic": "t", "characters": ["char_a", "char_b", "char_c"]})


def test_duplicate_characters_fails():
    with pytest.raises(ValidationError):
        validate_job({"topic": "t", "characters": ["char_a", "char_a"]})


# ---------------------------------------------------------------------------
# background_style validation
# ---------------------------------------------------------------------------


def test_unknown_background_style_fails():
    with pytest.raises(ValidationError):
        validate_job({"topic": "t", "background_style": "nonexistent_style"})


# ---------------------------------------------------------------------------
# output_preset validation
# ---------------------------------------------------------------------------


def test_unknown_output_preset_fails():
    with pytest.raises(ValidationError):
        validate_job({"topic": "t", "output_preset": "4k_landscape"})


# ---------------------------------------------------------------------------
# unknown fields
# ---------------------------------------------------------------------------


def test_unknown_field_fails():
    with pytest.raises(ValidationError):
        validate_job({"topic": "t", "extra_field": "oops"})


def test_multiple_unknown_fields_fail():
    with pytest.raises(ValidationError):
        validate_job({"topic": "t", "foo": 1, "bar": 2})
