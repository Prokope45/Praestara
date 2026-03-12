# Praestara Doctrine

## 1) Core Identity
Praestara is a constraint-aware identity alignment system. It is **not**:
- A gamified tracker
- A social network
- An engagement optimizer
- A clinical decision engine

## 2) Structural Layers
- **GrowthModule abstraction**: deterministic growth logic with explicit interfaces.
- **Projection layer**: lightweight, daily alignment signals.
- **Reflection layer**: daily signal capture without moral scoring.
- **Realignment layer**: weekly strategy shifts based on constraints.
- **Exposure telemetry**: structured execution events for behavioral signals.
- **PHI boundary**: Praestara emits de-identified fragments only.

## 3) Non-Negotiable Principles
- Deterministic core logic. No stochastic behavior in growth math.
- Adherence is a structural signal, never a moral score.
- Missed goals trigger strategy adjustment, not punishment.
- No streak counters, no leaderboards, no gamification loops.
- No AI-generated prescriptions inside the engine core.
- LLMs are allowed only for translation/presentation of structured outputs.

## 4) PHI Boundary Enforcement
- Praestara operates in PHI mode internally.
- Praestara emits **de-identified** fragments only.
- Praestara never exposes raw identifiers outside Synergen.
- Engine89 performs inference only; it does not prescribe treatment.

## 5) Engagement Contract
Daily:
- 1 projection (optional but encouraged)
- 1 reflection (required for adherence update)

Weekly:
- 1 realignment

The system must function with minimal interaction. Engagement is optional. Structure is constant.

## 6) GrowthModule Pattern
A GrowthModule must define:
- capacity vector
- ceiling
- stress budget
- allocation structure
- interference model (if applicable)
- adherence gating
- degradation ladder
- projection function
- update function

Fitness is one implementation. Other domains should follow the same pattern.

## 7) What Future Agents Must Not Do
- Introduce randomness into growth logic
- Optimize for dopamine engagement
- Collapse projection/reflection into streak logic
- Blend PHI with inference outputs
- Embed natural language generation into engine math

## 8) Unified Mathematical Growth Grammar
All modules must implement the same bounded/logistic growth grammar:
- Capacity vectors are bounded by explicit ceilings.
- Growth follows diminishing returns with adherence-first gating.
- Degradation ladders enforce feasibility under constraints.
- All modules expose commitments through the unified alignment surface.
- No module may introduce random growth logic.
