import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ThemeProvider } from '@mui/material/styles'
import { CssBaseline, responsiveFontSizes } from '@mui/material'
import { useMemo } from 'react'
import { lightTheme, darkTheme } from './theme'
import { useThemeStore } from './store/themeStore'

import Layout from './components/layout/Layout'
import Dashboard from './pages/Dashboard'
import Positions from './pages/Positions'
import Orders from './pages/Orders'
import Strategies from './pages/Strategies'
import Settings from './pages/Settings'
import Server from './pages/Server'
import DataCollection from './pages/DataCollection'

function App() {
  const mode = useThemeStore((state) => state.mode)
  
  const theme = useMemo(() => {
    const baseTheme = mode === 'light' ? lightTheme : darkTheme
    return responsiveFontSizes(baseTheme)
  }, [mode])

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <BrowserRouter basename="/crypto-trader">
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="positions" element={<Positions />} />
            <Route path="orders" element={<Orders />} />
            <Route path="strategies" element={<Strategies />} />
            <Route path="data-collection" element={<DataCollection />} />
            <Route path="settings" element={<Settings />} />
            <Route path="server" element={<Server />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  )
}

export default App
