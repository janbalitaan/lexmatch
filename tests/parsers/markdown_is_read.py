"""Fixtures the tests split out of markdown_is_read share.

The data for "markdown is read", kept in one place so that reducing each
test file to a single class did not mean copying it.
"""

from __future__ import annotations

PAGE = """\
# Support

## Are you open to remote work?

Yes, and I have done it for six years.

*Also asked: remote, work from home, wfh*

#hiring #logistics

## What is your notice period?

One month.

*Aliases: notice, when can you start*
"""
