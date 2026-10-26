"""
project/tests/test_quantum_persistence.py

Unit tests for Quantum Persistence & Multi-Universe Timeline Subsystem ("10x Smarter than Git").
Tests:
- Universe isolation & sandbox directory segregation
- Autosaves & quicksave non-interference between worlds
- Stale overwrite safeguard & auto-forking
- Autonomous black-box flight recorder
- Intelligent time-machine rewind engine (delta, safe, disaster)
- ASCII timeline DAG visualization
"""

import os
import shutil
import tempfile
import unittest
import time
from project.core.quantum_persistence import QuantumPersistenceManager, TimelineNode, UniverseProfile


class TestQuantumPersistence(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="test_quantum_persistence_")
        self.mgr = QuantumPersistenceManager(saves_root=self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _create_mock_state(self, tick: int, alive_count: int = 50) -> dict:
        return {
            "version": "1.3",
            "time": {"tick": tick, "seconds": tick * 0.1, "seconds_per_day": 120.0, "days_per_year": 360, "ticks_per_second": 60},
            "soil": {},
            "water": {},
            "vegetation": {},
            "resources": [],
            "entities": [{"id": f"ent_{i}", "species_id": "human", "type": "HUMAN", "alive": True, "x": 100.0, "y": 100.0} for i in range(alive_count)],
            "gemini": {"god_affinity": 75.0, "monolith_spawned": False},
        }

    def test_universe_creation_and_switching(self):
        """Tests spawning multiple isolated universes and switching active context."""
        u1 = self.mgr.create_universe("Alpha World")
        u2 = self.mgr.create_universe("Beta World")

        self.assertIn(u1.universe_id, self.mgr.universes)
        self.assertIn(u2.universe_id, self.mgr.universes)

        # Switch to Alpha
        switched = self.mgr.switch_universe("Alpha World")
        self.assertIsNotNone(switched)
        self.assertEqual(self.mgr.active_universe_id, u1.universe_id)

        # Switch to Beta
        switched2 = self.mgr.switch_universe(u2.universe_id)
        self.assertIsNotNone(switched2)
        self.assertEqual(self.mgr.active_universe_id, u2.universe_id)

    def test_multi_universe_directory_isolation(self):
        """Guarantees that saves in World A never contaminate World B."""
        u_alpha = self.mgr.create_universe("Alpha Realm")
        u_beta = self.mgr.create_universe("Beta Realm")

        # In Alpha, save a checkpoint and an autosave
        self.mgr.switch_universe(u_alpha.universe_id)
        state_alpha = self._create_mock_state(tick=1000, alive_count=40)
        self.mgr.save_universe_checkpoint(state_alpha, name="alpha_save.dat")
        self.mgr.save_universe_autosave(state_alpha, tick=1000, cause="INTERVAL")

        # In Beta, save a checkpoint
        self.mgr.switch_universe(u_beta.universe_id)
        state_beta = self._create_mock_state(tick=50, alive_count=10)
        self.mgr.save_universe_checkpoint(state_beta, name="beta_save.dat")

        # Verify Alpha sandbox
        alpha_snaps = self.mgr.list_universe_snapshots(u_alpha.universe_id)
        alpha_names = [s["name"] for s in alpha_snaps]
        self.assertTrue(any("alpha_save" in name for name in alpha_names))
        self.assertFalse(any("beta_save" in name for name in alpha_names))

        # Verify Beta sandbox
        beta_snaps = self.mgr.list_universe_snapshots(u_beta.universe_id)
        beta_names = [s["name"] for s in beta_snaps]
        self.assertTrue(any("beta_save" in name for name in beta_names))
        self.assertFalse(any("alpha_save" in name for name in beta_names))

    def test_quicksave_per_universe_isolation(self):
        """Tests that quicksaves are sandboxed per universe."""
        u1 = self.mgr.create_universe("Universe One")
        u2 = self.mgr.create_universe("Universe Two")

        self.mgr.switch_universe(u1.universe_id)
        self.mgr.save_quicksave(self._create_mock_state(tick=500, alive_count=25))

        self.mgr.switch_universe(u2.universe_id)
        self.mgr.save_quicksave(self._create_mock_state(tick=2000, alive_count=80))

        # Reload Universe One quicksave
        self.mgr.switch_universe(u1.universe_id)
        qs1 = self.mgr.load_quicksave()
        self.assertEqual(qs1["time"]["tick"], 500)
        self.assertEqual(len(qs1["entities"]), 25)

        # Reload Universe Two quicksave
        self.mgr.switch_universe(u2.universe_id)
        qs2 = self.mgr.load_quicksave()
        self.assertEqual(qs2["time"]["tick"], 2000)
        self.assertEqual(len(qs2["entities"]), 80)

    def test_stale_overwrite_guard_auto_fork(self):
        """Tests that saving an older state over a newer file auto-forks with zero data loss."""
        u = self.mgr.create_universe("Timeline Guard Test")
        self.mgr.switch_universe(u.universe_id)

        # 1. Save progressed state at Tick 5,000
        prog_state = self._create_mock_state(tick=5000, alive_count=100)
        saved_file = self.mgr.save_universe_checkpoint(prog_state, name="progressed.dat")
        self.assertTrue(os.path.exists(saved_file))

        # 2. Simulate user mistake: saving early Tick 500 over "progressed.dat"
        stale_state = self._create_mock_state(tick=500, alive_count=10)
        new_file = self.mgr.save_universe_checkpoint(stale_state, name="progressed.dat")

        # The system must NOT have overwritten progressed.dat; instead it spawned a fork snapshot!
        self.assertNotEqual(saved_file, new_file)
        self.assertIn("fork_t500", new_file)
        self.assertTrue(os.path.exists(saved_file))
        self.assertTrue(os.path.exists(new_file))

    def test_autonomous_blackbox_recorder(self):
        """Tests flight recorder capturing pre-disaster capsule and recording milestone."""
        u = self.mgr.create_universe("Disaster World")
        self.mgr.switch_universe(u.universe_id)

        state = self._create_mock_state(tick=3200, alive_count=15)
        bb_file = self.mgr.capture_blackbox(state, cause="METEOR_IMPACT")

        self.assertTrue(os.path.exists(bb_file))
        self.assertIn("blackbox_meteor_impact", bb_file)
        self.assertEqual(len(u.milestones), 1)
        self.assertEqual(u.milestones[0]["cause"], "METEOR_IMPACT")
        self.assertEqual(u.milestones[0]["tick"], 3200)

    def test_time_machine_rewind_engine(self):
        """Tests intelligent rewind by tick delta, safe population, and disaster capsule."""
        u = self.mgr.create_universe("Rewind Chrono")
        self.mgr.switch_universe(u.universe_id)

        # Node 1: Tick 1,000 (Safe population: 60 alive)
        s1 = self._create_mock_state(tick=1000, alive_count=60)
        self.mgr.save_universe_checkpoint(s1, name="checkpoint_t1000.dat")

        # Node 2: Tick 2,000 (Blackbox capsule before disaster)
        s2 = self._create_mock_state(tick=2000, alive_count=45)
        self.mgr.capture_blackbox(s2, cause="SOLAR_ECLIPSE")

        # Node 3: Tick 3,000 (Depleted population: 5 alive)
        s3 = self._create_mock_state(tick=3000, alive_count=5)
        self.mgr.save_universe_checkpoint(s3, name="checkpoint_t3000.dat")

        # 1. Rewind to disaster
        f_disaster, state_disaster = self.mgr.rewind("disaster")
        self.assertIn("blackbox", f_disaster)
        self.assertEqual(state_disaster["time"]["tick"], 2000)
        self.assertIn("fork_t2000", u.active_branch)

        # 2. Rewind to safe
        f_safe, state_safe = self.mgr.rewind("safe")
        self.assertEqual(state_safe["time"]["tick"], 1000)
        self.assertGreaterEqual(len(state_safe["entities"]), 30)

        # 3. Rewind by delta ticks (rewind 500 from 3000 -> target ~2500 -> finds tick 2000)
        u.current_tick = 3000
        f_delta, state_delta = self.mgr.rewind("500")
        self.assertIsNotNone(state_delta)

    def test_timeline_ascii_dag_generation(self):
        """Tests ASCII visual representation of the universe temporal tree."""
        u = self.mgr.create_universe("Timeline ASCII World")
        self.mgr.switch_universe(u.universe_id)

        s = self._create_mock_state(tick=100, alive_count=20)
        self.mgr.save_universe_checkpoint(s, name="ascii_save.dat")

        ascii_art = self.mgr.generate_timeline_ascii()
        self.assertIn("Timeline ASCII World", ascii_art)
        self.assertIn("ascii_save.dat", ascii_art)


if __name__ == "__main__":
    unittest.main()
