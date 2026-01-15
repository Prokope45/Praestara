import { createTheme } from '@mui/material/styles';

/**
 * Color theme: 
 * Deep Purple: #522f75 (Brand/Main)
 * Muted Purple: #987ca2 (Secondary)
 * Ghost White: #f8f7ff (Background)
 * Apricot: #ffeedd (Subtle accent)
 * Peach: #ffd8be (Accent)
 */

export const lightTheme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#522f75', // Deep Purple
      light: '#987ca2', // Muted Purple
      dark: '#3d2356',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#987ca2', // Muted Purple
      light: '#b39bb8',
      dark: '#7a6382',
      contrastText: '#ffffff',
    },
    background: {
      default: '#f8f7ff', // Ghost White
      paper: '#ffffff',
    },
    text: {
      primary: '#522f75', // Deep Purple
      secondary: '#987ca2', // Muted Purple
    },
    success: {
      main: '#48bb78',
      light: '#68d391',
    },
    warning: {
      main: '#ed8936',
      light: '#f6ad55',
    },
    error: {
      main: '#f56565',
      light: '#fc8181',
    },
    info: {
      main: '#ffd8be', // Peach
      light: '#ffeedd', // Apricot
      contrastText: '#522f75',
    },
  },
  typography: {
    fontSize: 14,
    fontFamily: [
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
    ].join(','),
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: 8,
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        head: {
          backgroundColor: '#ffeedd', // Apricot
          color: '#522f75', // Deep Purple
          fontWeight: 'bold',
        },
      },
    },
    MuiTableRow: {
      styleOverrides: {
        root: {
          '&:hover': {
            backgroundColor: '#ffeedd', // Apricot
          },
        },
      },
    },
  },
});

export const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#987ca2', // Muted Purple (lighter for dark mode)
      light: '#b39bb8',
      dark: '#7a6382',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#ffd8be', // Peach
      light: '#ffeedd', // Apricot
      dark: '#e5c3a8',
      contrastText: '#522f75',
    },
    background: {
      default: '#1a1a1a', // Darker anthracite
      paper: '#2a2a2a', // Slightly lighter anthracite
    },
    text: {
      primary: '#f8f7ff', // Ghost White
      secondary: '#ffd8be', // Peach
    },
    success: {
      main: '#48bb78',
      light: '#68d391',
    },
    warning: {
      main: '#ed8936',
      light: '#f6ad55',
    },
    error: {
      main: '#f56565',
      light: '#fc8181',
    },
    info: {
      main: '#ffd8be', // Peach
      light: '#ffeedd', // Apricot
      contrastText: '#1a1a1a',
    },
  },
  typography: {
    fontSize: 14,
    fontFamily: [
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
    ].join(','),
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: 8,
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        head: {
          backgroundColor: '#522f75', // Deep Purple
          color: '#f8f7ff', // Ghost White
          fontWeight: 'bold',
        },
      },
    },
    MuiTableRow: {
      styleOverrides: {
        root: {
          '&:hover': {
            backgroundColor: '#987ca2', // Muted Purple
          },
        },
      },
    },
  },
});
