import { IconButton, ListItemIcon, ListItemText } from "@mui/material"
import { FiEdit, FiEye, FiMoreVertical, FiTrash } from "react-icons/fi"
import { useNavigate } from "@tanstack/react-router"
import { useState } from "react"
import { Menu, MenuItem } from "../ui/menu"
import type { ObjectivePublic } from "../../types/objectives"

interface ObjectiveActionsMenuProps {
  objective: ObjectivePublic
}

const ObjectiveActionsMenu = ({ objective }: ObjectiveActionsMenuProps) => {
  const navigate = useNavigate()
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)
  const open = Boolean(anchorEl)

  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget)
  }

  const handleClose = () => {
    setAnchorEl(null)
  }

  const handleView = () => {
    navigate({
      to: "/tasks",
      search: { objectiveId: objective.id },
    })
    handleClose()
  }

  const handleEdit = () => {
    navigate({
      to: "/tasks",
      search: { objectiveId: objective.id, editMode: "true" },
    })
    handleClose()
  }

  const handleDelete = () => {
    // TODO: Implement delete objective functionality
    console.log("Delete objective clicked", objective)
    handleClose()
  }

  return (
    <>
      <IconButton
        onClick={handleClick}
        size="small"
        aria-label="objective actions"
      >
        <FiMoreVertical />
      </IconButton>
      <Menu anchorEl={anchorEl} open={open} onClose={handleClose}>
        <MenuItem onClick={handleView}>
          <ListItemIcon>
            <FiEye />
          </ListItemIcon>
          <ListItemText>View</ListItemText>
        </MenuItem>
        <MenuItem onClick={handleEdit}>
          <ListItemIcon>
            <FiEdit />
          </ListItemIcon>
          <ListItemText>Edit</ListItemText>
        </MenuItem>
        <MenuItem onClick={handleDelete} sx={{ color: "error.main" }}>
          <ListItemIcon sx={{ color: "error.main" }}>
            <FiTrash />
          </ListItemIcon>
          <ListItemText>Delete</ListItemText>
        </MenuItem>
      </Menu>
    </>
  )
}

export default ObjectiveActionsMenu
