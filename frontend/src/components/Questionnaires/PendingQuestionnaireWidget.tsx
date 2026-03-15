import { Box, Button, Paper, Stack, Typography } from "@mui/material"
import { useNavigate } from "@tanstack/react-router"
import { useMemo } from "react"

import type { QuestionnaireAssignmentPublic } from "../../client"
import { AnimatedProgressBar } from "../Common/AnimatedProgressBar"

interface PendingQuestionnaireWidgetProps {
  assignment: QuestionnaireAssignmentPublic
}

export function PendingQuestionnaireWidget({ assignment }: PendingQuestionnaireWidgetProps) {
  const navigate = useNavigate()
  
  const isOnboarding = assignment.questionnaire.title === "Praestara Onboarding"
  const hasProgress = assignment.saved_progress && Object.keys(assignment.saved_progress).length > 0
  
  // Calculate progress
  const { answeredCount, totalQuestions, progress } = useMemo(() => {
    const total = assignment.questionnaire.questions?.length || 0
    if (total === 0) return { answeredCount: 0, totalQuestions: 0, progress: 0 }
    
    let answered = 0
    if (assignment.saved_progress?.answers) {
      answered = Object.keys(assignment.saved_progress.answers).length
    } else if (assignment.saved_progress && !assignment.saved_progress.answers) {
      // Backwards compatibility: old format was just the answers object
      answered = Object.keys(assignment.saved_progress).length
    }
    
    return {
      answeredCount: answered,
      totalQuestions: total,
      progress: (answered / total) * 100
    }
  }, [assignment])
  
  const buttonText = useMemo(() => {
    if (isOnboarding) {
      return hasProgress ? "Resume onboarding" : "Start onboarding"
    }
    return hasProgress ? "Resume questionnaire" : "Take questionnaire"
  }, [isOnboarding, hasProgress])
  
  const title = useMemo(() => {
    if (isOnboarding) {
      return "Get started with your baseline"
    }
    return "Questionnaire assigned"
  }, [isOnboarding])
  
  const description = useMemo(() => {
    if (isOnboarding) {
      return "Complete the onboarding questionnaire to set your baseline. It takes about 12 to 18 minutes and anchors your future check-ins."
    }
    return `You have been assigned "${assignment.questionnaire.title}". ${assignment.questionnaire.description || ""}`
  }, [isOnboarding, assignment])

  return (
    <Paper
      sx={{
        p: 3,
        border: "1px solid",
        borderColor: "divider",
        background: "linear-gradient(135deg, rgba(102,126,234,0.12) 0%, rgba(118,75,162,0.12) 100%)",
      }}
    >
      <Stack spacing={2}>
        <Stack direction={{ xs: "column", sm: "row" }} spacing={2} alignItems="center">
          <Box sx={{ flex: 1 }}>
            <Typography variant="h6" sx={{ mb: 1 }}>
              {title}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {description}
            </Typography>
          </Box>
          <Button 
            variant="contained" 
            onClick={() => {
              navigate({ to: `/questionnaires/${assignment.id}/take` })
            }}
          >
            {buttonText}
          </Button>
        </Stack>
        
        {hasProgress && (
          <AnimatedProgressBar
            current={answeredCount}
            total={totalQuestions}
            percentage={progress}
            label="Progress"
          />
        )}
      </Stack>
    </Paper>
  )
}
