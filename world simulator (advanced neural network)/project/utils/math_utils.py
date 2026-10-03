"""
project/utils/math_utils.py

High-performance 2D/3D Euclidean mathematics, geometry, vector operations,
and fast mathematical helpers for the Echo Evolution Simulator.

Architectural Guarantees:
- Pure Python 3 standard library with zero external dependencies.
- Zero unnecessary allocations: returns tuples/primitives or operates on direct scalars.
- Robust boundary handling, trigonometric approximations, and vector normalization.
"""

from __future__ import annotations

import math
from typing import Tuple, List, Optional, Union

# Vector Type Aliases
Vector2 = Tuple[float, float]
Vector3 = Tuple[float, float, float]
Point2D = Tuple[float, float]
Point3D = Tuple[float, float, float]


# =============================================================================
# SCALAR UTILITIES
# =============================================================================

def clamp(val: float, min_val: float, max_val: float) -> float:
    """Clamps a value to the inclusive range [min_val, max_val]."""
    if val < min_val:
        return min_val
    if val > max_val:
        return max_val
    return val


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between a and b by factor t."""
    return a + (b - a) * t


def inverse_lerp(a: float, b: float, val: float) -> float:
    """Calculates the linear parameter t that produces val between a and b."""
    if abs(b - a) < 1e-9:
        return 0.0
    return clamp((val - a) / (b - a), 0.0, 1.0)


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    """Performs smooth Hermite interpolation between 0 and 1."""
    t = clamp((x - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def map_range(
    val: float,
    in_min: float,
    in_max: float,
    out_min: float,
    out_max: float
) -> float:
    """Maps a scalar value from input domain [in_min, in_max] to output domain [out_min, out_max]."""
    t = inverse_lerp(in_min, in_max, val)
    return lerp(out_min, out_max, t)


def normalize_angle(angle_rad: float) -> float:
    """Normalizes an angle in radians to the range [-pi, pi]."""
    return (angle_rad + math.pi) % (2.0 * math.pi) - math.pi


def angle_diff(target_rad: float, current_rad: float) -> float:
    """Calculates the shortest signed angular difference (target - current) in radians."""
    diff = (target_rad - current_rad) % (2.0 * math.pi)
    if diff > math.pi:
        diff -= 2.0 * math.pi
    return diff


# =============================================================================
# 2D VECTOR MATH (SCALAR ACCELERATED)
# =============================================================================

def vec2_add(v1: Vector2, v2: Vector2) -> Vector2:
    return (v1[0] + v2[0], v1[1] + v2[1])


def vec2_sub(v1: Vector2, v2: Vector2) -> Vector2:
    return (v1[0] - v2[0], v1[1] - v2[1])


def vec2_scale(v: Vector2, s: float) -> Vector2:
    return (v[0] * s, v[1] * s)


def vec2_dot(v1: Vector2, v2: Vector2) -> float:
    return v1[0] * v2[0] + v1[1] * v2[1]


def vec2_cross(v1: Vector2, v2: Vector2) -> float:
    """2D cross product scalar (v1.x * v2.y - v1.y * v2.x)."""
    return v1[0] * v2[1] - v1[1] * v2[0]


def vec2_length_sq(v: Vector2) -> float:
    return v[0] * v[0] + v[1] * v[1]


def vec2_length(v: Vector2) -> float:
    return math.hypot(v[0], v[1])


def vec2_normalize(v: Vector2) -> Vector2:
    l = math.hypot(v[0], v[1])
    if l < 1e-9:
        return (0.0, 0.0)
    inv = 1.0 / l
    return (v[0] * inv, v[1] * inv)


def vec2_distance_sq(p1: Vector2, p2: Vector2) -> float:
    dx = p1[0] - p2[0]
    dy = p1[1] - p2[1]
    return dx * dx + dy * dy


def vec2_distance(p1: Vector2, p2: Vector2) -> float:
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def vec2_direction(p_from: Vector2, p_to: Vector2) -> Vector2:
    return vec2_normalize((p_to[0] - p_from[0], p_to[1] - p_from[1]))


def vec2_heading(v: Vector2) -> float:
    """Returns the angle in radians of vector v relative to positive X axis."""
    return math.atan2(v[1], v[0])


def vec2_from_angle(angle_rad: float, length: float = 1.0) -> Vector2:
    """Creates a 2D vector from an angle in radians and magnitude length."""
    return (math.cos(angle_rad) * length, math.sin(angle_rad) * length)


def vec2_rotate(v: Vector2, angle_rad: float) -> Vector2:
    c = math.cos(angle_rad)
    s = math.sin(angle_rad)
    return (v[0] * c - v[1] * s, v[0] * s + v[1] * c)


def vec2_lerp(v1: Vector2, v2: Vector2, t: float) -> Vector2:
    return (v1[0] + (v2[0] - v1[0]) * t, v1[1] + (v2[1] - v1[1]) * t)


def vec2_reflect(v: Vector2, normal: Vector2) -> Vector2:
    """Reflects vector v across unit surface normal."""
    d = 2.0 * vec2_dot(v, normal)
    return (v[0] - d * normal[0], v[1] - d * normal[1])


# =============================================================================
# 3D VECTOR MATH
# =============================================================================

def vec3_add(v1: Vector3, v2: Vector3) -> Vector3:
    return (v1[0] + v2[0], v1[1] + v2[1], v1[2] + v2[2])


def vec3_sub(v1: Vector3, v2: Vector3) -> Vector3:
    return (v1[0] - v2[0], v1[1] - v2[1], v1[2] - v2[2])


def vec3_scale(v: Vector3, s: float) -> Vector3:
    return (v[0] * s, v[1] * s, v[2] * s)


def vec3_dot(v1: Vector3, v2: Vector3) -> float:
    return v1[0] * v2[0] + v1[1] * v2[1] + v1[2] * v2[2]


def vec3_cross(v1: Vector3, v2: Vector3) -> Vector3:
    return (
        v1[1] * v2[2] - v1[2] * v2[1],
        v1[2] * v2[0] - v1[0] * v2[2],
        v1[0] * v2[1] - v1[1] * v2[0]
    )


def vec3_length_sq(v: Vector3) -> float:
    return v[0] * v[0] + v[1] * v[1] + v[2] * v[2]


def vec3_length(v: Vector3) -> float:
    return math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])


def vec3_normalize(v: Vector3) -> Vector3:
    l = vec3_length(v)
    if l < 1e-9:
        return (0.0, 0.0, 0.0)
    inv = 1.0 / l
    return (v[0] * inv, v[1] * inv, v[2] * inv)


def vec3_distance_sq(p1: Vector3, p2: Vector3) -> float:
    dx = p1[0] - p2[0]
    dy = p1[1] - p2[1]
    dz = p1[2] - p2[2]
    return dx * dx + dy * dy + dz * dz


def vec3_distance(p1: Vector3, p2: Vector3) -> float:
    return math.sqrt(vec3_distance_sq(p1, p2))


# =============================================================================
# GEOMETRY & INTERSECTION HELPERS
# =============================================================================

def point_in_circle(px: float, py: float, cx: float, cy: float, radius: float) -> bool:
    dx = px - cx
    dy = py - cy
    return (dx * dx + dy * dy) <= (radius * radius)


def point_in_rect(
    px: float, py: float,
    min_x: float, min_y: float,
    max_x: float, max_y: float
) -> bool:
    return min_x <= px <= max_x and min_y <= py <= max_y


def circles_intersect(
    c1_x: float, c1_y: float, r1: float,
    c2_x: float, c2_y: float, r2: float
) -> bool:
    dx = c1_x - c2_x
    dy = c1_y - c2_y
    r_sum = r1 + r2
    return (dx * dx + dy * dy) <= (r_sum * r_sum)


def point_in_sector(
    px: float, py: float,
    origin_x: float, origin_y: float,
    facing_angle_rad: float,
    fov_angle_rad: float,
    max_radius: float
) -> bool:
    """
    Checks if point (px, py) is inside a vision cone/sector.
    facing_angle_rad: agent's forward direction.
    fov_angle_rad: total field of view in radians.
    """
    dx = px - origin_x
    dy = py - origin_y
    d_sq = dx * dx + dy * dy
    if d_sq > max_radius * max_radius or d_sq < 1e-9:
        return d_sq <= max_radius * max_radius and d_sq < 1e-9

    point_angle = math.atan2(dy, dx)
    diff = abs(angle_diff(point_angle, facing_angle_rad))
    return diff <= (fov_angle_rad * 0.5)


def ray_circle_intersect(
    ray_origin: Vector2,
    ray_dir: Vector2,
    circle_center: Vector2,
    circle_radius: float
) -> Optional[float]:
    """
    Ray-circle intersection test. Returns distance t along ray_dir to closest hit, or None.
    ray_dir must be normalized.
    """
    ox, oy = ray_origin[0] - circle_center[0], ray_origin[1] - circle_center[1]
    dx, dy = ray_dir[0], ray_dir[1]
    
    b = 2.0 * (ox * dx + oy * dy)
    c = (ox * ox + oy * oy) - (circle_radius * circle_radius)
    disc = b * b - 4.0 * c
    if disc < 0.0:
        return None

    sqrt_disc = math.sqrt(disc)
    t1 = (-b - sqrt_disc) * 0.5
    t2 = (-b + sqrt_disc) * 0.5

    if t1 >= 0.0:
        return t1
    if t2 >= 0.0:
        return t2
    return None
