import { Box } from "@mui/material"
import { Outlet, createFileRoute, redirect } from "@tanstack/react-router"

import Sidebar from "@/components/Common/Sidebar"
import { isLoggedIn } from "@/hooks/useAuth"
import Navbar from "../components/Common/Navbar"
import AutoCheckinModal from "@/components/Checkins/AutoCheckinModal"

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
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <Navbar />
      <Box sx={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        <Sidebar />
        <Box
          component="main"
          sx={{
            flex: 1,
            overflow: 'auto',
            p: { xs: 2, md: 4 },
          }}
        >
          <Outlet />
        </Box>
      </Box>
      <AutoCheckinModal />
    </Box>
  )
}
