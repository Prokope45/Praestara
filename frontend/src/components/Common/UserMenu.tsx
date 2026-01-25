import { Avatar, Box, Button, Menu, MenuItem, Typography } from "@mui/material"
import { Link } from "@tanstack/react-router"
import { FaUserCircle } from "react-icons/fa"
import { FiLogOut, FiUser } from "react-icons/fi"
import { useState } from "react"

import useAuth from "@/hooks/useAuth"

const UserMenu = () => {
  const { user, logout } = useAuth()
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)
  const open = Boolean(anchorEl)

  const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget)
  }

  const handleClose = () => {
    setAnchorEl(null)
  }

  const handleLogout = async () => {
    handleClose()
    logout()
  }

  const profileImage = user?.profile_image || "/assets/images/default-avatar.svg"

  return (
    <Box>
      <Button
        data-testid="user-menu"
        variant="contained"
        onClick={handleClick}
        startIcon={
          <Avatar 
            src={profileImage} 
            alt={user?.full_name || "User"}
            sx={{ width: 32, height: 32 }}
          >
            <FaUserCircle />
          </Avatar>
        }
        sx={{ maxWidth: 200, textTransform: 'none', pl: 1 }}
      >
        <Typography noWrap>{user?.full_name || "User"}</Typography>
      </Button>

      <Menu
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
      >
        <MenuItem 
          component={Link} 
          to="/settings" 
          onClick={handleClose}
          sx={{ gap: 2, py: 2 }}
        >
          <FiUser fontSize="18px" />
          <Box flex="1">My Profile</Box>
        </MenuItem>

        <MenuItem
          onClick={handleLogout}
          sx={{ gap: 2, py: 2 }}
        >
          <FiLogOut />
          Log Out
        </MenuItem>
      </Menu>
    </Box>
  )
}

export default UserMenu
