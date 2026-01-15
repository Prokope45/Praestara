import { SnackbarProvider } from 'notistack'

export const Toaster = () => {
  return (
    <SnackbarProvider 
      maxSnack={3}
      anchorOrigin={{
        vertical: 'top',
        horizontal: 'right',
      }}
      autoHideDuration={5000}
    />
  )
}

// Export a simple toaster object for compatibility
export const toaster = {
  create: (_options: { title?: string; description?: string; type?: 'success' | 'error' | 'warning' | 'info' }) => {
    // This will be handled by useCustomToast hook
    return { id: Date.now().toString() }
  },
}
