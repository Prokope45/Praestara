import * as React from "react"
import { TextField, TextFieldProps, IconButton, InputAdornment, Box, Stack, Typography } from "@mui/material"
import { forwardRef, useState } from "react"
import { FiEye, FiEyeOff } from "react-icons/fi"
import { Field } from "./field"

export interface PasswordVisibilityProps {
  defaultVisible?: boolean
  visible?: boolean
  onVisibleChange?: (visible: boolean) => void
  visibilityIcon?: { on: React.ReactNode; off: React.ReactNode }
}

export interface PasswordInputProps
  extends Omit<TextFieldProps, 'type'> {
  rootProps?: any
  startElement?: React.ReactNode
  type: string
  errors: any
}

export const PasswordInput = forwardRef<HTMLInputElement, PasswordInputProps>(
  function PasswordInput(props, ref) {
    const {
      rootProps,
      startElement,
      type,
      errors,
      ...rest
    } = props

    const [visible, setVisible] = useState(false)

    return (
      <Field
        invalid={!!errors[type]}
        errorText={errors[type]?.message}
        sx={{ alignSelf: 'start', width: '100%' }}
      >
        <TextField
          {...rest}
          inputRef={ref}
          type={visible ? "text" : "password"}
          fullWidth
          InputProps={{
            startAdornment: startElement ? (
              <InputAdornment position="start">{startElement}</InputAdornment>
            ) : undefined,
            endAdornment: (
              <InputAdornment position="end">
                <IconButton
                  tabIndex={-1}
                  size="small"
                  aria-label="Toggle password visibility"
                  onClick={() => setVisible(!visible)}
                  edge="end"
                >
                  {visible ? <FiEyeOff /> : <FiEye />}
                </IconButton>
              </InputAdornment>
            ),
          }}
        />
      </Field>
    )
  },
)

interface PasswordStrengthMeterProps {
  max?: number
  value: number
}

export const PasswordStrengthMeter = forwardRef<
  HTMLDivElement,
  PasswordStrengthMeterProps
>(function PasswordStrengthMeter(props, ref) {
  const { max = 4, value, ...rest } = props

  const percent = (value / max) * 100
  const { label, color } = getColor(percent)

  return (
    <Stack spacing={1} alignItems="flex-end" ref={ref} {...rest}>
      <Box sx={{ display: 'flex', width: '100%', gap: 0.5 }}>
        {Array.from({ length: max }).map((_, index) => (
          <Box
            key={index}
            sx={{
              height: 4,
              flex: 1,
              borderRadius: 0.5,
              bgcolor: index < value ? color : 'grey.300',
            }}
          />
        ))}
      </Box>
      {label && <Typography variant="caption">{label}</Typography>}
    </Stack>
  )
})

function getColor(percent: number) {
  switch (true) {
    case percent < 33:
      return { label: "Low", color: "error.main" }
    case percent < 66:
      return { label: "Medium", color: "warning.main" }
    default:
      return { label: "High", color: "success.main" }
  }
}
