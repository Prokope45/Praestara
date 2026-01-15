import { useSnackbar } from 'notistack'

const useCustomToast = () => {
  const { enqueueSnackbar } = useSnackbar()

  const showSuccessToast = (description: string) => {
    enqueueSnackbar(description, {
      variant: 'success',
      anchorOrigin: {
        vertical: 'top',
        horizontal: 'right',
      },
    })
  }

  const showErrorToast = (description: string) => {
    enqueueSnackbar(description, {
      variant: 'error',
      anchorOrigin: {
        vertical: 'top',
        horizontal: 'right',
      },
    })
  }

  return { showSuccessToast, showErrorToast }
}

export default useCustomToast
