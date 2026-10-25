"""Helpers that know nothing about matching.

The test for belonging here is whether a function would make sense in an
unrelated project. Splitting a string into comparable tokens would; deciding
which entry a query matches would not, so that stays in `index.py`.

Grouped as a class rather than left as loose functions, so each file is one
named thing a reader can look up.
"""

from lexmatch.utils.text import Tokenizer

__all__ = ["Tokenizer"]
