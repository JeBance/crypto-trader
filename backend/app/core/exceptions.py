"""Core exceptions for the application."""


class CryptoTraderException(Exception):
    """Base exception for all crypto trader errors."""
    
    def __init__(self, message: str, details: dict | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ConfigurationError(CryptoTraderException):
    """Configuration error."""
    pass


class PluginError(CryptoTraderException):
    """Plugin-related error."""
    pass


class PluginNotFoundError(PluginError):
    """Plugin not found error."""
    pass


class PluginLoadError(PluginError):
    """Plugin load error."""
    pass


class ExchangeError(CryptoTraderException):
    """Exchange-related error."""
    pass


class ExchangeConnectionError(ExchangeError):
    """Exchange connection error."""
    pass


class ExchangeAuthError(ExchangeError):
    """Exchange authentication error."""
    pass


class ExchangeOrderError(ExchangeError):
    """Exchange order error."""
    pass


class ExchangeRateLimitError(ExchangeError):
    """Exchange rate limit exceeded."""
    pass


class StrategyError(CryptoTraderException):
    """Strategy-related error."""
    pass


class StrategyExecutionError(StrategyError):
    """Strategy execution error."""
    pass


class OrderError(CryptoTraderException):
    """Order-related error."""
    pass


class OrderValidationError(OrderError):
    """Order validation error."""
    pass


class OrderExecutionError(OrderError):
    """Order execution error."""
    pass


class PositionError(CryptoTraderException):
    """Position-related error."""
    pass


class PositionNotFoundError(PositionError):
    """Position not found error."""
    pass


class RiskError(CryptoTraderException):
    """Risk management error."""
    pass


class RiskLimitExceededError(RiskError):
    """Risk limit exceeded error."""
    pass


class DatabaseError(CryptoTraderException):
    """Database-related error."""
    pass


class DataError(CryptoTraderException):
    """Data-related error."""
    pass


class DataNotFoundError(DataError):
    """Data not found error."""
    pass
