"""Fixtures the tests split out of csv_is_read share.

The data for "csv is read", kept in one place so that reducing each
test file to a single class did not mean copying it.
"""

from __future__ import annotations

SHEET = "\n".join(
    [
        "Question,Answer,Aliases,Category,Owner",
        'How do I cancel my subscription?,"Settings, then Billing, then Cancel'
        ' plan.",cancel;unsubscribe,billing,ops',
        "Where are my invoices?,Settings then Billing then Invoices."
        ",invoice;receipt,billing,ops",
        "",
    ]
)
