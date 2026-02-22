/** Positions Page */

import React, { useEffect, useState } from 'react'
import { Box, Typography, CircularProgress, Button } from '@mui/material'
import { api, Position } from '../services/api'
import { Table, StatusBadge, Paper } from '../components/ui'

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
    if (!confirm(`Close position for ${symbol}?`)) return

    try {
      await api.closePosition(symbol)
      loadPositions()
    } catch (error) {
      console.error('Failed to close position:', error)
      alert('Failed to close position')
    }
  }

  const columns = [
    { key: 'symbol', label: 'Symbol' },
    { 
      key: 'side', 
      label: 'Side',
      render: (row: Record<string, unknown>) => (
        <StatusBadge status={row.side as string} />
      ),
    },
    { 
      key: 'quantity', 
      label: 'Quantity',
      render: (row: Record<string, unknown>) => Number(row.quantity).toFixed(6),
    },
    { 
      key: 'entry_price', 
      label: 'Entry Price',
      render: (row: Record<string, unknown>) => `$${Number(row.entry_price).toFixed(2)}`,
    },
    { 
      key: 'current_price', 
      label: 'Current Price',
      render: (row: Record<string, unknown>) => `$${Number(row.current_price).toFixed(2)}`,
    },
    { 
      key: 'pnl_percent', 
      label: 'P&L %',
      render: (row: Record<string, unknown>) => {
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
      label: 'Unrealized P&L',
      render: (row: Record<string, unknown>) => {
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
      label: 'Actions',
      render: (row: Record<string, unknown>) => (
        <Button
          size="small"
          color="error"
          variant="outlined"
          onClick={() => handleClosePosition(row.symbol as string)}
        >
          Close
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
        Positions
      </Typography>

      {positions.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography color="textSecondary">
            No open positions
          </Typography>
        </Paper>
      ) : (
        <Table columns={columns} data={positions} />
      )}
    </Box>
  )
}

export default Positions
