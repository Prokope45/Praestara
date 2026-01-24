import { IconButton, ListItemIcon, ListItemText } from "@mui/material"
import { FiEdit, FiEye, FiMoreVertical, FiTrash } from "react-icons/fi"
import { useNavigate } from "@tanstack/react-router"
import { useState } from "react"
import { Menu, MenuItem } from "../ui/menu"
import type { OrientationPublic } from "../../types/orientations"
import { deleteTempOrientation } from "../../utils/tempOrientationStorage"

interface OrientationActionsMenuProps {
  orientation: OrientationPublic
  onDelete?: () => void
}

const OrientationActionsMenu = ({ orientation, onDelete }: OrientationActionsMenuProps) => {
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
      to: "/orientations",
      search: { orientationId: orientation.id },
    })
    handleClose()
  }

  const handleEdit = () => {
    navigate({
      to: "/orientations",
      search: { orientationId: orientation.id, editMode: "true" },
    })
    handleClose()
  }

  const handleDelete = () => {
    if (confirm(`Are you sure you want to delete "${orientation.title}"?`)) {
      deleteTempOrientation(orientation.id)
      if (onDelete) {
        onDelete()
      }
    }
    handleClose()
  }

  return (
    <>
      <IconButton onClick={handleClick} size="small" aria-label="orientation actions">
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

export default OrientationActionsMenu
