"""Headless tests for Workspace Trust helpers."""
import os
import tempfile
import unittest

from core.trust import is_too_broad, is_trusted, with_trusted, without_trusted


class TrustTests(unittest.TestCase):
    def test_untrusted_by_default(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertFalse(is_trusted([], folder))
            self.assertFalse(is_trusted(None, folder))

    def test_trust_and_untrust_roundtrip(self):
        with tempfile.TemporaryDirectory() as folder:
            trusted = with_trusted([], folder)
            self.assertTrue(is_trusted(trusted, folder))
            self.assertEqual(with_trusted(trusted, folder), trusted)      # no duplicates
            self.assertFalse(is_trusted(without_trusted(trusted, folder), folder))

    def test_trust_is_not_inherited_by_subfolders(self):
        with tempfile.TemporaryDirectory() as folder:
            child = os.path.join(folder, "child")
            os.mkdir(child)
            self.assertFalse(is_trusted(with_trusted([], folder), child))

    def test_home_and_roots_are_too_broad(self):
        self.assertTrue(is_too_broad(os.path.expanduser("~")))
        self.assertTrue(is_too_broad(os.path.abspath(os.sep)))
        with tempfile.TemporaryDirectory() as folder:
            self.assertFalse(is_too_broad(folder))


if __name__ == "__main__":
    unittest.main()
