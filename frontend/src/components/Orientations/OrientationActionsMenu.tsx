import { IconButton, ListItemIcon, ListItemText } from "@mui/material"
import { FiEdit, FiEye, FiMoreVertical, FiTrash } from "react-icons/fi"
import { useNavigate } from "@tanstack/react-router"
import { useState } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Menu, MenuItem } from "../ui/menu"
import type { OrientationPublic } from "../../types/orientations"
import { OrientationsService } from "../../client"
import type { ApiError } from "../../client/core/ApiError"
import useCustomToast from "../../hooks/useCustomToast"
import { handleError } from "../../utils"

interface OrientationActionsMenuProps {
  orientation: OrientationPublic
  onDelete?: () => void
}

const OrientationActionsMenu = ({ orientation, onDelete }: OrientationActionsMenuProps) => {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)
  const open = Boolean(anchorEl)

  const deleteMutation = useMutation({
    mutationFn: (id: string) =>
      OrientationsService.deleteOrientation({ id }),
    onSuccess: () => {
      showSuccessToast("Orientation deleted successfully.")
      if (onDelete) {
        onDelete()
      }
      // Navigate back to orientations list
      navigate({ to: "/orientations" })
    },
    onError: (err: ApiError) => {
      handleError(err)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["orientations"] })
    },
  })

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
      deleteMutation.mutate(orientation.id)
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
        <MenuItem onClick={handleDelete} sx={{ color: "error.main" }} disabled={deleteMutation.isPending}>
          <ListItemIcon sx={{ color: "error.main" }}>
            <FiTrash />
          </ListItemIcon>
          <ListItemText>{deleteMutation.isPending ? "Deleting..." : "Delete"}</ListItemText>
        </MenuItem>
      </Menu>
    </>
  )
}

export default OrientationActionsMenu
