import { IconButton } from "@mui/material"
import { FiTrash } from "react-icons/fi"
import type { ObjectivePublic } from "../../types/objectives"

interface DeleteObjectiveProps {
  objective: ObjectivePublic
}

const DeleteObjective = ({ objective }: DeleteObjectiveProps) => {
  return (
    <IconButton
      size="small"
      color="error"
      onClick={() => {
        // TODO: Implement delete objective functionality
        console.log("Delete objective clicked", objective)
      }}
    >
      <FiTrash />
    </IconButton>
  )
}

export default DeleteObjective
