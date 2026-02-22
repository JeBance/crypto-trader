/** Orders Page */

import React, { useEffect, useState } from 'react'
import { Box, Typography, CircularProgress, TextField, MenuItem, Button } from '@mui/material'
import { api, Order } from '../services/api'
import { Table, StatusBadge, Paper } from '../components/ui'

const Orders: React.FC = () => {
  const [loading, setLoading] = useState(true)
  const [orders, setOrders] = useState<Order[]>([])
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [symbolFilter, setSymbolFilter] = useState<string>('')

  useEffect(() => {
    loadOrders()
  }, [statusFilter, symbolFilter])

  const loadOrders = async () => {
    try {
      setLoading(true)
      const params: { status?: string; symbol?: string } = {}
      if (statusFilter !== 'all') params.status = statusFilter
      if (symbolFilter) params.symbol = symbolFilter
      
      const data = await api.getOrders(params)
      setOrders(data.orders)
    } catch (error) {
      console.error('Failed to load orders:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCancelOrder = async (orderId: string) => {
    if (!confirm(`Cancel order ${orderId}?`)) return

    try {
      await api.cancelOrder(orderId)
      loadOrders()
    } catch (error) {
      console.error('Failed to cancel order:', error)
      alert('Failed to cancel order')
    }
  }

  const columns = [
    { 
      key: 'symbol', 
      label: 'Symbol',
    },
    { 
      key: 'side', 
      label: 'Side',
      render: (row: Record<string, unknown>) => (
        <StatusBadge status={row.side as string} />
      ),
    },
    { 
      key: 'type', 
      label: 'Type',
      render: (row: Record<string, unknown>) => (
        <Typography component="span" textTransform="capitalize">
          {row.type as string}
        </Typography>
      ),
    },
    { 
      key: 'quantity', 
      label: 'Quantity',
      render: (row: Record<string, unknown>) => Number(row.quantity).toFixed(6),
    },
    { 
      key: 'price', 
      label: 'Price',
      render: (row: Record<string, unknown>) => {
        const price = row.price as number | null
        return price ? `$${price.toFixed(2)}` : 'Market'
      },
    },
    { 
      key: 'average_price', 
      label: 'Avg Price',
      render: (row: Record<string, unknown>) => {
        const price = Number(row.average_price)
        return price > 0 ? `$${price.toFixed(2)}` : '-'
      },
    },
    { 
      key: 'filled_quantity', 
      label: 'Filled',
      render: (row: Record<string, unknown>) => {
        const filled = Number(row.filled_quantity)
        const qty = Number(row.quantity)
        const pct = qty > 0 ? ((filled / qty) * 100).toFixed(0) : 0
        return `${filled.toFixed(6)} (${pct}%)`
      },
    },
    { 
      key: 'status', 
      label: 'Status',
      render: (row: Record<string, unknown>) => (
        <StatusBadge status={row.status as string} />
      ),
    },
    { 
      key: 'strategy_name', 
      label: 'Strategy',
      render: (row: Record<string, unknown>) => (
        <Typography component="span" variant="body2" color="textSecondary">
          {row.strategy_name as string || '-'}
        </Typography>
      ),
    },
    {
      key: 'actions',
      label: 'Actions',
      render: (row: Record<string, unknown>) => {
        const status = row.status as string
        const canCancel = ['open', 'pending'].includes(status.toLowerCase())
        
        return canCancel ? (
          <Button
            size="small"
            color="error"
            variant="outlined"
            onClick={() => handleCancelOrder(row.exchange_order_id as string)}
          >
            Cancel
          </Button>
        ) : (
          <Typography variant="body2" color="textSecondary">-</Typography>
        )
      },
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
        Orders
      </Typography>

      {/* Filters */}
      <Box display="flex" gap={2} mb={3}>
        <TextField
          select
          label="Status"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          size="small"
          sx={{ minWidth: 150 }}
        >
          <MenuItem value="all">All</MenuItem>
          <MenuItem value="open">Open</MenuItem>
          <MenuItem value="filled">Filled</MenuItem>
          <MenuItem value="cancelled">Cancelled</MenuItem>
          <MenuItem value="pending">Pending</MenuItem>
        </TextField>

        <TextField
          label="Symbol"
          value={symbolFilter}
          onChange={(e) => setSymbolFilter(e.target.value)}
          placeholder="BTCUSDT"
          size="small"
          sx={{ minWidth: 150 }}
        />

        <Button variant="contained" onClick={loadOrders}>
          Refresh
        </Button>
      </Box>

      {orders.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography color="textSecondary">
            No orders found
          </Typography>
        </Paper>
      ) : (
        <Table columns={columns} data={orders} />
      )}
    </Box>
  )
}

export default Orders
