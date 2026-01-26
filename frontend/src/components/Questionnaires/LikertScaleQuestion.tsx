import { Box, Radio, RadioGroup, Stack, Typography } from "@mui/material"
import { Field } from "../ui/field"

interface LikertScaleQuestionProps {
  questionText: string
  questionNumber: number
  scaleType: "LIKERT_5" | "LIKERT_7" | "YES_NO"
  isRequired: boolean
  value: number | null
  onChange: (value: number) => void
  error?: string
}

const LIKERT_5_LABELS = [
  "Strongly Disagree",
  "Disagree",
  "Neutral",
  "Agree",
  "Strongly Agree",
]

const LIKERT_7_LABELS = [
  "Strongly Disagree",
  "Disagree",
  "Somewhat Disagree",
  "Neutral",
  "Somewhat Agree",
  "Agree",
  "Strongly Agree",
]

const YES_NO_LABELS = ["No", "Yes"]

export function LikertScaleQuestion({
  questionText,
  questionNumber,
  scaleType,
  isRequired,
  value,
  onChange,
  error,
}: LikertScaleQuestionProps) {
  const getLabels = () => {
    switch (scaleType) {
      case "LIKERT_5":
        return LIKERT_5_LABELS
      case "LIKERT_7":
        return LIKERT_7_LABELS
      case "YES_NO":
        return YES_NO_LABELS
      default:
        return LIKERT_5_LABELS
    }
  }

  const labels = getLabels()

  return (
    <Box
      sx={{
        p: 3,
        mb: 3,
        border: "1px solid",
        borderColor: error ? "error.main" : "divider",
        borderRadius: 2,
        backgroundColor: "background.paper",
      }}
    >
      <Field
        label={
          <Typography variant="h6" component="div">
            {questionNumber}. {questionText}
            {isRequired && (
              <Typography component="span" color="error.main" sx={{ ml: 1 }}>
                *
              </Typography>
            )}
          </Typography>
        }
        invalid={!!error}
        errorText={error}
      >
        <RadioGroup
          value={value?.toString() || ""}
          onChange={(e) => onChange(parseInt(e.target.value))}
        >
          <Stack
            direction={{ base: "column", md: "row" }}
            spacing={2}
            mt={3}
            justifyContent="space-between"
            flexWrap="wrap"
          >
            {labels.map((label, index) => (
              <Box
                key={index}
                sx={{
                  flex: { base: "1 1 100%", md: `1 1 ${100 / labels.length}%` },
                  minWidth: { base: "100%", md: "120px" },
                }}
              >
                <Box
                  sx={{
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    p: 2,
                    border: "1px solid",
                    borderColor: value === index + 1 ? "primary.main" : "divider",
                    borderRadius: 1,
                    backgroundColor: value === index + 1 ? "primary.50" : "transparent",
                    cursor: "pointer",
                    transition: "all 0.2s",
                    "&:hover": {
                      borderColor: "primary.main",
                      backgroundColor: "primary.50",
                    },
                  }}
                  onClick={() => onChange(index + 1)}
                >
                  <Radio value={(index + 1).toString()} />
                  <Typography
                    variant="body2"
                    textAlign="center"
                    sx={{ mt: 1, fontWeight: value === index + 1 ? 600 : 400 }}
                  >
                    {label}
                  </Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5 }}>
                    {index + 1}
                  </Typography>
                </Box>
              </Box>
            ))}
          </Stack>
        </RadioGroup>
      </Field>
    </Box>
  )
}
