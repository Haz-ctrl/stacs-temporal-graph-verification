"""Tests for run directory naming with model labels."""

from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.run_llm_baseline import allocate_run_dir, utc_stamp


class TestAllocateRunDir:
    """Tests for the allocate_run_dir function with model labels."""

    def test_allocates_dir_without_model_label(self, tmp_path):
        """Should create directory with just timestamp when no model label provided."""
        run_id, run_dir = allocate_run_dir(tmp_path, model_label="")

        assert run_dir == tmp_path / run_id
        assert run_id == utc_stamp()
        assert run_dir.exists()

    def test_allocates_dir_with_model_label(self, tmp_path):
        """Should create directory with model_label_prefix_timestamp format."""
        model_name = "llama-2-7b"
        run_id, run_dir = allocate_run_dir(tmp_path, model_label=model_name)

        expected_prefix = model_name
        assert run_id.startswith(f"{expected_prefix}_"), (
            f"Expected run_id to start with '{expected_prefix}_, "
            f"but got '{run_id}'"
        )
        assert run_dir == tmp_path / run_id
        assert run_dir.exists()

    def test_sanitizes_slash_in_model_label(self, tmp_path):
        """Should replace / with - in model labels."""
        model_name = "meta/llama-2-7b"
        run_id, run_dir = allocate_run_dir(tmp_path, model_label=model_name)

        assert "/" not in run_id
        assert "meta-llama-2-7b" in run_id
        assert run_dir.exists()

    def test_sanitizes_colon_in_model_label(self, tmp_path):
        """Should replace : with - in model labels."""
        model_name = "llama-2:7b"
        run_id, run_dir = allocate_run_dir(tmp_path, model_label=model_name)

        assert ":" not in run_id
        assert "llama-2-7b" in run_id
        assert run_dir.exists()

    def test_sanitizes_dot_in_model_label(self, tmp_path):
        """Should replace . with - in model labels."""
        model_name = "llama.2.7b"
        run_id, run_dir = allocate_run_dir(tmp_path, model_label=model_name)

        assert "." not in run_id
        assert "llama-2-7b" in run_id
        assert run_dir.exists()

    def test_sanitizes_spaces_in_model_label(self, tmp_path):
        """Should replace spaces with underscores in model labels."""
        model_name = "llama 2 7b"
        run_id, run_dir = allocate_run_dir(tmp_path, model_label=model_name)

        assert " " not in run_id
        assert "llama_2_7b" in run_id
        assert run_dir.exists()

    def test_handles_multiple_special_chars(self, tmp_path):
        """Should handle model labels with multiple special characters."""
        model_name = "meta/llama.2:7b test"
        run_id, run_dir = allocate_run_dir(tmp_path, model_label=model_name)

        # Verify no special characters remain
        for char in ["/", ":", ".", " "]:
            assert char not in run_id, f"Special char '{char}' should be sanitized"

        # Verify the base name is preserved
        assert "meta" in run_id
        assert "llama" in run_id
        assert "7b" in run_id
        assert run_dir.exists()

    def test_appends_sequence_on_collision(self, tmp_path):
        """Should append _01 suffix when directory already exists."""
        model_name = "llama-2-7b"
        
        # First allocation
        run_id1, run_dir1 = allocate_run_dir(tmp_path, model_label=model_name)
        
        # Second allocation with same timestamp (mocked)
        with patch('scripts.run_llm_baseline.utc_stamp', return_value=utc_stamp()):
            run_id2, run_dir2 = allocate_run_dir(tmp_path, model_label=model_name)

        assert run_id2 != run_id1
        assert run_id2.endswith("_01")
        assert "llama-2-7b" in run_id2
        assert run_dir1.exists()
        assert run_dir2.exists()

    def test_sequence_suffix_format(self, tmp_path):
        """Should use two-digit sequence suffix format."""
        model_name = "test-model"
        fake_stamp = "2024-01-01_000000UTC"

        # Pre-create the expected first directory to force a collision.
        expected_first_dir = tmp_path / f"{model_name}_{fake_stamp}"
        expected_first_dir.mkdir()

        with patch('scripts.run_llm_baseline.utc_stamp', return_value=fake_stamp):
            run_id2, run_dir2 = allocate_run_dir(tmp_path, model_label=model_name)

        assert run_id2.endswith("_01")
        assert run_id2.startswith("test-model_")

    def test_empty_model_label_same_as_no_label(self, tmp_path):
        """Empty string model label should produce a bare timestamp run ID."""
        fake_stamp = "2024-01-01_000000UTC"

        with patch('scripts.run_llm_baseline.utc_stamp', return_value=fake_stamp):
            run_id, run_dir = allocate_run_dir(tmp_path, model_label="")

        assert run_id == fake_stamp
        assert run_dir == tmp_path / fake_stamp

    def test_preserves_model_specific_characters(self, tmp_path):
        """Should preserve hyphens and underscores in model names."""
        model_name = "llama-2-7b-instruct"
        run_id, run_dir = allocate_run_dir(tmp_path, model_label=model_name)
        
        assert "llama-2-7b-instruct" in run_id
        assert run_dir.exists()
        
    def test_handles_ollama_model_format(self, tmp_path):
        """Should handle typical Ollama model format like 'deepseek-r1:7b'."""
        model_name = "deepseek-r1:7b"
        run_id, run_dir = allocate_run_dir(tmp_path, model_label=model_name)
        
        assert "deepseek-r1-7b" in run_id
        assert ":" not in run_id
        assert run_dir.exists()
