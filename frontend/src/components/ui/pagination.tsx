import * as React from "react"
import { Pagination as MuiPagination, Box } from "@mui/material"
import {
  HiChevronLeft,
  HiChevronRight,
} from "react-icons/hi2"

export interface PaginationRootProps {
  count: number
  pageSize: number
  page?: number
  defaultPage?: number
  onPageChange?: (details: { page: number }) => void
  children?: React.ReactNode
}

interface PaginationContextValue {
  page: number
  totalPages: number
  count: number
  pageSize: number
  onPageChange: (page: number) => void
}

const PaginationContext = React.createContext<PaginationContextValue | null>(null)

const usePaginationContext = () => {
  const context = React.useContext(PaginationContext)
  if (!context) {
    throw new Error("usePaginationContext must be used within PaginationRoot")
  }
  return context
}

export const PaginationRoot = React.forwardRef<HTMLDivElement, PaginationRootProps>(
  function PaginationRoot(props, ref) {
    const { 
      count, 
      pageSize, 
      page: controlledPage, 
      defaultPage = 1,
      onPageChange,
      children,
      ...rest 
    } = props
    
    const [internalPage, setInternalPage] = React.useState(defaultPage)
    const page = controlledPage ?? internalPage
    const totalPages = Math.ceil(count / pageSize)

    const handlePageChange = React.useCallback((newPage: number) => {
      if (!controlledPage) {
        setInternalPage(newPage)
      }
      onPageChange?.({ page: newPage })
    }, [controlledPage, onPageChange])

    const contextValue = React.useMemo(() => ({
      page,
      totalPages,
      count,
      pageSize,
      onPageChange: handlePageChange,
    }), [page, totalPages, count, pageSize, handlePageChange])

    return (
      <PaginationContext.Provider value={contextValue}>
        <Box ref={ref} {...rest}>
          {children}
        </Box>
      </PaginationContext.Provider>
    )
  }
)

export const PaginationItems = () => {
  const { page, totalPages, onPageChange } = usePaginationContext()

  if (totalPages <= 1) return null

  return (
    <MuiPagination
      count={totalPages}
      page={page}
      onChange={(_, newPage) => onPageChange(newPage)}
      color="primary"
      shape="rounded"
      showFirstButton
      showLastButton
      sx={{
        '& .MuiPaginationItem-root': {
          minWidth: '32px',
          height: '32px',
        }
      }}
    />
  )
}

export const PaginationPrevTrigger = React.forwardRef<HTMLButtonElement, React.ButtonHTMLAttributes<HTMLButtonElement>>(
  function PaginationPrevTrigger(props, ref) {
    const { page, onPageChange } = usePaginationContext()
    const disabled = page <= 1

    return (
      <button
        ref={ref}
        onClick={() => !disabled && onPageChange(page - 1)}
        disabled={disabled}
        style={{
          padding: '8px',
          border: '1px solid #e0e0e0',
          borderRadius: '4px',
          background: disabled ? '#f5f5f5' : 'white',
          cursor: disabled ? 'not-allowed' : 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
        {...props}
      >
        <HiChevronLeft />
      </button>
    )
  }
)

export const PaginationNextTrigger = React.forwardRef<HTMLButtonElement, React.ButtonHTMLAttributes<HTMLButtonElement>>(
  function PaginationNextTrigger(props, ref) {
    const { page, totalPages, onPageChange } = usePaginationContext()
    const disabled = page >= totalPages

    return (
      <button
        ref={ref}
        onClick={() => !disabled && onPageChange(page + 1)}
        disabled={disabled}
        style={{
          padding: '8px',
          border: '1px solid #e0e0e0',
          borderRadius: '4px',
          background: disabled ? '#f5f5f5' : 'white',
          cursor: disabled ? 'not-allowed' : 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
        {...props}
      >
        <HiChevronRight />
      </button>
    )
  }
)
