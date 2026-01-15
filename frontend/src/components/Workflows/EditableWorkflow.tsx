import { Container, Typography, Box, Button } from "@mui/material"
import { useNavigate } from "@tanstack/react-router"

interface WorkflowPublic {
  id: string
  title: string
  description?: string
}

interface EditableWorkflowProps {
  workflow: WorkflowPublic
}

const EditableWorkflow = ({ workflow }: EditableWorkflowProps) => {
  const navigate = useNavigate()

  return (
    <Container maxWidth={false}>
      <Box sx={{ pt: 6 }}>
        <Typography variant="h4" component="h1">
          Edit Workflow: {workflow.title}
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mt: 2 }}>
          {workflow.description || "No description"}
        </Typography>
        <Box sx={{ mt: 4 }}>
          <Typography variant="body2" color="text.secondary">
            TODO: Implement workflow editing interface
          </Typography>
          <Button
            variant="outlined"
            sx={{ mt: 2 }}
            onClick={() => navigate({ to: "/tasks" })}
          >
            Back to Workflows
          </Button>
        </Box>
      </Box>
    </Container>
  )
}

export default EditableWorkflow
