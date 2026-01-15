import React, { useContext } from "react"
import { IconButton, IconButtonProps } from "@mui/material"
import { LuMoon, LuSun } from "react-icons/lu"
import { ColorModeContext } from "./provider"

export type ColorMode = "light" | "dark"

export interface UseColorModeReturn {
  colorMode: ColorMode
  setColorMode: (colorMode: ColorMode) => void
  toggleColorMode: () => void
}

export function useColorMode(): UseColorModeReturn {
  const { toggleColorMode, mode } = useContext(ColorModeContext)
  return {
    colorMode: mode as ColorMode,
    setColorMode: (colorMode: ColorMode) => {
      if (colorMode !== mode) {
        toggleColorMode()
      }
    },
    toggleColorMode,
  }
}

export function useColorModeValue<T>(light: T, dark: T) {
  const { colorMode } = useColorMode()
  return colorMode === "dark" ? dark : light
}

export function ColorModeIcon() {
  const { colorMode } = useColorMode()
  return colorMode === "dark" ? <LuMoon /> : <LuSun />
}

interface ColorModeButtonProps extends Omit<IconButtonProps, "aria-label"> {}

export const ColorModeButton = React.forwardRef<
  HTMLButtonElement,
  ColorModeButtonProps
>(function ColorModeButton(props, ref) {
  const { toggleColorMode } = useColorMode()
  return (
    <IconButton
      onClick={toggleColorMode}
      aria-label="Toggle color mode"
      size="small"
      ref={ref}
      {...props}
    >
      <ColorModeIcon />
    </IconButton>
  )
})
