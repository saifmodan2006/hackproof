import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from hackproof import audit, prose, render


class SubmissionJourney(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(ROOT / 'hackproof.py'), *map(str, args)],
                              capture_output=True, text=True, encoding='utf-8')

    def test_incomplete_entry_fails_with_actionable_findings(self):
        result = self.run_cli('audit', ROOT / 'examples/incomplete.md', '--format', 'json')
        self.assertEqual(result.returncode, 1, result.stderr)
        findings = json.loads(result.stdout)['findings']
        failed = {f['check'] for f in findings if f['status'] == 'fail'}
        self.assertTrue({'section:What I Built', 'demo-link', 'placeholders'} <= failed)

    def test_complete_entry_and_tampered_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            artifact, receipt = root / 'test-results.txt', root / 'evidence.json'
            artifact.write_text('Recorded demo output\n', encoding='utf-8')
            created = self.run_cli('receipt', artifact, '--claim', 'Demo output', '--output', receipt)
            self.assertEqual(created.returncode, 0, created.stderr)
            valid = self.run_cli('audit', ROOT / 'examples/complete.md', '--evidence', receipt)
            self.assertEqual(valid.returncode, 0, valid.stderr)
            artifact.write_text('Changed after receipt\n', encoding='utf-8')
            changed = self.run_cli('audit', ROOT / 'examples/complete.md', '--evidence', receipt)
            self.assertEqual(changed.returncode, 1, changed.stderr)
            self.assertIn('[FAIL] evidence:1', changed.stdout)

    def test_outside_evidence_is_rejected_even_with_correct_hash(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'receipts').mkdir()
            artifact = root / 'outside.txt'
            artifact.write_bytes(b'outside')
            receipt = root / 'receipts/evidence.json'
            receipt.write_text(json.dumps([{'claim': 'Outside file', 'path': '../outside.txt',
                'sha256': hashlib.sha256(b'outside').hexdigest()}]))
            report = audit(ROOT / 'examples/complete.md', receipt)
            self.assertFalse(report['passed'])
            self.assertEqual(report['findings'][-1]['status'], 'fail')

    def test_malformed_evidence_is_an_input_error(self):
        with tempfile.TemporaryDirectory() as folder:
            receipt = Path(folder) / 'evidence.json'
            for data in ({}, [], [None], [{'claim': 'x'}]):
                receipt.write_text(json.dumps(data))
                result = self.run_cli('audit', ROOT / 'examples/complete.md', '--evidence', receipt)
                self.assertEqual(result.returncode, 2, result.stdout)
                self.assertIn('hackproof:', result.stderr)

    def test_fenced_examples_do_not_count_as_prose(self):
        self.assertEqual(prose('```python\nTODO\n~~~\n```\nActual text'), 'Actual text')
        self.assertEqual(prose('<!-- TODO -->\nVisible'), '\nVisible')

    def test_html_escapes_content(self):
        report = {'passed': False, 'file': '<script>alert(1)</script>', 'limits': '<unsafe>',
                  'findings': [{'status': 'fail', 'check': '<img>', 'detail': '<script>oops</script>'}]}
        page = render(report, 'html')
        self.assertNotIn('<script>', page)
        self.assertIn('&lt;script&gt;', page)

    def test_outputs_do_not_overwrite_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            artifact = root / 'source.txt'
            artifact.write_text('keep this')
            result = self.run_cli('receipt', artifact, '--claim', 'test', '--output', artifact)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(artifact.read_text(), 'keep this')
            result = self.run_cli('audit', ROOT / 'examples/complete.md', '--output', artifact)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(artifact.read_text(), 'keep this')

    def test_missing_input_returns_two(self):
        result = self.run_cli('audit', ROOT / 'examples/not-present.md')
        self.assertEqual(result.returncode, 2)


if __name__ == '__main__':
    unittest.main()
