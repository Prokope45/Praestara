import * as React from "react"
import {
  Dialog as MuiDialog,
  DialogTitle as MuiDialogTitle,
  DialogContent as MuiDialogContent,
  DialogActions as MuiDialogActions,
  DialogProps,
  IconButton,
} from "@mui/material"
import { IoClose } from "react-icons/io5"

interface DialogRootProps extends DialogProps {
  open: boolean
  onOpenChange?: (open: boolean) => void
}

export const DialogRoot = React.forwardRef<HTMLDivElement, DialogRootProps>(
  function DialogRoot({ open, onOpenChange, children, ...props }, ref) {
    const handleClose = () => {
      onOpenChange?.(false)
    }

    return (
      <MuiDialog open={open} onClose={handleClose} ref={ref} {...props}>
        {children}
      </MuiDialog>
    )
  }
)

export const DialogContent = MuiDialogContent

export const DialogHeader = React.forwardRef<
  HTMLDivElement,
  React.ComponentProps<typeof MuiDialogTitle>
>(function DialogHeader(props, ref) {
  return <MuiDialogTitle ref={ref} {...props} />
})

export const DialogFooter = MuiDialogActions

export const DialogBody = MuiDialogContent

export const DialogTitle = MuiDialogTitle

export const DialogDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(function DialogDescription(props, ref) {
  return (
    <p
      ref={ref}
      style={{ margin: 0, color: 'text.secondary' }}
      {...props}
    />
  )
})

export const DialogCloseTrigger = React.forwardRef<
  HTMLButtonElement,
  React.ComponentProps<typeof IconButton>
>(function DialogCloseTrigger(props, ref) {
  return (
    <IconButton
      aria-label="close"
      ref={ref}
      sx={{
        position: 'absolute',
        right: 8,
        top: 8,
      }}
      {...props}
    >
      <IoClose />
    </IconButton>
  )
})

export const DialogBackdrop = React.forwardRef<HTMLDivElement, any>(
  function DialogBackdrop(props, ref) {
    return <div ref={ref} {...props} />
  }
)

export const DialogTrigger = React.forwardRef<HTMLButtonElement, any>(
  function DialogTrigger(props, ref) {
    return <button ref={ref} {...props} />
  }
)

export const DialogActionTrigger = React.forwardRef<HTMLButtonElement, any>(
  function DialogActionTrigger(props, ref) {
    return <button ref={ref} {...props} />
  }
)
