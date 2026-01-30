import {
  Box,
  Button,
  Divider,
  FormControl,
  FormControlLabel,
  FormLabel,
  Paper,
  Radio,
  RadioGroup,
  Slider,
  Stack,
  TextField,
  Typography,
} from "@mui/material"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { useMemo, useState } from "react"

import {
  QuestionnairesService,
  type QuestionnaireResponseCreate,
} from "@/client"
import {
  frequencyOptions,
  likertOptions,
  sectionAStatements,
  sectionBDomains,
  sectionCStatements,
  sectionDStatements,
  sectionEStatements,
  sectionFStatements,
  sectionGAnxietyItems,
  sectionGDepressionItems,
  sectionHStatements,
} from "./questionnaireData"

type LikertValue = 1 | 2 | 3 | 4 | 5 | null
type FrequencyValue = 0 | 1 | 2 | 3 | null

interface DomainRating {
  name: string
  importance: number
  consistency: number
  note: string
}

interface OnboardingResponses {
  sectionA: {
    a1: string
    a2: string
    a3: string
    statements: Record<string, LikertValue>
  }
  sectionB: {
    domains: DomainRating[]
  }
  sectionC: {
    statements: Record<string, LikertValue>
    futureSelf: string
  }
  sectionD: {
    statements: Record<string, LikertValue>
  }
  sectionE: {
    statements: Record<string, LikertValue>
  }
  sectionF: {
    statements: Record<string, LikertValue>
    stressHelp: string
  }
  sectionG: {
    mood: Record<string, FrequencyValue>
    anxiety: Record<string, FrequencyValue>
  }
  sectionH: {
    statements: Record<string, LikertValue>
    overallThoughts: string
    supportive: string
  }
}

const buildEmptyLikertMap = (ids: string[]) =>
  ids.reduce<Record<string, LikertValue>>((acc, id) => {
    acc[id] = null
    return acc
  }, {})

const buildEmptyFrequencyMap = (ids: string[]) =>
  ids.reduce<Record<string, FrequencyValue>>((acc, id) => {
    acc[id] = null
    return acc
  }, {})

const initialDomains: DomainRating[] = sectionBDomains.map((name) => ({
  name,
  importance: 0,
  consistency: 0,
  note: "",
}))

const initialResponses: OnboardingResponses = {
  sectionA: {
    a1: "",
    a2: "",
    a3: "",
    statements: buildEmptyLikertMap(sectionAStatements.map((item) => item.id)),
  },
  sectionB: {
    domains: initialDomains,
  },
  sectionC: {
    statements: buildEmptyLikertMap(sectionCStatements.map((item) => item.id)),
    futureSelf: "",
  },
  sectionD: {
    statements: buildEmptyLikertMap(sectionDStatements.map((item) => item.id)),
  },
  sectionE: {
    statements: buildEmptyLikertMap(sectionEStatements.map((item) => item.id)),
  },
  sectionF: {
    statements: buildEmptyLikertMap(sectionFStatements.map((item) => item.id)),
    stressHelp: "",
  },
  sectionG: {
    mood: buildEmptyFrequencyMap(sectionGDepressionItems.map((item) => item.id)),
    anxiety: buildEmptyFrequencyMap(sectionGAnxietyItems.map((item) => item.id)),
  },
  sectionH: {
    statements: buildEmptyLikertMap(sectionHStatements.map((item) => item.id)),
    overallThoughts: "",
    supportive: "",
  },
}

const LikertList = ({
  items,
  values,
  onChange,
}: {
  items: { id: string; text: string }[]
  values: Record<string, LikertValue>
  onChange: (id: string, value: LikertValue) => void
}) => {
  return (
    <Stack spacing={2}>
      {items.map((item) => (
        <FormControl key={item.id}>
          <FormLabel sx={{ mb: 1 }}>{item.text}</FormLabel>
          <RadioGroup
            row
            value={values[item.id] ?? ""}
            onChange={(_, value) => onChange(item.id, Number(value) as LikertValue)}
          >
            {likertOptions.map((option) => (
              <FormControlLabel
                key={option.value}
                value={option.value}
                control={<Radio />}
                label={option.label}
              />
            ))}
          </RadioGroup>
        </FormControl>
      ))}
    </Stack>
  )
}

