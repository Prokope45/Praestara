import * as React from "react"
import { Skeleton as MuiSkeleton, Stack } from "@mui/material"

export interface SkeletonCircleProps {
  size?: string | number
}

export const SkeletonCircle = React.forwardRef<HTMLDivElement, SkeletonCircleProps>(
  function SkeletonCircle(props, ref) {
    const { size = 40, ...rest } = props
    return (
      <MuiSkeleton
        ref={ref}
        variant="circular"
        width={size}
        height={size}
        {...rest}
      />
    )
  }
)

export interface SkeletonTextProps {
  noOfLines?: number
  gap?: number
}

export const SkeletonText = React.forwardRef<HTMLDivElement, SkeletonTextProps>(
  function SkeletonText(props, ref) {
    const { noOfLines = 3, gap = 2, ...rest } = props
    return (
      <Stack gap={gap} width="100%" ref={ref}>
        {Array.from({ length: noOfLines }).map((_, index) => (
          <MuiSkeleton
            key={index}
            variant="text"
            sx={{
              height: 16,
              ...(index === noOfLines - 1 && { maxWidth: '80%' })
            }}
            {...rest}
          />
        ))}
      </Stack>
    )
  }
)

export interface SkeletonProps {
  h?: string | number
  height?: string | number
  w?: string | number
  width?: string | number
  variant?: "text" | "rectangular" | "rounded" | "circular"
}

export const Skeleton = React.forwardRef<HTMLDivElement, SkeletonProps>(
  function Skeleton(props, ref) {
    const { h, height, w, width, variant = "rectangular", ...rest } = props
    const finalHeight = h || height
    const finalWidth = w || width
    
    return (
      <MuiSkeleton
        ref={ref}
        variant={variant}
        height={finalHeight}
        width={finalWidth}
        {...rest}
      />
    )
  }
)
