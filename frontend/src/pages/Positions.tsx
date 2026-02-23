/** Positions Page */

import React, { useEffect, useState } from 'react'
import { Box, Typography, CircularProgress, Button } from '@mui/material'
import { api, Position } from '../services/api'
import { Table, StatusBadge, Paper } from '../components/ui'
import { translations } from '../utils/translations'

const Positions: React.FC = () => {
  const [loading, setLoading] = useState(true)
  const [positions, setPositions] = useState<Position[]>([])

  useEffect(() => {
    loadPositions()
  }, [])

  const loadPositions = async () => {
    try {
      setLoading(true)
      const data = await api.getPositions()
      setPositions(data.positions)
    } catch (error) {
      console.error('Failed to load positions:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleClosePosition = async (symbol: string) => {
    if (!confirm(`Закрыть позицию для ${symbol}?`)) return

    try {
      await api.closePosition(symbol)
      loadPositions()
    } catch (error) {
      console.error('Failed to close position:', error)
      alert('Не удалось закрыть позицию')
    }
  }

  const columns = [
    { key: 'symbol', label: translations.positions.symbol },
    {
      key: 'side',
      label: translations.positions.side,
      render: (row: Position) => (
        <StatusBadge status={row.side} />
      ),
    },
    {
      key: 'quantity',
      label: translations.positions.quantity,
      render: (row: Position) => Number(row.quantity).toFixed(6),
    },
    {
      key: 'entry_price',
      label: translations.positions.entryPrice,
      render: (row: Position) => `$${Number(row.entry_price).toFixed(2)}`,
    },
    {
      key: 'current_price',
      label: translations.positions.currentPrice,
      render: (row: Position) => `$${Number(row.current_price).toFixed(2)}`,
    },
    {
      key: 'pnl_percent',
      label: 'P&L %',
      render: (row: Position) => {
        const pnl = Number(row.pnl_percent)
        return (
          <Typography
            component="span"
            color={pnl >= 0 ? 'success.main' : 'error.main'}
            fontWeight="bold"
          >
            {pnl >= 0 ? '+' : ''}{pnl.toFixed(2)}%
          </Typography>
        )
      },
    },
    {
      key: 'unrealized_pnl',
      label: translations.positions.unrealizedPnL,
      render: (row: Position) => {
        const pnl = Number(row.unrealized_pnl)
        return (
          <Typography
            component="span"
            color={pnl >= 0 ? 'success.main' : 'error.main'}
          >
            {pnl >= 0 ? '+' : ''}${pnl.toFixed(2)}
          </Typography>
        )
      },
    },
    {
      key: 'actions',
      label: 'Действия',
      render: (row: Position) => (
        <Button
          size="small"
          color="error"
          variant="outlined"
          onClick={() => handleClosePosition(row.symbol)}
        >
          {translations.positions.close}
        </Button>
      ),
    },
  ]

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
        {translations.positions.title}
      </Typography>

      {positions.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography color="textSecondary">
            {translations.positions.noPositions}
          </Typography>
        </Paper>
      ) : (
        <Table columns={columns} data={positions} />
      )}
    </Box>
  )
}

export default Positions