const FrequencyList = ({
  items,
  values,
  onChange,
}: {
  items: { id: string; text: string }[]
  values: Record<string, FrequencyValue>
  onChange: (id: string, value: FrequencyValue) => void
}) => {
  return (
    <Stack spacing={2}>
      {items.map((item) => (
        <FormControl key={item.id}>
          <FormLabel sx={{ mb: 1 }}>{item.text}</FormLabel>
          <RadioGroup
            row
            value={values[item.id] ?? ""}
            onChange={(_, value) => onChange(item.id, Number(value) as FrequencyValue)}
          >
            {frequencyOptions.map((option) => (
              <FormControlLabel
                key={option.value}
                value={option.value}
                control={<Radio />}
                label={option.label}
              />
            ))}
          </RadioGroup>
        </FormControl>
      ))}
    </Stack>
  )
}

const DomainRatingCard = ({
  domain,
  onChange,
}: {
  domain: DomainRating
  onChange: (next: DomainRating) => void
}) => {
  return (
    <Paper variant="outlined" sx={{ p: 2 }}>
      <Stack spacing={2}>
        <TextField
          label="Domain"
          value={domain.name}
          onChange={(event) => onChange({ ...domain, name: event.target.value })}
          fullWidth
        />
        <Box>
          <Typography variant="subtitle2" sx={{ mb: 1 }}>
            Importance
          </Typography>
          <Slider
            value={domain.importance}
            onChange={(_, value) => onChange({ ...domain, importance: value as number })}
            min={0}
            max={10}
            step={1}
            marks={[
              { value: 0, label: "0" },
              { value: 10, label: "10" },
            ]}
          />
        </Box>
        <Box>
          <Typography variant="subtitle2" sx={{ mb: 1 }}>
            Consistency
          </Typography>
          <Slider
            value={domain.consistency}
            onChange={(_, value) => onChange({ ...domain, consistency: value as number })}
            min={0}
            max={10}
            step={1}
            marks={[
              { value: 0, label: "0" },
              { value: 10, label: "10" },
            ]}
          />
        </Box>
        <TextField
          label="Optional note"
          value={domain.note}
          onChange={(event) => onChange({ ...domain, note: event.target.value })}
          fullWidth
          multiline
          minRows={2}
        />
      </Stack>
    </Paper>
  )
}

const buildPayload = (responses: OnboardingResponses) => {
  return {
    schema_version: "onboarding_v1",
    submitted_at: new Date().toISOString(),
    responses,
  }
}

