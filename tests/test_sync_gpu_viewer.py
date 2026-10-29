"""No-CUDA tests for preview-first local QUIC source integration."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/sync_gpu_viewer.py"
spec = importlib.util.spec_from_file_location("sync_gpu_viewer", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class TestSyncViewer(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.source, self.target = root / "working", root / "Q3DGStream"
        self.source.mkdir()
        self.target.mkdir()
        (self.target / ".git").mkdir()
        (self.target / "README.md").write_text("Q3DGStream")
        (self.target / "q3dgstream.py").write_text("print('ok')")
        for name in module.REQUIRED:
            data = "# Local QUIC viewer\n" + "\n".join(module.SOURCE_MARKERS.get(name, ()))
            (self.source / name).write_text(data)
        (self.target / "main.py").write_text("# Original viewer")

    def tearDown(self):
        self.tmp.cleanup()

    def test_preview_does_not_change_target(self):
        entries = module.plan(self.source, self.target)
        self.assertEqual(len(entries), len(module.REQUIRED))
        self.assertEqual((self.target / "main.py").read_text(), "# Original viewer")
        self.assertFalse((self.target / ".local_backups").exists())

    def test_apply_preserves_source_and_backs_up_target(self):
        digest_before = module.digest(self.source / "main.py")
        backup = module.apply(self.source, self.target, module.plan(self.source, self.target))
        self.assertEqual(module.digest(self.source / "main.py"), digest_before)
        self.assertEqual(module.digest(self.target / "main.py"), digest_before)
        self.assertEqual((backup / "main.py").read_text(), "# Original viewer")
        self.assertTrue((backup / "manifest.json").exists())
        self.assertTrue(all(x["action"] == "unchanged" for x in module.plan(self.source, self.target)))

    def test_missing_required_file_is_rejected(self):
        (self.source / "live_quic.py").unlink()
        with self.assertRaisesRegex(ValueError, "live_quic.py"):
            module.plan(self.source, self.target)

    def test_symlink_source_is_rejected(self):
        (self.source / "quic_transport.py").unlink()
        (self.source / "quic_transport.py").symlink_to(self.source / "main.py")
        with self.assertRaisesRegex(ValueError, "safe regular file"):
            module.plan(self.source, self.target)

if __name__ == "__main__":
    unittest.main()
