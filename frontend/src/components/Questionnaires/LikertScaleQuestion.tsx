import {
  Box,
  Paper,
  Radio,
  RadioGroup,
  Slider,
  Stack,
  TextField,
  Typography,
} from "@mui/material"
import { Field } from "../ui/field"

interface LikertScaleQuestionProps {
  questionText: string
  questionNumber: number
  scaleType:
    | "LIKERT_5"
    | "LIKERT_7"
    | "YES_NO"
    | "CUSTOM_NUMERIC"
    | "TEXT"
    | "FREQUENCY"
    | "DOMAIN_RATING"
  isRequired: boolean
  value: any
  onChange: (value: any) => void
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

const FREQUENCY_LABELS = [
  "Not at all",
  "Several days",
  "More than half the days",
  "Nearly every day",
]

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
  const isText = scaleType === "TEXT"
  const isFrequency = scaleType === "FREQUENCY"
  const isDomainRating = scaleType === "DOMAIN_RATING"

  // Handle TEXT type
  if (isText) {
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
          <TextField
            value={value || ""}
            onChange={(e) => onChange(e.target.value)}
            multiline
            minRows={3}
            fullWidth
            placeholder="Type your answer here..."
            sx={{
              mt: 2,
              "& textarea": { resize: "vertical" },
            }}
          />
        </Field>
      </Box>
    )
  }

  // Handle FREQUENCY type
  if (isFrequency) {
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
            onChange={(e) => onChange(Number.parseInt(e.target.value))}
          >
            <Box
              sx={{
                display: "flex",
                flexDirection: { xs: "column", md: "row" },
                gap: 2,
                mt: 2,
                width: "100%",
              }}
            >
              {FREQUENCY_LABELS.map((label, index) => (
                <Box
                  key={index}
                  sx={{ flex: 1 }}
                >
                  <Box
                    sx={{
                      display: "flex",
                      flexDirection: { xs: "row", md: "column" },
                      alignItems: "center",
                      justifyContent: { xs: "flex-start", md: "center" },
                      p: 2,
                      height: { xs: "auto", md: "120px" },
                      border: "1px solid",
                      borderColor: value === index ? "primary.main" : "divider",
                      borderRadius: 1,
                      backgroundColor:
                        value === index ? "primary.50" : "transparent",
                      cursor: "pointer",
                      transition: "all 0.2s",
                      "&:hover": {
                        borderColor: "primary.main",
                        backgroundColor: "primary.50",
                      },
                    }}
                    onClick={() => onChange(index)}
                  >
                    <Radio value={index.toString()} sx={{ mb: { xs: 0, md: 1 }, mr: { xs: 2, md: 0 } }} />
                    <Typography
                      variant="body2"
                      textAlign={{ xs: "left", md: "center" }}
                      sx={{
                        fontWeight: value === index ? 600 : 400,
                        wordBreak: "break-word",
                        flex: 1,
                        display: "flex",
                        alignItems: "center",
                        px: { xs: 0, md: 1 },
                      }}
                    >
                      <Box component="span" sx={{ display: { xs: "inline", md: "none" }, mr: 1 }}>
                        {index} -
                      </Box>
                      {label}
                    </Typography>
                    <Typography
                      variant="caption"
                      color="text.secondary"
                      sx={{ mt: 0.5, display: { xs: "none", md: "block" } }}
                    >
                      {index}
                    </Typography>
                  </Box>
                </Box>
              ))}
            </Box>
          </RadioGroup>
        </Field>
      </Box>
    )
  }

  // Handle DOMAIN_RATING type
  if (isDomainRating) {
    const domainValue = value || { importance: 0, consistency: 0, note: "" }

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
          <Paper variant="outlined" sx={{ p: 3, mt: 2 }}>
            <Stack spacing={3}>
              <Box>
                <Typography variant="subtitle2" sx={{ mb: 2 }}>
                  Importance (0-10)
                </Typography>
                <Slider
                  value={domainValue.importance}
                  onChange={(_, newValue) =>
                    onChange({ ...domainValue, importance: newValue as number })
                  }
                  min={0}
                  max={10}
                  step={1}
                  marks={[
                    { value: 0, label: "0" },
                    { value: 5, label: "5" },
                    { value: 10, label: "10" },
                  ]}
                  valueLabelDisplay="auto"
                />
              </Box>
              <Box>
                <Typography variant="subtitle2" sx={{ mb: 2 }}>
                  Consistency (0-10)
                </Typography>
                <Slider
                  value={domainValue.consistency}
                  onChange={(_, newValue) =>
                    onChange({
                      ...domainValue,
                      consistency: newValue as number,
                    })
                  }
                  min={0}
                  max={10}
                  step={1}
                  marks={[
                    { value: 0, label: "0" },
                    { value: 5, label: "5" },
                    { value: 10, label: "10" },
                  ]}
                  valueLabelDisplay="auto"
                />
              </Box>
              <TextField
                label="Optional note"
                value={domainValue.note}
                onChange={(e) =>
                  onChange({ ...domainValue, note: e.target.value })
                }
                multiline
                minRows={2}
                fullWidth
              />
            </Stack>
          </Paper>
        </Field>
      </Box>
    )
  }

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
                  onChange={(e) => onChange(Number.parseInt(e.target.value))}
                >
                  <Box
                    sx={{
                      display: "flex",
                      flexDirection: { xs: "column", md: "row" },
                      gap: 2,
                      mt: 2,
                      width: "100%",
                    }}
                  >
                    {options.map((optionValue) => (
                      <Box
                        key={optionValue}
                        sx={{ flex: 1 }}
                      >
                        <Box
                          sx={{
                            display: "flex",
                            flexDirection: { xs: "row", md: "column" },
                            alignItems: "center",
                            justifyContent: { xs: "flex-start", md: "center" },
                            p: 2,
                            height: { xs: "auto", md: "120px" },
                            border: "1px solid",
                            borderColor:
                              value === optionValue
                                ? "primary.main"
                                : "divider",
                            borderRadius: 1,
                            backgroundColor:
                              value === optionValue
                                ? "primary.50"
                                : "transparent",
                            cursor: "pointer",
                            transition: "all 0.2s",
                            "&:hover": {
                              borderColor: "primary.main",
                              backgroundColor: "primary.50",
                            },
                          }}
                          onClick={() => onChange(optionValue)}
                        >
                          <Radio
                            value={optionValue.toString()}
                            sx={{ mb: { xs: 0, md: 1 }, mr: { xs: 2, md: 0 } }}
                          />
                          <Typography
                            variant="h6"
                            textAlign={{ xs: "left", md: "center" }}
                            sx={{
                              fontWeight: value === optionValue ? 600 : 400,
                              flex: { xs: 1, md: "unset" },
                            }}
                          >
                            {optionValue}
                            {customUnitLabel && (
                              <Box component="span" sx={{ ml: 1, display: { xs: "inline", md: "none" } }}>
                                {customUnitLabel}
                              </Box>
                            )}
                          </Typography>
                          {customUnitLabel && (
                            <Typography
                              variant="caption"
                              color="text.secondary"
                              sx={{ mt: 0.5, display: { xs: "none", md: "block" } }}
                            >
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
              <Box sx={{ mt: 2, maxWidth: "100%", width: { xs: "100%", sm: 400 } }}>
                <TextField
                  type="number"
                  value={value ?? ""}
                  onChange={(e) => {
                    const val = e.target.value
                      ? Number.parseInt(e.target.value)
                      : null
                    if (val !== null && val >= min && val <= max) {
                      onChange(val)
                    }
                  }}
                  fullWidth
                  label={
                    customUnitLabel
                      ? `Enter value (${customUnitLabel})`
                      : "Enter value"
                  }
                  helperText={`Range: ${min} - ${max}${
                    customUnitLabel ? ` ${customUnitLabel}` : ""
                  }`}
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
            onChange={(e) => onChange(Number.parseInt(e.target.value))}
          >
            <Box
              sx={{
                display: "flex",
                flexDirection: { xs: "column", md: "row" },
                gap: 2,
                mt: 2,
                width: "100%",
              }}
            >
              {labels.map((label, index) => (
                <Box
                  key={index}
                  sx={{ flex: 1 }}
                >
                  <Box
                    sx={{
                      display: "flex",
                      flexDirection: { xs: "row", md: "column" },
                      alignItems: "center",
                      justifyContent: { xs: "flex-start", md: "center" },
                      p: 2,
                      height: { xs: "auto", md: "120px" },
                      border: "1px solid",
                      borderColor:
                        value === index + 1 ? "primary.main" : "divider",
                      borderRadius: 1,
                      backgroundColor:
                        value === index + 1 ? "primary.50" : "transparent",
                      cursor: "pointer",
                      transition: "all 0.2s",
                      "&:hover": {
                        borderColor: "primary.main",
                        backgroundColor: "primary.50",
                      },
                    }}
                    onClick={() => onChange(index + 1)}
                  >
                    <Radio value={(index + 1).toString()} sx={{ mb: { xs: 0, md: 1 }, mr: { xs: 2, md: 0 } }} />
                    <Typography
                      variant="body2"
                      textAlign={{ xs: "left", md: "center" }}
                      sx={{
                        fontWeight: value === index + 1 ? 600 : 400,
                        wordBreak: "break-word",
                        flex: 1,
                        display: "flex",
                        alignItems: "center",
                        px: { xs: 0, md: 1 },
                      }}
                    >
                      {!isYesNo && (
                        <Box component="span" sx={{ display: { xs: "inline", md: "none" }, mr: 1 }}>
                          {index + 1} -
                        </Box>
                      )}
                      {label}
                    </Typography>
                    {!isYesNo && (
                      <Typography
                        variant="caption"
                        color="text.secondary"
                        sx={{ mt: 0.5, display: { xs: "none", md: "block" } }}
                      >
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
