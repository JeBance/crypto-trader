/**
 * Data Collection Page - Management of market data collection
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Card,
  CardContent,
  Button,
  TextField,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  CircularProgress,
  IconButton,
  Tooltip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
} from '@mui/material';
import {
  Add as AddIcon,
  Refresh as RefreshIcon,
  Pause as PauseIcon,
  PlayArrow as PlayArrowIcon,
  Delete as DeleteIcon,
  Info as InfoIcon,
  Edit as EditIcon,
} from '@mui/icons-material';

// API types
interface MonitoredPair {
  id: number;
  exchange: string;
  symbol: string;
  timeframes: string[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_data_at: string | null;
}

interface CollectionStats {
  exchange: string;
  total_monitored_pairs: number;
  active_pairs: number;
  total_candles: number;
  date_range_from: string | null;
  date_range_to: string | null;
  last_collection: string | null;
}

interface CollectionLog {
  id: number;
  exchange: string;
  symbol: string;
  timeframe: string | null;
  data_type: string;
  status: string;
  records_collected: number;
  error_message: string | null;
  collected_at: string;
}

const DataCollectionPage: React.FC = () => {
  // State
  const [monitoredPairs, setMonitoredPairs] = useState<MonitoredPair[]>([]);
  const [stats, setStats] = useState<CollectionStats | null>(null);
  const [logs, setLogs] = useState<CollectionLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Dialog state
  const [openDialog, setOpenDialog] = useState(false);
  const [editingPair, setEditingPair] = useState<MonitoredPair | null>(null);
  const [newSymbol, setNewSymbol] = useState('');
  const [newExchange, setNewExchange] = useState('binance');
  const [newTimeframes, setNewTimeframes] = useState<string[]>(['1h', '4h', '1d']);

  // Timeframe options
  const timeframeOptions = ['1m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '12h', '1d', '1w'];

  // Exchange options
  const exchangeOptions = [
    { value: 'binance', label: 'Binance' },
    { value: 'bybit', label: 'Bybit' },
  ];

  // Fetch data
  const fetchData = async () => {
    try {
      setLoading(true);

      // Fetch monitored pairs
      const pairsResponse = await fetch('/api/market-data/monitored-pairs');
      if (pairsResponse.ok) {
        const pairsData = await pairsResponse.json();
        setMonitoredPairs(pairsData);
      }

      // Fetch stats
      const statsResponse = await fetch('/api/market-data/stats');
      if (statsResponse.ok) {
        const statsData = await statsResponse.json();
        setStats(statsData);
      }

      // Fetch logs
      const logsResponse = await fetch('/api/market-data/logs?limit=20');
      if (logsResponse.ok) {
        const logsData = await logsResponse.json();
        setLogs(logsData);
      }

      setError(null);
    } catch (err) {
      setError('Failed to fetch data collection information');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  // Open dialog for adding pair
  const handleOpenAddDialog = () => {
    setEditingPair(null);
    setNewSymbol('');
    setNewExchange('binance');
    setNewTimeframes(['1h', '4h', '1d']);
    setOpenDialog(true);
  };

  // Open dialog for editing pair
  const handleOpenEditDialog = (pair: MonitoredPair) => {
    setEditingPair(pair);
    setNewSymbol(pair.symbol);
    setNewExchange(pair.exchange);
    setNewTimeframes(pair.timeframes);
    setOpenDialog(true);
  };

  // Add/Edit monitored pair
  const handleSavePair = async () => {
    if (!newSymbol.trim()) {
      return;
    }

    try {
      const url = editingPair
        ? `/api/market-data/monitored-pairs/${editingPair.symbol}`
        : '/api/market-data/monitored-pairs';
      
      const method = editingPair ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method: method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          symbol: newSymbol.toUpperCase(),
          exchange: newExchange,
          timeframes: newTimeframes,
          is_active: true,
        }),
      });

      if (response.ok) {
        setNewSymbol('');
        setOpenDialog(false);
        setEditingPair(null);
        fetchData();
      } else {
        const errorData = await response.json();
        setError(`Failed to save pair: ${errorData.detail || 'Unknown error'}`);
      }
    } catch (err) {
      setError('Failed to save pair');
      console.error(err);
    }
  };

  // Delete monitored pair (hard delete)
  const handleDeletePair = async (symbol: string, exchange: string) => {
    if (!confirm(`Delete ${exchange}:${symbol} completely? Historical data will be DELETED!`)) {
      return;
    }

    try {
      const response = await fetch(`/api/market-data/monitored-pairs/${exchange}/${symbol}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        fetchData();
      } else {
        setError('Failed to delete pair');
      }
    } catch (err) {
      setError('Failed to delete pair');
      console.error(err);
    }
  };

  // Remove monitored pair (soft delete - pause monitoring)
  const handleRemovePair = async (symbol: string, exchange: string) => {
    if (!confirm(`Stop monitoring ${exchange}:${symbol}? Historical data will be preserved.`)) {
      return;
    }

    try {
      const response = await fetch(`/api/market-data/monitored-pairs/${exchange}/${symbol}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        fetchData();
      } else {
        setError('Failed to remove pair');
      }
    } catch (err) {
      setError('Failed to remove pair');
      console.error(err);
    }
  };

  // Resume monitoring
  const handleResumePair = async (symbol: string) => {
    try {
      const response = await fetch(`/api/market-data/monitored-pairs/${symbol}/resume`, {
        method: 'POST',
      });

      if (response.ok) {
        fetchData();
      } else {
        setError('Failed to resume monitoring');
      }
    } catch (err) {
      setError('Failed to resume monitoring');
      console.error(err);
    }
  };

  // Toggle timeframe selection
  const toggleTimeframe = (tf: string) => {
    setNewTimeframes(prev =>
      prev.includes(tf)
        ? prev.filter(t => t !== tf)
        : [...prev, tf]
    );
  };

  // Format date
  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };

  if (loading && !monitoredPairs.length) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" gutterBottom>
            📊 Data Collection
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage market data collection and monitoring
          </Typography>
        </Box>
        <Box display="flex" gap={2}>
          <Tooltip title="Refresh data">
            <IconButton onClick={fetchData} color="primary">
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleOpenAddDialog}
          >
            Add Pair
          </Button>
        </Box>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Statistics Cards */}
      {stats && (
        <Grid container spacing={3} mb={4}>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Monitored Pairs
                </Typography>
                <Typography variant="h4">
                  {stats.total_monitored_pairs}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {stats.active_pairs} active
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Total Candles
                </Typography>
                <Typography variant="h4">
                  {stats.total_candles.toLocaleString()}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Stored in database
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Date Range
                </Typography>
                <Typography variant="body2">
                  From: {formatDate(stats.date_range_from)}
                </Typography>
                <Typography variant="body2">
                  To: {formatDate(stats.date_range_to)}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Last Collection
                </Typography>
                <Typography variant="body2">
                  {formatDate(stats.last_collection)}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Monitored Pairs Table */}
      <Typography variant="h6" gutterBottom mb={2}>
        Monitored Pairs
      </Typography>
      <TableContainer component={Paper} sx={{ mb: 4 }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Exchange</TableCell>
              <TableCell>Symbol</TableCell>
              <TableCell>Timeframes</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Last Data</TableCell>
              <TableCell>Created</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {monitoredPairs.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} align="center">
                  <Typography color="text.secondary" py={3}>
                    No monitored pairs yet. Click "Add Pair" to start collecting data.
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              monitoredPairs.map((pair) => (
                <TableRow key={pair.id}>
                  <TableCell>
                    <Chip 
                      label={pair.exchange} 
                      size="small" 
                      color={pair.exchange === 'binance' ? 'warning' : 'default'}
                    />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" fontWeight="bold">
                      {pair.symbol}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Box display="flex" gap={0.5} flexWrap="wrap">
                      {pair.timeframes.map((tf) => (
                        <Chip key={tf} label={tf} size="small" variant="outlined" />
                      ))}
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={pair.is_active ? 'Active' : 'Paused'}
                      color={pair.is_active ? 'success' : 'default'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>{formatDate(pair.last_data_at)}</TableCell>
                  <TableCell>{formatDate(pair.created_at)}</TableCell>
                  <TableCell>
                    <Box display="flex" gap={0.5}>
                      <Tooltip title="Edit pair">
                        <IconButton
                          size="small"
                          color="primary"
                          onClick={() => handleOpenEditDialog(pair)}
                        >
                          <EditIcon />
                        </IconButton>
                      </Tooltip>
                      {pair.is_active ? (
                        <Tooltip title="Stop monitoring (data preserved)">
                          <IconButton
                            size="small"
                            color="warning"
                            onClick={() => handleRemovePair(pair.symbol, pair.exchange)}
                          >
                            <PauseIcon />
                          </IconButton>
                        </Tooltip>
                      ) : (
                        <Tooltip title="Resume monitoring">
                          <IconButton
                            size="small"
                            color="success"
                            onClick={() => handleResumePair(pair.symbol, pair.exchange)}
                          >
                            <PlayArrowIcon />
                          </IconButton>
                        </Tooltip>
                      )}
                      <Tooltip title="Delete completely (data will be deleted!)">
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => handleDeletePair(pair.symbol, pair.exchange)}
                        >
                          <DeleteIcon />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Recent Collection Logs */}
      <Typography variant="h6" gutterBottom mb={2}>
        Recent Collection Logs
      </Typography>
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Time</TableCell>
              <TableCell>Symbol</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Records</TableCell>
              <TableCell>Error</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {logs.slice(0, 10).map((log) => (
              <TableRow key={log.id}>
                <TableCell>{formatDate(log.collected_at)}</TableCell>
                <TableCell>{log.symbol}</TableCell>
                <TableCell>
                  <Chip label={log.data_type} size="small" />
                </TableCell>
                <TableCell>
                  <Chip
                    label={log.status}
                    color={log.status === 'success' ? 'success' : 'error'}
                    size="small"
                  />
                </TableCell>
                <TableCell>{log.records_collected}</TableCell>
                <TableCell>
                  {log.error_message && (
                    <Tooltip title={log.error_message}>
                      <InfoIcon color="error" fontSize="small" />
                    </Tooltip>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Add/Edit Pair Dialog */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingPair ? `Edit ${editingPair.exchange}:${editingPair.symbol}` : 'Add Monitored Pair'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            {/* Exchange Selection */}
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Exchange</InputLabel>
              <Select
                value={newExchange}
                label="Exchange"
                onChange={(e: SelectChangeEvent) => setNewExchange(e.target.value)}
              >
                {exchangeOptions.map((ex) => (
                  <MenuItem key={ex.value} value={ex.value}>
                    {ex.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {/* Symbol */}
            <TextField
              fullWidth
              label="Symbol"
              placeholder="BTCUSDT"
              value={newSymbol}
              onChange={(e) => setNewSymbol(e.target.value.toUpperCase())}
              sx={{ mb: 2 }}
            />

            {/* Timeframes */}
            <Typography variant="subtitle2" gutterBottom>
              Timeframes
            </Typography>
            <Box display="flex" flexWrap="wrap" gap={1} sx={{ mb: 2 }}>
              {timeframeOptions.map((tf) => (
                <Chip
                  key={tf}
                  label={tf}
                  onClick={() => {
                    setNewTimeframes(prev =>
                      prev.includes(tf)
                        ? prev.filter(t => t !== tf)
                        : [...prev, tf]
                    );
                  }}
                  color={newTimeframes.includes(tf) ? 'primary' : 'default'}
                  variant={newTimeframes.includes(tf) ? 'filled' : 'outlined'}
                />
              ))}
            </Box>

            <Alert severity="info" sx={{ mt: 2 }}>
              <Typography variant="caption">
                {editingPair 
                  ? 'Changes will be saved. Historical data will be preserved.'
                  : 'Data will be collected continuously and stored permanently. You can stop monitoring at any time.'}
              </Typography>
            </Alert>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
          {editingPair && (
            <Button 
              onClick={() => {
                handleDeletePair(editingPair.symbol, editingPair.exchange);
                setOpenDialog(false);
              }} 
              color="error"
              variant="outlined"
            >
              Delete
            </Button>
          )}
          <Button 
            onClick={handleSavePair} 
            variant="contained" 
            disabled={!newSymbol.trim() || newTimeframes.length === 0}
          >
            {editingPair ? 'Save Changes' : 'Add Pair'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default DataCollectionPage;
