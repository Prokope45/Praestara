# Goal Scaffold System — Design Document

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the complete deterministic behavioral infrastructure for Praestara — the backend data structures, lifecycle engines, and governance guardrails that give an LLM (Koios) deterministic rails to operate within, never needing to hallucinate structure.

**Architecture:** Domain-module architecture (`backend/app/goal_scaffold/`) with event-sourced state mutations ready for Synergen subscription. Each domain owns its models, service logic, routes, and cognition interface. Weekly cycles are the sacred temporal primitive. All business rules are deterministic in the service layer; cognition (LLM) is optional and bounded.

**Tech Stack:** FastAPI, SQLModel, PostgreSQL, Pydantic, Alembic (migrations)

**Branch:** `ethan-goalscaffold` from `main`

---

## 1. Guiding Principles

1. **WeeklyCycle is the core temporal primitive.** Not goals, not habits, not logs. Every behavioral unit derives meaning from its position in a weekly cycle.
2. **Every state mutation emits a DomainEvent.** Praestara is event-sourced from day one. Synergen integration becomes subscription, not rewrite.
3. **Deterministic rules in the service layer.** The LLM (Koios) is a framing layer, not a rule engine. Graduation thresholds, health priority order, adjustment bounds, and cadence are hardcoded.
4. **Stability before escalation.** No user is pushed to improve until they are stable. Stability is measured explicitly and gates all escalation logic.
5. **Cognitive load guardrails are first-class.** The system prevents over-scaffolding by limiting active behavioral axes per cycle.
6. **Cognition boundary, not vendor hook.** Integration points are `cognition_interface.py`, not named after any specific LLM system.

---

## 2. Package Structure

```
backend/app/goal_scaffold/
├── __init__.py
├── router.py                        # Mounts all sub-routers under /scaffold
├── events.py                        # DomainEvent model + emit() helper
├── enums.py                         # Shared enums across domains
│
├── self_concept/
│   ├── __init__.py
│   ├── models.py                    # ConceptDimension, QualitativeObservation,
│   │                                #   SelfConceptSnapshot, IdentityConsistencyIndex
│   ├── service.py                   # Snapshot recomputation, ICI calculation
│   ├── routes.py
│   └── cognition_interface.py       # Qualitative→quantitative decoding boundary
│
├── goals/
│   ├── __init__.py
│   ├── models.py                    # Goal (with intensity_level), GoalCycle, GoalLog
│   ├── service.py                   # Lifecycle, adjustment rules, cognitive load guard
│   ├── routes.py
│   └── cognition_interface.py       # Goal adjustment suggestion boundary
│
├── habits/
│   ├── __init__.py
│   ├── models.py                    # Habit, HabitLog
│   ├── service.py                   # Graduation logic, streak tracking
│   ├── routes.py
│   └── cognition_interface.py       # Habit coaching boundary
│
├── health/
│   ├── __init__.py
│   ├── models.py                    # HealthProfile, HealthPillar, PillarAssessment
│   ├── service.py                   # Priority loop with stability gating
│   ├── routes.py
│   └── cognition_interface.py       # Exercise programming boundary
│
├── nutrition/
│   ├── __init__.py
│   ├── models.py                    # MealPlan, MealEntry, NutritionLog
│   ├── service.py                   # Weekly meal planning, reflection
│   ├── routes.py
│   └── cognition_interface.py       # Recipe/meal suggestion boundary
│
├── weekly_cycle/
│   ├── __init__.py
│   ├── models.py                    # WeeklyCycle, WeeklyReview (with structured reflection)
│   ├── service.py                   # Cycle orchestration, cognitive load guard enforcement
│   ├── routes.py
│   └── cognition_interface.py       # Weekly meeting conversation boundary
│
├── stability/
│   ├── __init__.py
│   ├── models.py                    # StabilityScore, EscalationSignal
│   ├── service.py                   # Stability computation, escalation detection
│   └── routes.py
│
├── resource_profile/
│   ├── __init__.py
│   ├── models.py                    # UserResourceProfile
│   ├── service.py                   # Feasibility filtering
│   └── routes.py
│
├── trajectory/
│   ├── __init__.py
│   ├── models.py                    # TrajectoryVector
│   ├── service.py                   # Vector computation, export
│   └── routes.py
│
└── metrics/
    ├── __init__.py
    ├── models.py                    # MetricTimeSeries, MetricDataPoint
    ├── service.py                   # Aggregation, trend computation
    └── routes.py
```

