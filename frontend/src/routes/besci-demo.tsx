import {
  Alert,
  Box,
  Button,
  Container,
  Paper,
  Stack,
  TextField,
  Typography,
} from "@mui/material"
import { useMutation } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { useMemo, useState } from "react"

export const Route = createFileRoute("/besci-demo")({
  component: BeSciDemoPage,
})

type BeSciState = {
  arousal: number
  valence: number
  control: number
  volatility: number
  social_orientation: number
  reward_seeking: number
  cognitive_flexibility: number
  self_focus: number
}

type BeSciSignal = {
  name: string
  score: number
  rationale: string
}

type BeSciEvidence = {
  name: string
  summary: string
  matches: string[]
}

type BeSciNarrativeBlock = {
  lens: string
  title: string
  body: string
}

type BeSciDomainAnalysis = {
  domain: string
  matched_terms: string[]
  sample_count: number
  current_state: BeSciState
  trajectory_score: number
  summary: string
  higher_order_factors?: BeSciSignal[]
}

type BeSciAlignmentSignal = {
  name: string
  score: number
  rationale: string
  related_domains: string[]
}

type BeSciAnalysis = {
  sample_count: number
  model_version: string
  representation_backend: string
  summary_backend?: string
  instant_state: BeSciState
  calibrated_state: BeSciState
  current_state: BeSciState
  baseline_state: BeSciState
  recent_state: BeSciState
  change_from_baseline: BeSciState
  change_from_recent: BeSciState
  trajectory_score: number
  summary: string
  current_state_summary: string
  temporal_scope: string
  total_summary: string
  narrative_blocks?: BeSciNarrativeBlock[]
  signals: BeSciSignal[]
  dimension_signals?: BeSciSignal[]
  process_signals?: BeSciSignal[]
  computational_axes?: BeSciSignal[]
  higher_order_factors?: BeSciSignal[]
  domain_analyses?: BeSciDomainAnalysis[]
  alignment_signals?: BeSciAlignmentSignal[]
  evidence?: BeSciEvidence[]
  feature_summary?: {
    lexical_density: number
    semantic_density: number
    temporal_balance: number
    token_count: number
    calibration_confidence: number
    contextual_richness: number
    signal_coverage: number
  } | null
}

type DemoResponse = {
  analysis: BeSciAnalysis
}

const EXPRESSIVE_SIGNAL_NAMES = new Set([
  "imagery_density",
  "sensory_grounding",
  "affective_explicitness",
  "affective_implication",
  "abstract_reflection",
])

const apiBase = import.meta.env.DEV
  ? "/api/v1"
  : import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1"

const CASE_A = [
  "I have been feeling overwhelmed and scattered all week. I keep thinking about everything I am not getting done.",
  "I felt isolated today and stayed home even though a friend invited me out. I just did not have the energy.",
  "This morning I still felt unsure, but I made a small plan and followed through on one task.",
  "I feel a little steadier tonight. I am not all the way better, but I do feel more grounded and hopeful.",
].join("\n")

const CASE_B = [
  "I feel flat lately. Nothing sounds especially rewarding and I mostly go through the motions.",
  "I skipped my workout again and ignored a message from my sister. It all felt like too much effort.",
  "Today I managed to walk for ten minutes and answer one message. It was small, but it felt a little easier.",
  "I am still tired, but I want to keep trying and see if a routine helps me feel more like myself.",
].join("\n")

const formatScore = (value: number) => `${value >= 0 ? "+" : ""}${value.toFixed(2)}`

