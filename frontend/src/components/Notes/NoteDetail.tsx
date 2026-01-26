import { Container, Typography, Box, Button, Paper } from "@mui/material"
import { useNavigate } from "@tanstack/react-router"
import { useCallback } from "react"
import { FiEdit } from "react-icons/fi"
import type { ItemPublic } from "../../client"
import 'react-quill/dist/quill.snow.css'

interface NoteDetailProps {
  note: ItemPublic
}

const NoteDetail = ({ note }: NoteDetailProps) => {
  const navigate = useNavigate()

  const handleEdit = useCallback(() => {
    navigate({
      to: "/notes",
      search: (prev: Record<string, unknown>) => ({ ...prev, noteId: note.id, editMode: "true" }),
    })
  }, [navigate, note.id])

  return (
    <Container maxWidth={false}>
      <Box sx={{ pt: 6 }}>
        <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
          <Typography variant="h4" component="h1">
            {note.title}
          </Typography>
          <Button variant="outlined" startIcon={<FiEdit />} onClick={handleEdit}>
            Edit
          </Button>
        </Box>

        {/* Note Content */}
        {note.description ? (
          <Paper sx={{ p: 3, mb: 3 }}>
            <Box
              className="ql-editor"
              sx={{
                '& p': { marginBottom: 1 },
                '& h1, & h2, & h3, & h4, & h5, & h6': { marginTop: 2, marginBottom: 1 },
                '& ul, & ol': { paddingLeft: 3 },
                '& pre': { 
                  backgroundColor: 'grey.100', 
                  padding: 2, 
                  borderRadius: 1,
                  overflow: 'auto'
                },
                '& blockquote': {
                  borderLeft: '4px solid',
                  borderColor: 'primary.main',
                  paddingLeft: 2,
                  marginLeft: 0,
                  fontStyle: 'italic'
                }
              }}
              dangerouslySetInnerHTML={{ __html: note.description }}
            />
          </Paper>
        ) : (
          <Paper sx={{ p: 3, mb: 3, textAlign: "center" }}>
            <Typography variant="body1" color="text.secondary">
              No content
            </Typography>
          </Paper>
        )}

        <Button variant="outlined" onClick={() => navigate({ to: "/notes" })}>
          Back to Notes
        </Button>
      </Box>
    </Container>
  )
}

export default NoteDetail