---

## 3. Event Bridge (Synergen-Ready)

```python
class DomainEvent(SQLModel, table=True):
    __tablename__ = "goal_scaffold_event"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    event_type: str              # "goal.created", "goal.cycle_completed", "habit.graduated"
    domain: str                  # "goals", "habits", "self_concept", "health", etc.
    payload: dict = Field(sa_column=Column(JSON))
    emitted_at: datetime = Field(default_factory=datetime.utcnow)
    schema_version: str = "1.0"
    processed: bool = False      # Synergen consumption flag
```

**emit() helper:**
```python
def emit(session: Session, *, user_id: UUID, event_type: str, domain: str, payload: dict) -> DomainEvent:
    event = DomainEvent(user_id=user_id, event_type=event_type, domain=domain, payload=payload)
    session.add(event)
    return event
```

Every service function calls `emit()` alongside its CRUD operation. The `processed` flag lets Synergen mark events as consumed without deleting them.

**Event type taxonomy:**
- `self_concept.observation_recorded`
- `self_concept.snapshot_computed`
- `self_concept.ici_updated`
- `goal.created`, `goal.updated`, `goal.archived`
- `goal.cycle_started`, `goal.cycle_completed`, `goal.cycle_adjusted`
- `goal.log_recorded`
- `habit.graduated`, `habit.log_recorded`, `habit.streak_broken`
- `health.assessment_recorded`, `health.focus_shifted`
- `nutrition.plan_created`, `nutrition.log_recorded`
- `weekly.cycle_started`, `weekly.review_completed`
- `stability.score_computed`, `stability.escalation_triggered`
- `trajectory.vector_computed`

---

## 4. Shared Enums

```python
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
```

---

## 5. Core Models — Detailed

### 5.1 Self-Concept

**ConceptDimension** — A named axis of self-concept per user:
```
id, user_id, name (str), value (float 0.0-1.0),
source (str: "questionnaire"|"observation"|"adherence"|"computed"),
last_updated (datetime)
```

Default dimensions seeded from initial questionnaire:
- self_efficacy, optimism, social_connection, body_awareness,
  discipline, emotional_regulation, purpose_clarity, stress_tolerance

**QualitativeObservation** — Raw text with decoded signals:
```
id, user_id, text (str), context (str: "daily_log"|"weekly_reflection"|"goal_note"),
decoded_dimensions (JSON: {dimension_name: delta_value}),
decoded_by (str: "stub"|"koios"), observed_at (datetime)
```

**SelfConceptSnapshot** — Point-in-time materialization:
```
id, user_id, dimensions (JSON: {name: value}),
identity_consistency_index (float 0.0-1.0),
computed_at (datetime), cycle_id (FK to WeeklyCycle, nullable)
```

**IdentityConsistencyIndex** — Derived scalar:
```
id, user_id, value (float 0.0-1.0),
components (JSON: {goal_alignment: float, adherence_alignment: float, tone_alignment: float}),
computed_at (datetime), cycle_id (FK)
```

**ICI Computation (deterministic):**
```
goal_alignment = correlation(stated_goal_priorities, time_allocated_to_goals)
adherence_alignment = mean(achieved / target) across active goals
tone_alignment = sentiment_consistency(recent_qualitative_observations)
ICI = weighted_mean(goal_alignment * 0.4, adherence_alignment * 0.4, tone_alignment * 0.2)
```
Note: `tone_alignment` uses the stub's keyword-based scoring until Koios provides richer decoding.

### 5.2 Goals

**Goal:**
```
id, user_id, category (GoalCategory), title (str), description (str, nullable),
target_value (float), target_unit (str: "days"|"minutes"|"servings"|"sessions"|...),
intensity_level (int 1-5),
time_horizon (str: "weekly"|"biweekly"|"monthly", default "weekly"),
parent_goal_id (FK to self, nullable),
status (GoalStatus), created_at, updated_at
```

The `intensity_level` field (1=minimal, 5=maximal) separates frequency from intensity. "3 days of cardio at intensity 2" is fundamentally different from "3 days at intensity 5." This enables progressive overload logic later.

