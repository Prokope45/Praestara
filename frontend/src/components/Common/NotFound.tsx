import { Box, Typography } from "@mui/material"
import { Link } from "@tanstack/react-router"
import { Button } from "@/components/ui/button"

const NotFound = () => {
  return (
    <Box
      sx={{
        height: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexDirection: 'column',
        p: 4,
      }}
      data-testid="not-found"
    >
      <Box sx={{ display: 'flex', alignItems: 'center', zIndex: 1 }}>
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            ml: 4,
            alignItems: 'center',
            justifyContent: 'center',
            p: 4,
          }}
        >
          <Typography
            variant="h1"
            sx={{
              fontSize: { xs: '6rem', md: '8rem' },
              fontWeight: 'bold',
              lineHeight: 1,
              mb: 4,
            }}
          >
            404
          </Typography>
          <Typography variant="h4" fontWeight="bold" sx={{ mb: 2 }}>
            Oops!
          </Typography>
        </Box>
      </Box>

      <Typography
        variant="h6"
        color="text.secondary"
        sx={{ mb: 4, textAlign: 'center', zIndex: 1 }}
      >
        The page you are looking for was not found.
      </Typography>
      <Box sx={{ zIndex: 1 }}>
        <Link to="/">
          <Button variant="contained" color="primary" sx={{ mt: 4 }}>
            Go Back
          </Button>
        </Link>
      </Box>
    </Box>
  )
}

export default NotFound
