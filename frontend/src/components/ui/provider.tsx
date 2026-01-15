import React, { type PropsWithChildren, useMemo, useState } from "react"
import { ThemeProvider, CssBaseline } from "@mui/material"
import { lightTheme, darkTheme } from "../../theme"
import { Toaster } from "./toaster"

// Create a context for theme mode
export const ColorModeContext = React.createContext({ 
  toggleColorMode: () => {},
  mode: 'light' as 'light' | 'dark'
})

export function ColorModeProvider({ children, defaultTheme = 'light' }: PropsWithChildren<{ defaultTheme?: 'light' | 'dark' }>) {
  const [mode, setMode] = useState<'light' | 'dark'>(defaultTheme)

  const colorMode = useMemo(
    () => ({
      toggleColorMode: () => {
        setMode((prevMode) => (prevMode === 'light' ? 'dark' : 'light'))
      },
      mode,
    }),
    [mode],
  )

  const theme = useMemo(() => (mode === 'light' ? lightTheme : darkTheme), [mode])

  return (
    <ColorModeContext.Provider value={colorMode}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        {children}
      </ThemeProvider>
    </ColorModeContext.Provider>
  )
}

export function CustomProvider(props: PropsWithChildren) {
  return (
    <ColorModeProvider defaultTheme="light">
      {props.children}
      <Toaster />
    </ColorModeProvider>
  )
}
