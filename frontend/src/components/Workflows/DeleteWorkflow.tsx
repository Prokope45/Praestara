import { IconButton } from "@mui/material"
import { FiTrash } from "react-icons/fi"

interface WorkflowPublic {
  id: string
  title: string
  description?: string
}

interface DeleteWorkflowProps {
  workflow: WorkflowPublic
}

const DeleteWorkflow = ({ workflow }: DeleteWorkflowProps) => {
  return (
    <IconButton
      size="small"
      color="error"
      onClick={() => {
        // TODO: Implement delete workflow functionality
        console.log("Delete workflow clicked", workflow)
      }}
    >
      <FiTrash />
    </IconButton>
  )
}

export default DeleteWorkflow
