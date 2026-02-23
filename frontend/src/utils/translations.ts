/** Translations for UI */ 

export const translations = {
  // Навигация
  nav: {
    dashboard: 'Дашборд',
    positions: 'Позиции',
    orders: 'Ордера',
    strategies: 'Стратегии',
    settings: 'Настройки',
  },

  // Дашборд
  dashboard: {
    title: 'Дашборд',
    totalBalance: 'Общий баланс',
    todayPnL: 'P&L за сегодня',
    activePositions: 'Активные позиции',
    activeStrategies: 'Активные стратегии',
    systemStatus: 'Статус системы',
    quickActions: 'Быстрые действия',
    environment: 'Окружение',
    tradingMode: 'Режим торговли',
    version: 'Версия',
    noData: 'Нет данных',
    useNavigation: 'Используйте меню навигации для доступа к:',
    positionsDesc: 'Просмотр и управление открытыми позициями',
    ordersDesc: 'История ордеров',
    strategiesDesc: 'Настройка торговых стратегий',
    settingsDesc: 'Настройки приложения',
  },

  // Позиции
  positions: {
    title: 'Позиции',
    noPositions: 'Нет открытых позиций',
    symbol: 'Символ',
    side: 'Сторона',
    quantity: 'Количество',
    entryPrice: 'Цена входа',
    currentPrice: 'Текущая цена',
    unrealizedPnL: 'Нереализованный P&L',
    close: 'Закрыть',
    long: 'Лонг',
    short: 'Шорт',
    loading: 'Загрузка...',
  },

  // Ордера
  orders: {
    title: 'Ордера',
    noOrders: 'Нет ордеров',
    id: 'ID',
    symbol: 'Символ',
    side: 'Сторона',
    type: 'Тип',
    quantity: 'Количество',
    price: 'Цена',
    status: 'Статус',
    createdAt: 'Создан',
    market: 'Рыночный',
    limit: 'Лимитный',
    buy: 'Покупка',
    sell: 'Продажа',
    pending: 'Ожидает',
    filled: 'Исполнен',
    cancelled: 'Отменен',
    rejected: 'Отклонен',
    loading: 'Загрузка...',
  },

  // Стратегии
  strategies: {
    title: 'Стратегии',
    noStrategies: 'Нет стратегий',
    name: 'Название',
    status: 'Статус',
    parameters: 'Параметры',
    activate: 'Активировать',
    deactivate: 'Деактивировать',
    active: 'Активна',
    inactive: 'Неактивна',
    loading: 'Загрузка...',
    rsi: 'RSI Стратегия',
    crossover: 'Crossover Стратегия',
    macd: 'MACD Стратегия',
    period: 'Период',
    oversold: 'Перепроданность',
    overbought: 'Перекупленность',
    fast: 'Быстрый',
    slow: 'Медленный',
    signal: 'Сигнал',
  },

  // Настройки
  settings: {
    title: 'Настройки',
    exchangeSettings: 'Настройки бирж',
    binance: 'Binance',
    bybit: 'Bybit',
    apiKey: 'API Ключ',
    apiSecret: 'API Секрет',
    testnet: 'Testnet',
    save: 'Сохранить',
    saved: 'Сохранено',
    tradingSettings: 'Настройки торговли',
    maxPositionSize: 'Макс. размер позиции (%)',
    stopLoss: 'Stop Loss (%)',
    takeProfit: 'Take Profit (%)',
    dailyLossLimit: 'Дневной лимит убытка (%)',
    notificationSettings: 'Настройки уведомлений',
    telegramBotToken: 'Telegram Bot Token',
    telegramChatId: 'Telegram Chat ID',
    configured: 'Настроено',
    notConfigured: 'Не настроено',
  },

  // Общие
  common: {
    loading: 'Загрузка...',
    error: 'Ошибка',
    success: 'Успешно',
    cancel: 'Отмена',
    confirm: 'Подтвердить',
    delete: 'Удалить',
    edit: 'Редактировать',
    close: 'Закрыть',
    cryptoTrader: '📱 Crypto Trader',
  },
}

export type TranslationKey = keyof typeof translations
