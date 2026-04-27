import { Box } from "@mui/material"
import { Outlet, createFileRoute, redirect } from "@tanstack/react-router"
import { useEffect } from "react"

import AutoCheckinModal from "@/components/Checkins/AutoCheckinModal"
import AutoTrajectoryModal from "@/components/Trajectories/AutoTrajectoryModal"
import Sidebar from "@/components/Common/Sidebar"
import { isLoggedIn } from "@/hooks/useAuth"
import Navbar from "../components/Common/Navbar"

export const Route = createFileRoute("/_layout")({
  beforeLoad: async () => {
    if (!isLoggedIn()) {
      throw redirect({
        to: "/login",
      })
    }
  },
  component: Layout,
})

function Layout() {
  useEffect(() => {
    const url = new URL(window.location.href)
    if (url.searchParams.get("clearLocalState") !== "1") return

    const dayKey = new Date().toISOString().slice(0, 10)
    const keys = [
      "praestara_checkin_force",
      "praestara_trajectory_force",
      `praestara_checkin_dismissed_morning_${dayKey}`,
      `praestara_checkin_dismissed_evening_${dayKey}`,
    ]
    keys.forEach((key) => window.localStorage.removeItem(key))
    url.searchParams.delete("clearLocalState")
    window.history.replaceState({}, "", `${url.pathname}${url.search}${url.hash}`)
  }, [])

  return (
    <Box sx={{ display: "flex", flexDirection: "column", height: "100vh" }}>
      <Navbar />
      <Box sx={{ display: "flex", flex: 1, overflow: "hidden" }}>
        <Sidebar />
        <Box
          component="main"
          sx={{
            flex: 1,
            overflow: "auto",
            p: { xs: 2, md: 4 },
          }}
        >
          <Outlet />
        </Box>
      </Box>
      <AutoTrajectoryModal />
      <AutoCheckinModal />
    </Box>
  )
}
