/** Strategies Page */

import React, { useEffect, useState } from 'react'
import { Box, Typography, CircularProgress, Card, CardContent, Grid, Button, Chip, Switch, FormControlLabel } from '@mui/material'
import { api, Strategy } from '../services/api'
import PsychologyIcon from '@mui/icons-material/Psychology'
import CheckCircleIcon from '@mui/icons-material/CheckCircle'
import StopCircleIcon from '@mui/icons-material/StopCircle'

const Strategies: React.FC = () => {
  const [loading, setLoading] = useState(true)
  const [strategies, setStrategies] = useState<Strategy[]>([])

  useEffect(() => {
    loadStrategies()
  }, [])

  const loadStrategies = async () => {
    try {
      setLoading(true)
      const data = await api.getStrategies()
      setStrategies(data.strategies)
    } catch (error) {
      console.error('Failed to load strategies:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleToggleStrategy = async (strategy: Strategy) => {
    try {
      if (strategy.active) {
        await api.deactivateStrategy(strategy.name)
      } else {
        await api.activateStrategy(strategy.name)
      }
      loadStrategies()
    } catch (error) {
      console.error('Failed to toggle strategy:', error)
      alert('Failed to toggle strategy')
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
        Strategies
      </Typography>

      <Grid container spacing={3}>
        {strategies.map((strategy) => (
          <Grid item xs={12} md={6} lg={4} key={strategy.name}>
            <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <CardContent sx={{ flexGrow: 1 }}>
                <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
                  <Box display="flex" alignItems="center">
                    <PsychologyIcon color="primary" sx={{ mr: 1 }} />
                    <Typography variant="h6" component="h2">
                      {strategy.name.toUpperCase()}
                    </Typography>
                  </Box>
                  <Chip 
                    label={strategy.active ? 'Active' : 'Inactive'} 
                    color={strategy.active ? 'success' : 'default'}
                    size="small"
                    icon={strategy.active ? <CheckCircleIcon /> : <StopCircleIcon />}
                  />
                </Box>

                <Typography color="textSecondary" variant="body2" mb={2}>
                  {strategy.description}
                </Typography>

                <Box mb={2}>
                  <Typography variant="body2" color="textSecondary" gutterBottom>
                    Parameters:
                  </Typography>
                  {Object.entries(strategy.parameters).map(([key, value]) => (
                    <Box key={key} display="flex" justifyContent="space-between" py={0.5}>
                      <Typography variant="body2" textTransform="capitalize">
                        {key}:
                      </Typography>
                      <Typography variant="body2" fontFamily="monospace">
                        {String(value)}
                      </Typography>
                    </Box>
                  ))}
                </Box>

                {strategy.symbols && strategy.symbols.length > 0 && (
                  <Box mb={2}>
                    <Typography variant="body2" color="textSecondary" gutterBottom>
                      Symbols:
                    </Typography>
                    <Box display="flex" flexWrap="wrap" gap={0.5}>
                      {strategy.symbols.map((symbol) => (
                        <Chip key={symbol} label={symbol} size="small" variant="outlined" />
                      ))}
                    </Box>
                  </Box>
                )}

                {strategy.timeframe && (
                  <Box mb={2}>
                    <Typography variant="body2" color="textSecondary" gutterBottom>
                      Timeframe:
                    </Typography>
                    <Chip label={strategy.timeframe} size="small" />
                  </Box>
                )}
              </CardContent>

              <CardContent sx={{ pt: 2, borderTop: 1, borderColor: 'divider' }}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={strategy.active}
                      onChange={() => handleToggleStrategy(strategy)}
                      color="success"
                    />
                  }
                  label={strategy.active ? 'Active' : 'Inactive'}
                />
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {strategies.length === 0 && (
        <Box textAlign="center" py={8}>
          <PsychologyIcon sx={{ fontSize: 64, opacity: 0.3, mb: 2 }} />
          <Typography color="textSecondary">
            No strategies available
          </Typography>
        </Box>
      )}
    </Box>
  )
}

export default Strategies