**GoalCycle** — One week's instance:
```
id, goal_id (FK), cycle_id (FK to WeeklyCycle),
target_value (float — can differ from Goal.target_value after adjustment),
intensity_level (int — inherited or adjusted),
achieved_value (float, default 0),
status (CycleStatus), adjustment_note (str, nullable),
created_at, completed_at (nullable)
```

**GoalLog** — Daily entry:
```
id, goal_cycle_id (FK), date (date),
completed (bool), value (float, nullable), intensity_actual (int 1-5, nullable),
note (str, nullable — qualitative, feeds QualitativeObservation pipeline),
logged_at (datetime)
```

### 5.3 Habits

**Habit** — Graduated from a Goal:
```
id, user_id, origin_goal_id (FK to Goal),
category (GoalCategory), title (str),
frequency (int — per week), intensity_level (int 1-5),
established_at (datetime), streak_weeks (int, default 0),
status (str: "active"|"paused"|"broken")
```

**HabitLog:**
```
id, habit_id (FK), date (date),
completed (bool), value (float, nullable), intensity_actual (int 1-5, nullable),
note (str, nullable), logged_at (datetime)
```

### 5.4 Health Pillars

**HealthProfile:**
```
id, user_id (FK, unique),
primary_focus (PillarType — auto-computed),
balance_score (float 0.0-1.0),
last_assessed (datetime)
```

**HealthPillar:**
```
id, health_profile_id (FK), pillar_type (PillarType),
current_level (float 0.0-1.0),
sub_axes (JSON):
  endurance: {cardio_capacity, recovery, resting_hr_estimate}
  strength: {upper_body, lower_body, core, functional}
  mobility: {flexibility, joint_health, balance, range_of_motion}
```

**PillarAssessment** — Time-series:
```
id, pillar_id (FK), assessed_at (datetime),
level (float), sub_axes_snapshot (JSON),
source (str: "self_report"|"goal_adherence"|"cognition_inference")
```

**Priority Loop (with stability gating):**
```python
def compute_primary_focus(profile: HealthProfile, stability: StabilityScore) -> PillarType:
    if stability.value < STABILITY_THRESHOLD:
        return profile.primary_focus  # Don't change focus when unstable

    pillars = sorted(profile.pillars, key=lambda p: p.current_level)
    lowest = pillars[0]
    highest = pillars[-1]

    if highest.current_level - lowest.current_level > IMBALANCE_THRESHOLD:
        return lowest.pillar_type  # Push weakest pillar

    # Balanced — default priority order
    return PillarType.ENDURANCE
```

### 5.5 Nutrition

**MealPlan:**
```
id, user_id (FK), week_start (date), status (str: "draft"|"active"|"completed"),
notes (str, nullable), created_at
```

**MealEntry:**
```
id, meal_plan_id (FK), day_of_week (int 0-6),
meal_type (MealType), description (str),
recipe_ref (str, nullable), prep_notes (str, nullable)
```

**NutritionLog:**
```
id, user_id (FK), date (date), meal_type (MealType),
completed (bool), description (str, nullable),
nutrients (JSON, nullable — optional depth for detail-oriented users),
logged_at (datetime)
```

### 5.6 Weekly Cycle

**WeeklyCycle:**
```
id, user_id (FK), week_start (date), week_end (date),
status (WeeklyCycleStatus), created_at
```

**WeeklyReview** — The "goal meeting":
```
id, cycle_id (FK, unique),
goals_met (int), goals_missed (int), goals_adjusted (int),
qualitative_reflection (str, nullable — freeform text),

# Structured reflection (deterministic self-concept input)
reflection_energy_level (float 0.0-1.0),
reflection_motivation (float 0.0-1.0),
reflection_perceived_control (float 0.0-1.0),

adjustments_made (JSON: [{goal_id, old_target, new_target, reason}]),
self_concept_delta (JSON: {dimension_name: delta_value}),
cognition_session_id (str, nullable — for when Koios drives the meeting),
completed_at (datetime, nullable)
```

### 5.7 Stability

**StabilityScore:**
```
id, user_id (FK), value (float 0.0-1.0),
components (JSON: {adherence_variance, missed_cycle_frequency, tone_volatility}),
computed_at (datetime), cycle_id (FK)
```

