import { Box, IconButton, Typography } from "@mui/material"
import { useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { FaBars } from "react-icons/fa"
import { FiLogOut } from "react-icons/fi"

import type { UserPublic } from "@/client"
import useAuth from "@/hooks/useAuth"
import {
  DrawerRoot,
  DrawerContent,
  DrawerBody,
  DrawerCloseTrigger,
} from "../ui/drawer"
import SidebarItems from "./SidebarItems"

const Sidebar = () => {
  const queryClient = useQueryClient()
  const currentUser = queryClient.getQueryData<UserPublic>(["currentUser"])
  const { logout } = useAuth()
  const [open, setOpen] = useState(false)

  const handleLogout = async () => {
    logout()
  }

  return (
    <>
      {/* Mobile */}
      <DrawerRoot
        placement="left"
        open={open}
        onOpenChange={setOpen}
      >
        <DrawerContent>
          <DrawerCloseTrigger />
          <DrawerBody>
            <Box sx={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', height: '100%' }}>
              <Box>
                <SidebarItems />
                <Box
                  component="button"
                  onClick={handleLogout}
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 4,
                    px: 4,
                    py: 2,
                    border: 'none',
                    background: 'none',
                    cursor: 'pointer',
                    width: '100%',
                    textAlign: 'left',
                  }}
                >
                  <FiLogOut />
                  <Typography>Log Out</Typography>
                </Box>
              </Box>
              {currentUser?.email && (
                <Typography variant="body2" sx={{ p: 2 }}>
                  Logged in as: {currentUser.email}
                </Typography>
              )}
            </Box>
          </DrawerBody>
        </DrawerContent>
      </DrawerRoot>

      <IconButton
        onClick={() => setOpen(true)}
        sx={{
          display: { xs: 'flex', md: 'none' },
          position: 'absolute',
          zIndex: 100,
          m: 4,
        }}
        aria-label="Open Menu"
      >
        <FaBars />
      </IconButton>

      {/* Desktop */}
      <Box
        sx={{
          display: { xs: 'none', md: 'flex' },
          position: 'sticky',
          bgcolor: 'background.default',
          top: 0,
          minWidth: 280,
          height: '100vh',
          p: 4,
        }}
      >
        <Box sx={{ width: '100%' }}>
          <SidebarItems />
        </Box>
      </Box>
    </>
  )
}

export default Sidebar
