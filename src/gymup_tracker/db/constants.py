"""Constants for muscle groups and equipment mappings."""

MUSCLE_GROUPS = {
    1: "Neck",
    2: "Traps",
    3: "Shoulders",
    4: "Chest",
    5: "Back",
    6: "Biceps",
    7: "Triceps",
    8: "Forearms",
    9: "Core/Abs",
    10: "Lower Back",
    11: "Glutes",
    12: "Hip Flexors",
    13: "Adductors",
    14: "Quads",
    15: "Abductors",
    16: "Hamstrings",
    17: "Calves",
}

EQUIPMENT = {
    1: "Barbell",
    2: "Dumbbell",
    3: "Bodyweight",
    4: "Machine",
    5: "Cable",
    6: "Smith Machine",
    7: "Kettlebell",
    9: "Resistance Band",
    10: "Other",
}

# Reverse mappings for lookups
MUSCLE_GROUPS_BY_NAME = {v: k for k, v in MUSCLE_GROUPS.items()}
EQUIPMENT_BY_NAME = {v: k for k, v in EQUIPMENT.items()}


def get_muscle_name(muscle_id: int | None) -> str:
    """Get muscle group name from ID."""
    if muscle_id is None:
        return "Unknown"
    return MUSCLE_GROUPS.get(muscle_id, "Unknown")


def get_equipment_name(equipment_id: int | None) -> str:
    """Get equipment name from ID."""
    if equipment_id is None:
        return "Unknown"
    return EQUIPMENT.get(equipment_id, "Unknown")


def get_exercise_display_name(exercise) -> str:
    """Get display name for an exercise, with fallback for unnamed exercises."""
    if exercise.name:
        return exercise.name.strip()
    # Fallback for built-in exercises without names
    muscle = get_muscle_name(exercise.mainMuscleWorked)
    equipment = get_equipment_name(exercise.equipment)
    return f"{muscle} ({equipment}) #{exercise.id}"
