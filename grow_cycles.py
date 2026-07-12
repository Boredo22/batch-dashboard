#!/usr/bin/env python3
"""
Grow-cycle reporting logic (pure - no Flask, no file I/O).

Extracted from app.py's /api/grow-cycles/report handler so the agronomic math
(stage detection, recipe selection, dose scaling, EC/pH targets, harvest dates)
can be unit-tested directly. The Flask handler stays responsible for loading the
cycles / nutrients / settings and passing them in here.
"""

from datetime import date, timedelta

# Agronomic constants (previously hard-coded inline in the handler)
DEFAULT_FLOWER_VEG_NUTE_DAYS = 21
DEFAULT_FEEDINGS_PER_DAY = 2
DEFAULT_FLUSH_RECIPE = {'Cake': 2.0}   # cropsalt flush when no flush_formula exists
TARGET_PH = 6.2


def compute_stage(current_day, veg_days, flower_days, flush_days):
    """Return (stage, stage_day, total_days) for a 1-based current_day."""
    total_days = veg_days + flower_days + flush_days
    if current_day <= 0:
        return 'not_started', 0, total_days
    if current_day <= veg_days:
        return 'veg', current_day, total_days
    if current_day <= veg_days + flower_days:
        return 'flower', current_day - veg_days, total_days
    if current_day <= total_days:
        return 'flush', current_day - veg_days - flower_days, total_days
    return 'complete', 0, total_days


def select_recipe(stage, stage_day, flower_veg_nute_days, nutrients_data):
    """Return (recipe_key, sub_stage, recipe_dict) for the given stage.

    Flower's first `flower_veg_nute_days` use the veg formula, then bloom.
    Flush falls back to a Cake-only cropsalt flush if no flush_formula exists.
    """
    sub_stage = None
    if stage == 'veg':
        recipe_key = 'veg_formula'
    elif stage == 'flower':
        if stage_day <= flower_veg_nute_days:
            recipe_key, sub_stage = 'veg_formula', 'flower_veg'
        else:
            recipe_key, sub_stage = 'bloom_formula', 'flower_bloom'
    elif stage == 'flush':
        recipe_key = 'flush_formula'
    else:
        recipe_key = None

    recipe = dict(nutrients_data.get(recipe_key, {})) if recipe_key else {}
    if stage == 'flush' and not recipe:
        recipe = dict(DEFAULT_FLUSH_RECIPE)
    return recipe_key, sub_stage, recipe


def compute_ec_targets(stage, stage_day, flower_days):
    """Return [low, high] EC targets for the stage (heavy bump mid-flower)."""
    if stage == 'veg':
        return [2.2, 2.2]
    if stage == 'flower':
        # Heavy flower bump roughly weeks 4-6 of the flower window.
        heavy_start = max(1, int(flower_days * 0.4))
        heavy_end = int(flower_days * 0.75)
        if heavy_start <= stage_day <= heavy_end:
            return [2.3, 2.3]
        return [2.2, 2.2]
    if stage == 'flush':
        return [0.0, 0.3]
    return [0, 0]


def build_cycle_report(room_id, cycle, today, nutrients_data,
                       flower_veg_nute_days, feedings_per_day):
    """Compute the full report dict for a single (active) cycle."""
    start = date.fromisoformat(cycle['start_date'])
    current_day = (today - start).days + 1

    veg_days = int(cycle['veg_days'])
    flower_days = int(cycle['flower_days'])
    flush_days = int(cycle['flush_days'])

    stage, stage_day, total_days = compute_stage(
        current_day, veg_days, flower_days, flush_days)
    recipe_key, sub_stage, recipe = select_recipe(
        stage, stage_day, flower_veg_nute_days, nutrients_data)

    # Scale doses by watering volume (per feeding, and per day).
    volume = cycle.get('watering_volume_gallons', 1)
    scaled = {name: round(ml * volume, 1) for name, ml in recipe.items()}
    daily_scaled = {name: round(ml * volume * feedings_per_day, 1)
                    for name, ml in recipe.items()}

    target_ec = compute_ec_targets(stage, stage_day, flower_days)

    harvest_date = start + timedelta(days=total_days - 1)
    days_remaining = max(0, (harvest_date - today).days + 1)

    return {
        'room_id': room_id,
        'room_name': cycle.get('room_name', f'Room {room_id}'),
        'strain': cycle.get('strain', ''),
        'current_day': max(0, current_day),
        'total_days': total_days,
        'current_stage': stage,
        'sub_stage': sub_stage,
        'stage_day': stage_day,
        'veg_days': veg_days,
        'flower_days': flower_days,
        'flush_days': flush_days,
        'days_remaining': days_remaining if stage != 'complete' else 0,
        'harvest_date': harvest_date.isoformat(),
        'recipe_name': recipe_key or ('flush' if stage == 'flush' else 'none'),
        'recipe_per_gallon': recipe,
        'recipe_total_ml': scaled,
        'recipe_daily_total_ml': daily_scaled,
        'feedings_per_day': feedings_per_day,
        'watering_volume_gallons': volume,
        'target_ec': target_ec,
        'target_ph': TARGET_PH,
        'notes': cycle.get('notes', ''),
    }


def build_reports(cycles_data, nutrients_data, grow_defaults, today=None):
    """Build daily watering reports for all active cycles.

    Args:
        cycles_data: parsed grow_cycles.json, shape {'cycles': {room_id: {...}}}
        nutrients_data: parsed nutrients.json (recipe_key -> {nutrient: ml})
        grow_defaults: user.growDefaults from settings (may be empty)
        today: date to compute against (defaults to date.today())

    Returns:
        list[dict]: one report per active cycle
    """
    if today is None:
        today = date.today()
    flower_veg_nute_days = int(
        grow_defaults.get('flower_veg_nute_days', DEFAULT_FLOWER_VEG_NUTE_DAYS))
    feedings_per_day = int(
        grow_defaults.get('feedings_per_day', DEFAULT_FEEDINGS_PER_DAY))

    reports = []
    for room_id, cycle in cycles_data.get('cycles', {}).items():
        if not cycle.get('active', False):
            continue
        reports.append(build_cycle_report(
            room_id, cycle, today, nutrients_data,
            flower_veg_nute_days, feedings_per_day))
    return reports
