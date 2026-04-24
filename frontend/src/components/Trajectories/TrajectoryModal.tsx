import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
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
import { FaTrash, FaCopy, FaChevronDown } from "react-icons/fa"
import { LuBrainCircuit } from "react-icons/lu";
import { MdSubdirectoryArrowRight } from "react-icons/md";
import { WiSunrise } from "react-icons/wi";
import { WiSunset } from "react-icons/wi";

import { TrajectoriesService, UsersService, type TrajectoryPublic, type BrainstormResponse } from "@/client"
import useAuth from "@/hooks/useAuth"
import { ValueMapSunburstChart } from "@/components/ValueMap/ValueMapSunburstChart"

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
  const [showValueMap, setShowValueMap] = useState(false)

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
    <Dialog open={open} fullWidth maxWidth={showValueMap ? "lg" : "sm"}>
      <DialogTitle sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        Weekly Trajectory
        <Button variant="outlined" size="small" onClick={() => setShowValueMap(!showValueMap)}>
          {showValueMap ? "Hide Value Map" : "Show Value Map"}
        </Button>
      </DialogTitle>
      <DialogContent>
        <Stack direction="row" spacing={3}>
          <Box sx={{ flex: 1, minWidth: 0 }}>
            <Stack spacing={3} sx={{ mt: 1 }}>
              <Typography variant="body2" color="text.secondary">
                Set the goals you want to work on for the upcoming week. They will be framed as yes/no questions during your daily check-ins.
              </Typography>

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

              <List sx={{ maxHeight: 400, overflowY: "auto", overflowX: "hidden", pr: 1 }}>
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
                        <Box component="span" sx={{ display: "flex", alignItems: "center", gap: 0.5, mt: 0.5 }}>
                          <MdSubdirectoryArrowRight size={22} />
                          <Box component="span" sx={{ display: "flex", flexDirection: "column", gap: 0.5 }}>
                            <Box component="span" sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
                              <WiSunrise size={20} color="#FF8C00" /> { t.rephrased_morning_question }
                            </Box>
                            <Box component="span" sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
                              <WiSunset size={20} color="#4B0082" /> { t.rephrased_evening_question }
                            </Box>
                          </Box>
                        </Box>
                      }
                    />
                  </ListItem>
                ))}
              </List>

              <Accordion 
                disableGutters 
                elevation={0} 
                sx={{ border: "1px solid", borderColor: "divider", "&:before": { display: "none" }, borderRadius: 1, overflow: "hidden" }} 
                expanded={brainstormMode} 
                onChange={() => setBrainstormMode((prev) => !prev)}
              >
                <AccordionSummary expandIcon={<FaChevronDown size={14} />}>
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                    <LuBrainCircuit />
                    <Typography variant="body2" sx={{ fontWeight: 500 }}>
                      Brainstorm with Praestara
                    </Typography>
                  </Box>
                </AccordionSummary>
                
                <AccordionDetails sx={{ bgcolor: "primary.50", borderTop: "1px solid", borderColor: "divider", p: 2 }}>
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
                    <Box sx={{ bgcolor: "white", p: 1.5, borderRadius: 1 }}>
                      {brainstormReply.split(/\n+/).filter(Boolean).map((option, idx) => (
                        <Box key={idx} sx={{ display: "flex", alignItems: "flex-start", gap: 1, mb: 1, "&:last-child": { mb: 0 } }}>
                          <Typography variant="body2" sx={{ fontStyle: "italic", flex: 1, mt: 0.5 }}>
                            {option.replace(/^- /, "").trim()}
                          </Typography>
                          <IconButton 
                            size="small" 
                            onClick={() => {
                              const textToCopy = option.replace(/^- /, "").replace(/^\d+\.\s*/, "").trim();
                              navigator.clipboard.writeText(textToCopy)
                              setNewGoal(textToCopy)
                            }}
                            title="Copy and use this goal"
                          >
                            <FaCopy size={14} />
                          </IconButton>
                        </Box>
                      ))}
                    </Box>
                  )}
                </AccordionDetails>
              </Accordion>
            </Stack>
          </Box>
          
          {showValueMap && (
            <Box sx={{ flex: 1, minWidth: 0, borderLeft: "1px solid", borderColor: "divider", pl: 3, display: "flex", flexDirection: "column" }}>
              <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 600 }}>Value Map Context</Typography>
              <Box sx={{ flex: 1, position: "relative", minHeight: 400, borderRadius: 1, border: "1px solid", borderColor: "divider", overflow: "hidden" }}>
                <ValueMapSunburstChart />
              </Box>
            </Box>
          )}
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
