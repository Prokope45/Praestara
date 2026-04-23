import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  List,
  ListItem,
  ListItemText,
  Stack,
  TextField,
  Typography,
} from "@mui/material"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { FaTrash, FaRobot } from "react-icons/fa"

import { TrajectoriesService, UsersService, type TrajectoryPublic, type BrainstormResponse } from "@/client"
import useAuth from "@/hooks/useAuth"

interface TrajectoryModalProps {
  open: boolean
  onClose: () => void
}

function TrajectoryModal({ open, onClose }: TrajectoryModalProps) {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const [newGoal, setNewGoal] = useState("")
  const [brainstormMode, setBrainstormMode] = useState(false)
  const [brainstormInput, setBrainstormInput] = useState("")
  const [brainstormReply, setBrainstormReply] = useState<string | null>(null)

  const { data: activeTrajectories } = useQuery({
    queryKey: ["trajectories", "active"],
    queryFn: () => TrajectoriesService.getActiveTrajectories(),
    enabled: open,
  })

  const createMutation = useMutation({
    mutationFn: (goal: string) =>
      TrajectoriesService.createTrajectory({ requestBody: { original_goal: goal, is_active: true } }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trajectories", "active"] })
      setNewGoal("")
    },
  })

  const deactivateMutation = useMutation({
    mutationFn: (id: string) =>
      TrajectoriesService.updateTrajectory({ id, requestBody: { is_active: false } }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trajectories", "active"] })
    },
  })

  const brainstormMutation = useMutation({
    mutationFn: (message: string) =>
      TrajectoriesService.brainstormTrajectory({ requestBody: { message } }),
    onSuccess: (data: BrainstormResponse) => {
      setBrainstormReply(data.response)
    },
  })
  
  const finishMutation = useMutation({
    mutationFn: async () => {
      // Set next trajectory date to the coming configured day
      const now = new Date()
      const targetDay = user?.trajectory_update_day ?? 6
      let daysUntilTarget = targetDay - now.getDay()
      if (daysUntilTarget <= 0) {
        daysUntilTarget += 7
      }
      
      const nextDate = new Date()
      nextDate.setDate(now.getDate() + daysUntilTarget)
      nextDate.setHours(0, 0, 0, 0)
      
      await UsersService.updateUserMe({
        requestBody: {
          next_trajectory_date: nextDate.toISOString()
        }
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["currentUser"] })
      onClose()
    }
  })

  const handleAddGoal = () => {
    if (!newGoal.trim()) return
    createMutation.mutate(newGoal)
  }

  const handleBrainstorm = () => {
    if (!brainstormInput.trim()) return
    brainstormMutation.mutate(brainstormInput)
  }

  return (
    <Dialog open={open} fullWidth maxWidth="sm">
      <DialogTitle>Weekly Trajectory</DialogTitle>
      <DialogContent>
        <Stack spacing={3} sx={{ mt: 1 }}>
          <Typography variant="body2" color="text.secondary">
            Set the goals you want to work on for the upcoming week. They will be framed as yes/no questions during your daily check-ins.
          </Typography>

          <List>
            {(activeTrajectories?.data ?? []).map((t: TrajectoryPublic) => (
              <ListItem
                key={t.id}
                secondaryAction={
                  <IconButton edge="end" onClick={() => deactivateMutation.mutate(t.id)} disabled={deactivateMutation.isPending}>
                    <FaTrash size={14} />
                  </IconButton>
                }
                sx={{ bgcolor: "grey.50", mb: 1, borderRadius: 1 }}
              >
                <ListItemText
                  primary={t.original_goal}
                  secondary={
                    t.rephrased_morning_question && t.rephrased_evening_question
                      ? `Morning: ${t.rephrased_morning_question} | Evening: ${t.rephrased_evening_question}`
                      : "Rephrasing..."
                  }
                />
              </ListItem>
            ))}
          </List>

          <Box sx={{ display: "flex", gap: 1 }}>
            <TextField
              value={newGoal}
              onChange={(e) => setNewGoal(e.target.value)}
              placeholder="e.g. Work out for 30 minutes"
              size="small"
              fullWidth
              onKeyDown={(e) => {
                if (e.key === "Enter") handleAddGoal()
              }}
            />
            <Button
              variant="contained"
              onClick={handleAddGoal}
              disabled={!newGoal.trim() || createMutation.isPending}
            >
              Add
            </Button>
          </Box>

          <Box>
            <Button
              startIcon={<FaRobot />}
              variant="text"
              size="small"
              onClick={() => setBrainstormMode((prev) => !prev)}
            >
              Ask Koios for ideas?
            </Button>
            
            {brainstormMode && (
              <Box sx={{ mt: 2, p: 2, bgcolor: "primary.50", borderRadius: 2 }}>
                <Typography variant="subtitle2" sx={{ mb: 1 }}>Brainstorm with Praestara</Typography>
                <Box sx={{ display: "flex", gap: 1, mb: 2 }}>
                  <TextField
                    value={brainstormInput}
                    onChange={(e) => setBrainstormInput(e.target.value)}
                    placeholder="I want to be more productive..."
                    size="small"
                    fullWidth
                    onKeyDown={(e) => {
                      if (e.key === "Enter") handleBrainstorm()
                    }}
                  />
                  <Button
                    variant="contained"
                    size="small"
                    onClick={handleBrainstorm}
                    disabled={!brainstormInput.trim() || brainstormMutation.isPending}
                  >
                    Ask
                  </Button>
                </Box>
                {brainstormReply && (
                  <Typography variant="body2" sx={{ fontStyle: "italic", bgcolor: "white", p: 1.5, borderRadius: 1 }}>
                    {brainstormReply}
                  </Typography>
                )}
              </Box>
            )}
          </Box>
        </Stack>
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 3 }}>
        <Button
          variant="contained"
          onClick={() => finishMutation.mutate()}
          disabled={finishMutation.isPending}
        >
          Finish
        </Button>
      </DialogActions>
    </Dialog>
  )
}

export default TrajectoryModal
