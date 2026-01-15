import { IconButton } from "@mui/material"
import { FiEdit } from "react-icons/fi"

interface WorkflowPublic {
  id: string
  title: string
  description?: string
}

interface EditWorkflowProps {
  workflow: WorkflowPublic
}

const EditWorkflow = ({ workflow }: EditWorkflowProps) => {
  return (
    <IconButton
      size="small"
      onClick={() => {
        // TODO: Implement edit workflow functionality
        console.log("Edit workflow clicked", workflow)
      }}
    >
      <FiEdit />
    </IconButton>
  )
}

export default EditWorkflow
