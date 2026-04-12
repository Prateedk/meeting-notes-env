"""Unit tests for semantic scoring and grading functions."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from server.meeting_notes_env_environment import (
    _semantic_score,
    _token_overlap,
    _bigram_overlap,
    _sequence_similarity,
    _tfidf_cosine,
    _who_field_score,
    _deadline_field_score,
    _what_field_score,
    _score_single_item,
    _grade_all_submitted,
    REWARD_MIN,
    REWARD_MAX,
)


class TestSemanticScore:
    def test_identical_strings(self):
        score = _semantic_score("fix the CI pipeline", "fix the CI pipeline")
        assert score > 0.95

    def test_empty_vs_nonempty(self):
        assert _semantic_score("", "fix something") == 0.0

    def test_both_empty(self):
        assert _semantic_score("", "") == 1.0

    def test_partial_overlap(self):
        score = _semantic_score("fix the pipeline", "fix the CI pipeline")
        assert 0.3 < score < 1.0

    def test_no_overlap(self):
        score = _semantic_score("apple banana cherry", "xylophone zebra quantum")
        assert score < 0.1

    def test_deterministic(self):
        a = _semantic_score("send report to finance", "send Q2 budget report to finance")
        b = _semantic_score("send report to finance", "send Q2 budget report to finance")
        assert a == b

    def test_score_range(self):
        score = _semantic_score("update the docs", "write documentation for the API")
        assert 0.0 <= score <= 1.0


class TestTokenOverlap:
    def test_perfect_match(self):
        assert _token_overlap("hello world", "hello world") == 1.0

    def test_no_match(self):
        assert _token_overlap("hello", "goodbye") == 0.0


class TestScoreSingleItem:
    def test_exact_match(self):
        pred = {"who": "Bob", "what": "fix the CI pipeline", "deadline": "Wednesday"}
        expected = [{"who": "Bob", "what": "fix the CI pipeline", "deadline": "Wednesday"}]
        score, idx, bd = _score_single_item(pred, expected, set())
        assert score > 0.9
        assert idx == 0

    def test_paraphrase_easy_1(self):
        pred = {
            "who": "Bob",
            "what": "repair the CI pipeline",
            "deadline": "end of day Wednesday",
        }
        expected = [{"who": "Bob", "what": "fix the CI pipeline", "deadline": "Wednesday"}]
        score, idx, _ = _score_single_item(pred, expected, set())
        assert idx == 0
        assert score > 0.75

    def test_field_scores_helpers(self):
        assert _who_field_score("Bob Smith", "Bob") >= 0.9
        assert _deadline_field_score("end of day Wednesday", "Wednesday") >= 0.85
        assert _what_field_score("repair the CI pipeline", "fix the CI pipeline") > 0.55

    def test_no_match_when_all_matched(self):
        pred = {"who": "Bob", "what": "fix CI", "deadline": "Wed"}
        expected = [{"who": "Bob", "what": "fix CI", "deadline": "Wed"}]
        score, idx, _ = _score_single_item(pred, expected, {0})
        assert idx == -1
        assert score == 0.0


class TestGradeAllSubmitted:
    def test_perfect_submission(self):
        submitted = [
            {"who": "Bob", "what": "fix the CI pipeline", "deadline": "Wednesday"},
        ]
        expected = [
            {"who": "Bob", "what": "fix the CI pipeline", "deadline": "Wednesday"},
        ]
        reward, feedback = _grade_all_submitted(submitted, expected)
        assert reward > 0.8

    def test_empty_submission(self):
        reward, feedback = _grade_all_submitted([], [{"who": "A", "what": "B", "deadline": "C"}])
        assert reward < 0.1

    def test_extra_items_penalty(self):
        submitted = [
            {"who": "Bob", "what": "fix CI", "deadline": "Wed"},
            {"who": "Alice", "what": "random task", "deadline": "never"},
        ]
        expected = [{"who": "Bob", "what": "fix CI", "deadline": "Wed"}]
        reward, _ = _grade_all_submitted(submitted, expected)
        reward_exact, _ = _grade_all_submitted(submitted[:1], expected)
        assert reward < reward_exact

    def test_no_expected(self):
        reward, _ = _grade_all_submitted([], [])
        assert reward == REWARD_MAX
