"""Offline submission checks and SHA-256 evidence receipts. Python 3.10+."""
import argparse
import hashlib
import html
import json
from pathlib import Path
import re
import sys

SECTIONS = ('What I Built', 'Demo', 'Partner Technologies', 'Hackathon Experience')


def prose(markdown):
    """Exclude fenced examples and editorial comments from content checks."""
    lines, fence = [], None
    for line in markdown.splitlines():
        marker = re.match(r'^ {0,3}(`{3,}|~{3,})(.*)$', line)
        if marker:
            run, tail = marker.groups()
            if fence is None:
                fence = run
            elif run[0] == fence[0] and len(run) >= len(fence) and not tail.strip():
                fence = None
            continue
        if fence is None:
            lines.append(line)
    return re.sub(r'<!--[\s\S]*?-->', '', '\n'.join(lines))


def audit(path, evidence=None):
    raw = path.read_text(encoding='utf-8-sig')
    clean = prose(raw)
    findings = []

    def check(key, ok, detail):
        findings.append({'check': key, 'status': 'pass' if ok else 'fail', 'detail': detail})

    front = re.match(r'\A---\s*\n([\s\S]*?)\n---(?:\n|$)', clean)
    metadata = {}
    if front:
        metadata = dict(re.findall(r'^([\w-]+):[ \t]*(.*)$', front[1], re.M))
        clean = clean[front.end():]
    title = metadata.get('title', '').strip().strip('\"\'')
    check('title', bool(title), 'A nonempty title is required.')
    tags = re.findall(r'[\w-]+', metadata.get('tags', '').lower())
    check('tags', 'mlhacks' in tags and len(tags) <= 4,
          'Include mlhacks and use at most four DEV tags.')
    headings = list(re.finditer(r'^##[ \t]+(.+?)[ \t]*#*[ \t]*$', clean, re.M))
    sections = {}
    for i, heading in enumerate(headings):
        end = headings[i + 1].start() if i + 1 < len(headings) else len(clean)
        sections[heading[1].strip().casefold()] = clean[heading.end():end].strip()
    for section in SECTIONS:
        content = sections.get(section.casefold(), '')
        check('section:' + section, bool(re.search(r'[A-Za-z0-9]', content)),
              section + ' needs content beyond comments or fenced examples.')
    urls = re.findall(r'https?://[^\s<>\)\]\"\']+', sections.get('demo', ''))
    usable = [url for url in urls if not re.search(
        r'^https?://(?:www\.)?(?:example\.(?:com|org|net)|localhost)(?:[:/]|$)', url, re.I)]
    check('demo-link', bool(usable), 'Demo needs a real URL; reachability is not checked.')
    placeholders = re.findall(
        r'\b(?:TODO|TBD|FIXME)\b|\[(?:insert|add|your|project name|describe|replace|event name)[^\]\n]*\]|\{\{[^}\n]+\}\}',
        title + '\n' + clean, re.I)
    check('placeholders', not placeholders,
          'Unfinished markers: ' + ', '.join(dict.fromkeys(placeholders)) if placeholders
          else 'No recognized unfinished markers in prose.')
    if evidence:
        receipts = json.loads(evidence.read_text(encoding='utf-8-sig'))
        if not isinstance(receipts, list) or not receipts:
            raise ValueError('Evidence must be a nonempty JSON array.')
        root = evidence.resolve().parent
        for i, receipt in enumerate(receipts, 1):
            if not isinstance(receipt, dict):
                raise ValueError('Each evidence receipt must be an object.')
            claim, relative, expected = (receipt.get(k) for k in ('claim', 'path', 'sha256'))
            if not all(isinstance(v, str) and v.strip() for v in (claim, relative, expected)):
                raise ValueError('Each receipt needs claim, path, and sha256 strings.')
            artifact = (root / relative).resolve()
            inside = artifact.is_relative_to(root) and not Path(relative).is_absolute()
            valid = inside and artifact.is_file() and bool(re.fullmatch(r'[a-fA-F0-9]{64}', expected))
            matched = valid and hashlib.sha256(artifact.read_bytes()).hexdigest() == expected.lower()
            check('evidence:' + str(i), bool(matched), claim + ' — ' + relative)
    return {
        'file': path.name,
        'passed': all(f['status'] == 'pass' for f in findings),
        'findings': findings,
        'limits': 'Structural checks and byte-integrity receipts only. No eligibility, attendance, authorship, factual claim, or URL availability verification.',
    }


