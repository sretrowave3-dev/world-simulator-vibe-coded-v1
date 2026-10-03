# ARCHITECTURE.md

# Echo Evolution Simulator
## Architecture Specification v1.0 (Frozen)

---

# Status

Architecture Version: **1.0**

Status: **FROZEN**

All future development must follow this document.

Breaking architectural changes require increasing the architecture version.

---

# Project Vision

The project is a professional Artificial Life (ALife) simulation platform capable of simulating:

- Biological evolution
- Neural learning
- Ecosystem dynamics
- Species formation
- Civilization growth
- Knowledge accumulation
- Long-term history
- AI-assisted reasoning using Gemini
- Real-time graphical visualization

The simulation is the source of truth.

Everything else observes or extends it.

---

# Core Philosophy

The architecture follows one principle:

> One responsibility.
> One owner.
> One direction of dependencies.

Every subsystem owns its own data.

No subsystem performs another subsystem's job.

---

# System Layers

Simulation Core

↓

World

↓

Entities

↓

AI

↓

Systems

↓

Gemini

↓

Analytics

↓

Renderer

↓

Save System

Each layer has clearly defined responsibilities.

---

# Folder Responsibilities

## core/

Owns:

- Simulation startup
- Main loop
- Scheduler
- Time
- Configuration

Files

- config.py
- scheduler.py
- world.py
- simulation.py

Nothing imports Renderer from here.

---

## entities/

Owns biological entities.

Includes

- Bacteria
- Plant
- Herbivore
- Predator
- Species

Entities only store state and expose behaviour.

They never perform rendering.

They never save themselves.

---

## ai/

Owns intelligence.

Includes

- Brain
- Genome
- Evolution
- Memory
- Pheromones

AI never performs rendering.

AI never performs saving.

AI never calls Gemini directly.

---

## systems/

Owns game logic.

Each system performs one job.

Movement

Digestion

Combat

Mutation

Learning

Reproduction

Perception

Species

Civilization

Knowledge

Gemini

Statistics

Etc.

Systems coordinate entities.

Entities never coordinate systems.

---

## world/

Owns environment.

Terrain

Food

Weather

Climate

Disasters

Resources

Only world modifies environmental state.

---

## gemini/

Owns every interaction with Gemini.

Includes

Gemini Engine

Prompt Builder

Response Validator

Knowledge

Caching

Statistics

Nothing outside this folder communicates directly with Gemini.

---

## renderer/

Responsible only for visualization.

Reads simulation state.

Never changes simulation.

Never changes entities.

Never changes AI.

---

## save/

Responsible only for serialization.

Loading

Saving

Compression

Autosave

Replay storage

---

## analytics/

Responsible for

Population statistics

Graphs

Reports

Timeline

Performance metrics

Historical analysis

---

## civilization/

Responsible for

History

Culture

Traditions

Technology

Diplomacy

Politics

Religion

Knowledge evolution

---

# Data Ownership

Every piece of information has exactly one owner.

Example

Position

Owner

Bacteria

Genome

Owner

Genome

Brain

Owner

Brain

Weather

Owner

Weather

Terrain

Owner

Terrain

Food

Owner

Food System

Knowledge

Owner

Knowledge System

Gemini Memory

Owner

Gemini Engine

Renderer owns nothing.

Renderer only reads.

---

# Dependency Rules

Allowed

core

↓

systems

↓

entities

↓

ai

↓

world

↓

gemini

↓

analytics

↓

renderer

↓

save

Forbidden

Renderer → AI

Renderer → Simulation

Gemini → Renderer

Brain → Save

Entity → Renderer

Entity → Save

Renderer → World mutation

---

# Simulation Update Order

Every frame follows this order.

Time

↓

Weather

↓

Disasters

↓

Terrain

↓

Plants

↓

Food

↓

Perception

↓

Brain

↓

Decision

↓

Movement

↓

Combat

↓

Digestion

↓

Learning

↓

Gemini

↓

Reproduction

↓

Mutation

↓

Species

↓

Civilization

↓

Knowledge

↓

Events

↓

Statistics

↓

Renderer Sync

↓

Autosave

This order is fixed.

---

# Entity Design

Entities contain only

State

Small helper methods

Validation

They never contain large systems.

Large behaviour belongs inside Systems.

---

# System Design

Systems are stateless processors whenever possible.

Example

Movement System

↓

Reads World

↓

Reads Entity

↓

Updates Position

The system owns the algorithm.

The entity owns the data.

---

# Gemini Architecture

Gemini is NOT a movement controller.

Gemini is a reasoning engine.

Gemini responsibilities

Planning

Knowledge

Civilization

Predictions

Scientific reasoning

Historical summaries

Strategy

Gemini never receives Python objects.

Gemini never receives internal implementation details.

---

# Gemini Input

Gemini always receives structured summaries.

Example

Energy

Food Nearby

Danger

History

Current Goal

Allowed Actions

Never

Python objects

NumPy arrays

Hidden states

Weights

Large JSON dumps

---

# Gemini Output

Gemini returns structured JSON only.

Example

Action

Reason

Confidence

Knowledge

Invalid responses are rejected.

---

# Renderer

Renderer only visualizes.

Renderer receives immutable snapshots.

Renderer cannot change simulation.

Renderer cannot modify entities.

---

# Visualization Goals

Real-time rendering.

Smooth movement.

Camera.

Zoom.

Minimap.

Heatmaps.

Overlays.

Organism inspector.

Timeline replay.

Gemini visualization.

---

# Civilization

Civilizations own

History

Knowledge

Culture

Traditions

Technology

Politics

Diplomacy

Religion

Knowledge is persistent.

---

# Memory

Memory exists on multiple levels.

Individual

Species

Civilization

World

Gemini only receives relevant memories.

Never the full history.

---

# Knowledge Objects

Knowledge is stored structurally.

Not raw text.

Each knowledge object contains

Type

Creator

Confidence

Timestamp

Conditions

Evidence

Usage count

---

# Save System

Save files are modular.

World

Species

Knowledge

Civilizations

Statistics

Gemini

Replay

Settings

Avoid giant monolithic saves.

---

# Event System

Everything important becomes an event.

Birth

Death

Mutation

Discovery

Migration

Disaster

Gemini Consultation

Technology

Extinction

Events are immutable.

---

# Performance Goals

Simulation

60+ UPS

Renderer

60–144 FPS

Gemini

Asynchronous

Autosave

Background thread

Logging

Background thread

Rendering never blocks simulation.

Gemini never blocks simulation.

---

# Coding Standards

Single Responsibility Principle.

Composition over inheritance.

No God classes.

No circular imports.

No duplicated state.

Meaningful naming.

Document public APIs.

---

# Source of Truth

Simulation owns reality.

Renderer displays reality.

Gemini advises reality.

Analytics measures reality.

Save preserves reality.

Nothing else defines reality.

---

# Long-Term Goals

Procedural worlds

Multiple biomes

Advanced weather

Large civilizations

Knowledge evolution

Scientific discovery

Social behaviour

Real-time visualization

Replay system

Plugin support

Multi-threaded simulation

Research platform

---

# Architecture Rule

If a feature does not fit this architecture,

the feature changes.

The architecture does not.