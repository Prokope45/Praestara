import * as React from "react"
import {
  Drawer as MuiDrawer,
  DrawerProps,
  Box,
  IconButton,
  Typography,
} from "@mui/material"
import { IoClose } from "react-icons/io5"

interface DrawerRootProps extends DrawerProps {
  open: boolean
  onOpenChange?: (open: boolean) => void
  placement?: 'left' | 'right' | 'top' | 'bottom'
}

export const DrawerRoot = React.forwardRef<HTMLDivElement, DrawerRootProps>(
  function DrawerRoot({ open, onOpenChange, placement = 'right', children, ...props }, ref) {
    const handleClose = () => {
      onOpenChange?.(false)
    }

    return (
      <MuiDrawer 
        open={open} 
        onClose={handleClose} 
        anchor={placement}
        ref={ref}
        {...props}
      >
        {children}
      </MuiDrawer>
    )
  }
)

export const DrawerContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & { portalled?: boolean; portalRef?: React.RefObject<HTMLElement>; offset?: any }
>(function DrawerContent({ children, portalled, portalRef, offset, ...props }, ref) {
  return (
    <Box ref={ref} sx={{ width: 350, p: 2 }} {...props}>
      {children}
    </Box>
  )
})

export const DrawerHeader = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(function DrawerHeader(props, ref) {
  return (
    <Box ref={ref} sx={{ mb: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }} {...props} />
  )
})

export const DrawerBody = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(function DrawerBody(props, ref) {
  return <Box ref={ref} sx={{ flex: 1 }} {...props} />
})

export const DrawerFooter = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(function DrawerFooter(props, ref) {
  return <Box ref={ref} sx={{ mt: 2, display: 'flex', gap: 1, justifyContent: 'flex-end' }} {...props} />
})

export const DrawerTitle = React.forwardRef<
  HTMLHeadingElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(function DrawerTitle(props, ref) {
  return <Typography ref={ref} variant="h6" component="h2" {...props} />
})

export const DrawerDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(function DrawerDescription(props, ref) {
  return <Typography ref={ref} variant="body2" color="text.secondary" {...props} />
})

export const DrawerCloseTrigger = React.forwardRef<
  HTMLButtonElement,
  React.ComponentProps<typeof IconButton>
>(function DrawerCloseTrigger(props, ref) {
  return (
    <IconButton
      aria-label="close"
      ref={ref}
      size="small"
      {...props}
    >
      <IoClose />
    </IconButton>
  )
})

export const DrawerBackdrop = React.forwardRef<HTMLDivElement, any>(
  function DrawerBackdrop(props, ref) {
    return <div ref={ref} {...props} />
  }
)

export const DrawerTrigger = React.forwardRef<HTMLButtonElement, any>(
  function DrawerTrigger(props, ref) {
    return <button ref={ref} {...props} />
  }
)

export const DrawerActionTrigger = React.forwardRef<HTMLButtonElement, any>(
  function DrawerActionTrigger(props, ref) {
    return <button ref={ref} {...props} />
  }
)
