import { SnackbarProvider } from "notistack"

export const Toaster = ({ children }: { children?: React.ReactNode }) => {
  return (
    <SnackbarProvider
      maxSnack={3}
      anchorOrigin={{
        vertical: "top",
        horizontal: "right",
      }}
      disableWindowBlurListener={true}
      autoHideDuration={5000}
    >
      {children}
    </SnackbarProvider>
  )
}

// Export a simple toaster object for compatibility
export const toaster = {
  create: (_options: {
    title?: string
    description?: string
    type?: "success" | "error" | "warning" | "info"
  }) => {
    return { id: Date.now().toString() }
  },
}
