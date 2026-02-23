/** Theme Configuration - Light & Dark Modes */

import { createTheme, ThemeOptions } from '@mui/material/styles'

declare module '@mui/material/styles' {
  interface Theme {
    customShadows: {
      card: string
      cardHover: string
      floating: string
    }
  }
  interface ThemeOptions {
    customShadows?: {
      card?: string
      cardHover?: string
      floating?: string
    }
  }
}

// Common theme settings
const commonThemeOptions: ThemeOptions = {
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: { fontWeight: 700 },
    h2: { fontWeight: 700 },
    h3: { fontWeight: 600 },
    h4: { fontWeight: 600 },
    h5: { fontWeight: 600 },
    h6: { fontWeight: 600 },
  },
  shape: {
    borderRadius: 12,
  },
  customShadows: {
    card: '0 2px 8px rgba(0,0,0,0.08)',
    cardHover: '0 8px 24px rgba(0,0,0,0.12)',
    floating: '0 4px 16px rgba(0,0,0,0.1)',
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 600,
          borderRadius: 10,
          padding: '10px 20px',
        },
        contained: {
          boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 16,
          overflow: 'hidden',
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
    MuiChip: {
      styleOverrides: {
        root: {
          fontWeight: 600,
        },
      },
    },
  },
}

// Light Theme
export const lightThemeOptions: ThemeOptions = {
  ...commonThemeOptions,
  palette: {
    mode: 'light',
    primary: {
      main: '#1e40af',
      light: '#3b82f6',
      dark: '#1e3a8a',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#6b21a8',
      light: '#9333ea',
      dark: '#581c87',
      contrastText: '#ffffff',
    },
    success: {
      main: '#059669',
      light: '#10b981',
      dark: '#047857',
    },
    error: {
      main: '#dc2626',
      light: '#ef4444',
      dark: '#b91c1c',
    },
    warning: {
      main: '#d97706',
      light: '#f59e0b',
      dark: '#b45309',
    },
    info: {
      main: '#0891b2',
      light: '#06b6d4',
      dark: '#0e7490',
    },
    background: {
      default: '#e2e8f0',
      paper: '#ffffff',
    },
    text: {
      primary: '#0f172a',
      secondary: '#334155',
    },
  },
  shape: {
    borderRadius: 12,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 600,
          borderRadius: 10,
          padding: '10px 20px',
        },
        contained: {
          boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 16,
          overflow: 'hidden',
          boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
          backgroundColor: '#ffffff',
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundColor: '#ffffff',
          color: '#0f172a',
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          fontWeight: 600,
        },
      },
    },
    MuiTypography: {
      styleOverrides: {
        root: {
          color: '#0f172a',
        },
      },
    },
    MuiListItemText: {
      styleOverrides: {
        primary: {
          color: '#0f172a',
        },
        secondary: {
          color: '#334155',
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          color: '#0f172a',
        },
      },
    },
    MuiToolbar: {
      styleOverrides: {
        root: {
          color: '#0f172a',
        },
      },
    },
    MuiIconButton: {
      styleOverrides: {
        root: {
          color: '#0f172a',
        },
      },
    },
    MuiListItemButton: {
      styleOverrides: {
        root: {
          color: '#0f172a',
          '&.Mui-selected': {
            color: '#ffffff',
          },
        },
      },
    },
    MuiListItemIcon: {
      styleOverrides: {
        root: {
          color: '#0f172a',
        },
      },
    },
  },
}

// Dark Theme
export const darkThemeOptions: ThemeOptions = {
  ...commonThemeOptions,
  palette: {
    mode: 'dark',
    primary: {
      main: '#3b82f6',
      light: '#60a5fa',
      dark: '#2563eb',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#8b5cf6',
      light: '#a78bfa',
      dark: '#7c3aed',
      contrastText: '#ffffff',
    },
    success: {
      main: '#34d399',
      light: '#6ee7b7',
      dark: '#10b981',
    },
    error: {
      main: '#f87171',
      light: '#fca5a5',
      dark: '#ef4444',
    },
    warning: {
      main: '#fbbf24',
      light: '#fcd34d',
      dark: '#f59e0b',
    },
    info: {
      main: '#22d3ee',
      light: '#67e8f9',
      dark: '#06b6d4',
    },
    background: {
      default: '#0f172a',
      paper: '#1e293b',
    },
    text: {
      primary: '#f1f5f9',
      secondary: '#94a3b8',
    },
  },
  shape: {
    borderRadius: 12,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 600,
          borderRadius: 10,
          padding: '10px 20px',
        },
        contained: {
          boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 16,
          overflow: 'hidden',
          boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
          backgroundColor: '#1e293b',
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundColor: '#1e293b',
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          fontWeight: 600,
        },
      },
    },
  },
}

// Create themes
export const lightTheme = createTheme(lightThemeOptions)
export const darkTheme = createTheme(darkThemeOptions)

// Gradient backgrounds
export const gradients = {
  light: {
    primary: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    success: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
    error: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
    warning: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
    info: 'linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)',
  },
  dark: {
    primary: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
    success: 'linear-gradient(135deg, #34d399 0%, #10b981 100%)',
    error: 'linear-gradient(135deg, #f87171 0%, #ef4444 100%)',
    warning: 'linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%)',
    info: 'linear-gradient(135deg, #22d3ee 0%, #06b6d4 100%)',
  },
}
