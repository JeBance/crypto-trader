/** Settings Page */

import React, { useEffect, useState } from 'react'
import { Box, Typography, Paper, Grid, Switch, FormControlLabel, Divider, TextField, Button, Alert } from '@mui/material'
import { api, Config } from '../services/api'
import { Card } from '../components/ui'
import SaveIcon from '@mui/icons-material/Save'

const Settings: React.FC = () => {
  const [loading, setLoading] = useState(true)
  const [config, setConfig] = useState<Config | null>(null)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    loadConfig()
  }, [])

  const loadConfig = async () => {
    try {
      setLoading(true)
      const data = await api.getConfig()
      setConfig(data)
    } catch (error) {
      console.error('Failed to load config:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSave = () => {
    setSaved(true)
    setTimeout(() => setSaved(false), 3000)
  }

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <Typography>Loading settings...</Typography>
      </Box>
    )
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>

      {saved && (
        <Alert severity="success" sx={{ mb: 3 }}>
          Settings saved successfully
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Application Settings */}
        <Grid item xs={12} md={6}>
          <Card title="Application">
            <Box p={2}>
              <FormControlLabel
                control={
                  <Switch
                    checked={config?.app.debug || false}
                    disabled
                  />
                }
                label="Debug Mode"
              />
              <Box mt={2}>
                <Typography variant="body2" color="textSecondary">
                  Environment: <strong>{config?.app.env}</strong>
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Log Level: <strong>{config?.app.log_level}</strong>
                </Typography>
              </Box>
            </Box>
          </Card>
        </Grid>

        {/* Trading Settings */}
        <Grid item xs={12} md={6}>
          <Card title="Trading">
            <Box p={2}>
              <Typography variant="body2" color="textSecondary" mb={1}>
                Trading Mode
              </Typography>
              <Chip label={config?.trading.mode} size="small" sx={{ mb: 2 }} />
              
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    Max Position Size
                  </Typography>
                  <Typography variant="h6">
                    {config?.trading.max_position_size_percent}%
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    Stop Loss
                  </Typography>
                  <Typography variant="h6" color="error.main">
                    {config?.trading.stop_loss_percent}%
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    Take Profit
                  </Typography>
                  <Typography variant="h6" color="success.main">
                    {config?.trading.take_profit_percent}%
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    Daily Loss Limit
                  </Typography>
                  <Typography variant="h6" color="warning.main">
                    {config?.trading.daily_loss_limit_percent}%
                  </Typography>
                </Grid>
              </Grid>
            </Box>
          </Card>
        </Grid>

        {/* Exchange Settings */}
        <Grid item xs={12} md={6}>
          <Card title="Exchanges">
            <Box p={2}>
              <Box mb={3}>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                  <Typography variant="subtitle2">Binance</Typography>
                  <Chip 
                    label={config?.exchanges.binance.configured ? 'Configured' : 'Not Configured'} 
                    color={config?.exchanges.binance.configured ? 'success' : 'default'}
                    size="small"
                  />
                </Box>
                <Typography variant="body2" color="textSecondary">
                  {config?.exchanges.binance.testnet ? 'Testnet' : 'Production'}
                </Typography>
              </Box>

              <Divider sx={{ my: 2 }} />

              <Box>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                  <Typography variant="subtitle2">Bybit</Typography>
                  <Chip 
                    label={config?.exchanges.bybit.configured ? 'Configured' : 'Not Configured'} 
                    color={config?.exchanges.bybit.configured ? 'success' : 'default'}
                    size="small"
                  />
                </Box>
                <Typography variant="body2" color="textSecondary">
                  {config?.exchanges.bybit.testnet ? 'Testnet' : 'Production'}
                </Typography>
              </Box>
            </Box>
          </Card>
        </Grid>

        {/* Notifications */}
        <Grid item xs={12} md={6}>
          <Card title="Notifications">
            <Box p={2}>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="subtitle2">Telegram</Typography>
                <Chip 
                  label={config?.notifications.telegram.configured ? 'Connected' : 'Not Configured'} 
                  color={config?.notifications.telegram.configured ? 'success' : 'default'}
                  size="small"
                />
              </Box>
              <Typography variant="body2" color="textSecondary">
                {config?.notifications.telegram.configured 
                  ? 'Telegram bot is configured and ready to send notifications'
                  : 'Configure TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env file'
                }
              </Typography>
            </Box>
          </Card>
        </Grid>

        {/* Server Info */}
        <Grid item xs={12}>
          <Card title="Server">
            <Box p={2}>
              <Grid container spacing={4}>
                <Grid item xs={6} sm={3}>
                  <Typography variant="body2" color="textSecondary">
                    Host
                  </Typography>
                  <Typography variant="h6" fontFamily="monospace">
                    {config?.server.host}
                  </Typography>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Typography variant="body2" color="textSecondary">
                    Port
                  </Typography>
                  <Typography variant="h6" fontFamily="monospace">
                    {config?.server.port}
                  </Typography>
                </Grid>
              </Grid>
            </Box>
          </Card>
        </Grid>
      </Grid>

      <Box mt={4} display="flex" justifyContent="flex-end">
        <Button 
          variant="contained" 
          startIcon={<SaveIcon />}
          onClick={handleSave}
        >
          Save Changes
        </Button>
      </Box>
    </Box>
  )
}

export default Settings
