"""Every example has to actually run.

An example that stopped working is worse than no example: it is the first
thing a reader tries, and it fails in a way that looks like their mistake
rather than ours.

Each runs in a subprocess, because an example is a script — importing it
would not catch a failure in module-level code, which is most of what an
example is.
"""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import pytest

EXAMPLES = sorted((Path(__file__).resolve().parents[2] / "examples").glob("*.py"))


class TestEveryExampleRuns:
    def test_the_directory_is_not_empty(self):
        assert EXAMPLES, "no examples found"

    @pytest.mark.parametrize("example", EXAMPLES, ids=lambda item: item.name)
    def test_it_exits_cleanly(self, example):
        finished = subprocess.run(
            [sys.executable, str(example)], capture_output=True, text=True, check=False
        )
        assert finished.returncode == 0, finished.stderr

    @pytest.mark.parametrize("example", EXAMPLES, ids=lambda item: item.name)
    def test_it_prints_something(self, example):
        """An example that runs silently teaches nothing."""
        finished = subprocess.run(
            [sys.executable, str(example)], capture_output=True, text=True, check=False
        )
        assert finished.stdout.strip()

    def test_every_example_is_listed(self):
        """A file nobody links to is one nobody opens."""
        listed = (EXAMPLES[0].parent / "README.md").read_text()
        for example in EXAMPLES:
            assert example.name in listed, f"{example.name} is not in examples/README.md"
