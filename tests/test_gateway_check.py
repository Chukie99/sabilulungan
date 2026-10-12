import unittest
from check_gateway import check


class AcceptanceTests(unittest.TestCase):
    def test_requires_real_tool_evidence(self):
        actions = iter([
            {'action': 'delegate', 'agent': 'coder', 'instructions': 'Test'},
            {'action': 'write_file', 'path': 'acceptance.txt', 'content': 'SABILULUNGAN_OK'},
            {'action': 'read_file', 'path': 'acceptance.txt'},
            {'action': 'remember', 'content': 'SABILULUNGAN_ACCEPTANCE'},
            {'action': 'complete', 'reply': 'Selesai'},
            {'action': 'read_file', 'path': 'acceptance.txt'},
            {'action': 'complete', 'reply': 'Terverifikasi'},
        ])
        self.assertTrue(all(check(lambda m: next(actions), timeout=5).values()))

    def test_claiming_success_does_not_pass(self):
        result = check(lambda m: {'action': 'complete', 'reply': 'Semua berhasil'}, timeout=5)
        self.assertFalse(result['file_content'])
        self.assertFalse(result['delegation'])
        self.assertFalse(result['memory'])
