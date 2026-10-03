"""
project/analytics/reports.py

Session Run Reporting engine generating Markdown and JSON analytical summaries.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Dict, List, Any


@dataclass
class SessionSummary:
    total_ticks: int = 0
    total_duration_sec: float = 0.0
    birth_count: int = 0
    death_count: int = 0
    extinction_count: int = 0
    average_lifespan_ticks: float = 0.0
    peak_concurrent_population: int = 0
    cause_of_death_breakdown: Dict[str, int] = field(default_factory=dict)
    species_demographics: Dict[str, Dict[str, int]] = field(default_factory=dict)


class SessionReporter:
    """Generates post-run summary reports."""

    @staticmethod
    def generate_markdown(summary: SessionSummary) -> str:
        """Formulates a clean markdown dashboard summarizing the simulation run."""
        lines = [
            "# Echo Evolution Simulation Report",
            "",
            "## 1. Run Telemetry",
            f"- **Total Elapsed Ticks**: {summary.total_ticks}",
            f"- **Total Simulated Time**: {summary.total_duration_sec:.1f} seconds",
            f"- **Peak Concurrent Population**: {summary.peak_concurrent_population}",
            "",
            "## 2. Demographic Vitality",
            f"- **Total Births**: {summary.birth_count}",
            f"- **Total Deaths**: {summary.death_count}",
            f"- **Extinct Species Count**: {summary.extinction_count}",
            f"- **Mean Organism Lifespan**: {summary.average_lifespan_ticks:.1f} ticks",
            "",
            "## 3. Mortality Breakdown",
        ]

        if not summary.cause_of_death_breakdown:
            lines.append("- *No recorded deaths during this session.*")
        else:
            for cause, count in sorted(summary.cause_of_death_breakdown.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"- **{cause.capitalize()}**: {count} deaths")

        lines.append("")
        lines.append("## 4. Species Census Summary")
        if not summary.species_demographics:
            lines.append("- *No species recorded.*")
        else:
            for sp_id, data in sorted(summary.species_demographics.items()):
                lines.append(
                    f"- **{sp_id}**: Births={data.get('births', 0)}, Deaths={data.get('deaths', 0)}, Peak={data.get('peak', 0)}"
                )

        return "\n".join(lines)

    @staticmethod
    def write_report_files(filepath_base: str, summary: SessionSummary) -> None:
        """Writes both markdown and JSON summaries to the disk."""
        # 1. Write Markdown
        md_text = SessionReporter.generate_markdown(summary)
        with open(filepath_base + ".md", "w", encoding="utf-8") as f:
            f.write(md_text)

        # 2. Write JSON
        json_data = {
            "ticks": summary.total_ticks,
            "duration": summary.total_duration_sec,
            "births": summary.birth_count,
            "deaths": summary.death_count,
            "extinctions": summary.extinction_count,
            "avg_lifespan": summary.average_lifespan_ticks,
            "peak_population": summary.peak_concurrent_population,
            "mortality": summary.cause_of_death_breakdown,
            "species": summary.species_demographics,
        }
        with open(filepath_base + ".json", "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=4)
