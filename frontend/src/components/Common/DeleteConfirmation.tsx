import {
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Typography,
} from "@mui/material"
import { Button } from "../ui/button"

interface DeleteConfirmationProps {
  open: boolean
  onClose: () => void
  onConfirm: () => void
  title: string
  description: string
  subDescription?: string
  isPending?: boolean
}

export function DeleteConfirmation({
  open,
  onClose,
  onConfirm,
  title,
  description,
  subDescription,
  isPending = false,
}: DeleteConfirmationProps) {
  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{title}</DialogTitle>
      <DialogContent>
        <Typography>{description}</Typography>
        {subDescription && (
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            {subDescription}
          </Typography>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={isPending}>
          Cancel
        </Button>
        <Button
          onClick={onConfirm}
          variant="contained"
          color="error"
          loading={isPending}
          disabled={isPending}
        >
          Delete
        </Button>
      </DialogActions>
    </Dialog>
  )
}
