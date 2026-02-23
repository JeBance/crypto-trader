/** Dashboard Page - Fully Responsive with Consistent Widths */

import React, { useEffect, useState } from 'react'
import { 
  Grid, 
  Box, 
  Typography, 
  CircularProgress,
  Card,
  CardContent,
  CardActions,
  Button,
  Stack,
  useMediaQuery,
  useTheme,
} from '@mui/material'
import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet'
import TrendingUpIcon from '@mui/icons-material/TrendingUp'
import TrendingDownIcon from '@mui/icons-material/TrendingDown'
import PsychologyIcon from '@mui/icons-material/Psychology'
import StorageIcon from '@mui/icons-material/Storage'
import { api } from '../services/api'
import { translations } from '../utils/translations'

interface DashboardStats {
  totalBalance: number
  todayPnL: number
  activePositions: number
  activeStrategies: number
  totalCandles: number
}

const Dashboard: React.FC = () => {
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'))
  const isTablet = useMediaQuery(theme.breakpoints.between('sm', 'md'))
  
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState<DashboardStats>({
    totalBalance: 0,
    todayPnL: 0,
    activePositions: 0,
    activeStrategies: 0,
    totalCandles: 0,
  })

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      setLoading(true)

      // Load positions
      const positionsData = await api.getPositions()
      const activePositions = positionsData.positions?.filter((p: any) => p.quantity > 0) || []

      // Load strategies
      const strategiesData = await api.getStrategies()
      const activeStrategies = strategiesData.strategies?.filter((s: any) => s.active) || []

      // Load data collection stats
      let totalCandles = 0
      try {
        const dataStats = await fetch('/api/market-data/stats').then(r => r.json())
        totalCandles = dataStats.total_candles || 0
      } catch (e) {
        // Ignore if not available
      }

      // Calculate stats
      const totalUnrealizedPnL = activePositions.reduce((sum: number, p: any) => sum + (p.unrealized_pnl || 0), 0)

      setStats({
        totalBalance: 10000, // TODO: Get from exchange
        todayPnL: totalUnrealizedPnL,
        activePositions: activePositions.length,
        activeStrategies: activeStrategies.length,
        totalCandles,
      })
    } catch (error) {
      console.error('Failed to load dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    )
  }

  // Stat cards data
  const statCards = [
    {
      title: translations.dashboard.totalBalance,
      value: `$${stats.totalBalance.toLocaleString()}`,
      icon: <AccountBalanceWalletIcon />,
      color: 'primary',
    },
    {
      title: 'Today PnL',
      value: `${stats.todayPnL >= 0 ? '+' : ''}$${stats.todayPnL.toFixed(2)}`,
      icon: stats.todayPnL >= 0 ? <TrendingUpIcon /> : <TrendingDownIcon />,
      color: stats.todayPnL >= 0 ? 'success' : 'error',
    },
    {
      title: 'Active Positions',
      value: stats.activePositions.toString(),
      icon: <StorageIcon />,
      color: 'info',
    },
    {
      title: 'Active Strategies',
      value: stats.activeStrategies.toString(),
      icon: <PsychologyIcon />,
      color: 'secondary',
    },
  ]

  return (
    <Box sx={{ p: { xs: 1, sm: 2, md: 3 } }}>
      {/* Header */}
      <Box mb={{ xs: 2, sm: 3 }}>
        <Typography 
          variant={isMobile ? 'h5' : 'h4'} 
          gutterBottom
          sx={{ fontWeight: 'bold' }}
        >
          {translations.dashboard.title}
        </Typography>
      </Box>

      {/* Stats Cards - Full width on mobile, 2 cols on tablet, 4 cols on desktop */}
      <Grid 
        container 
        spacing={{ xs: 2, sm: 3 }} 
        mb={{ xs: 2, sm: 3 }}
      >
        {statCards.map((card, index) => (
          <Grid 
            item
            xs={12} 
            sm={isTablet ? 6 : 6} 
            md={3}
            key={index}
          >
            <Card 
              sx={{ 
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                transition: 'transform 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 6,
                },
              }}
              elevation={3}
            >
              <CardContent sx={{ flexGrow: 1 }}>
                <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
                  <Box
                    sx={{
                      p: 1,
                      borderRadius: 2,
                      bgcolor: `${card.color}.lighter`,
                      color: `${card.color}.main`,
                    }}
                  >
                    {card.icon}
                  </Box>
                </Box>
                <Typography 
                  color="text.secondary" 
                  variant="body2"
                  sx={{ 
                    fontSize: { xs: '0.75rem', sm: '0.875rem' },
                    mb: 1,
                  }}
                >
                  {card.title}
                </Typography>
                <Typography 
                  variant={isMobile ? 'h5' : 'h4'}
                  sx={{ 
                    fontWeight: 'bold',
                    fontSize: { xs: '1.5rem', sm: '1.75rem', md: '2rem' },
                  }}
                >
                  {card.value}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Data Collection Stats - Same width as other cards */}
      {stats.totalCandles > 0 && (
        <Card sx={{ mb: 3 }} elevation={3}>
          <CardContent>
            <Typography 
              variant={isMobile ? 'h6' : 'h5'} 
              gutterBottom
              sx={{ fontWeight: 'bold', mb: 2 }}
            >
              📊 Data Collection
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6} md={4}>
                <Box display="flex" alignItems="center" gap={2}>
                  <StorageIcon color="primary" fontSize="large" />
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Total Candles
                    </Typography>
                    <Typography variant="h6" fontWeight="bold">
                      {stats.totalCandles.toLocaleString()}
                    </Typography>
                  </Box>
                </Box>
              </Grid>
            </Grid>
          </CardContent>
          <CardActions sx={{ px: 2, pb: 2 }}>
            <Button 
              size="small" 
              variant="outlined"
              href="/data-collection"
              fullWidth={isMobile}
            >
              Manage Data Collection
            </Button>
          </CardActions>
        </Card>
      )}

      {/* Quick Actions - Same width as Data Collection */}
      <Card elevation={3}>
        <CardContent>
          <Typography 
            variant={isMobile ? 'h6' : 'h5'} 
            gutterBottom
            sx={{ fontWeight: 'bold', mb: 2 }}
          >
            ⚡ Quick Actions
          </Typography>
          <Stack 
            direction={{ xs: 'column', sm: 'row' }}
            spacing={2}
          >
            <Button 
              variant="contained" 
              startIcon={<StorageIcon />}
              href="/data-collection"
              fullWidth
            >
              Data Collection
            </Button>
            <Button 
              variant="outlined" 
              startIcon={<PsychologyIcon />}
              href="/strategies"
              fullWidth
            >
              Strategies
            </Button>
            <Button 
              variant="outlined" 
              startIcon={<AccountBalanceWalletIcon />}
              href="/positions"
              fullWidth
            >
              Positions
            </Button>
          </Stack>
        </CardContent>
      </Card>
    </Box>
  )
}

export default Dashboard
