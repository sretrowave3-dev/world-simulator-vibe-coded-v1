"""
project/world/miracles.py

Advanced Celestial Miracles & Divine Interventions Engine.
Provides modular powers: Solar Eclipses, Meteor Stardust Showers, Torrential Rain,
Bountiful Harvests, Epiphany Waves, and Threat Purges.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from project.entities.entity import Entity, EntityType
from project.entities.human import Human
from project.entities.plant import Plant


@dataclass
class StardustDeposit:
    """A fallen celestial meteorite fragment rich in cosmic minerals and tech insights."""
    pos_x: float
    pos_y: float
    energy_value: float = 120.0
    iq_bonus: float = 25.0
    is_collected: bool = False


@dataclass
class WorldMiracleManager:
    """Coordinates celestial anomalies and world-altering divine interventions."""
    
    # Active Anomaly States
    eclipse_remaining_seconds: float = 0.0
    rainstorm_remaining_seconds: float = 0.0
    stardust_deposits: List[StardustDeposit] = field(default_factory=list)
    recent_miracle_events: List[str] = field(default_factory=list)

    @property
    def is_eclipse_active(self) -> bool:
        return self.eclipse_remaining_seconds > 0.0

    @property
    def is_rainstorm_active(self) -> bool:
        return self.rainstorm_remaining_seconds > 0.0

    def trigger_solar_eclipse(self, duration_seconds: float = 30.0) -> str:
        """Dims sunlight into an eerie Blood Moon / Solar Eclipse event."""
        self.eclipse_remaining_seconds = duration_seconds
        msg = f"🌘 [CELESTIAL ECLIPSE] The Sun is eclipsed! An eerie blood-crimson twilight envelops the biosphere for {duration_seconds:.0f}s!"
        print(f"\n{'='*75}\n{msg}\n{'='*75}\n")
        self.recent_miracle_events.append(msg)
        return msg

    def trigger_divine_rainstorm(self, duration_seconds: float = 40.0, soil_mgr: Optional[Any] = None) -> str:
        """Summons a torrential thunderstorm that replenishes all soils and waters."""
        self.rainstorm_remaining_seconds = duration_seconds
        if soil_mgr and hasattr(soil_mgr, "chunks"):
            for chunk in soil_mgr.chunks.values():
                for i in range(len(chunk.moisture)):
                    chunk.moisture[i] = min(1.0, chunk.moisture[i] + 0.5)
        msg = f"⛈️ [DIVINE RAINSTORM] Sacred torrential rain falls across the lands, nourishing all flora and replenishing water tables!"
        print(f"\n{'='*75}\n{msg}\n{'='*75}\n")
        self.recent_miracle_events.append(msg)
        return msg

    def trigger_meteor_stardust_shower(
        self,
        center_x: float,
        center_y: float,
        count: int = 6,
        radius: float = 250.0,
    ) -> str:
        """Spawns glowing stardust meteor deposits containing cosmic knowledge."""
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            dist = random.uniform(20.0, radius)
            mx = center_x + math.cos(angle) * dist
            my = center_y + math.sin(angle) * dist
            self.stardust_deposits.append(StardustDeposit(pos_x=mx, pos_y=my))
        msg = f"🌠 [METEOR SHOWER] {count} luminous celestial stardust fragments fell near ({center_x:.0f}, {center_y:.0f})!"
        print(f"\n{'='*75}\n{msg}\n{'='*75}\n")
        self.recent_miracle_events.append(msg)
        return msg

    def trigger_bountiful_harvest(
        self,
        entities_list: List[Entity],
        veg_mgr: Optional[Any] = None,
        center_x: float = 500.0,
        center_y: float = 500.0,
        radius: float = 300.0,
    ) -> str:
        """Accelerates all plant vitality and feeds nearby humans with bountiful sacred fruit."""
        fed_count = 0
        for e in entities_list:
            if not e.is_alive:
                continue
            if math.hypot(e.pos_x - center_x, e.pos_y - center_y) <= radius:
                if isinstance(e, Human) or e.entity_type == EntityType.HUMAN:
                    e.gain_energy(100.0)
                    e.quench_thirst(60.0)
                    e.custom_data["dopamine"] = 1.0
                    e.custom_data["stress"] = 0.0
                    fed_count += 1
                elif isinstance(e, Plant) or e.entity_type == EntityType.PLANT:
                    e.heal(40.0)
                    e.gain_energy(50.0)

        msg = f"🌾 [BOUNTIFUL HARVEST] Divine fertility revitalized flora and fed {fed_count} organisms with sacred fruit!"
        print(f"\n{'='*75}\n{msg}\n{'='*75}\n")
        self.recent_miracle_events.append(msg)
        return msg

    def trigger_epiphany_wave(self, entities_list: List[Entity], tick: int = 0) -> str:
        """Telepathically broadcasts cosmic enlightenment to all humans."""
        blessed_count = 0
        for e in entities_list:
            if e.is_alive and (isinstance(e, Human) or e.entity_type == EntityType.HUMAN):
                e.intelligence_quotient += 15.0
                e.custom_data["consciousness_level"] = min(1.0, e.custom_data.get("consciousness_level", 0.0) + 0.25)
                e.custom_data["dopamine"] = 1.0
                e.custom_data["stress"] = 0.0
                blessed_count += 1
                if hasattr(e, "thought_logger") and e.thought_logger:
                    e.thought_logger.log_thought(
                        tick=tick,
                        human_id=e.entity_id,
                        human_name=getattr(e, "name", f"Human_{e.entity_id}"),
                        thought="🌟 [DIVINE EPIPHANY] A radiant wave of celestial cosmic intellect has illuminated our minds!",
                        emotion="TRANSCENDENCE",
                        iq_at_time=e.intelligence_quotient,
                        god_affinity=e.custom_data.get("god_affinity", 50.0),
                    )

        msg = f"🧠 [EPIPHANY WAVE] Cosmic inspiration illuminated {blessed_count} human minds with transcendental wisdom!"
        print(f"\n{'='*75}\n{msg}\n{'='*75}\n")
        self.recent_miracle_events.append(msg)
        return msg

    def trigger_purge_threats(
        self,
        entities_list: List[Entity],
        center_x: float = 500.0,
        center_y: float = 500.0,
        radius: float = 400.0,
    ) -> str:
        """Radiates a divine pacification wave that drives hostile carnivores into retreat."""
        calmed_count = 0
        for e in entities_list:
            if e.is_alive and e.entity_type in (EntityType.PREDATOR, EntityType.CARNIVORE):
                dist = math.hypot(e.pos_x - center_x, e.pos_y - center_y)
                if dist <= radius:
                    e.custom_data["fear"] = 1.0
                    e.custom_data["ambush_mode"] = False
                    # Push predator outward
                    angle = math.atan2(e.pos_y - center_y, e.pos_x - center_x)
                    e.pos_x += math.cos(angle) * 80.0
                    e.pos_y += math.sin(angle) * 80.0
                    calmed_count += 1

        msg = f"🛡️ [HOLY SANCTUARY WAVE] Divine radiance repelled {calmed_count} predatory threats from the settlement!"
        print(f"\n{'='*75}\n{msg}\n{'='*75}\n")
        self.recent_miracle_events.append(msg)
        return msg

    def update(self, dt: float, entities_list: List[Entity]) -> None:
        """Advances active anomaly timers and checks stardust collections."""
        if self.eclipse_remaining_seconds > 0.0:
            self.eclipse_remaining_seconds = max(0.0, self.eclipse_remaining_seconds - dt)

        if self.rainstorm_remaining_seconds > 0.0:
            self.rainstorm_remaining_seconds = max(0.0, self.rainstorm_remaining_seconds - dt)

        # Check stardust meteorite pickups by humans
        for deposit in self.stardust_deposits:
            if deposit.is_collected:
                continue
            for e in entities_list:
                if e.is_alive and (isinstance(e, Human) or e.entity_type == EntityType.HUMAN):
                    if math.hypot(e.pos_x - deposit.pos_x, e.pos_y - deposit.pos_y) <= 15.0:
                        deposit.is_collected = True
                        e.gain_energy(deposit.energy_value)
                        e.intelligence_quotient += deposit.iq_bonus
                        e.custom_data["dopamine"] = 1.0
                        print(f"✨ {getattr(e, 'name', e.entity_id)} absorbed celestial stardust (+{deposit.iq_bonus:.0f} IQ, +{deposit.energy_value:.0f} Energy)!")
                        break

        # Remove collected deposits
        self.stardust_deposits = [d for d in self.stardust_deposits if not d.is_collected]


# Global singleton miracle manager
world_miracles_mgr = WorldMiracleManager()
