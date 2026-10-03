"""
core/config.py

Central Configuration Registry for the Artificial Life (ALife) Research Platform.

Architectural Guarantees:
1. Single Source of Truth: Centralized registry pattern via `ConfigRegistry`.
2. Immutability: Deeply frozen dataclasses prevent runtime side-effects.
3. Zero Hardcoding: Completely parameterizes physics, AI, rendering, terrain, biomes, 
   Gemini reasoning layers, and simulation constraints.
4. Extensibility: Clean namespace separation allowing infinite research expansion.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Tuple, Optional


# =============================================================================
# ENUMS & CONSTANTS
# =============================================================================

class WorldShape(Enum):
    RECTANGLE = auto()
    TORUS = auto()
    SPHERE = auto()


class ActivationFunction(Enum):
    RELU = auto()
    TANH = auto()
    SIGMOID = auto()
    LEAKY_RELU = auto()


class RendererType(Enum):
    HEADLESS = auto()
    PYGAME = auto()
    OPENGL = auto()


class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class PathfindingAlgorithm(Enum):
    A_STAR = auto()
    FLOW_FIELD = auto()
    NAV_MESH = auto()
    DIJKSTRA = auto()


ColorRGBA = Tuple[int, int, int, int]


# =============================================================================
# 1. CORE APPLICATION & SIMULATION
# =============================================================================

@dataclass(frozen=True)
class AppConfig:
    name: str = "ALife Research Platform"
    version: str = "2.0.0"
    author: str = "Lead Principal Software Architect"
    architecture_version: str = "v3.0"
    build_number: int = 2048
    debug_mode: bool = False


@dataclass(frozen=True)
class SimulationConfig:
    target_ups: int = 60
    max_years: int = 100_000
    start_paused: bool = False
    time_scale: float = 1.0
    max_simulation_speed: float = 10.0
    auto_spawn_initial_entities: bool = True
    thread_count: int = 8


@dataclass(frozen=True)
class PerformanceConfig:
    target_fps: int = 60
    target_ups: int = 60
    chunk_size: int = 64
    spatial_hash_cell_size: int = 32
    max_worker_threads: int = 16
    enable_gpu_acceleration: bool = False
    enable_parallel_systems: bool = True


@dataclass(frozen=True)
class RandomConfig:
    seed: int = 42
    deterministic_mode: bool = True
    enable_random_mutations: bool = True
    enable_random_weather: bool = True
    enable_random_disasters: bool = True


@dataclass(frozen=True)
class TimeConfig:
    ticks_per_second: int = 60
    seconds_per_day: int = 120
    days_per_year: int = 365
    calendar_enabled: bool = True
    season_count: int = 4
    epoch_start_year: int = 0


# =============================================================================
# 2. PHYSICAL & ENVIRONMENTAL WORLD CONFIGURATIONS
# =============================================================================

@dataclass(frozen=True)
class WorldConfig:
    width: int = 4096
    height: int = 4096
    shape: WorldShape = WorldShape.TORUS
    infinite_world: bool = False
    wrapping_enabled: bool = True
    sea_level: float = 0.35


@dataclass(frozen=True)
class ChunkConfig:
    chunk_width: int = 64
    chunk_height: int = 64
    unload_distance_chunks: int = 4
    active_radius_chunks: int = 2


@dataclass(frozen=True)
class StreamingConfig:
    enable_asynchronous_loading: bool = True
    max_chunks_loaded_per_frame: int = 4
    disk_cache_enabled: bool = True


@dataclass(frozen=True)
class LODConfig:
    enable_lod: bool = True
    lod_distance_high: float = 500.0
    lod_distance_medium: float = 1500.0
    lod_distance_low: float = 3000.0


@dataclass(frozen=True)
class BiomeConfig:
    biome_count: int = 12
    biome_transition_smoothness: float = 0.15
    cave_frequency: float = 0.05
    beach_width: float = 12.0
    cliff_height_threshold: float = 0.82
    lava_regions_frequency: float = 0.02
    ice_regions_frequency: float = 0.08
    fertility_noise_scale: float = 0.01
    elevation_noise_scale: float = 0.005
    resource_noise_scale: float = 0.02


@dataclass(frozen=True)
class ClimateConfig:
    global_temperature_offset: float = 0.0
    global_humidity_offset: float = 0.0
    greenhouse_effect_modifier: float = 1.0
    solar_radiation_index: float = 1.0


@dataclass(frozen=True)
class RiverConfig:
    river_count: int = 16
    min_river_length: int = 100
    river_meander_factor: float = 0.4
    spring_elevation_threshold: float = 0.75


@dataclass(frozen=True)
class TerrainConfig:
    biome_scale: float = 0.005
    mountain_frequency: float = 0.02
    forest_density: float = 0.65
    ocean_size_ratio: float = 0.30
    swamp_frequency: float = 0.08
    temperature_noise_octaves: int = 4
    moisture_noise_octaves: int = 4


@dataclass(frozen=True)
class WeatherConfig:
    base_rain_probability: float = 0.05
    cloud_cover_ratio: float = 0.40
    base_humidity: float = 0.50
    wind_vector_change_rate: float = 0.01
    base_temperature_celsius: float = 22.0
    season_length_ticks: int = 21600
    snow_threshold_temperature: float = 0.0
    fog_density_max: float = 0.85


@dataclass(frozen=True)
class DisasterConfig:
    drought_probability: float = 0.0001
    meteor_probability: float = 0.00001
    wildfire_probability: float = 0.0005
    flood_probability: float = 0.0002
    storm_probability: float = 0.001
    earthquake_probability: float = 0.00005
    volcano_probability: float = 0.00001
    pandemic_probability: float = 0.00005
    min_duration_ticks: int = 100
    max_duration_ticks: int = 1000
    min_intensity: float = 0.1
    max_intensity: float = 1.0
    global_cooldown_ticks: int = 5000


@dataclass(frozen=True)
class PhysicsConfig:
    friction: float = 0.1
    acceleration_modifier: float = 1.0
    gravity: float = 9.81
    elasticity: float = 0.5
    collision_iterations: int = 4
    max_velocity: float = 15.0


@dataclass(frozen=True)
class NavigationConfig:
    algorithm: PathfindingAlgorithm = PathfindingAlgorithm.A_STAR
    grid_cell_size: int = 16
    obstacle_cost_multiplier: float = 5.0
    enable_steering_avoidance: bool = True
    max_pathfinding_nodes_searched: int = 2000


# =============================================================================
# 3. ORGANISMS, ECOLOGY & BIOLOGY
# =============================================================================

@dataclass(frozen=True)
class ResourceConfig:
    fruit_spawn_rate: float = 0.2
    grass_regrowth_rate: float = 0.5
    meat_decay_rate: float = 0.05
    wood_node_density: float = 0.1
    stone_node_density: float = 0.08
    minerals_node_density: float = 0.03
    water_purity_base: float = 1.0
    medicine_plant_rarity: float = 0.01
    rare_resources_spawn_chance: float = 0.001


@dataclass(frozen=True)
class FoodConfig:
    spawn_rate_per_tick: int = 10
    nutrition_value_base: float = 25.0
    decay_rate_per_tick: float = 0.01
    poison_chance: float = 0.03
    max_global_food: int = 5000
    respawn_interval_ticks: int = 30


@dataclass(frozen=True)
class PlantConfig:
    base_growth_rate: float = 0.05
    reproduction_threshold_energy: float = 100.0
    seed_spread_radius: float = 15.0
    max_age_ticks: int = 12000
    base_energy_capacity: float = 150.0
    root_competition_radius: float = 5.0


@dataclass(frozen=True)
class SensorConfig:
    vision_angle_degrees: float = 120.0
    smell_sensitivity: float = 0.8
    hearing_radius: float = 150.0
    touch_distance: float = 2.0
    enable_predictive_sensing: bool = True


@dataclass(frozen=True)
class EntityConfig:
    max_population: int = 10000
    spawn_radius: float = 50.0
    enable_collision_physics: bool = True
    base_vision_range: float = 40.0
    physics_drag: float = 0.05


@dataclass(frozen=True)
class BacteriaConfig:
    starting_energy: float = 50.0
    maximum_energy: float = 200.0
    hunger_threshold: float = 30.0
    digestion_efficiency: float = 0.85
    max_age_ticks: int = 3000
    starvation_damage_per_tick: float = 1.0
    reproduction_energy_cost: float = 60.0
    base_movement_cost: float = 0.1
    vision_radius: float = 20.0


@dataclass(frozen=True)
class HerbivoreConfig:
    starting_energy: float = 150.0
    maximum_energy: float = 500.0
    hunger_threshold: float = 100.0
    digestion_efficiency: float = 0.90
    max_age_ticks: int = 15000
    reproduction_cost: float = 120.0
    base_speed: float = 2.5
    vision_radius: float = 80.0


@dataclass(frozen=True)
class PredatorConfig:
    starting_energy: float = 250.0
    maximum_energy: float = 800.0
    hunger_threshold: float = 200.0
    digestion_efficiency: float = 0.75
    max_age_ticks: int = 18000
    reproduction_cost: float = 200.0
    base_speed: float = 3.2
    vision_radius: float = 120.0
    attack_damage: float = 35.0


@dataclass(frozen=True)
class SpeciesConfig:
    speciation_threshold_distance: float = 0.25
    extinction_population_limit: int = 0
    merge_similarity_threshold: float = 0.05
    naming_prefix_length: int = 4
    procedural_color_variance: float = 0.15


@dataclass(frozen=True)
class GenomeConfig:
    mutation_rate: float = 0.02
    mutation_magnitude: float = 0.1
    trait_count: int = 64
    inheritance_blend_factor: float = 0.5
    crossover_points: int = 2
    enable_gene_dominance: bool = True
    min_gene_value: float = -1.0
    max_gene_value: float = 1.0


@dataclass(frozen=True)
class EvolutionConfig:
    selection_pressure_modifier: float = 1.2
    fitness_decay_rate: float = 0.001
    adaptation_rate: float = 0.05
    enable_natural_selection: bool = True


@dataclass(frozen=True)
class BrainConfig:
    input_count: int = 24
    hidden_layer_sizes: Tuple[int, ...] = (32, 16)
    activation_function: ActivationFunction = ActivationFunction.TANH
    learning_rate: float = 0.01
    enable_hebbian_learning: bool = True
    reward_signal_discount: float = 0.95
    working_memory_cells: int = 4
    output_count: int = 8


@dataclass(frozen=True)
class MemoryConfig:
    short_term_capacity: int = 100
    long_term_capacity: int = 1000
    forgetting_rate_per_tick: float = 0.0005
    memory_compression_ratio: float = 0.20


@dataclass(frozen=True)
class PheromoneConfig:
    food_decay_rate: float = 0.05
    danger_decay_rate: float = 0.10
    mate_decay_rate: float = 0.02
    territory_decay_rate: float = 0.005
    diffusion_coefficient: float = 0.15


@dataclass(frozen=True)
class SocialConfig:
    max_group_size: int = 50
    leadership_election_interval_ticks: int = 600
    cooperation_utility_bonus: float = 0.15
    aggression_threshold: float = 0.70
    communication_radius: float = 30.0
    reputation_decay_rate: float = 0.01


@dataclass(frozen=True)
class CivilizationConfig:
    max_history_events_stored: int = 5000
    tech_tree_nodes: int = 32
    cultural_drift_rate: float = 0.005
    political_alignment_variance: float = 0.1
    religion_creation_threshold_population: int = 100
    tradition_retention_probability: float = 0.95


@dataclass(frozen=True)
class KnowledgeConfig:
    knowledge_lifetime_ticks: int = 50000
    confidence_decay_rate: float = 0.001
    verification_threshold: float = 0.75
    vertical_inheritance_efficiency: float = 0.80
    horizontal_sharing_radius: float = 15.0


# =============================================================================
# 4. GEMINI REASONING LAYER
# =============================================================================

@dataclass(frozen=True)
class GeminiRuntimeConfig:
    api_key_env_var: str = "GEMINI_API_KEY"
    model_name: str = "gemini-2.5-flash"
    temperature: float = 0.2
    top_p: float = 0.95
    top_k: int = 40
    seed: Optional[int] = 42
    timeout_seconds: float = 10.0
    retry_count: int = 3


@dataclass(frozen=True)
class GeminiReasoningConfig:
    enable_individual_reasoning: bool = False
    enable_colony_reasoning: bool = True
    enable_species_reasoning: bool = True
    enable_civilization_reasoning: bool = True
    enable_world_reasoning: bool = True
    reflection_interval_ticks: int = 1200
    research_consultation_interval_ticks: int = 3600
    prediction_horizon_ticks: int = 5000
    planning_depth_steps: int = 5


@dataclass(frozen=True)
class GeminiMemoryConfig:
    max_stored_memories: int = 500
    retrieval_count_per_prompt: int = 10
    memory_decay_rate: float = 0.01
    enable_auto_summarization: bool = True
    compression_ratio: float = 0.25
    importance_threshold: float = 0.6


@dataclass(frozen=True)
class GeminiPromptConfig:
    prompt_version: str = "v2.0"
    enforce_strict_json_schema: bool = True
    max_context_window_tokens: int = 8192
    formatting_strictness: str = "EXACT_JSON"
    allowed_action_verbs: Tuple[str, ...] = ("MIGRATE", "RESEARCH", "DIPLOMACY", "CULL", "ADAPT", "BUILD")


@dataclass(frozen=True)
class GeminiKnowledgeConfig:
    knowledge_lifetime_ticks: int = 50000
    trust_system_decay: float = 0.05
    verification_threshold: float = 0.80
    confidence_decay: float = 0.001
    peer_sharing_enabled: bool = True
    persistent_knowledge_storage: bool = True


@dataclass(frozen=True)
class GeminiAggregateConfig:
    runtime: GeminiRuntimeConfig = field(default_factory=GeminiRuntimeConfig)
    reasoning: GeminiReasoningConfig = field(default_factory=GeminiReasoningConfig)
    memory: GeminiMemoryConfig = field(default_factory=GeminiMemoryConfig)
    prompt: GeminiPromptConfig = field(default_factory=GeminiPromptConfig)
    knowledge: GeminiKnowledgeConfig = field(default_factory=GeminiKnowledgeConfig)


# =============================================================================
# 5. RENDERER & VISUALIZATION
# =============================================================================

@dataclass(frozen=True)
class WindowConfig:
    window_width: int = 1920
    window_height: int = 1080
    fullscreen: bool = False
    resizable: bool = True
    title: str = "ALife Research Simulation"


@dataclass(frozen=True)
class GraphicsConfig:
    enable_vsync: bool = True
    renderer_backend: RendererType = RendererType.PYGAME
    target_resolution: Tuple[int, int] = (1920, 1080)
    anti_aliasing_samples: int = 4


@dataclass(frozen=True)
class ParticleConfig:
    enable_particles: bool = True
    max_active_particles: int = 5000
    particle_lifetime_scale: float = 1.0


@dataclass(frozen=True)
class AnimationConfig:
    enable_interpolation: bool = True
    sprite_animation_speed: float = 1.0


@dataclass(frozen=True)
class LightingConfig:
    enable_lighting: bool = True
    day_night_cycle_darkness: float = 0.7
    ambient_light_color: ColorRGBA = (255, 255, 255, 255)


@dataclass(frozen=True)
class PostProcessingConfig:
    enable_bloom: bool = False
    enable_vignette: bool = True
    color_temperature_shift: float = 0.0


@dataclass(frozen=True)
class CameraConfig:
    min_zoom: float = 0.1
    max_zoom: float = 10.0
    pan_speed: float = 15.0
    edge_scrolling_enabled: bool = True
    zoom_speed: float = 0.1
    rotation_enabled: bool = False
    camera_shake_decay: float = 0.9
    follow_speed: float = 0.15
    smoothing_factor: float = 0.1
    free_camera_mode: bool = True
    minimap_size_pixels: Tuple[int, int] = (250, 250)


@dataclass(frozen=True)
class UIConfig:
    enable_hud: bool = True
    enable_inspector: bool = True
    enable_analytics_graphs: bool = True
    enable_timeline_controls: bool = True
    enable_dev_console: bool = True
    enable_debug_overlays: bool = True


@dataclass(frozen=True)
class RenderAggregateConfig:
    window: WindowConfig = field(default_factory=WindowConfig)
    graphics: GraphicsConfig = field(default_factory=GraphicsConfig)
    particles: ParticleConfig = field(default_factory=ParticleConfig)
    animation: AnimationConfig = field(default_factory=AnimationConfig)
    lighting: LightingConfig = field(default_factory=LightingConfig)
    post_processing: PostProcessingConfig = field(default_factory=PostProcessingConfig)
    camera: CameraConfig = field(default_factory=CameraConfig)
    ui: UIConfig = field(default_factory=UIConfig)


# =============================================================================
# 6. PALETTES & COLOR REGISTRY
# =============================================================================

@dataclass(frozen=True)
class TerrainColors:
    water: ColorRGBA = (52, 152, 219, 255)
    forest: ColorRGBA = (20, 90, 50, 255)
    mountain: ColorRGBA = (127, 140, 141, 255)
    desert: ColorRGBA = (241, 196, 15, 255)
    beach: ColorRGBA = (243, 229, 171, 255)
    ice: ColorRGBA = (236, 240, 241, 255)
    lava: ColorRGBA = (192, 57, 43, 255)


@dataclass(frozen=True)
class EntityColors:
    food: ColorRGBA = (46, 204, 113, 255)
    plants: ColorRGBA = (39, 174, 96, 255)
    species_default: ColorRGBA = (155, 89, 182, 255)
    predators: ColorRGBA = (231, 76, 60, 255)
    herbivores: ColorRGBA = (52, 152, 219, 255)
    bacteria: ColorRGBA = (26, 188, 156, 255)
    leaders: ColorRGBA = (241, 196, 15, 255)


@dataclass(frozen=True)
class UIColors:
    background: ColorRGBA = (44, 62, 80, 200)
    text: ColorRGBA = (236, 240, 241, 255)
    accent: ColorRGBA = (41, 128, 185, 255)
    border: ColorRGBA = (127, 140, 141, 255)


@dataclass(frozen=True)
class HeatmapColors:
    cold: ColorRGBA = (41, 128, 185, 128)
    hot: ColorRGBA = (192, 57, 43, 128)


@dataclass(frozen=True)
class DebugColors:
    bounding_box: ColorRGBA = (0, 255, 0, 255)
    velocity_vector: ColorRGBA = (255, 255, 0, 255)
    vision_cone: ColorRGBA = (255, 255, 255, 30)


@dataclass(frozen=True)
class GeminiColors:
    accent: ColorRGBA = (142, 68, 173, 255)
    query_pulse: ColorRGBA = (155, 89, 182, 180)


@dataclass(frozen=True)
class ColorConfig:
    terrain: TerrainColors = field(default_factory=TerrainColors)
    entity: EntityColors = field(default_factory=EntityColors)
    ui: UIColors = field(default_factory=UIColors)
    heatmap: HeatmapColors = field(default_factory=HeatmapColors)
    debug: DebugColors = field(default_factory=DebugColors)
    gemini: GeminiColors = field(default_factory=GeminiColors)


# =============================================================================
# 7. ANALYTICS, SAVING, REPLAY & LOGGING
# =============================================================================

@dataclass(frozen=True)
class AnalyticsMetricsConfig:
    track_performance_metrics: bool = True
    track_evolution_metrics: bool = True
    track_knowledge_metrics: bool = True
    track_civilization_metrics: bool = True
    track_gemini_metrics: bool = True


@dataclass(frozen=True)
class AnalyticsConfig:
    enable_realtime_graphs: bool = True
    max_history_data_points: int = 10000
    sampling_interval_ticks: int = 10
    enable_timeline_recording: bool = True
    metrics: AnalyticsMetricsConfig = field(default_factory=AnalyticsMetricsConfig)


@dataclass(frozen=True)
class LoggingConfig:
    enable_console_logging: bool = True
    enable_file_logging: bool = True
    log_file_path: str = "logs/simulation.log"
    max_log_file_size_bytes: int = 10_485_760
    log_file_backup_count: int = 5
    global_log_level: LogLevel = LogLevel.INFO
    log_performance_metrics: bool = True
    log_gemini_interactions: bool = True
    log_exceptions: bool = True


@dataclass(frozen=True)
class SaveConfig:
    enable_autosave: bool = True
    autosave_interval_ticks: int = 6000
    enable_zlib_compression: bool = True
    max_backup_files: int = 5
    schema_version: str = "2.0.0"
    enable_checksum_integrity_checks: bool = True
    save_directory: str = "saves/"


@dataclass(frozen=True)
class ReplayConfig:
    enable_replay_recording: bool = True
    keyframe_interval_ticks: int = 300
    compression_level: int = 6
    enable_delta_frames: bool = True
    recording_fps: int = 30
    maximum_replay_length_ticks: int = 216000
    default_playback_speed: float = 1.0


@dataclass(frozen=True)
class DebugConfig:
    show_collision_boxes: bool = False
    show_brain_network_overlay: bool = False
    show_genome_inspector: bool = False
    show_fps_counter: bool = True
    show_ups_counter: bool = True
    show_memory_usage: bool = True
    show_spatial_heatmaps: bool = False
    show_entity_ids: bool = False
    show_pathfinding_vectors: bool = False
    show_vision_cones: bool = False
    dump_raw_gemini_logs: bool = False


# =============================================================================
# 8. RESEARCH, SYSTEM INFRASTRUCTURE & EXTENSIONS
# =============================================================================

@dataclass(frozen=True)
class SoundConfig:
    enable_sound: bool = False
    master_volume: float = 0.8
    effects_volume: float = 1.0


@dataclass(frozen=True)
class InputConfig:
    key_bindings_map: Dict[str, str] = field(default_factory=lambda: {
        "PAUSE": "SPACE",
        "SPEED_UP": "EQUALS",
        "SLOW_DOWN": "MINUS"
    })


@dataclass(frozen=True)
class ScreenshotConfig:
    output_directory: str = "screenshots/"
    format: str = "PNG"


@dataclass(frozen=True)
class ProfilerConfig:
    enable_cpu_profiling: bool = False
    enable_memory_profiling: bool = False


@dataclass(frozen=True)
class PluginConfig:
    enable_plugins: bool = True
    plugins_directory: str = "plugins/"


@dataclass(frozen=True)
class NetworkConfig:
    enable_networking: bool = False
    port: int = 8080


@dataclass(frozen=True)
class ModdingConfig:
    enable_modding: bool = False


@dataclass(frozen=True)
class ResearchConfig:
    experiment_id: str = "EXP-ALIFE-001"
    data_export_format: str = "PARQUET"


@dataclass(frozen=True)
class ExperimentConfig:
    control_group_seed: int = 101


@dataclass(frozen=True)
class BenchmarkConfig:
    benchmark_duration_ticks: int = 10000


@dataclass(frozen=True)
class TestingConfig:
    is_headless_test_run: bool = False


@dataclass(frozen=True)
class SecurityConfig:
    sandbox_plugin_execution: bool = True


@dataclass(frozen=True)
class ScriptingConfig:
    enable_python_console: bool = False


@dataclass(frozen=True)
class FeatureFlags:
    enable_renderer: bool = True
    enable_gemini: bool = True
    enable_predators: bool = True
    enable_plants: bool = True
    enable_civilization: bool = True
    enable_knowledge: bool = True
    enable_replay: bool = True
    enable_weather: bool = True
    enable_disasters: bool = True
    enable_multithreading: bool = True
    enable_gpu: bool = False
    enable_sound: bool = False
    enable_ui: bool = True
    enable_heatmaps: bool = True
    enable_profiler: bool = False


# =============================================================================
# CENTRAL CONFIGURATION REGISTRY
# =============================================================================

@dataclass(frozen=True)
class ConfigRegistry:
    """
    Unified immutable configuration registry object containing every operational parameter.
    
    Access Pattern:
        from core.config import CONFIG
        
        speed = CONFIG.physics.max_velocity
        model = CONFIG.gemini.runtime.model_name
        color = CONFIG.colors.terrain.water
    """
    app: AppConfig = field(default_factory=AppConfig)
    simulation: SimulationConfig = field(default_factory=SimulationConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    random: RandomConfig = field(default_factory=RandomConfig)
    time: TimeConfig = field(default_factory=TimeConfig)
    
    world: WorldConfig = field(default_factory=WorldConfig)
    chunk: ChunkConfig = field(default_factory=ChunkConfig)
    streaming: StreamingConfig = field(default_factory=StreamingConfig)
    lod: LODConfig = field(default_factory=LODConfig)
    biome: BiomeConfig = field(default_factory=BiomeConfig)
    climate: ClimateConfig = field(default_factory=ClimateConfig)
    river: RiverConfig = field(default_factory=RiverConfig)
    terrain: TerrainConfig = field(default_factory=TerrainConfig)
    weather: WeatherConfig = field(default_factory=WeatherConfig)
    disaster: DisasterConfig = field(default_factory=DisasterConfig)
    physics: PhysicsConfig = field(default_factory=PhysicsConfig)
    navigation: NavigationConfig = field(default_factory=NavigationConfig)
    
    resource: ResourceConfig = field(default_factory=ResourceConfig)
    food: FoodConfig = field(default_factory=FoodConfig)
    plant: PlantConfig = field(default_factory=PlantConfig)
    sensor: SensorConfig = field(default_factory=SensorConfig)
    entity: EntityConfig = field(default_factory=EntityConfig)
    bacteria: BacteriaConfig = field(default_factory=BacteriaConfig)
    herbivore: HerbivoreConfig = field(default_factory=HerbivoreConfig)
    predator: PredatorConfig = field(default_factory=PredatorConfig)
    species: SpeciesConfig = field(default_factory=SpeciesConfig)
    genome: GenomeConfig = field(default_factory=GenomeConfig)
    evolution: EvolutionConfig = field(default_factory=EvolutionConfig)
    brain: BrainConfig = field(default_factory=BrainConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    pheromone: PheromoneConfig = field(default_factory=PheromoneConfig)
    social: SocialConfig = field(default_factory=SocialConfig)
    civilization: CivilizationConfig = field(default_factory=CivilizationConfig)
    knowledge: KnowledgeConfig = field(default_factory=KnowledgeConfig)
    
    gemini: GeminiAggregateConfig = field(default_factory=GeminiAggregateConfig)
    renderer: RenderAggregateConfig = field(default_factory=RenderAggregateConfig)
    colors: ColorConfig = field(default_factory=ColorConfig)
    
    analytics: AnalyticsConfig = field(default_factory=AnalyticsConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    save: SaveConfig = field(default_factory=SaveConfig)
    replay: ReplayConfig = field(default_factory=ReplayConfig)
    debug: DebugConfig = field(default_factory=DebugConfig)
    
    sound: SoundConfig = field(default_factory=SoundConfig)
    input: InputConfig = field(default_factory=InputConfig)
    screenshot: ScreenshotConfig = field(default_factory=ScreenshotConfig)
    profiler: ProfilerConfig = field(default_factory=ProfilerConfig)
    plugin: PluginConfig = field(default_factory=PluginConfig)
    network: NetworkConfig = field(default_factory=NetworkConfig)
    modding: ModdingConfig = field(default_factory=ModdingConfig)
    research: ResearchConfig = field(default_factory=ResearchConfig)
    experiment: ExperimentConfig = field(default_factory=ExperimentConfig)
    benchmark: BenchmarkConfig = field(default_factory=BenchmarkConfig)
    testing: TestingConfig = field(default_factory=TestingConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    scripting: ScriptingConfig = field(default_factory=ScriptingConfig)
    
    feature_flags: FeatureFlags = field(default_factory=FeatureFlags)


# Global Immutable Configuration Instance
CONFIG = ConfigRegistry()


# =============================================================================
# BACKWARD COMPATIBLE GLOBAL ACCESSORS
# =============================================================================

APP_CONFIG = CONFIG.app
SIMULATION_CONFIG = CONFIG.simulation
PERFORMANCE_CONFIG = CONFIG.performance
RANDOM_CONFIG = CONFIG.random
TIME_CONFIG = CONFIG.time
WORLD_CONFIG = CONFIG.world
CHUNK_CONFIG = CONFIG.chunk
STREAMING_CONFIG = CONFIG.streaming
LOD_CONFIG = CONFIG.lod
BIOME_CONFIG = CONFIG.biome
CLIMATE_CONFIG = CONFIG.climate
RIVER_CONFIG = CONFIG.river
TERRAIN_CONFIG = CONFIG.terrain
WEATHER_CONFIG = CONFIG.weather
DISASTER_CONFIG = CONFIG.disaster
PHYSICS_CONFIG = CONFIG.physics
NAVIGATION_CONFIG = CONFIG.navigation
RESOURCE_CONFIG = CONFIG.resource
FOOD_CONFIG = CONFIG.food
PLANT_CONFIG = CONFIG.plant
SENSOR_CONFIG = CONFIG.sensor
ENTITY_CONFIG = CONFIG.entity
BACTERIA_CONFIG = CONFIG.bacteria
HERBIVORE_CONFIG = CONFIG.herbivore
PREDATOR_CONFIG = CONFIG.predator
SPECIES_CONFIG = CONFIG.species
GENOME_CONFIG = CONFIG.genome
EVOLUTION_CONFIG = CONFIG.evolution
BRAIN_CONFIG = CONFIG.brain
MEMORY_CONFIG = CONFIG.memory
PHEROMONE_CONFIG = CONFIG.pheromone
SOCIAL_CONFIG = CONFIG.social
CIVILIZATION_CONFIG = CONFIG.civilization
KNOWLEDGE_CONFIG = CONFIG.knowledge
GEMINI_CONFIG = CONFIG.gemini
RENDER_CONFIG = CONFIG.renderer
COLOR_CONFIG = CONFIG.colors
ANALYTICS_CONFIG = CONFIG.analytics
LOGGING_CONFIG = CONFIG.logging
SAVE_CONFIG = CONFIG.save
REPLAY_CONFIG = CONFIG.replay
DEBUG_CONFIG = CONFIG.debug
SOUND_CONFIG = CONFIG.sound
INPUT_CONFIG = CONFIG.input
SCREENSHOT_CONFIG = CONFIG.screenshot
PROFILER_CONFIG = CONFIG.profiler
PLUGIN_CONFIG = CONFIG.plugin
NETWORK_CONFIG = CONFIG.network
MODDING_CONFIG = CONFIG.modding
RESEARCH_CONFIG = CONFIG.research
EXPERIMENT_CONFIG = CONFIG.experiment
BENCHMARK_CONFIG = CONFIG.benchmark
TESTING_CONFIG = CONFIG.testing
SECURITY_CONFIG = CONFIG.security
SCRIPTING_CONFIG = CONFIG.scripting
FEATURE_FLAGS = CONFIG.feature_flags