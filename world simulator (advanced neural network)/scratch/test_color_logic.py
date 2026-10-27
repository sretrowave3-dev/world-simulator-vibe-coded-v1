import math
import numpy as np

# Let's inspect the color blending for:
# 1. Churning whitewater rapids foam (white/pale ice blue with churn pattern)
# 2. Glacial azure deep water (matching joris-visser photo: [52, 89, 106])
# 3. Riverbank gorge rock (matching joris-visser photo: [23, 35, 42])
# 4. Lush grass (matching jake-nackos photo: [29, 70, 26] with lime highlights [90, 165, 55])

def get_modern_terrain_color(h, w_str, b_type, wx, wy, sim_tick=0):
    # Micro relief hillshade
    hillshade = 0.88 + (h - 0.45) * 0.35 + (math.sin(wx * 0.06 + wy * 0.06) * 0.04)

    if "RIVER" in w_str or "STREAM" in w_str:
        # Dynamic animated alpine river
        # Rapids churn wave
        flow = sim_tick * 0.08
        churn = math.sin(wx * 0.15 + wy * 0.12 - flow) * math.cos(wx * 0.08 - wy * 0.14 + flow * 0.7)
        foam_intensity = max(0.0, churn * 1.4)
        
        # Base glacial deep azure water: RGB (42, 105, 145) to (58, 138, 175)
        r_base = 45 + int(math.sin(wx * 0.05 + wy * 0.05) * 8)
        g_base = 115 + int(math.cos(wx * 0.05 + wy * 0.05) * 15)
        b_base = 165 + int(math.sin(wx * 0.07) * 12)

        if foam_intensity > 0.45:
            # Churning whitewater rapids crest
            foam_t = min(1.0, (foam_intensity - 0.45) * 2.2)
            r = int(r_base * (1.0 - foam_t) + 225 * foam_t)
            g = int(g_base * (1.0 - foam_t) + 240 * foam_t)
            b = int(b_base * (1.0 - foam_t) + 252 * foam_t)
        else:
            r, g, b = r_base, g_base, b_base

        return (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))

    elif "OCEAN" in w_str:
        if h < 0.2:
            return (14, 38, 75)
        return (22, 68, 128)

    elif h > 0.82 or "SNOW" in b_type or "ICE" in b_type:
        val = int(245 * hillshade)
        return (max(200, min(255, val)), max(205, min(255, val + 5)), 255)

    elif h > 0.68 or "MOUNTAIN" in b_type:
        val = int(105 * hillshade)
        return (max(45, min(170, int(val * 0.95))), max(50, min(175, val)), max(55, min(180, int(val * 1.05))))

    elif "DESERT" in b_type or "BEACH" in b_type:
        return (max(140, min(230, int(205 * hillshade))), max(120, min(205, int(180 * hillshade))), max(80, min(155, int(125 * hillshade))))

    elif "FOREST" in b_type or "JUNGLE" in b_type or "RAINFOREST" in b_type:
        return (max(15, min(55, int(22 * hillshade))), max(45, min(125, int(82 * hillshade))), max(20, min(65, int(35 * hillshade))))

    else:
        # Lush photorealistic grassland matching jake-nackos photo
        # Multi-scale micro-texture + gentle wind wave
        micro = math.sin(wx * 0.45) * math.cos(wy * 0.45) * 8.0 + math.sin(wx * 1.1 + wy * 0.9) * 4.0
        wind = math.sin(wx * 0.04 + wy * 0.02 + sim_tick * 0.03) * 6.0
        total_dither = micro + wind

        r = max(22, min(95, int((34 + total_dither * 0.6) * hillshade)))
        g = max(60, min(175, int((112 + total_dither * 1.8) * hillshade)))
        b = max(24, min(90, int((38 + total_dither * 0.7) * hillshade)))
        return (r, g, b)

print("Color test for river:", get_modern_terrain_color(0.5, "RIVER", "RIVER", 100, 200, 10))
print("Color test for grass:", get_modern_terrain_color(0.5, "NONE", "GRASSLAND", 100, 200, 10))
