import { Box, LinearProgress, Stack, Typography } from "@mui/material"
import { useEffect, useState } from "react"

interface AnimatedProgressBarProps {
  current: number
  total: number
  percentage: number
  label?: string
}

export function AnimatedProgressBar({
  current,
  total,
  percentage,
  label = "Progress",
}: AnimatedProgressBarProps) {
  const [animatedProgress, setAnimatedProgress] = useState(0)

  // Animate progress bar on mount or when percentage changes
  useEffect(() => {
    const timer = setTimeout(() => {
      setAnimatedProgress(percentage)
    }, 100)
    return () => clearTimeout(timer)
  }, [percentage])

  return (
    <Box>
      <Stack direction="row" justifyContent="space-between" sx={{ mb: 1 }}>
        <Typography variant="body2" color="text.secondary">
          {label}: {current} of {total} questions answered
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {Math.round(percentage)}%
        </Typography>
      </Stack>
      <LinearProgress
        variant="determinate"
        value={animatedProgress}
        sx={{
          "& .MuiLinearProgress-bar": {
            transition: "transform 0.8s ease-in-out",
          },
        }}
      />
    </Box>
  )
}
