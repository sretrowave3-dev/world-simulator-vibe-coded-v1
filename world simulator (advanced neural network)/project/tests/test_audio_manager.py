"""
project/tests/test_audio_manager.py

Unit tests for BGMManager, audio asset discovery, fade-in/fade-out routines,
and dynamic volume/mute toggles.
"""

import os
import time
import unittest
from project.core.audio_manager import BGMManager, global_bgm


class TestAudioManager(unittest.TestCase):

    def setUp(self) -> None:
        self.mgr = BGMManager(target_volume=0.5)

    def tearDown(self) -> None:
        self.mgr.stop(fade_out_ms=10)

    def test_audio_file_discovery(self) -> None:
        path = self.mgr._resolve_audio_file()
        self.assertIsNotNone(path)
        self.assertTrue(os.path.exists(path))
        self.assertGreater(os.path.getsize(path), 1024)

    def test_volume_controls(self) -> None:
        self.mgr.set_volume(0.8)
        self.assertAlmostEqual(self.mgr.target_volume, 0.8)

        # Clamping
        self.mgr.set_volume(1.5)
        self.assertEqual(self.mgr.target_volume, 1.0)

        self.mgr.set_volume(-0.5)
        self.assertEqual(self.mgr.target_volume, 0.0)

    def test_mute_toggle(self) -> None:
        self.assertFalse(self.mgr.is_muted)
        muted = self.mgr.toggle_mute()
        self.assertTrue(muted)
        self.assertTrue(self.mgr.is_muted)

        unmuted = self.mgr.toggle_mute()
        self.assertFalse(unmuted)
        self.assertFalse(self.mgr.is_muted)

    def test_fade_in_and_fade_out_lifecycle(self) -> None:
        started = self.mgr.start(fade_in_ms=100)
        # Should initiate without crashing regardless of backend
        self.assertIsInstance(started, bool)
        time.sleep(0.15)
        
        self.mgr.stop(fade_out_ms=100)
        self.assertFalse(self.mgr.is_playing)
        self.assertEqual(self.mgr.current_volume, 0.0)


if __name__ == "__main__":
    unittest.main()