async function analyzeText(rawText: string): Promise<DemoResponse> {
  const samples = rawText
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((text) => ({ text }))

  const response = await fetch(`${apiBase}/besci/demo/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ samples }),
  })

  if (!response.ok) {
    throw new Error(`BeSci demo request failed with status ${response.status}`)
  }

  return response.json()
}

function BeSciDemoPage() {
  const [rawText, setRawText] = useState("")

  const mutation = useMutation({
    mutationFn: analyzeText,
  })

  const dimensions = useMemo(() => {
    const analysis = mutation.data?.analysis
    if (!analysis) return []
    return [
      ["Arousal", analysis.instant_state.arousal, analysis.calibrated_state.arousal, analysis.change_from_baseline.arousal],
      ["Valence", analysis.instant_state.valence, analysis.calibrated_state.valence, analysis.change_from_baseline.valence],
      ["Control", analysis.instant_state.control, analysis.calibrated_state.control, analysis.change_from_baseline.control],
      ["Volatility", analysis.instant_state.volatility, analysis.calibrated_state.volatility, analysis.change_from_baseline.volatility],
      ["Social", analysis.instant_state.social_orientation, analysis.calibrated_state.social_orientation, analysis.change_from_baseline.social_orientation],
      ["Reward", analysis.instant_state.reward_seeking, analysis.calibrated_state.reward_seeking, analysis.change_from_baseline.reward_seeking],
      ["Flexibility", analysis.instant_state.cognitive_flexibility, analysis.calibrated_state.cognitive_flexibility, analysis.change_from_baseline.cognitive_flexibility],
      ["Self-focus", analysis.instant_state.self_focus, analysis.calibrated_state.self_focus, analysis.change_from_baseline.self_focus],
    ] as Array<[string, number, number, number]>
  }, [mutation.data])

  return (
    <Container maxWidth="lg" sx={{ py: 6 }}>
      <Stack spacing={3}>
        <Box>
          <Typography variant="h3" sx={{ fontWeight: 700, mb: 1 }}>
            BeSci Demo
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Local qualitative-text sandbox for Praestara. Paste one longitudinal entry per line and
            inspect the passive, non-diagnostic trajectory estimate from your own text.
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            This demo is now running on BeSci v4.6: the v4.5 backbone plus BeSci4-informed
            expressive-style logic for imagery, symbolism, sensory grounding, and indirect emotion.
          </Typography>
        </Box>

        <Paper sx={{ p: 3 }}>
          <Stack spacing={2}>
            <Typography variant="h6">Qualitative text samples</Typography>
            <TextField
              multiline
              minRows={10}
              fullWidth
              value={rawText}
              onChange={(event) => setRawText(event.target.value)}
              placeholder="Paste one time-ordered entry per line. This demo analyzes exactly what you provide."
              helperText="No sample text is required. Use one time-ordered sample per line."
            />
            <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
              <Button variant="outlined" onClick={() => setRawText("")}>
                Clear
              </Button>
              <Button variant="outlined" onClick={() => setRawText(CASE_A)}>
                Load Case A
              </Button>
              <Button variant="outlined" onClick={() => setRawText(CASE_B)}>
                Load Case B
              </Button>
              <Button
                variant="contained"
                onClick={() => mutation.mutate(rawText)}
                disabled={mutation.isPending || !rawText.trim()}
              >
                {mutation.isPending ? "Analyzing..." : "Run BeSci"}
              </Button>
            </Stack>
          </Stack>
        </Paper>

        {mutation.isError ? (
          <Alert severity="error">
            {mutation.error.message}. If this keeps happening, the local backend may not be running.
          </Alert>
        ) : null}

        {mutation.data ? (
          <>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ mb: 1 }}>
                Summary
              </Typography>
              <Typography variant="body1" sx={{ mb: 2, whiteSpace: "pre-wrap" }}>
                {mutation.data.analysis.current_state_summary}
              </Typography>
              <Typography variant="body1" sx={{ mb: 2, whiteSpace: "pre-wrap" }}>
                {mutation.data.analysis.summary}
              </Typography>
              <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
                <Paper variant="outlined" sx={{ p: 2, flex: 1 }}>
                  <Typography variant="overline" color="text.secondary">
                    Trajectory score
                  </Typography>
                  <Typography variant="h4">
                    {formatScore(mutation.data.analysis.trajectory_score)}
                  </Typography>
                </Paper>
                <Paper variant="outlined" sx={{ p: 2, flex: 1 }}>
                  <Typography variant="overline" color="text.secondary">
                    Sample count
                  </Typography>
                  <Typography variant="h4">
                    {mutation.data.analysis.sample_count}
                  </Typography>
                </Paper>
                <Paper variant="outlined" sx={{ p: 2, flex: 1 }}>
                  <Typography variant="overline" color="text.secondary">
                    Representation backend
                  </Typography>
                  <Typography variant="h6">
                    {mutation.data.analysis.representation_backend}
                  </Typography>
                </Paper>
                <Paper variant="outlined" sx={{ p: 2, flex: 1 }}>
                  <Typography variant="overline" color="text.secondary">
                    Summary backend
                  </Typography>
                  <Typography variant="h6">
                    {mutation.data.analysis.summary_backend ?? "deterministic_template"}
                  </Typography>
                </Paper>
                <Paper variant="outlined" sx={{ p: 2, flex: 1 }}>
                  <Typography variant="overline" color="text.secondary">
                    Calibration confidence
                  </Typography>
                  <Typography variant="h6">
                    {mutation.data.analysis.feature_summary
                      ? `${Math.round(mutation.data.analysis.feature_summary.calibration_confidence * 100)}%`
                      : "--"}
                  </Typography>
                </Paper>
              </Stack>
              <Stack direction={{ xs: "column", md: "row" }} spacing={2} sx={{ mt: 2 }}>
                <Paper variant="outlined" sx={{ p: 2, flex: 1 }}>
                  <Typography variant="overline" color="text.secondary">
                    Signal coverage
                  </Typography>
                  <Typography variant="h6">
                    {mutation.data.analysis.feature_summary
                      ? `${Math.round(mutation.data.analysis.feature_summary.signal_coverage * 100)}%`
                      : "--"}
                  </Typography>
                </Paper>
                <Paper variant="outlined" sx={{ p: 2, flex: 1 }}>
                  <Typography variant="overline" color="text.secondary">
                    Context richness
                  </Typography>
                  <Typography variant="h6">
                    {mutation.data.analysis.feature_summary
                      ? mutation.data.analysis.feature_summary.contextual_richness.toFixed(2)
                      : "--"}
                  </Typography>
                </Paper>
              </Stack>
            </Paper>

            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Time-Scale Narrative
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                BeSci now separates present-state reading from the time-scale the text appears to cover, so a
                same-day fluctuation is not interpreted the same way as a multi-day shift.
              </Typography>
              <Typography sx={{ fontFamily: "monospace", fontSize: 13, mb: 2 }}>
                temporal_scope: {mutation.data.analysis.temporal_scope}
              </Typography>
              <Stack spacing={2}>
                {(mutation.data.analysis.narrative_blocks ?? []).map((block) => (
                  <Paper key={block.lens} variant="outlined" sx={{ p: 2 }}>
                    <Typography sx={{ fontWeight: 600, mb: 0.5 }}>{block.title}</Typography>
                    <Typography color="text.secondary">{block.body}</Typography>
                  </Paper>
                ))}
              </Stack>
            </Paper>

            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Current state vs calibrated state
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                The instant state is what the latest entry suggests by itself. The calibrated state blends that with
                recent and baseline history so the estimate becomes more person-specific over time.
              </Typography>
              <Stack spacing={1}>
                {dimensions.map(([label, instantValue, calibratedValue, baselineDelta]) => (
                  <Box
                    key={label}
                    sx={{
                      display: "grid",
                      gridTemplateColumns: { xs: "1fr 1fr", md: "1.2fr 1fr 1fr 1fr" },
                      gap: 1,
                      py: 1,
                      borderBottom: "1px solid",
                      borderColor: "divider",
                    }}
                  >
                    <Typography>{label}</Typography>
                    <Typography sx={{ fontFamily: "monospace" }}>
                      Instant {formatScore(instantValue)}
                    </Typography>
                    <Typography sx={{ fontFamily: "monospace" }}>
                      Calibrated {formatScore(calibratedValue)}
                    </Typography>
                    <Typography sx={{ fontFamily: "monospace" }}>
                      Delta {formatScore(baselineDelta)}
                    </Typography>
                  </Box>
                ))}
              </Stack>
            </Paper>

            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Dimension interpretation
              </Typography>
              <Stack spacing={2}>
                {(mutation.data.analysis.dimension_signals ?? []).map((signal) => (
                  <Paper key={signal.name} variant="outlined" sx={{ p: 2 }}>
                    <Typography sx={{ fontWeight: 600 }}>
                      {signal.name} ({formatScore(signal.score)})
                    </Typography>
                    <Typography color="text.secondary">{signal.rationale}</Typography>
                  </Paper>
                ))}
              </Stack>
            </Paper>

            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Process signals
              </Typography>
              <Stack spacing={2}>
                {(mutation.data.analysis.process_signals ?? []).map((signal) => (
                  <Paper key={signal.name} variant="outlined" sx={{ p: 2 }}>
                    <Typography sx={{ fontWeight: 600 }}>
                      {signal.name} ({formatScore(signal.score)})
                    </Typography>
                    <Typography color="text.secondary">{signal.rationale}</Typography>
                  </Paper>
                ))}
              </Stack>
            </Paper>

            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Expressive style layer
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                This layer is where BeSci tries to respect figurative or qualitative writing. It
                separates direct emotion naming from imagery-driven, sensory, and more symbolic
                expression so the summary is not limited to blunt literal language.
              </Typography>
              <Stack spacing={2}>
                {(mutation.data.analysis.process_signals ?? [])
                  .filter((signal) => EXPRESSIVE_SIGNAL_NAMES.has(signal.name))
                  .map((signal) => (
                    <Paper key={signal.name} variant="outlined" sx={{ p: 2 }}>
                      <Typography sx={{ fontWeight: 600 }}>
                        {signal.name} ({formatScore(signal.score)})
                      </Typography>
                      <Typography color="text.secondary">{signal.rationale}</Typography>
                    </Paper>
                  ))}
              </Stack>
            </Paper>

            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Neuro-computational axes
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                These are deterministic approximations inspired by computational psychiatry and
                reward-control models. They are not brain measurements; they are structured
                intermediates that help BeSci refine the final psychological state estimate.
              </Typography>
              <Stack spacing={2}>
                {(mutation.data.analysis.computational_axes ?? []).map((signal) => (
                  <Paper key={signal.name} variant="outlined" sx={{ p: 2 }}>
                    <Typography sx={{ fontWeight: 600 }}>
                      {signal.name} ({formatScore(signal.score)})
                    </Typography>
                    <Typography color="text.secondary">{signal.rationale}</Typography>
                  </Paper>
                ))}
              </Stack>
            </Paper>

            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Higher-order factors
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                These summarize broader covariance patterns across the base dimensions and process
                channels. They are still passive and non-diagnostic.
              </Typography>
              <Stack spacing={2}>
                {(mutation.data.analysis.higher_order_factors ?? []).map((signal) => (
                  <Paper key={signal.name} variant="outlined" sx={{ p: 2 }}>
                    <Typography sx={{ fontWeight: 600 }}>
                      {signal.name} ({formatScore(signal.score)})
                    </Typography>
                    <Typography color="text.secondary">{signal.rationale}</Typography>
                  </Paper>
                ))}
              </Stack>
            </Paper>

            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Life-domain analyses
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                This keeps different areas of life from cancelling each other out. A strong day at
                work and a painful relationship event can both be true at the same time.
              </Typography>
              {mutation.data.analysis.domain_analyses?.length ? (
                <Stack spacing={2}>
                  {mutation.data.analysis.domain_analyses.map((domain) => (
                    <Paper key={domain.domain} variant="outlined" sx={{ p: 2 }}>
                      <Typography sx={{ fontWeight: 600, mb: 0.5 }}>
                        {domain.domain} ({formatScore(domain.trajectory_score)})
                      </Typography>
                      <Typography color="text.secondary" sx={{ mb: 1 }}>
                        {domain.summary}
                      </Typography>
                      <Typography sx={{ fontFamily: "monospace", fontSize: 13, mb: 0.5 }}>
                        matched: {domain.matched_terms.join(", ")}
                      </Typography>
                      <Typography sx={{ fontFamily: "monospace", fontSize: 13 }}>
                        valence {formatScore(domain.current_state.valence)} | control{" "}
                        {formatScore(domain.current_state.control)} | arousal{" "}
                        {formatScore(domain.current_state.arousal)}
                      </Typography>
                    </Paper>
                  ))}
                </Stack>
              ) : (
                <Typography color="text.secondary">
                  No distinct life-domain clusters were detected in this sample set.
                </Typography>
              )}
            </Paper>

            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Alignment signals
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                These signals estimate whether the current text is split across domains, concentrated
                in personally important value areas, or resonating with tracked self-concept themes.
              </Typography>
              {mutation.data.analysis.alignment_signals?.length ? (
                <Stack spacing={2}>
                  {mutation.data.analysis.alignment_signals.map((signal) => (
                    <Paper key={signal.name} variant="outlined" sx={{ p: 2 }}>
                      <Typography sx={{ fontWeight: 600 }}>
                        {signal.name} ({formatScore(signal.score)})
                      </Typography>
                      <Typography color="text.secondary" sx={{ mb: 1 }}>
                        {signal.rationale}
                      </Typography>
                      {signal.related_domains.length ? (
                        <Typography sx={{ fontFamily: "monospace", fontSize: 13 }}>
                          {signal.related_domains.join(", ")}
                        </Typography>
                      ) : null}
                    </Paper>
                  ))}
                </Stack>
              ) : (
                <Typography color="text.secondary">
                  No additional alignment signals were computed for this sample set.
                </Typography>
              )}
            </Paper>

            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Evidence map
              </Typography>
              {mutation.data.analysis.evidence?.length ? (
                <Stack spacing={2}>
                  {mutation.data.analysis.evidence.map((item) => (
                    <Paper key={item.name} variant="outlined" sx={{ p: 2 }}>
                      <Typography sx={{ fontWeight: 600 }}>{item.name}</Typography>
                      <Typography color="text.secondary" sx={{ mb: 1 }}>
                        {item.summary}
                      </Typography>
                      <Typography sx={{ fontFamily: "monospace", fontSize: 13 }}>
                        {item.matches.join(", ")}
                      </Typography>
                    </Paper>
                  ))}
                </Stack>
              ) : (
                <Typography color="text.secondary">
                  No direct lexical or phrase evidence was captured for this sample set.
                </Typography>
              )}
            </Paper>

            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Pattern flags
              </Typography>
              {mutation.data.analysis.signals.length === 0 ? (
                <Typography color="text.secondary">
                  No strong soft-pattern flags were detected for this sample set.
                </Typography>
              ) : (
                <Stack spacing={2}>
                  {mutation.data.analysis.signals.map((signal) => (
                    <Paper key={signal.name} variant="outlined" sx={{ p: 2 }}>
                      <Typography sx={{ fontWeight: 600 }}>
                        {signal.name} ({formatScore(signal.score)})
                      </Typography>
                      <Typography color="text.secondary">{signal.rationale}</Typography>
                    </Paper>
                  ))}
                </Stack>
              )}
            </Paper>
          </>
        ) : null}
      </Stack>
    </Container>
  )
}
