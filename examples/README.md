# Examples

Each one runs on its own with no arguments and no setup.

| | |
| --- | --- |
| [`01_answer_a_question.py`](01_answer_a_question.py) | An index, some questions, and an honest refusal. |
| [`02_why_did_it_match.py`](02_why_did_it_match.py) | Reading the scores, which is how you write aliases. |
| [`03_tuning_it.py`](03_tuning_it.py) | Changing how it scores without editing the package. |
| [`04_synonyms_and_compound.py`](04_synonyms_and_compound.py) | A word that means the same thing everywhere, and a message asking several things. |

```bash
python examples/01_answer_a_question.py
```

They are run by the test suite, so an example that stops working fails CI
rather than failing the next person who tries it.