**Computation (deterministic):**
```
adherence_variance = 1.0 - stddev(achieved/target over last 4 cycles)
missed_cycle_frequency = 1.0 - (missed_cycles / total_cycles over last 4)
tone_volatility = 1.0 - stddev(reflection_motivation over last 4 cycles)
stability = weighted_mean(adherence_variance * 0.5, missed_frequency * 0.3, tone_volatility * 0.2)
```

**EscalationSignal:**
```
id, user_id (FK), reason (EscalationReason),
stability_score (float), drift_score (float, nullable),
details (JSON), generated_at (datetime),
acknowledged (bool, default False), acknowledged_at (datetime, nullable)
```

### 5.8 Resource Profile

**UserResourceProfile:**
```
id, user_id (FK, unique),
weekly_available_hours (float),
equipment_access (JSON: ["bodyweight"|"dumbbells"|"full_gym"|"pool"|"outdoor"]),
cooking_access (str: "full_kitchen"|"limited"|"none"),
time_variability (float 0.0-1.0 — how consistent is their schedule),
stress_baseline (float 0.0-1.0 — self-reported chronic stress level),
updated_at (datetime)
```

All pillar recommendations and goal suggestions are filtered through ResourceProfile feasibility checks.

### 5.9 Trajectory Vector

**TrajectoryVector** — The exportable individual state packet:
```
id, user_id (FK),
stability_trend (float -1.0 to 1.0 — direction of stability change),
intensity_trend (float -1.0 to 1.0 — direction of goal intensity change),
identity_alignment_trend (float -1.0 to 1.0 — ICI direction),
pillar_balance (float 0.0-1.0 — health pillar evenness),
overall_trajectory (float -1.0 to 1.0 — composite direction),
computed_at (datetime), cycle_id (FK)
```

This is what gets exported to Synergen, Engine89, or any research layer. Compact, versioned, reconstructible from events.

### 5.10 Metrics

**MetricTimeSeries:**
```
id, user_id (FK), metric_name (str), category (str),
aggregation_period (str: "daily"|"weekly"|"monthly")
```

**MetricDataPoint:**
```
id, series_id (FK), timestamp (datetime), value (float),
metadata (JSON, nullable)
```

Auto-populated metrics: goal_completion_rate, stability_score, ici_value, pillar_balance, streak_length, trajectory_composite.

---

## 6. Deterministic Business Rules

### 6.1 Goal Adjustment
- If `achieved_value < target_value` → suggest lowering to `achieved_value` for next cycle
- If `achieved_value >= target_value` for 2+ consecutive cycles AND stability > threshold → suggest raising by 1 unit
- Never suggest raising intensity_level and target_value simultaneously

### 6.2 Cognitive Load Guard
```python
MAX_NEW_GOALS_PER_CYCLE = 1
MAX_INTENSITY_INCREASES_PER_CYCLE = 1

def check_cognitive_load(user_id, cycle_id, proposed_changes) -> bool:
    new_goals_this_cycle = count_new_goals(user_id, cycle_id)
    intensity_increases = count_intensity_increases(user_id, cycle_id)

    if new_goals_this_cycle + proposed_changes.new_goals > MAX_NEW_GOALS_PER_CYCLE:
        return False  # "System stability guard"
    if intensity_increases + proposed_changes.intensity_ups > MAX_INTENSITY_INCREASES_PER_CYCLE:
        return False
    return True
```

### 6.3 Habit Graduation
- Goal met for 4 consecutive weekly cycles → eligible for graduation
- StabilityScore must be > 0.6 to graduate
- User confirms graduation (not automatic)

### 6.4 Health Priority Loop (with stability gating)
- If `stability_score < 0.5` → suppress all pillar escalation, maintain current focus
- If balanced (all pillars within 0.1) → push endurance
- If imbalanced → push lowest pillar
- Priority order for new users: endurance → strength → mobility
- All recommendations filtered through UserResourceProfile

### 6.5 Weekly Cycle Automation
- New WeeklyCycle auto-created Monday (or on first interaction of the week)
- GoalCycles auto-created for all active Goals
- Previous cycle moves to REVIEW status on Sunday
- StabilityScore, ICI, and TrajectoryVector computed on review completion

