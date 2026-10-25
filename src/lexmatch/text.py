"""Text normalization and tokenization for lexical matching.

The implementation moved to `utils.text` when the helpers were separated
from the matching logic. These names stay because they are public API.
"""

from __future__ import annotations

from lexmatch.utils.text import Tokenizer

normalize = Tokenizer.normalize
query_terms = Tokenizer.query_terms

__all__ = ["normalize", "query_terms"]
