# HackProof

**Find the gaps in a hackathon story before you publish it.**

HackProof is an offline Python CLI that checks a Markdown submission and produces
text, JSON, or a standalone HTML report. Optional SHA-256 receipts detect changed
local evidence artifacts. No accounts, API keys, telemetry, or dependencies.

Built with AI coding assistance during MLH Global Hack Week: Builders Week,
November 6–12, 2026, for the accompanying MLH × DEV writing challenge preparation.
Global Hack Week check-in was visible in the signed-in event account. Acceptance
of Global Hack Week projects for the writing competition has not been confirmed
by the organizers. This project does not certify eligibility.

## Try the demo

Requires Python 3.10 or later. Clone or download this repository, then run:

```sh
python hackproof.py audit examples/incomplete.md
python hackproof.py audit examples/complete.md
python hackproof.py audit examples/complete.md --format html --output report.html
```

The first command exits with code **1** and identifies the unfinished title,
empty project section, placeholder demo domain, and unfinished prose. The second
exits with **0**. Open `report.html` in a browser for a readable report.

The checked-in [HTML report](docs/report.html), [JSON report](docs/report.json),
and [demo transcript](docs/demo.txt) are generated artifacts, not a hosted service.
GitHub displays the HTML source; download it or generate it locally to view it.

## Evidence receipts

```sh
python hackproof.py receipt docs/validation.txt --claim "Recorded unittest run" --output evidence.json
python hackproof.py audit examples/complete.md --evidence evidence.json
```

Receipts contain a claim label, a relative artifact path, and a SHA-256 digest.
Artifacts must reside within the receipt directory or its descendants. Changing
the artifact after recording the receipt causes the evidence check to fail.
To try it without changing project files, copy the validation log to a temporary
directory, create a receipt there, edit that copy, and audit again.

A receipt proves only that bytes match a recorded digest. Anyone can generate a
receipt for inaccurate evidence. Human review is still necessary.

## What is checked

- A nonempty `title` and the `mlhacks` tag, with at most four tags.
- Content under the four official template headings.
- At least one HTTP(S) link under Demo, excluding common example domains and localhost.
- Recognized unfinished markers in prose, such as TODO, TBD, and `[Insert …]`.
- Optional local evidence integrity and containment within the receipt directory.

HTML comments and fenced code examples do not count as section prose or unfinished
markers. Reports escape user content before embedding it in HTML. Outputs use
exclusive file creation to avoid overwriting existing files.

The parser handles a deliberately limited subset of Markdown/front matter. It
does not parse arbitrary YAML, detect every placeholder, validate URL availability,
or inspect image/video content. A pass means the configured checks passed, not
that the post is publication-ready. Event attendance, authorship, account linkage,
factual accuracy, and competition eligibility require separate verification.

## Exit codes and automation

| Code | Meaning |
| --- | --- |
| 0 | All configured checks passed |
| 1 | Report contains failed checks |
| 2 | Input, receipt, or output error |

```sh
python hackproof.py audit examples/complete.md --format json
python -m unittest discover -s tests -v
```

Eight integration and regression tests cover an incomplete entry, a complete
entry followed by evidence tampering, path traversal, malformed receipts,
fenced/commented examples, HTML escaping, output preservation, and missing input.
The validation log records the local run; CI independently reruns the tests.

## Why build this?

A submission template provides headings, but headings alone do not make a story
complete. HackProof adds a small, repeatable review step with inspectable findings.
The most useful design decision was separating structural completeness from
factual verification, so a green report cannot silently stand in for evidence.

## Development disclosure

OpenAI Codex generated and tested this implementation, documentation, and demo
under the account owner's direction. No interviews, teammates, workshop attendance,
or unobserved event experiences are claimed. No MLH partner service is used at
runtime. This is an independent project, not an official MLH or DEV validator.

License: MIT.
