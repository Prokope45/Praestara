import { IconButton } from "@mui/material"
import { BsThreeDotsVertical } from "react-icons/bs"
import { Menu } from "../ui/menu"
import { useState } from "react"

import type { UserPublic } from "@/client"
import DeleteUser from "../Admin/DeleteUser"
import EditUser from "../Admin/EditUser"

interface UserActionsMenuProps {
  user: UserPublic
  disabled?: boolean
}

export const UserActionsMenu = ({ user, disabled }: UserActionsMenuProps) => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)
  const open = Boolean(anchorEl)

  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget)
  }

  const handleClose = () => {
    setAnchorEl(null)
  }

  return (
    <>
      <IconButton
        onClick={handleClick}
        size="small"
        disabled={disabled}
        aria-label="user actions"
      >
        <BsThreeDotsVertical />
      </IconButton>
      <Menu
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
      >
        <EditUser user={user} />
        <DeleteUser id={user.id} />
      </Menu>
    </>
  )
}