const OnboardingQuestionnaire = () => {
  const [responses, setResponses] = useState<OnboardingResponses>(initialResponses)
  const queryClient = useQueryClient()
  const navigate = useNavigate()

  const mutation = useMutation({
    mutationFn: (payload: QuestionnaireResponseCreate) =>
      QuestionnairesService.createQuestionnaireResponse({ requestBody: payload }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["currentUser"] })
      navigate({ to: "/" })
    },
  })

  const payload = useMemo(() => buildPayload(responses), [responses])

  const handleSubmit = () => {
    mutation.mutate({
      kind: "onboarding",
      schema_version: "onboarding_v1",
      payload,
    })
  }

  return (
    <Stack spacing={4}>
      <Paper sx={{ p: 3 }}>
        <Typography variant="h4" sx={{ mb: 1 }}>
          Praestara Onboarding
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Values, self-concept, agency, regulation, and context baseline. About 12 to 18 minutes.
        </Typography>
      </Paper>

      <Paper sx={{ p: 3 }}>
        <Typography variant="h5" sx={{ mb: 2 }}>
          Section A - Values and direction
        </Typography>
        <Stack spacing={2} sx={{ mb: 3 }}>
          <TextField
            label="In your own words, what feels most worth building, protecting, or moving toward in your life right now"
            value={responses.sectionA.a1}
            onChange={(event) =>
              setResponses((prev) => ({
                ...prev,
                sectionA: { ...prev.sectionA, a1: event.target.value },
              }))
            }
            multiline
            minRows={3}
          />
          <TextField
            label="When you feel most like yourself, what are you usually doing"
            value={responses.sectionA.a2}
            onChange={(event) =>
              setResponses((prev) => ({
                ...prev,
                sectionA: { ...prev.sectionA, a2: event.target.value },
              }))
            }
            multiline
            minRows={3}
          />
          <TextField
            label="What do you tend to regret not doing more than doing"
            value={responses.sectionA.a3}
            onChange={(event) =>
              setResponses((prev) => ({
                ...prev,
                sectionA: { ...prev.sectionA, a3: event.target.value },
              }))
            }
            multiline
            minRows={3}
          />
        </Stack>
        <Divider sx={{ my: 3 }} />
        <LikertList
          items={sectionAStatements}
          values={responses.sectionA.statements}
          onChange={(id, value) =>
            setResponses((prev) => ({
              ...prev,
              sectionA: {
                ...prev.sectionA,
                statements: { ...prev.sectionA.statements, [id]: value },
              },
            }))
          }
        />
      </Paper>

      <Paper sx={{ p: 3 }}>
        <Typography variant="h5" sx={{ mb: 1 }}>
          Section B - Valued living across domains
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Rate importance and consistency for each domain on a 0 to 10 scale. You can rename any domain.
        </Typography>
        <Stack spacing={2}>
          {responses.sectionB.domains.map((domain, index) => (
            <DomainRatingCard
              key={`${domain.name}-${index}`}
              domain={domain}
              onChange={(next) =>
                setResponses((prev) => {
                  const updated = [...prev.sectionB.domains]
                  updated[index] = next
                  return { ...prev, sectionB: { domains: updated } }
                })
              }
            />
          ))}
        </Stack>
      </Paper>

      <Paper sx={{ p: 3 }}>
        <Typography variant="h5" sx={{ mb: 2 }}>
          Section C - Self-concept clarity
        </Typography>
        <LikertList
          items={sectionCStatements}
          values={responses.sectionC.statements}
          onChange={(id, value) =>
            setResponses((prev) => ({
              ...prev,
              sectionC: {
                ...prev.sectionC,
                statements: { ...prev.sectionC.statements, [id]: value },
              },
            }))
          }
        />
        <Divider sx={{ my: 3 }} />
        <TextField
          label="In a few sentences, describe the kind of person you are trying to become"
          value={responses.sectionC.futureSelf}
          onChange={(event) =>
            setResponses((prev) => ({
              ...prev,
              sectionC: { ...prev.sectionC, futureSelf: event.target.value },
            }))
          }
          multiline
          minRows={3}
          fullWidth
        />
      </Paper>

      <Paper sx={{ p: 3 }}>
        <Typography variant="h5" sx={{ mb: 2 }}>
          Section D - Agency and self-efficacy
        </Typography>
        <LikertList
          items={sectionDStatements}
          values={responses.sectionD.statements}
          onChange={(id, value) =>
            setResponses((prev) => ({
              ...prev,
              sectionD: {
                statements: { ...prev.sectionD.statements, [id]: value },
              },
            }))
          }
        />
      </Paper>

      <Paper sx={{ p: 3 }}>
        <Typography variant="h5" sx={{ mb: 2 }}>
          Section E - Motivation style
        </Typography>
        <LikertList
          items={sectionEStatements}
          values={responses.sectionE.statements}
          onChange={(id, value) =>
            setResponses((prev) => ({
              ...prev,
              sectionE: {
                statements: { ...prev.sectionE.statements, [id]: value },
              },
            }))
          }
        />
      </Paper>

      <Paper sx={{ p: 3 }}>
        <Typography variant="h5" sx={{ mb: 2 }}>
          Section F - Emotion regulation and reflection
        </Typography>
        <LikertList
          items={sectionFStatements}
          values={responses.sectionF.statements}
          onChange={(id, value) =>
            setResponses((prev) => ({
              ...prev,
              sectionF: {
                ...prev.sectionF,
                statements: { ...prev.sectionF.statements, [id]: value },
              },
            }))
          }
        />
        <Divider sx={{ my: 3 }} />
        <TextField
          label="When you are under stress, what tends to help you return to yourself"
          value={responses.sectionF.stressHelp}
          onChange={(event) =>
            setResponses((prev) => ({
              ...prev,
              sectionF: { ...prev.sectionF, stressHelp: event.target.value },
            }))
          }
          multiline
          minRows={3}
          fullWidth
        />
      </Paper>

      <Paper sx={{ p: 3 }}>
        <Typography variant="h5" sx={{ mb: 1 }}>
          Section G - Current context and symptom burden
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Answer based on the past week.
        </Typography>
        <Typography variant="h6" sx={{ mb: 2 }}>
          Mood and energy
        </Typography>
        <FrequencyList
          items={sectionGDepressionItems}
          values={responses.sectionG.mood}
          onChange={(id, value) =>
            setResponses((prev) => ({
              ...prev,
              sectionG: { ...prev.sectionG, mood: { ...prev.sectionG.mood, [id]: value } },
            }))
          }
        />
        <Divider sx={{ my: 3 }} />
        <Typography variant="h6" sx={{ mb: 2 }}>
          Anxiety burden
        </Typography>
        <FrequencyList
          items={sectionGAnxietyItems}
          values={responses.sectionG.anxiety}
          onChange={(id, value) =>
            setResponses((prev) => ({
              ...prev,
              sectionG: {
                ...prev.sectionG,
                anxiety: { ...prev.sectionG.anxiety, [id]: value },
              },
            }))
          }
        />
      </Paper>

      <Paper sx={{ p: 3 }}>
        <Typography variant="h5" sx={{ mb: 2 }}>
          Section H - Consent-bounded use and preferences
        </Typography>
        <LikertList
          items={sectionHStatements}
          values={responses.sectionH.statements}
          onChange={(id, value) =>
            setResponses((prev) => ({
              ...prev,
              sectionH: {
                ...prev.sectionH,
                statements: { ...prev.sectionH.statements, [id]: value },
              },
            }))
          }
        />
        <Divider sx={{ my: 3 }} />
        <TextField
          label="What are your overall thoughts and feelings about this program"
          value={responses.sectionH.overallThoughts}
          onChange={(event) =>
            setResponses((prev) => ({
              ...prev,
              sectionH: { ...prev.sectionH, overallThoughts: event.target.value },
            }))
          }
          multiline
          minRows={3}
          fullWidth
          sx={{ mb: 3 }}
        />
        <TextField
          label="What would make this system feel supportive rather than intrusive"
          value={responses.sectionH.supportive}
          onChange={(event) =>
            setResponses((prev) => ({
              ...prev,
              sectionH: { ...prev.sectionH, supportive: event.target.value },
            }))
          }
          multiline
          minRows={3}
          fullWidth
        />
      </Paper>

      <Box sx={{ display: "flex", justifyContent: "space-between", pb: 4 }}>
        <Button variant="outlined" onClick={() => navigate({ to: "/" })}>
          Back to dashboard
        </Button>
        <Button
          variant="contained"
          onClick={handleSubmit}
          disabled={mutation.isPending}
        >
          {mutation.isPending ? "Submitting..." : "Submit onboarding"}
        </Button>
      </Box>
    </Stack>
  )
}

export default OnboardingQuestionnaire
