/** Dashboard Page */

import React, { useEffect, useState } from 'react'
import { Grid, Paper, Box, Typography, CircularProgress } from '@mui/material'
import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet'
import TrendingUpIcon from '@mui/icons-material/TrendingUp'
import PsychologyIcon from '@mui/icons-material/Psychology'
import { api } from '../services/api'
import { Card, Chip } from '../components/ui'
import { translations } from '../utils/translations'

interface DashboardStats {
  totalBalance: number
  todayPnL: number
  activePositions: number
  activeStrategies: number
}

const Dashboard: React.FC = () => {
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState<DashboardStats>({
    totalBalance: 0,
    todayPnL: 0,
    activePositions: 0,
    activeStrategies: 0,
  })
  const [health, setHealth] = useState<Record<string, unknown> | null>(null)

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      setLoading(true)
      
      // Load health status
      const healthData = await api.getHealthStatus()
      setHealth(healthData)

      // Load positions
      const positionsData = await api.getPositions()
      const activePositions = positionsData.positions.filter(p => p.quantity > 0)
      
      // Load strategies
      const strategiesData = await api.getStrategies()
      const activeStrategies = strategiesData.strategies.filter(s => s.active)

      // Calculate stats
      const totalUnrealizedPnL = activePositions.reduce((sum, p) => sum + p.unrealized_pnl, 0)
      
      setStats({
        totalBalance: 10000, // TODO: Get from exchange
        todayPnL: totalUnrealizedPnL,
        activePositions: activePositions.length,
        activeStrategies: activeStrategies.length,
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

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        {translations.dashboard.title}
      </Typography>

      {/* Stats Cards */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <Box display="flex" alignItems="center" justifyContent="space-between">
              <Box>
                <Typography color="textSecondary" variant="body2">
                  {translations.dashboard.totalBalance}
                </Typography>
                <Typography variant="h4">
                  ${stats.totalBalance.toLocaleString()}
                </Typography>
              </Box>
              <AccountBalanceWalletIcon color="primary" sx={{ fontSize: 48, opacity: 0.3 }} />
            </Box>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <Box display="flex" alignItems="center" justifyContent="space-between">
              <Box>
                <Typography color="textSecondary" variant="body2">
                  {translations.dashboard.todayPnL}
                </Typography>
                <Typography
                  variant="h4"
                  color={stats.todayPnL >= 0 ? 'success.main' : 'error.main'}
                >
                  {stats.todayPnL >= 0 ? '+' : ''}${stats.todayPnL.toFixed(2)}
                </Typography>
              </Box>
              <TrendingUpIcon
                color={stats.todayPnL >= 0 ? 'success' : 'error'}
                sx={{ fontSize: 48, opacity: 0.3 }}
              />
            </Box>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <Box display="flex" alignItems="center" justifyContent="space-between">
              <Box>
                <Typography color="textSecondary" variant="body2">
                  {translations.dashboard.activePositions}
                </Typography>
                <Typography variant="h4">{stats.activePositions}</Typography>
              </Box>
              <AccountBalanceWalletIcon color="info" sx={{ fontSize: 48, opacity: 0.3 }} />
            </Box>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <Box display="flex" alignItems="center" justifyContent="space-between">
              <Box>
                <Typography color="textSecondary" variant="body2">
                  {translations.dashboard.activeStrategies}
                </Typography>
                <Typography variant="h4">{stats.activeStrategies}</Typography>
              </Box>
              <PsychologyIcon color="warning" sx={{ fontSize: 48, opacity: 0.3 }} />
            </Box>
          </Card>
        </Grid>
      </Grid>

      {/* System Status */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              {translations.dashboard.systemStatus}
            </Typography>
            {health ? (
              <Box>
                <Box display="flex" justifyContent="space-between" mb={1}>
                  <Typography variant="body2">{translations.dashboard.environment}</Typography>
                  <Chip
                    label={(health.application as Record<string, string>)?.environment || translations.common.loading}
                    size="small"
                  />
                </Box>
                <Box display="flex" justifyContent="space-between" mb={1}>
                  <Typography variant="body2">{translations.dashboard.tradingMode}</Typography>
                  <Chip
                    label={(health.application as Record<string, string>)?.trading_mode || translations.common.loading}
                    size="small"
                  />
                </Box>
                <Box display="flex" justifyContent="space-between">
                  <Typography variant="body2">{translations.dashboard.version}</Typography>
                  <Typography variant="body2" fontFamily="monospace">
                    v{(health.application as Record<string, string>)?.version || '0.1.0'}
                  </Typography>
                </Box>
              </Box>
            ) : (
              <Typography color="textSecondary">{translations.dashboard.noData}</Typography>
            )}
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              {translations.dashboard.quickActions}
            </Typography>
            <Box>
              <Typography color="textSecondary" variant="body2">
                {translations.dashboard.useNavigation}
              </Typography>
              <Box mt={2}>
                <Typography variant="body2">• {translations.nav.positions} - {translations.dashboard.positionsDesc}</Typography>
                <Typography variant="body2">• {translations.nav.orders} - {translations.dashboard.ordersDesc}</Typography>
                <Typography variant="body2">• {translations.nav.strategies} - {translations.dashboard.strategiesDesc}</Typography>
                <Typography variant="body2">• {translations.nav.settings} - {translations.dashboard.settingsDesc}</Typography>
              </Box>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  )
}

export default Dashboard
