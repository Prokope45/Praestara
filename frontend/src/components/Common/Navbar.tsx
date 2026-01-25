import { AppBar, Toolbar, Box, Typography, useMediaQuery, useTheme } from "@mui/material"
import { Link } from "@tanstack/react-router"

import Logo from "/assets/images/praestara-logo.png"
import UserMenu from "./UserMenu"

function Navbar() {
  const theme = useTheme()
  const isMdUp = useMediaQuery(theme.breakpoints.up('md'))

  if (!isMdUp) {
    return null
  }

  return (
    <AppBar 
      position="sticky" 
      sx={{ 
        bgcolor: 'background.paper',
        color: 'text.primary',
        boxShadow: 1
      }}
    >
      <Toolbar sx={{ justifyContent: 'space-between' }}>
        <Link to="/" style={{ textDecoration: 'none', color: 'inherit' }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Box
              component="img"
              src={Logo}
              alt="Logo"
              sx={{ width: 100, maxWidth: '2xs', pr: 2}}
            />
            <Typography variant="h3" fontWeight="bold">
              Praestara
            </Typography>
          </Box>
        </Link>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <UserMenu />
        </Box>
      </Toolbar>
    </AppBar>
  )
}

export default Navbar
