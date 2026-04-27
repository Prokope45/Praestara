# BeSci Theory Synthesis

## Purpose

This document synthesizes the theory behind BeSci so the system can interpret language and behavior in a way that stays aligned with the scientific ideas that shaped its deterministic structure.

BeSci is not meant to be:

- a one-shot diagnosis engine
- a pure sentiment analyzer
- a chatbot improvising psychology from scratch

BeSci is meant to be:

- a passive, longitudinal phenotyping layer
- a dimensional and process-aware interpretation engine
- a bridge between text, behavior, context, and structured human meaning

## Core orientation

### 1. Longitudinal over single-point

The system should approximate current state from a single entry when necessary, but it should become more accurate as history accumulates.

Interpretive rule:
- single entries estimate current state
- repeated entries estimate change, baseline, persistence, and volatility
- long-run trajectories say more about the person's world and enduring patterns than one isolated utterance ever can

### 2. Dimensional over categorical

The system should describe where the person's language falls across dimensions and processes rather than forcing them into discrete clinical boxes.

Interpretive rule:
- prioritize gradients, tensions, and mixed states
- allow contradictory truths across domains
- treat syndromic labels as downstream possibilities, not upstream assumptions

### 3. Multi-domain over flattened mood

A person can be doing well at work and poorly in relationships on the same day.

Interpretive rule:
- maintain domain separation
- do not let opposing life areas cancel each other into one flat summary
- explicitly report cross-domain divergence when it is meaningful

### 4. Contextual human over decontextualized text

Language is not only a direct report of inner state. It is shaped by effort, reward, environment, social structure, relational input, self-concept, threat, bodily state, and expressive style.

Interpretive rule:
- read text as a noisy observation of broader human functioning
- include environment, time-scale, and domain context whenever possible
- assume the text is embedded in a life, not isolated from it

## Corpus families and what they contribute

## Affective language and psycholinguistics

These sources ground the basic dimensions of valence, arousal, self-focus, absolutist language, negative style, and language-based mental health measurement.

Contributions:
- language can reflect stable and shifting affective patterns
- self-focus, negative style, and absolutist language can matter
- aggregated language can track real-world mental health trends

Implication for BeSci:
- direct emotional wording matters
- lexical choices can carry psychological information
- but the system should not stop at surface sentiment

## Computational psychiatry and process models

These sources motivate treating text as an observation layer over latent processes rather than a direct diagnosis.

Contributions:
- reward, control, uncertainty, and prediction-error sensitivity are useful process-level approximations
- computational variables can mediate between language and broader behavior
- state depends not only on "how bad someone feels," but on how their system is weighting reward, effort, threat, and volatility

Implication for BeSci:
- computational axes are approximation layers, not decorative extras
- they should influence interpretation and trajectory reading

## Reward, motivation, and anhedonia

These sources deepen the distinction between wanting, reward sensitivity, effort, and activation.

Contributions:
- low reward is not identical to sadness
- effort cost and reward pull can dissociate
- a person can still function behaviorally while reward experience is blunted

Implication for BeSci:
- reward-seeking must remain separate from valence
- dopaminergic-pressure and effort-cost logic help interpret why a person sounds "flat," "uphill," or "unmoved"

## Social, relational, and attachment-related dynamics

These sources emphasize that social functioning is not one variable.

Contributions:
- social salience, evaluative concern, avoidance, relational ambivalence, boundary strain, and audience effects can all differ
- people can be socially active yet relationally misaligned
- social context can alter reward and performance

Implication for BeSci:
- social interpretation should not be reduced to "withdrawn vs connected"
- relationship functioning should remain multi-dimensional
- interpersonal context can change how other dimensions behave

## Dimensional hierarchy and symptom covariance

These sources support the idea that psychological difficulties cluster but should still be modeled dimensionally.

Contributions:
- higher-order spectra help summarize covariance patterns
- negative affectivity, detachment, disinhibition, interpersonal instability, and similar factors can organize lower-level signals

