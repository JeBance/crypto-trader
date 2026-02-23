/** Orders Page */

import React, { useEffect, useState } from 'react'
import { Box, Typography, CircularProgress, TextField, MenuItem, Button } from '@mui/material'
import { api, Order } from '../services/api'
import { Table, StatusBadge, Paper } from '../components/ui'
import { translations } from '../utils/translations'

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
    if (!confirm(`Отменить ордер ${orderId}?`)) return

    try {
      await api.cancelOrder(orderId)
      loadOrders()
    } catch (error) {
      console.error('Failed to cancel order:', error)
      alert('Не удалось отменить ордер')
    }
  }

  const columns = [
    {
      key: 'symbol',
      label: translations.orders.symbol,
    },
    {
      key: 'side',
      label: translations.orders.side,
      render: (row: Order) => (
        <StatusBadge status={row.side} />
      ),
    },
    {
      key: 'type',
      label: translations.orders.type,
      render: (row: Order) => (
        <Typography component="span" textTransform="capitalize">
          {row.type === 'market' ? translations.orders.market : row.type === 'limit' ? translations.orders.limit : row.type}
        </Typography>
      ),
    },
    {
      key: 'quantity',
      label: translations.orders.quantity,
      render: (row: Order) => Number(row.quantity).toFixed(6),
    },
    {
      key: 'price',
      label: translations.orders.price,
      render: (row: Order) => {
        const price = row.price
        return price ? `$${price.toFixed(2)}` : translations.orders.market
      },
    },
    {
      key: 'average_price',
      label: 'Ср. цена',
      render: (row: Order) => {
        const price = Number(row.average_price)
        return price > 0 ? `$${price.toFixed(2)}` : '-'
      },
    },
    {
      key: 'filled_quantity',
      label: 'Исполнено',
      render: (row: Order) => {
        const filled = Number(row.filled_quantity)
        const qty = Number(row.quantity)
        const pct = qty > 0 ? ((filled / qty) * 100).toFixed(0) : 0
        return `${filled.toFixed(6)} (${pct}%)`
      },
    },
    {
      key: 'status',
      label: translations.orders.status,
      render: (row: Order) => (
        <StatusBadge status={row.status} />
      ),
    },
    {
      key: 'strategy_name',
      label: 'Стратегия',
      render: (row: Order) => (
        <Typography component="span" variant="body2" color="textSecondary">
          {row.strategy_name || '-'}
        </Typography>
      ),
    },
    {
      key: 'actions',
      label: 'Действия',
      render: (row: Order) => {
        const status = row.status
        const canCancel = ['open', 'pending'].includes(status.toLowerCase())

        return canCancel ? (
          <Button
            size="small"
            color="error"
            variant="outlined"
            onClick={() => handleCancelOrder(row.exchange_order_id)}
          >
            {translations.common.cancel}
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
        {translations.orders.title}
      </Typography>

      {/* Filters */}
      <Box display="flex" gap={2} mb={3}>
        <TextField
          select
          label="Статус"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          size="small"
          sx={{ minWidth: 150 }}
        >
          <MenuItem value="all">Все</MenuItem>
          <MenuItem value="open">Открытые</MenuItem>
          <MenuItem value="filled">Исполненные</MenuItem>
          <MenuItem value="cancelled">Отмененные</MenuItem>
          <MenuItem value="pending">Ожидают</MenuItem>
        </TextField>

        <TextField
          label="Символ"
          value={symbolFilter}
          onChange={(e) => setSymbolFilter(e.target.value)}
          placeholder="BTCUSDT"
          size="small"
          sx={{ minWidth: 150 }}
        />

        <Button variant="contained" onClick={loadOrders}>
          Обновить
        </Button>
      </Box>

      {orders.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography color="textSecondary">
            {translations.orders.noOrders}
          </Typography>
        </Paper>
      ) : (
        <Table columns={columns} data={orders} />
      )}
    </Box>
  )
}

export default Orders