### 6.6 Self-Concept Recomputation
Triggered after WeeklyReview completion:
1. Ingest structured reflection scores (energy, motivation, control)
2. Ingest goal/habit adherence data
3. Ingest decoded qualitative observations from the cycle
4. Recompute ConceptDimension values
5. Materialize new SelfConceptSnapshot
6. Compute IdentityConsistencyIndex
7. Check for EscalationSignals

### 6.7 Escalation Detection
```python
def check_escalation(user_id, cycle_id):
    stability = get_latest_stability(user_id)
    ici = get_latest_ici(user_id)

    if stability.value < 0.3:
        emit_escalation(user_id, LOW_STABILITY, stability.value)
    if ici.value < 0.3:
        emit_escalation(user_id, IDENTITY_DRIFT, drift_score=1.0 - ici.value)
    if count_consecutive_missed(user_id) >= 3:
        emit_escalation(user_id, REPEATED_MISSED_CYCLES)
```

---

## 7. Cognition Interface (Koios Integration Points)

Each `cognition_interface.py` defines:
1. A **request schema** — what data the cognition layer needs
2. A **response schema** — what the cognition layer returns
3. A **stub function** — deterministic rule-based fallback

Koios replaces the stub function body. The interface contract is permanent.

**Interfaces by domain:**

| Domain | Request Contains | Response Contains |
|--------|-----------------|-------------------|
| self_concept | qualitative_text, context, current_dimensions | decoded_dimensions (dict of deltas) |
| goals | cycle_history, self_concept, resource_profile | suggested_target, rationale, confidence |
| habits | habit_data, streak_history, resource_profile | coaching_message, suggested_adjustment |
| health | pillar_levels, resource_profile, stability | exercise_suggestions, rationale |
| nutrition | meal_history, resource_profile, preferences | meal_plan_suggestions, prep_tips |
| weekly_cycle | full_cycle_data, all_domain_summaries | meeting_narrative, suggested_adjustments |

---

## 8. API Surface

All endpoints under `/api/v1/scaffold/`:

| Prefix | Endpoints |
|--------|-----------|
| `/self-concept` | GET /snapshot, GET /dimensions, POST /observation, GET /history, GET /ici |
| `/goals` | CRUD /goals, GET/POST /goals/{id}/cycles, POST /goals/{id}/log, GET /goals/{id}/summary |
| `/habits` | GET /habits, POST /habits/{id}/log, GET /habits/{id}/streak |
| `/health` | GET /profile, POST /assessment, GET /pillars, GET /priority, GET /pillar-history |
| `/nutrition` | CRUD /meal-plans, POST /log, GET /weekly-summary |
| `/weekly` | GET /current, POST /start-review, POST /complete-review, GET /history |
| `/stability` | GET /current, GET /history, GET /escalations |
| `/resources` | GET/PUT /profile |
| `/trajectory` | GET /current, GET /history |
| `/metrics` | GET /series/{name}, GET /dashboard |

---

## 9. What Changes in Existing Code

**One line added** to `backend/app/api/main.py`:
```python
from app.goal_scaffold.router import goal_scaffold_router
api_router.include_router(goal_scaffold_router, prefix="/scaffold", tags=["goal-scaffold"])
```

**Nothing else changes.** All existing models, routes, CRUD, and migrations remain untouched.

---

## 10. Migration Strategy

One new Alembic migration creates all goal_scaffold tables. No modifications to existing tables. The new tables reference `user.id` via foreign keys but add no columns to the `user` table.

---

## 11. Integration Map

```
Questionnaires (existing) ──→ Self-Concept (dimensions seeded from responses)
                                    │
                                    ▼
                            SelfConceptSnapshot
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
     Goals ◄──── WeeklyCycle ────► Habits              HealthPillars
        │              │              │                       │
        ▼              ▼              ▼                       ▼
   GoalCycle     WeeklyReview    HabitLog            PillarAssessment
        │              │                                      │
        ▼              ▼                                      ▼
    GoalLog    StabilityScore ◄─────────────────── ResourceProfile
                    │
                    ▼
            IdentityConsistencyIndex
                    │
                    ▼
            EscalationSignal
                    │
                    ▼
            TrajectoryVector ──→ [Synergen / Engine89 / Research]
```
