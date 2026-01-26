import { IconButton, ListItemIcon, ListItemText } from "@mui/material"
import { FiEdit, FiEye, FiMoreVertical, FiTrash } from "react-icons/fi"
import { Menu, MenuItem } from "../ui/menu"
import { useState } from "react"

interface ActionsMenuProps {
  onView?: () => void
  onEdit: () => void
  onDelete: () => void
  isDeleting?: boolean
  showView?: boolean
}

export const ActionsMenu = ({ 
  onView, 
  onEdit, 
  onDelete, 
  isDeleting = false,
  showView = false 
}: ActionsMenuProps) => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)
  const open = Boolean(anchorEl)

  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    event.stopPropagation()
    setAnchorEl(event.currentTarget)
  }

  const handleClose = () => {
    setAnchorEl(null)
  }

  const handleView = () => {
    if (onView) {
      onView()
    }
    handleClose()
  }

  const handleEdit = () => {
    onEdit()
    handleClose()
  }

  const handleDelete = () => {
    onDelete()
    handleClose()
  }

  return (
    <>
      <IconButton
        onClick={handleClick}
        size="small"
        aria-label="actions"
        data-action="menu"
      >
        <FiMoreVertical />
      </IconButton>
      <Menu
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
      >
        {showView && onView && (
          <MenuItem onClick={handleView}>
            <ListItemIcon>
              <FiEye />
            </ListItemIcon>
            <ListItemText>View</ListItemText>
          </MenuItem>
        )}
        <MenuItem onClick={handleEdit} data-action="edit">
          <ListItemIcon>
            <FiEdit />
          </ListItemIcon>
          <ListItemText>Edit</ListItemText>
        </MenuItem>
        <MenuItem onClick={handleDelete} sx={{ color: "error.main" }} disabled={isDeleting}>
          <ListItemIcon sx={{ color: "error.main" }}>
            <FiTrash />
          </ListItemIcon>
          <ListItemText>{isDeleting ? "Deleting..." : "Delete"}</ListItemText>
        </MenuItem>
      </Menu>
    </>
  )
}
