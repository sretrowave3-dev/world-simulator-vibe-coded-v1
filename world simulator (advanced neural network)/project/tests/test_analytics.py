"""
tests/test_analytics.py

Unit tests for simulation metrics, time-series telemetry, session reports, and vector graph plots.
"""

import os
import unittest
from project.analytics.metrics import TelemetryTracker
from project.analytics.reports import SessionSummary, SessionReporter

try:
    import pygame
    from project.analytics.graphs import PopulationGraphRenderer
    HAS_PYGAME = True
except ImportError:
    HAS_PYGAME = False
    PopulationGraphRenderer = None  # type: ignore


class TestAnalyticsSubsystem(unittest.TestCase):

    def setUp(self) -> None:
        self.csv_filepath = "test_metrics.csv"
        self.report_basepath = "test_session_report"

    def tearDown(self) -> None:
        if os.path.exists(self.csv_filepath):
            os.remove(self.csv_filepath)
        if os.path.exists(self.report_basepath + ".md"):
            os.remove(self.report_basepath + ".md")
        if os.path.exists(self.report_basepath + ".json"):
            os.remove(self.report_basepath + ".json")

    def test_telemetry_csv_buffering_and_export(self) -> None:
        tracker = TelemetryTracker(flush_interval_ticks=5)
        self.assertEqual(len(tracker.history), 0)

        # Record points
        tracker.record(
            tick=100,
            timestamp_sec=50.0,
            populations={"bacteria": 20, "herbivore": 10},
            avg_vitals={"health": 90.0, "energy": 80.0},
        )
        tracker.record(
            tick=200,
            timestamp_sec=100.0,
            populations={"bacteria": 40, "herbivore": 8},
            avg_vitals={"health": 85.0, "energy": 75.0},
        )

        self.assertEqual(len(tracker.history), 2)

        # Flush to CSV
        tracker.flush_to_csv(self.csv_filepath)
        self.assertTrue(os.path.exists(self.csv_filepath))

        # Check if buffer was cleared
        self.assertEqual(len(tracker._buffered_points), 0)

    def test_session_reporting(self) -> None:
        summary = SessionSummary(
            total_ticks=5000,
            total_duration_sec=300.0,
            birth_count=250,
            death_count=180,
            extinction_count=2,
            average_lifespan_ticks=850.5,
            peak_concurrent_population=120,
            cause_of_death_breakdown={"hunger": 100, "combat": 80},
        )

        md_text = SessionReporter.generate_markdown(summary)
        self.assertIn("Total Elapsed Ticks**: 5000", md_text)
        self.assertIn("Hunger**: 100 deaths", md_text)

        # Write reports
        SessionReporter.write_report_files(self.report_basepath, summary)
        self.assertTrue(os.path.exists(self.report_basepath + ".md"))
        self.assertTrue(os.path.exists(self.report_basepath + ".json"))

    @unittest.skipUnless(HAS_PYGAME, "pygame not installed")
    def test_graph_vector_plotting(self) -> None:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        pygame.init()
        
        surface = pygame.Surface((300, 200))
        font = pygame.font.SysFont("Arial", 12)
        
        graph = PopulationGraphRenderer(x=10, y=10, width=200, height=150)
        history = [
            {"total": 30, "bacteria": 20, "herbivore": 10},
            {"total": 50, "bacteria": 35, "herbivore": 15},
            {"total": 40, "bacteria": 30, "herbivore": 10},
        ]

        # Draw graph on surface
        graph.draw_graph(surface, font, history)
        # Verify it completes without crash
        self.assertTrue(True)
        pygame.quit()


if __name__ == "__main__":
    unittest.main()
