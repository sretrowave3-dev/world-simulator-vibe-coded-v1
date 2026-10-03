"""
project/systems/__init__.py

Stateless Simulation System modules for the Echo Evolution Simulator.
"""

from project.systems.time_system import TimeSystem
from project.systems.weather_system import WeatherSystem
from project.systems.weather_sync_system import WeatherSyncSystem
from project.systems.disaster_system import DisasterSystem
from project.systems.soil_system import SoilSystem
from project.systems.water_system import WaterSystem
from project.systems.vegetation_system import VegetationSystem
from project.systems.resource_system import ResourceSystem
from project.systems.food_system import FoodSystem
from project.systems.perception_system import PerceptionSystem
from project.systems.decision_system import DecisionSystem
from project.systems.pheromone_system import PheromoneSystem
from project.systems.movement_system import MovementSystem
from project.systems.combat_system import CombatSystem
from project.systems.digestion_system import DigestionSystem
from project.systems.aging_system import AgingSystem
from project.systems.death_system import DeathSystem
from project.systems.reproduction_system import ReproductionSystem
from project.systems.birth_system import BirthSystem
from project.systems.mutation_system import MutationSystem
from project.systems.learning_system import LearningSystem
from project.systems.gemini_system import GeminiSystem
from project.systems.social_system import SocialSystem
from project.systems.civilization_system import CivilizationSystem
from project.systems.knowledge_system import KnowledgeSystem
from project.systems.event_system import EventSystem
from project.systems.statistics_system import StatisticsSystem
from project.systems.render_sync_system import RenderSyncSystem
from project.systems.save_system import SaveSystem
from project.systems.security_system import SecuritySystem

__all__ = [
    "TimeSystem",
    "WeatherSystem",
    "WeatherSyncSystem",
    "DisasterSystem",
    "SoilSystem",
    "WaterSystem",
    "VegetationSystem",
    "ResourceSystem",
    "FoodSystem",
    "PerceptionSystem",
    "DecisionSystem",
    "PheromoneSystem",
    "MovementSystem",
    "CombatSystem",
    "DigestionSystem",
    "AgingSystem",
    "DeathSystem",
    "ReproductionSystem",
    "BirthSystem",
    "MutationSystem",
    "LearningSystem",
    "GeminiSystem",
    "SocialSystem",
    "CivilizationSystem",
    "KnowledgeSystem",
    "EventSystem",
    "StatisticsSystem",
    "RenderSyncSystem",
    "SaveSystem",
    "SecuritySystem",
]
