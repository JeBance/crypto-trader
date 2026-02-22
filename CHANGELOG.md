# 📝 Changelog

All notable changes to Crypto Trader will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-02-22

### 🎉 Added

#### Core Features
- **Self-Healing Server** with auto-recovery and auto-update
- **Web UI** (React SPA) with realtime updates
- **REST API** with 15+ endpoints
- **WebSocket** support for realtime data
- **Plugin System** for exchanges, strategies, notifiers

#### Exchanges
- **Binance** plugin (REST API v3, testnet/prod)
- **Bybit** plugin (V5 API, testnet/prod)

#### Strategies
- **RSI Strategy** - Overbought/Oversold signals
- **Crossover Strategy** - SMA/EMA Golden/Death Cross
- **MACD Strategy** - Bullish/Bearish crossovers

#### Indicators
- **SMA** - Simple Moving Average
- **EMA** - Exponential Moving Average
- **RSI** - Relative Strength Index
- **MACD** - Moving Average Convergence Divergence

#### Services
- **OrderManager** - Order creation, cancellation, sync
- **PositionManager** - Position tracking, PnL calculation
- **DataService** - Market data with LRU cache
- **StrategyExecutor** - Strategy lifecycle management
- **RiskManager** - Position sizing, SL/TP, risk checks
- **BacktestEngine** - Historical strategy testing

#### Notifications
- **Telegram Bot** - Trade notifications, signals

#### Infrastructure
- **Auto-Installer** (setup.sh) for Termux/Linux/macOS
- **Self-Healing** server with auto-restart
- **Auto-Update** from Git repository
- **Health Monitoring** for all components

### 🔧 Changed
- Default configuration works without .env file
- Improved logging with emoji indicators
- Enhanced error messages and troubleshooting

### 📖 Documentation
- Complete API documentation (Swagger/ReDoc)
- User Guide for UI interaction
- Installation Guide for all platforms
- Strategies documentation
- Self-Healing Server guide

### 🧪 Testing
- Unit tests for indicators (16 tests)
- Unit tests for RiskManager (25+ tests)
- Integration tests for strategies
- CI/CD pipeline with GitHub Actions

---

## [0.2.0] - 2026-02-22

### Added
- Self-Healing Server implementation
- Auto-update functionality
- Bash scripts for easy management

---

## [0.1.0] - 2026-02-22

### Added
- Initial project structure
- Basic plugin system
- FastAPI backend
- React frontend

---

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.0.0 | 2026-02-22 | Production Release |
| 0.2.0 | 2026-02-22 | Self-Healing Server |
| 0.1.0 | 2026-02-22 | Initial Release |

---

## Upcoming Features

### v1.1.0 (Planned)
- [ ] More exchanges (OKX, Kraken)
- [ ] Additional strategies (Bollinger Bands, Stochastic)
- [ ] Mobile app (React Native)
- [ ] Advanced backtesting with optimization

### v1.2.0 (Planned)
- [ ] Multi-strategy portfolio
- [ ] Machine learning predictions
- [ ] Cloud sync for settings
- [ ] Advanced risk management

---

*Last updated: 22 февраля 2026*
