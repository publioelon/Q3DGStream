"""Keep the repository independent of local workstation paths."""
from __future__ import annotations

import importlib
import os
import re
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


class PortabilityTests(unittest.TestCase):
    def test_path_overrides(self):
        import q3dg_paths as paths

        env = {
            "Q3DGSTREAM_DATA_DIR": "/example/data",
            "Q3DGSTREAM_SCENE_DIR": "/example/assets/scene",
            "Q3DGSTREAM_EXPERIMENT_DIR": "/example/checkpoints",
        }
        try:
            with patch.dict(os.environ, env):
                importlib.reload(paths)
                self.assertEqual(paths.SCENE_DIR, Path(env["Q3DGSTREAM_SCENE_DIR"]))
                self.assertEqual(paths.WIRE_DIR, Path(env["Q3DGSTREAM_EXPERIMENT_DIR"]) / "wire")
                self.assertEqual(paths.PRIORITIES_DIR, Path(env["Q3DGSTREAM_DATA_DIR"]) / "priorities")
        finally:
            importlib.reload(paths)

    def test_shell_scripts_parse(self):
        scripts = sorted(ROOT.rglob("*.sh"))
        self.assertGreaterEqual(len(scripts), 10)
        for script in scripts:
            with self.subTest(file=str(script.relative_to(ROOT))):
                result = subprocess.run(["bash", "-n", str(script)],
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_no_workstation_specific_paths(self):
        # Historical absolute mount paths should never be committed.
        forbidden = ["snap/firefox/" + "common",
                     "/data/" + "3dgs_storage", "3DGS-" + "QuaNTiC-Demo"]
        sources = list(ROOT.rglob("*.py")) + list(ROOT.rglob("*.sh"))
        sources += list(ROOT.rglob("*.md")) + list(ROOT.rglob("*.txt"))
        for source in sources:
            if source == Path(__file__) or ".git" in source.parts:
                continue
            text = source.read_text(encoding="utf-8", errors="replace")
            for token in forbidden:
                with self.subTest(path=str(source.relative_to(ROOT)), token=token):
                    self.assertNotIn(token, text)
            # Catch absolute paths into a particular user's home directory.
            self.assertIsNone(re.search(r"/home/[^/\\s]+/(?:snap|venvs|qntc_scenes|3DGS-)", text))


if __name__ == "__main__":
    unittest.main()