def render(report, format):
    if format == 'json':
        return json.dumps(report, indent=2, ensure_ascii=False) + '\n'
    if format == 'text':
        lines = ['HackProof: ' + ('PASS' if report['passed'] else 'NEEDS WORK')]
        lines += [f"[{f['status'].upper()}] {f['check']}: {f['detail']}" for f in report['findings']]
        return '\n'.join(lines + ['', report['limits'], ''])
    rows = ''.join(
        '<tr><td class="' + f['status'] + '">' + f['status'].upper() + '</td><th scope="row">'
        + html.escape(f['check']) + '</th><td>' + html.escape(f['detail']) + '</td></tr>'
        for f in report['findings'])
    return '''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>HackProof submission report</title><style>
body{background:#0b1320;color:#e5edf5;font:17px/1.6 system-ui;margin:0;padding:5vw}
main{max-width:1050px;margin:auto}.eyebrow{color:#78dfc3;letter-spacing:.15em;font-size:12px}
h1{font-size:clamp(38px,6vw,70px);line-height:1.1;margin:18px 0}p{color:#a9b9cb}
table{border-collapse:collapse;width:100%;margin:36px 0;background:#142133}
th,td{text-align:left;padding:16px;border-bottom:1px solid #2d4057;overflow-wrap:anywhere}
.pass{color:#78dfc3}.fail{color:#ffbb87}th{font-size:14px}footer{font-size:14px}
@media(max-width:600px){body{padding:20px}th,td{padding:9px;font-size:12px}}
</style><main><div class="eyebrow">HACKPROOF / LOCAL EVIDENCE CHECK</div><h1>''' + (
        'Ready for human review.' if report['passed'] else 'A few gaps to close.') + (
        '</h1><p>' + html.escape(report['file']) + '</p><table><caption>Submission checks</caption>'
        '<thead><tr><th>Status</th><th>Check</th><th>Details</th></tr></thead><tbody>' + rows
        + '</tbody></table><footer>' + html.escape(report['limits']) + '</footer></main></html>\n')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    scan = sub.add_parser('audit', help='Check a Markdown submission offline')
    scan.add_argument('file', type=Path)
    scan.add_argument('--evidence', type=Path)
    scan.add_argument('--format', choices=('text', 'json', 'html'), default='text')
    scan.add_argument('--output', type=Path)
    receipt = sub.add_parser('receipt', help='Hash one artifact; does not verify its claims')
    receipt.add_argument('file', type=Path)
    receipt.add_argument('--claim', required=True)
    receipt.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'receipt':
            artifact = args.file.resolve(strict=True)
            root = args.output.resolve().parent
            if not artifact.is_file() or not artifact.is_relative_to(root):
                raise ValueError('Artifact must be a file inside the receipt output directory.')
            if artifact == args.output.resolve():
                raise ValueError('Receipt output must differ from the artifact.')
            if args.output.exists():
                raise ValueError('Receipt output already exists; choose a new path.')
            if not args.claim.strip():
                raise ValueError('Claim must not be empty.')
            data = [{'claim': args.claim, 'path': artifact.relative_to(root).as_posix(),
                     'sha256': hashlib.sha256(artifact.read_bytes()).hexdigest()}]
            with args.output.open('x', encoding='utf-8') as handle:
                json.dump(data, handle, indent=2, ensure_ascii=False)
                handle.write('\n')
            print('Receipt created. It records bytes, not proof that the claim is true.')
            return 0
        if args.output and args.output.resolve() in {args.file.resolve(),
                                                   args.evidence.resolve() if args.evidence else None}:
            raise ValueError('Report output must not overwrite its inputs.')
        report = audit(args.file, args.evidence)
        output = render(report, args.format)
        if args.output:
            with args.output.open('x', encoding='utf-8') as handle:
                handle.write(output)
        else:
            print(output, end='')
        return 0 if report['passed'] else 1
    except (OSError, ValueError, UnicodeError) as error:
        print('hackproof: ' + str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
