---
title: "HackProof: catch missing pieces in your hackathon write-up"
published: true
tags: mlhacks, devchallenge, hackathon
---

_This is a submission for the [MLH × DEV Writing Challenge](https://dev.to/mlh-hackathon). Published: [dev.to/saif_modan/hackproof-catch-missing-pieces-in-your-hackathon-write-up-cn1](https://dev.to/saif_modan/hackproof-catch-missing-pieces-in-your-hackathon-write-up-cn1)._

## What I Built

A hackathon project can be almost finished and still be difficult to share. The demo link may be missing, a template placeholder may still be in the draft, or a paragraph may describe a claim without pointing to anything that supports it. I built **HackProof**, a small offline command-line tool to catch some of those gaps before publishing.

Give it a DEV-style Markdown post and HackProof checks for a title, the `mlhacks` tag, the four sections in the official challenge template, a demo URL, and obvious draft markers such as an empty title or bracketed fill-in instructions. It can print a text summary, produce JSON for automation, or create a standalone HTML report. It does not need an API key, an account, a network connection, or extra Python packages.

I also wanted to explore a useful boundary for evidence. HackProof can create an optional SHA-256 receipt for a local file and later tell you if the bytes changed. The receipt keeps a claim label, a relative path, and a digest; the audit rejects paths outside the receipt directory. That can help preserve a demo log or test result alongside a draft. A matching hash confirms that file is unchanged. It cannot establish that the file proves the claim, that the underlying claim is true, or that the project meets competition rules. A person still has to review the evidence.

I used the November 6–12 MLH Global Hack Week: Builders Week window to make this project. The event is online, and my MLH account showed me as checked in. I used the writing challenge template itself as a concrete test case: could I turn its repeated, easy-to-miss requirements into a quick local review? The public overview describes projects built at MLH events, but it also says additional participation terms are forthcoming. HackProof does not decide eligibility; the event organizer remains the source for that.

The working code and setup instructions are [on GitHub](https://github.com/saifmodan2006/hackproof). It is a standard-library Python program, not an official MLH or DEV product. I used AI coding assistance to implement and validate it, and the repository includes the test output and a sample report.

## Demo

The quickest way to see the checks is to run the deliberately incomplete example and then the complete one:

```sh
python hackproof.py audit examples/incomplete.md
python hackproof.py audit examples/complete.md
```

The first command reports the unfinished title, missing project story, placeholder demo URL, and incomplete prose. The second passes the configured checks. To create a browser-readable report, run:

```sh
python hackproof.py audit examples/complete.md --format html --output report.html
```

There is a [checked-in HTML report](https://github.com/saifmodan2006/hackproof/blob/main/docs/report.html), a [JSON report](https://github.com/saifmodan2006/hackproof/blob/main/docs/report.json), and a [test transcript](https://github.com/saifmodan2006/hackproof/blob/main/docs/validation.txt). GitHub shows the HTML source in its file viewer; running the command locally opens it as a proper page.

Eight automated tests cover the end-to-end audit, evidence tampering, unsafe receipt paths, malformed evidence, examples hidden in code fences and comments, HTML escaping, output preservation, and missing input. GitHub Actions runs the suite on Python 3.10 and 3.13.

## Partner Technologies

HackProof uses Python's standard library. It does not call an MLH partner service or require a partner API. I used AI coding assistance during development and documented that in the repository. The project is MIT licensed.

## Hackathon Experience

Global Hack Week: Builders Week ran online from November 6 through November 12, 2026. My project grew from the practical problem of preparing a clear project story while a challenge window was still open. The interesting part was keeping the checks modest: a green result should mean only that the checks ran and passed, not that a tool can certify a real-world claim. That distinction shaped both the evidence receipt design and the report's limitations.

I worked on HackProof individually with AI coding assistance; I am not claiming teammates, partner prizes, workshop participation, or any event interaction beyond the account's checked-in status. You can try it from the [repository](https://github.com/saifmodan2006/hackproof) and adapt the checks to your own submission checklist.
