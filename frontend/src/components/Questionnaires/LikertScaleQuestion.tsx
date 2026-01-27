import { Box, Radio, RadioGroup, Typography } from "@mui/material"
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
  const isYesNo = scaleType === "YES_NO"

  return (
    <Box
      sx={{
        py: 3,
        mb: 3,
        borderBottom: "1px solid",
        borderColor: "divider",
      }}
    >
      <Field
        label={
          <Typography variant="h6" component="div" sx={{ mb: 2 }}>
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
          <Box
            sx={{
              display: "flex",
              flexWrap: "wrap",
              gap: 2,
              mt: 2,
              justifyContent: "center",
            }}
          >
            {labels.map((label, index) => (
              <Box
                key={index}
                sx={{
                  flex: "0 0 auto",
                  width: "130px",
                }}
              >
                <Box
                  sx={{
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    justifyContent: "center",
                    p: 2,
                    height: "120px",
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
                  <Radio value={(index + 1).toString()} sx={{ mb: 1 }} />
                  <Typography
                    variant="body2"
                    textAlign="center"
                    sx={{ 
                      fontWeight: value === index + 1 ? 600 : 400,
                      wordBreak: "break-word",
                      flex: 1,
                      display: "flex",
                      alignItems: "center",
                      px: 1,
                    }}
                  >
                    {label}
                  </Typography>
                  {!isYesNo && (
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5 }}>
                      {index + 1}
                    </Typography>
                  )}
                </Box>
              </Box>
            ))}
          </Box>
        </RadioGroup>
      </Field>
    </Box>
  )
}
