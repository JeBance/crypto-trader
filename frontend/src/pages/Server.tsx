/** Server Management Page */

import React, { useEffect, useState } from 'react'
import { Box, Typography, Paper, Button, Grid, Chip, CircularProgress, Alert, Divider } from '@mui/material'
import RefreshIcon from '@mui/icons-material/Refresh'
import UpdateIcon from '@mui/icons-material/Update'
import CheckCircleIcon from '@mui/icons-material/CheckCircle'
import { api } from '../services/api'
import { Card } from '../components/ui'

interface ServerStatus {
  status: string
  uptime_seconds: number | null
  last_restart: string | null
  last_update: string | null
  restart_pending: boolean
  update_pending: boolean
  version: string
}

const Server: React.FC = () => {
  const [loading, setLoading] = useState(true)
  const [status, setStatus] = useState<ServerStatus | null>(null)
  const [restarting, setRestarting] = useState(false)
  const [updating, setUpdating] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'info', text: string } | null>(null)

  useEffect(() => {
    loadStatus()
    // Poll status every 5 seconds
    const interval = setInterval(loadStatus, 5000)
    return () => clearInterval(interval)
  }, [])

  const loadStatus = async () => {
    try {
      const data = await api.getServerStatus()
      setStatus(data)
      setLoading(false)
    } catch (error) {
      console.error('Failed to load server status:', error)
    }
  }

  const handleRestart = async () => {
    if (!confirm('Вы уверены, что хотите перезапустить сервер?')) return

    try {
      setRestarting(true)
      await api.restartServer()
      setMessage({ type: 'success', text: 'Перезапуск сервера инициирован...' })
      
      // Wait for restart
      setTimeout(() => {
        window.location.reload()
      }, 5000)
    } catch (error) {
      setMessage({ type: 'error', text: 'Ошибка при перезапуске сервера' })
    } finally {
      setRestarting(false)
    }
  }

  const handleUpdate = async () => {
    if (!confirm('Вы уверены, что хотите обновить сервер? Будет выполнена команда git pull и перезапуск.')) return

    try {
      setUpdating(true)
      await api.updateServer()
      setMessage({ type: 'success', text: 'Обновление загружается. Сервер будет перезапущен автоматически.' })
      
      // Wait for update and restart
      setTimeout(() => {
        window.location.reload()
      }, 10000)
    } catch (error) {
      setMessage({ type: 'error', text: 'Ошибка при обновлении сервера' })
    } finally {
      setUpdating(false)
    }
  }

  const formatUptime = (seconds: number | null): string => {
    if (!seconds) return '0s'
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = Math.floor(seconds % 60)
    
    if (hours > 0) {
      return `${hours}ч ${minutes}м ${secs}с`
    } else if (minutes > 0) {
      return `${minutes}м ${secs}с`
    }
    return `${secs}с`
  }

  const formatDate = (dateString: string | null | undefined): string => {
    if (!dateString) return 'Никогда'
    return new Date(dateString).toLocaleString('ru-RU')
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
        Управление сервером
      </Typography>

      {message && (
        <Alert severity={message.type} sx={{ mb: 3 }} onClose={() => setMessage(null)}>
          {message.text}
        </Alert>
      )}

      {/* Status Cards */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <Box display="flex" alignItems="center" justifyContent="space-between">
              <Box>
                <Typography color="textSecondary" variant="body2">
                  Статус
                </Typography>
                <Typography variant="h6" color="success.main" display="flex" alignItems="center">
                  <CheckCircleIcon sx={{ mr: 1, fontSize: 24 }} />
                  Работает
                </Typography>
              </Box>
            </Box>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <Box display="flex" alignItems="center" justifyContent="space-between">
              <Box>
                <Typography color="textSecondary" variant="body2">
                  Время работы
                </Typography>
                <Typography variant="h6">
                  {formatUptime(status?.uptime_seconds || 0)}
                </Typography>
              </Box>
            </Box>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <Box display="flex" alignItems="center" justifyContent="space-between">
              <Box>
                <Typography color="textSecondary" variant="body2">
                  Версия
                </Typography>
                <Typography variant="h6">
                  v{status?.version || '1.0.0'}
                </Typography>
              </Box>
            </Box>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <Box display="flex" alignItems="center" justifyContent="space-between">
              <Box>
                <Typography color="textSecondary" variant="body2">
                  Перезапуск
                </Typography>
                <Typography variant="h6">
                  {status?.restart_pending ? '⏳ Ожидается' : '✅ Нет'}
                </Typography>
              </Box>
            </Box>
          </Card>
        </Grid>
      </Grid>

      {/* Control Panel */}
      <Card title="Панель управления" sx={{ mb: 3 }}>
        <Box p={2}>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <Button
                variant="contained"
                color="warning"
                fullWidth
                size="large"
                startIcon={restarting ? <CircularProgress size={20} /> : <RefreshIcon />}
                onClick={handleRestart}
                disabled={restarting || updating}
              >
                {restarting ? 'Перезапуск...' : 'Перезапустить сервер'}
              </Button>
            </Grid>

            <Grid item xs={12} sm={6}>
              <Button
                variant="contained"
                color="primary"
                fullWidth
                size="large"
                startIcon={updating ? <CircularProgress size={20} /> : <UpdateIcon />}
                onClick={handleUpdate}
                disabled={restarting || updating}
              >
                {updating ? 'Обновление...' : 'Обновить из GitHub'}
              </Button>
            </Grid>
          </Grid>

          <Alert severity="info" sx={{ mt: 2 }}>
            <Typography variant="body2">
              ⚠️ Перезапуск сервера остановит все активные процессы на несколько секунд.
              Обновление загрузит последние изменения из репозитория GitHub и выполнит перезапуск.
            </Typography>
          </Alert>
        </Box>
      </Card>

      {/* Information */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Информация
            </Typography>
            <Box>
              <Box display="flex" justifyContent="space-between" py={1}>
                <Typography variant="body2" color="textSecondary">
                  Последний перезапуск:
                </Typography>
                <Typography variant="body2">
                  {formatDate(status?.last_restart)}
                </Typography>
              </Box>
              <Box display="flex" justifyContent="space-between" py={1}>
                <Typography variant="body2" color="textSecondary">
                  Последнее обновление:
                </Typography>
                <Typography variant="body2">
                  {formatDate(status?.last_update)}
                </Typography>
              </Box>
              <Box display="flex" justifyContent="space-between" py={1}>
                <Typography variant="body2" color="textSecondary">
                  Ожидается обновление:
                </Typography>
                <Chip
                  label={status?.update_pending ? 'Да' : 'Нет'}
                  size="small"
                  color={status?.update_pending ? 'warning' : 'default'}
                />
              </Box>
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Как это работает
            </Typography>
            <Box>
              <Typography variant="body2" paragraph>
                <strong>🔄 Перезапуск:</strong> Сервер будет перезапущен с использованием системы 
                самовосстановления. Все процессы будут остановлены и запущены заново.
              </Typography>
              <Divider sx={{ my: 1 }} />
              <Typography variant="body2" paragraph>
                <strong>⬇️ Обновление:</strong> Будет выполнена команда <code>git pull</code> для 
                загрузки последних изменений из репозитория GitHub, после чего сервер автоматически 
                перезапустится.
              </Typography>
              <Divider sx={{ my: 1 }} />
              <Typography variant="body2">
                <strong>✅ Авто-восстановление:</strong> Если сервер упадет, он автоматически 
                перезапустится через 5 секунд.
              </Typography>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  )
}

export default Server
