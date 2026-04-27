import { useEffect, useState } from "react"
import useAuth from "@/hooks/useAuth"
import TrajectoryModal from "@/components/Trajectories/TrajectoryModal"

function AutoTrajectoryModal() {
  const { user } = useAuth()
  const [open, setOpen] = useState(false)

  useEffect(() => {
    // Must be logged in and finished onboarding
    if (!user || !user.onboarding_completed_at) return
    
    // If the checkin modal force key is set, maybe don't interfere, but trajectory has priority.
    // In AutoCheckinModal we check for praestara_trajectory_force to block checkin.
    
    const now = new Date()
    
    // First time? Or is it past the next trajectory date?
    let shouldOpen = false
    
    if (!user.next_trajectory_date) {
      shouldOpen = true
    } else {
      const nextDate = new Date(user.next_trajectory_date)
      if (now >= nextDate) {
        shouldOpen = true
      }
    }
    
    if (shouldOpen && !open) {
      setOpen(true)
      localStorage.setItem("praestara_trajectory_force", "1")
    }
  }, [user, open])

  useEffect(() => {
    const handleTrigger = () => {
      setOpen(true)
      localStorage.setItem("praestara_trajectory_force", "1")
    }

    window.addEventListener("praestara_trajectory_trigger", handleTrigger)
    return () =>
      window.removeEventListener("praestara_trajectory_trigger", handleTrigger)
  }, [])

  const handleClose = () => {
    setOpen(false)
    localStorage.removeItem("praestara_trajectory_force")
  }

  if (!open) return null

  return <TrajectoryModal open={open} onClose={handleClose} />
}

export default AutoTrajectoryModal