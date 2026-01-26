import { useNavigate } from "@tanstack/react-router"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import type { OrientationPublic } from "../../types/orientations"
import { OrientationsService } from "../../client"
import type { ApiError } from "../../client/core/ApiError"
import useCustomToast from "../../hooks/useCustomToast"
import { handleError } from "../../utils"
import { ActionsMenu } from "../Common/ActionsMenu"

interface OrientationActionsMenuProps {
  orientation: OrientationPublic
  onDelete?: () => void
}

const OrientationActionsMenu = ({ orientation, onDelete }: OrientationActionsMenuProps) => {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { showSuccessToast } = useCustomToast()

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

  const handleView = () => {
    navigate({
      to: "/orientations",
      search: { orientationId: orientation.id },
    })
  }

  const handleEdit = () => {
    navigate({
      to: "/orientations",
      search: { orientationId: orientation.id, editMode: "true" },
    })
  }

  const handleDelete = () => {
    if (confirm(`Are you sure you want to delete "${orientation.title}"?`)) {
      deleteMutation.mutate(orientation.id)
    }
  }

  return (
    <ActionsMenu
      onView={handleView}
      onEdit={handleEdit}
      onDelete={handleDelete}
      isDeleting={deleteMutation.isPending}
      showView={true}
    />
  )
}

export default OrientationActionsMenu
