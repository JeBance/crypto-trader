/** Responsive Layout with Theme Toggle */

import React, { useState } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import {
  Box,
  Drawer,
  AppBar,
  Toolbar,
  List,
  Typography,
  Divider,
  IconButton,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Container,
  Badge,
  useMediaQuery,
  useTheme,
  Tooltip,
} from '@mui/material'
import MenuIcon from '@mui/icons-material/Menu'
import DashboardIcon from '@mui/icons-material/Dashboard'
import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet'
import ReceiptIcon from '@mui/icons-material/Receipt'
import PsychologyIcon from '@mui/icons-material/Psychology'
import StorageIcon from '@mui/icons-material/Storage'
import SettingsIcon from '@mui/icons-material/Settings'
import ServerIcon from '@mui/icons-material/Dns'
import Brightness4Icon from '@mui/icons-material/Brightness4'
import Brightness7Icon from '@mui/icons-material/Brightness7'
import { translations } from '../../utils/translations'
import { useThemeStore } from '../../store/themeStore'

const drawerWidth = 280
const collapsedDrawerWidth = 70

const menuItems = [
  { text: translations.nav.dashboard, icon: <DashboardIcon />, path: '/' },
  { text: translations.nav.positions, icon: <AccountBalanceWalletIcon />, path: '/positions' },
  { text: translations.nav.orders, icon: <ReceiptIcon />, path: '/orders' },
  { text: translations.nav.strategies, icon: <PsychologyIcon />, path: '/strategies' },
  { text: 'Data Collection', icon: <StorageIcon />, path: '/data-collection' },
  { text: translations.nav.settings, icon: <SettingsIcon />, path: '/settings' },
  { text: 'Сервер', icon: <ServerIcon />, path: '/server' },
]

interface LayoutProps {
  children?: React.ReactNode
}

const Layout: React.FC<LayoutProps> = () => {
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'))
  const isTablet = useMediaQuery(theme.breakpoints.between('sm', 'md'))
  
  const [mobileOpen, setMobileOpen] = useState(false)
  const [collapsed, setCollapsed] = useState(isTablet)
  
  const navigate = useNavigate()
  const location = useLocation()
  const { mode, toggleTheme } = useThemeStore()

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen)
  }

  const handleNavigation = (path: string) => {
    navigate(path)
    if (isMobile) {
      setMobileOpen(false)
    }
  }

  const drawerContent = (
    <Box sx={{ 
      width: collapsed ? collapsedDrawerWidth : drawerWidth,
      transition: 'width 0.3s ease',
      overflow: 'hidden',
    }}>
      <Toolbar sx={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: collapsed ? 'center' : 'flex-start',
        px: collapsed ? 1 : 2,
      }}>
        {!collapsed && (
          <Typography 
            variant="h6" 
            sx={{ 
              fontWeight: 'bold',
              fontSize: '18px',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              backgroundClip: 'text',
              textFillColor: 'transparent',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            Crypto Trader
          </Typography>
        )}
        {collapsed && (
          <Typography sx={{ fontSize: '24px', fontWeight: 'bold' }}>
            CT
          </Typography>
        )}
      </Toolbar>
      <Divider />
      <List sx={{ py: 2 }}>
        {menuItems.map((item) => (
          <ListItem key={item.text} disablePadding sx={{ display: 'block', mb: 1 }}>
            <ListItemButton
              selected={location.pathname === item.path}
              onClick={() => handleNavigation(item.path)}
              sx={{
                minHeight: 56,
                justifyContent: collapsed ? 'center' : 'initial',
                px: collapsed ? 2.5 : 3,
                mx: 1,
                borderRadius: 3,
                '&.Mui-selected': {
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  color: 'white',
                  '&:hover': {
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    opacity: 0.9,
                  },
                },
              }}
            >
              <ListItemIcon
                sx={{
                  minWidth: 0,
                  mr: collapsed ? 0 : 'auto',
                  justifyContent: 'center',
                  color: location.pathname === item.path ? 'inherit' : 'inherit',
                }}
              >
                {item.icon}
              </ListItemIcon>
              {!collapsed && (
                <ListItemText 
                  primary={item.text}
                  sx={{ opacity: location.pathname === item.path ? 1 : 0.8 }}
                />
              )}
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </Box>
  )

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <AppBar
        position="fixed"
        elevation={0}
        sx={{
          width: { sm: `calc(100% - ${collapsed ? collapsedDrawerWidth : drawerWidth}px)` },
          ml: { sm: `${collapsed ? collapsedDrawerWidth : drawerWidth}px` },
          background: 'rgba(255,255,255,0.1)',
          backdropFilter: 'blur(20px)',
          borderBottom: '1px solid',
          borderColor: 'divider',
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { sm: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          
          <Typography 
            variant="h6" 
            noWrap 
            sx={{ 
              flexGrow: 1, 
              fontSize: { xs: '16px', sm: '18px' },
              fontWeight: 600,
            }}
          >
            {menuItems.find(item => item.path === location.pathname)?.text || 'Crypto Trader'}
          </Typography>
          
          <Tooltip title={`Switch to ${mode === 'light' ? 'dark' : 'light'} mode`}>
            <IconButton 
              color="inherit" 
              onClick={toggleTheme}
              sx={{ mr: 1 }}
            >
              {mode === 'light' ? <Brightness4Icon /> : <Brightness7Icon />}
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Notifications">
            <IconButton color="inherit">
              <Badge badgeContent={0} color="error">
                <StorageIcon />
              </Badge>
            </IconButton>
          </Tooltip>
          
          {!isMobile && (
            <IconButton
              onClick={() => setCollapsed(!collapsed)}
              sx={{ ml: 1 }}
            >
              <MenuIcon sx={{ transform: collapsed ? 'rotate(180deg)' : 'rotate(0)', transition: 'transform 0.3s' }} />
            </IconButton>
          )}
        </Toolbar>
      </AppBar>
      
      <Box
        component="nav"
        sx={{ 
          width: { sm: collapsed ? collapsedDrawerWidth : drawerWidth },
          flexShrink: { sm: 0 },
        }}
      >
        {/* Mobile drawer */}
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{ keepMounted: true }}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': { 
              boxSizing: 'border-box', 
              width: drawerWidth,
            },
          }}
        >
          {drawerContent}
        </Drawer>
        
        {/* Desktop drawer */}
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': { 
              boxSizing: 'border-box',
              width: collapsed ? collapsedDrawerWidth : drawerWidth,
              transition: 'width 0.3s ease',
              overflowX: 'hidden',
            },
          }}
          open
        >
          {drawerContent}
        </Drawer>
      </Box>
      
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          width: { sm: `calc(100% - ${collapsed ? collapsedDrawerWidth : drawerWidth}px)` },
          mt: { xs: 8, sm: 9 },
          minHeight: '100vh',
          background: mode === 'light' 
            ? 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)'
            : 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
          transition: 'all 0.3s ease',
        }}
      >
        <Container 
          maxWidth="xl" 
          sx={{ 
            px: { xs: 1, sm: 2, md: 3 },
            py: { xs: 2, sm: 3 },
          }}
        >
          <Outlet />
        </Container>
      </Box>
    </Box>
  )
}

export default Layout
