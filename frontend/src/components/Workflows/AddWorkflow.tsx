import { Box, Button } from "@mui/material"
import { FiPlus } from "react-icons/fi"

const AddWorkflow = () => {
  return (
    <Box sx={{ mt: 3, mb: 2 }}>
      <Button
        variant="contained"
        color="primary"
        startIcon={<FiPlus />}
        onClick={() => {
          // TODO: Implement add workflow functionality
          console.log("Add workflow clicked")
        }}
      >
        Add Workflow
      </Button>
    </Box>
  )
}

export default AddWorkflow
