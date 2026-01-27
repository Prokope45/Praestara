import { Box, Radio, RadioGroup, Typography, TextField } from "@mui/material"
import { Field } from "../ui/field"

interface LikertScaleQuestionProps {
  questionText: string
  questionNumber: number
  scaleType: "LIKERT_5" | "LIKERT_7" | "YES_NO" | "CUSTOM_NUMERIC"
  isRequired: boolean
  value: number | null
  onChange: (value: number) => void
  error?: string
  customMinValue?: number | null
  customMaxValue?: number | null
  customUnitLabel?: string | null
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
  customMinValue,
  customMaxValue,
  customUnitLabel,
}: LikertScaleQuestionProps) {
  const getLabels = () => {
    switch (scaleType) {
      case "LIKERT_5":
        return LIKERT_5_LABELS
      case "LIKERT_7":
        return LIKERT_7_LABELS
      case "YES_NO":
        return YES_NO_LABELS
      case "CUSTOM_NUMERIC":
        return []
      default:
        return LIKERT_5_LABELS
    }
  }

  const labels = getLabels()
  const isYesNo = scaleType === "YES_NO"
  const isCustomNumeric = scaleType === "CUSTOM_NUMERIC"

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
        {isCustomNumeric ? (
          (() => {
            const min = customMinValue ?? 0
            const max = customMaxValue ?? 100
            const range = max - min + 1
            
            // If range is 10 (inclusive 0) or less, show as radio buttons like Likert scale
            if (range <= 11) {
              const options = Array.from({ length: range }, (_, i) => min + i)
              
              return (
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
                    {options.map((optionValue) => (
                      <Box
                        key={optionValue}
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
                            borderColor: value === optionValue ? "primary.main" : "divider",
                            borderRadius: 1,
                            backgroundColor: value === optionValue ? "primary.50" : "transparent",
                            cursor: "pointer",
                            transition: "all 0.2s",
                            "&:hover": {
                              borderColor: "primary.main",
                              backgroundColor: "primary.50",
                            },
                          }}
                          onClick={() => onChange(optionValue)}
                        >
                          <Radio value={optionValue.toString()} sx={{ mb: 1 }} />
                          <Typography
                            variant="h6"
                            textAlign="center"
                            sx={{ 
                              fontWeight: value === optionValue ? 600 : 400,
                            }}
                          >
                            {optionValue}
                          </Typography>
                          {customUnitLabel && (
                            <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5 }}>
                              {customUnitLabel}
                            </Typography>
                          )}
                        </Box>
                      </Box>
                    ))}
                  </Box>
                </RadioGroup>
              )
            }
            
            // For ranges > 10, show number input
            return (
              <Box sx={{ mt: 2, maxWidth: 400 }}>
                <TextField
                  type="number"
                  value={value ?? ""}
                  onChange={(e) => {
                    const val = e.target.value ? parseInt(e.target.value) : null
                    if (val !== null && val >= min && val <= max) {
                      onChange(val)
                    }
                  }}
                  fullWidth
                  label={customUnitLabel ? `Enter value (${customUnitLabel})` : "Enter value"}
                  helperText={`Range: ${min} - ${max}${customUnitLabel ? ` ${customUnitLabel}` : ""}`}
                  inputProps={{
                    min,
                    max,
                  }}
                />
              </Box>
            )
          })()
        ) : (
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
        )}
      </Field>
    </Box>
  )
}
