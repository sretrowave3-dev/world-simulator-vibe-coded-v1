"""
project/entities/__init__.py

Biological Entity models for the Echo Evolution Simulator.
"""

from project.entities.entity import Entity, EntityType, HealthState
from project.entities.species import Species, SpeciesRegistry
from project.entities.bacteria import Bacteria
from project.entities.plant import Plant
from project.entities.herbivore import Herbivore
from project.entities.carnivore import Carnivore
from project.entities.predator import Predator
from project.entities.omnivore import Omnivore
from project.entities.decomposer import Decomposer
from project.entities.human import Human

__all__ = [
    "Entity",
    "EntityType",
    "HealthState",
    "Species",
    "SpeciesRegistry",
    "Bacteria",
    "Plant",
    "Herbivore",
    "Carnivore",
    "Predator",
    "Omnivore",
    "Decomposer",
    "Human",
]
