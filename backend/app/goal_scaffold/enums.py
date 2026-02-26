from enum import Enum


class GoalCategory(str, Enum):
    EXERCISE = "exercise"
    NUTRITION = "nutrition"
    SLEEP = "sleep"
    MINDFULNESS = "mindfulness"
    SOCIAL = "social"
    LEARNING = "learning"
    CUSTOM = "custom"


class GoalStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class CycleStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    MET = "met"
    MISSED = "missed"
    ADJUSTED = "adjusted"


class WeeklyCycleStatus(str, Enum):
    UPCOMING = "upcoming"
    ACTIVE = "active"
    REVIEW = "review"
    COMPLETED = "completed"


class PillarType(str, Enum):
    ENDURANCE = "endurance"
    STRENGTH = "strength"
    MOBILITY = "mobility"


class MealType(str, Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


class EscalationReason(str, Enum):
    LOW_STABILITY = "low_stability"
    IDENTITY_DRIFT = "identity_drift"
    REPEATED_MISSED_CYCLES = "repeated_missed_cycles"
    COGNITIVE_OVERLOAD = "cognitive_overload"
    PILLAR_IMBALANCE = "pillar_imbalance"


class HabitStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    BROKEN = "broken"


class MealPlanStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"


class ObservationContext(str, Enum):
    DAILY_LOG = "daily_log"
    WEEKLY_REFLECTION = "weekly_reflection"
    GOAL_NOTE = "goal_note"
    HABIT_NOTE = "habit_note"


class DimensionSource(str, Enum):
    QUESTIONNAIRE = "questionnaire"
    OBSERVATION = "observation"
    ADHERENCE = "adherence"
    COMPUTED = "computed"


class AssessmentSource(str, Enum):
    SELF_REPORT = "self_report"
    GOAL_ADHERENCE = "goal_adherence"
    COGNITION_INFERENCE = "cognition_inference"
