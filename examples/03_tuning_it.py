"""Changing how it scores, without editing the package.

Every number the scorer uses is replaceable. The defaults suit a few dozen
one-sentence questions; these are the levers for when they do not.

    python examples/03_tuning_it.py
"""

from lexmatch import Entry, Index, Tuning

# Four entries sharing most of their wording, which is where the overlap
# guard earns its place.
entries = [
    Entry(question=f"What is your rate for {kind} work?", answer=f"The {kind} rate.")
    for kind in ("design", "review", "audit", "training")
]

query = "what is your rate for consulting"
print(f"query: {query!r}\n")

for overlap in (1, 2):
    index = Index(entries, tuning=Tuning(minimum_overlap=overlap))
    entry, score = index.answer(query)
    verdict = entry.answer if entry else "refused"
    print(f"  minimum_overlap={overlap}  score={score:.3f}  ->  {verdict}")

print()
print("Sharing one diluted word with four near-identical entries is not")
print("enough to be sure which one was meant. Raising the guard says so.")
print()

print("a stopword that is content in your domain:")
contracts = [Entry(question="Will you sign the contract?", answer="Yes.")]
for label, tuning in (
    ("default", None),
    ("keep 'will'", Tuning().with_stopwords(keep=["will"])),
):
    index = Index(contracts, tuning=tuning)
    print(f"  {label:<14} 'will' is a stopword: {'will' in index.tuning.stopwords}")

print()
print("and words that are noise here but not in general:")
polite = Tuning().with_stopwords(extra=["please", "kindly"])
print(f"  {polite.describe()}")

print()
print("nonsense is refused when the tuning is built, not when scoring runs:")
from lexmatch import TuningError

try:
    Tuning(saturation=0)
except TuningError as error:
    print(f"  {error}")
