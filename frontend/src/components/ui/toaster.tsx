import type { PropsWithChildren } from 'react'
import { SnackbarProvider } from 'notistack'

export const Toaster = ({ children }: PropsWithChildren) => {
  return (
    <SnackbarProvider
      maxSnack={3}
      anchorOrigin={{
        vertical: 'top',
        horizontal: 'right',
      }}
      autoHideDuration={5000}
    >
      {children}
    </SnackbarProvider>
  )
}

// Export a simple toaster object for compatibility
export const toaster = {
  create: (_options: { title?: string; description?: string; type?: 'success' | 'error' | 'warning' | 'info' }) => {
    // This will be handled by useCustomToast hook
    return { id: Date.now().toString() }
  },
}