Implication for BeSci:
- higher-order factors should summarize, not erase, lower-level nuance
- they are useful for pattern recognition, not for categorical diagnosis

## Trajectory modeling and longitudinal epidemiology

These sources motivate a strong temporal layer.

Contributions:
- trajectories can differ by baseline, direction, volatility, and timing
- the same score means different things in same-day vs multi-week contexts

Implication for BeSci:
- time-scale should always shape interpretation
- short-term event swings and longer-term environment shifts should not be conflated

## Expressive, poetic, and aesthetic corpora

These sources matter because humans often do not speak in literal symptom-report language.

Contributions:
- concrete imagery, sensory language, symbolism, metaphor, and reflective distance all carry affective information
- emotion can be explicit or indirect
- art-like and poetic language can hold meaning without bluntly naming the feeling

Implication for BeSci:
- the model should not under-read figurative writing
- expressive style is part of the signal, not noise
- interpretation should distinguish direct feeling labels from implied affective communication

## BeSci interpretive layers

## Layer 1. Base dimensions

These are the core psychological coordinates:

- valence
- arousal
- control
- volatility
- social_orientation
- reward_seeking
- cognitive_flexibility
- self_focus

These answer:
- what tone is present?
- how activated is the person?
- how much control and flexibility is available?
- what is happening with reward, social orientation, and inward focus?

## Layer 2. Process signals

These answer:
- what mechanisms or styles seem active in the language?

Examples:
- threat_sensitivity
- perseverative_cognition
- relational_ambivalence
- social_evaluative_concern
- self_criticism
- imagery_density
- affective_implication

These are useful for saying not only what the state looks like, but how it seems to be organized.

## Layer 3. Computational axes

These answer:
- what broader process approximations might explain the state?

Examples:
- dopaminergic_pressure
- control_allocation
- volatility_expectancy
- prediction_error_weighting
- social_salience
- effort_cost_load

These help bridge language to motivation, effort, uncertainty, and salience.

## Layer 4. Higher-order factors

These answer:
- what covariance patterns best summarize the overall configuration?

Examples:
- negative_affectivity
- internalizing_distress
- detachment
- interpersonal_instability
- expressive_symbolization

These are summary layers and should not displace lower-level detail.

## Layer 5. Domain and context layers

These answer:
- where in life is this happening?
- how should time-scale and environment change interpretation?

Examples:
- work/proficiency
- relationship/romance
- family/social
- identity/integrity
- health/body
- same-day vs multiday vs long-horizon sequence

## What the LLM should understand about humans

The LLM should treat each BeSci output as part of a larger human ecology.

That ecology includes:

- the person's history
- the person's body
- the person's relationships
- the person's environment
- the person's values and self-concept
- the person's current role demands
- the person's style of expression

This means the LLM should not interpret text as though it were only a confession of mood.

It should instead ask:

- what is being signaled?
- through what channel is it being signaled?
- in what life area?
- at what time-scale?
- under what likely pressures?
- with what likely relevance to functioning, reward, attachment, or agency?

## Recommended retrieval design

If retrieval is added, do not retrieve the entire theory corpus each time.

Retrieve selectively:

### Always retrieve

- general BeSci interpretation rules
- current time-scale rule
- current domain rule if any

### Retrieve when relevant

- reward/motivation theory when reward or effort axes are strong
- social/interpersonal theory when social, attachment, or relational signals are strong
- expressive/poetic theory when imagery or affective implication is strong
- covariance theory when higher-order factors dominate the reading

## Best-practice summary

The strongest architecture is not:
- deterministic model here
- theory docs there
- LLM doing something else over the top

The strongest architecture is:
- deterministic structure generates state, process, axis, factor, and domain outputs
- theory retrieval provides the interpretation frame for those outputs
- the LLM explains only within that frame

That is how the scientific nuance becomes part of the fabric of interpretation rather than only part of the build history.
