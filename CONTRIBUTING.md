# 🤝 CONTRIBUTING.md — Руководство по внесению изменений

Гайд для разработчиков, участвующих в проекте Crypto Trader.

---

## 📋 Содержание

1. [Начало работы](#начало-работы)
2. [Ветвление](#ветвление)
3. [Коммиты](#коммиты)
4. [Pull Request](#pull-request)
5. [Code Review](#code-review)
6. [Тестирование](#тестирование)
7. [Документация](#документация)

---

## 🚀 Начало работы

### 1. Форк и клонирование

```bash
# Форкните репозиторий на GitHub
# Затем клонируйте свою копию
git clone https://github.com/YOUR_USERNAME/crypto-trader.git
cd crypto-trader

# Добавьте оригинальный репозиторий как upstream
git remote add upstream https://github.com/JeBance/crypto-trader.git

# Проверьте remote
git remote -v
# origin    https://github.com/YOUR_USERNAME/crypto-trader.git (fetch)
# origin    https://github.com/YOUR_USERNAME/crypto-trader.git (push)
# upstream  https://github.com/JeBance/crypto-trader.git (fetch)
# upstream  https://github.com/JeBance/crypto-trader.git (push)
```

### 2. Настройка окружения

```bash
# Backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r backend/requirements.txt

# Frontend
cd frontend
npm install
```

### 3. Синхронизация с upstream

```bash
# Перед началом работы синхронизируйтесь
git fetch upstream
git checkout main
git merge upstream/main

# Или используйте rebase
git pull --rebase upstream main
```

---

## 🌿 Ветвление

### Названия веток

Используйте формат: `<type>/<description>`

| Тип | Описание | Пример |
|-----|----------|--------|
| `feature/` | Новая функция | `feature/binance-exchange` |
| `fix/` | Исправление бага | `fix/rsi-calculation` |
| `docs/` | Документация | `docs/readme-update` |
| `refactor/` | Рефакторинг | `refactor/plugin-system` |
| `test/` | Тесты | `test/order-manager` |
| `chore/` | Обслуживание | `chore/update-deps` |

### Примеры

```bash
# Новая функция
git checkout -b feature/bybit-exchange

# Исправление бага
git checkout -b fix/websocket-reconnect

# Обновление документации
git checkout -b docs/strategy-guide
```

---

## ✍️ Коммиты

### Conventional Commits

Используйте формат [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Типы коммитов

| Тип | Описание |
|-----|----------|
| `feat` | Новая функция |
| `fix` | Исправление бага |
| `docs` | Документация |
| `style` | Форматирование, пробелы |
| `refactor` | Рефакторинг без изменений функциональности |
| `test` | Добавление тестов |
| `chore` | Обновление зависимостей, инструменты |
| `perf` | Улучшение производительности |
| `ci` | Изменения CI/CD |

### Примеры коммитов

```bash
# Хорошие коммиты
git commit -m "feat(exchange): добавить поддержку Bybit API"
git commit -m "fix(strategy): исправить расчёт RSI при нулевых значениях"
git commit -m "docs(readme): обновить инструкции установки"
git commit -m "refactor(core): упростить логику EventBus"
git commit -m "test(order): добавить unit-тесты для OrderManager"

# Плохие коммиты (не делайте так)
git commit -m "fix"
git commit -m "update"
git commit -m "changes"
git commit -m "wip"
```

### Атомарные коммиты

Делайте маленькие, логически завершённые коммиты:

```bash
# ✅ ХОРОШО: несколько атомарных коммитов
git add app/exchanges/binance.py
git commit -m "feat(exchange): добавить класс BinanceExchange"

git add app/exchanges/binance.py
git commit -m "feat(exchange): реализовать get_ticker для Binance"

git add app/exchanges/binance.py
git commit -m "feat(exchange): реализовать create_order для Binance"

# ❌ ПЛОХО: один большой коммит
git add .
git commit -m "добавил Binance"
```

---

## 📬 Pull Request

### Создание PR

1. **Запушьте ветку**
   ```bash
   git push origin feature/your-feature
   ```

2. **Создайте PR на GitHub**
   - Перейдите в репозиторий
   - Нажмите "Compare & pull request"
   - Выберите base: `main`, compare: вашу ветку

3. **Заполните описание PR**

### Шаблон Pull Request

```markdown
## Описание
Краткое описание изменений

## Тип изменений
- [ ] ✨ Новая функция
- [ ] 🐛 Исправление бага
- [ ] 📝 Документация
- [ ] ♻️ Рефакторинг
- [ ] ✅ Тесты
- [ ] ⚙️ Конфигурация/CI

## Связанные задачи
Fixes #123

## Чеклист
- [ ] Код следует стилю проекта
- [ ] Добавлены тесты
- [ ] Обновлена документация
- [ ] Запущены линтеры
- [ ] Протестировано локально

## Скриншоты (если применимо)
<!-- Скриншоты UI изменений -->

## Замечания
<!-- Особые замечания для ревьюеров -->
```

### Размер PR

- **Идеально:** 200-400 строк изменений
- **Максимум:** 1000 строк
- **Большие изменения:** Разбивайте на несколько PR

---

## 🔍 Code Review

### Для автора

1. **Ответьте на все комментарии**
2. **Внесите запрошенные изменения**
3. **Запушьте исправления** в ту же ветку
4. **Пометьте resolved** после исправления

### Для ревьюера

Чеклист ревью:

```
□ Код работает корректно
□ Нет дублирования (DRY)
□ Следует архитектуре проекта
□ Обработаны ошибки
□ Добавлены тесты
□ Обновлена документация
□ Нет security issues
□ Логи и мониторинг добавлены
```

### Тон коммуникации

```
✅ "Можно рассмотреть использование..."
✅ "Есть ли причина для...?"
✅ "Предлагаю изменить на..."

❌ "Это неправильно"
❌ "Зачем ты сделал так?"
❌ "Переделай"
```

---

## 🧪 Тестирование

### Backend тесты

```bash
# Запустить все тесты
pytest backend/tests/ -v

# Запустить с покрытием
pytest backend/tests/ -v --cov=app --cov-report=html

# Запустить конкретный тест
pytest backend/tests/test_rsi.py -v

# Запустить по метке
pytest backend/tests/ -v -m "slow"
```

### Frontend тесты

```bash
cd frontend

# Запустить тесты
npm test

# Запустить с покрытием
npm test -- --coverage

# Запустить в watch режиме
npm test -- --watch
```

### Минимальное покрытие

| Компонент | Мин. покрытие |
|-----------|---------------|
| Core модули | 90% |
| Стратегии | 95% |
| Индикаторы | 100% |
| API роуты | 80% |
| UI компоненты | 70% |

---

## 📚 Документация

### Обновление документации

При добавлении новой функции:

1. **Обновите README.md** (если меняется установка/использование)
2. **Добавьте в AGENT.md** (если меняется архитектура)
3. **Обновите ARCHITECTURE.md** (если меняется структура)
4. **Добавьте docstrings** в код

### Docstrings (Python)

```python
def calculate_rsi(prices: list[float], period: int = 14) -> float:
    """
    Рассчитывает индекс относительной силы (RSI).

    Args:
        prices: Список цен закрытия
        period: Период расчёта (по умолчанию 14)

    Returns:
        Значение RSI от 0 до 100

    Example:
        >>> prices = [44, 44.34, 44.09, 43.61, 44.33, 44.83]
        >>> calculate_rsi(prices, period=3)
        67.5
    """
    pass
```

### JSDoc (TypeScript)

```typescript
/**
 * Рассчитывает индекс относительной силы (RSI).
 *
 * @param prices - Список цен закрытия
 * @param period - Период расчёта (по умолчанию 14)
 * @returns Значение RSI от 0 до 100
 *
 * @example
 * ```ts
 * const prices = [44, 44.34, 44.09, 43.61, 44.33, 44.83];
 * const rsi = calculateRsi(prices, 3);
 * ```
 */
function calculateRsi(prices: number[], period: number = 14): number {
  // ...
}
```

---

## 🎯 Стиль кода

### Python

```bash
# Линтинг
ruff check backend/app/
black backend/app/ --check
mypy backend/app/

# Автоформатирование
black backend/app/
ruff check backend/app/ --fix
```

**Основные правила:**
- 4 пробела для отступов
- Максимум 88 символов в строке
- Type hints для всех функций
- Docstrings для публичных API

### TypeScript

```bash
cd frontend

# Линтинг
npm run lint

# Автоформатирование
npm run format
```

**Основные правила:**
- 2 пробела для отступов
- Строгий TypeScript (noImplicitAny)
- Интерфейсы для типов
- Functional компоненты + hooks

---

## 🔄 Процесс релиза

### Версионирование

Используется [Semantic Versioning](https://semver.org/):

```
MAJOR.MINOR.PATCH

2.1.0
│   │   └─ PATCH: исправление бага (обратно совместимо)
│   └───── MINOR: новая функция (обратно совместимо)
└───────── MAJOR: ломающее изменение
```

### Подготовка релиза

```bash
# 1. Обновите версию
# backend/pyproject.toml
# frontend/package.json

# 2. Обновите CHANGELOG.md
git log --oneline v1.0.0..HEAD

# 3. Создайте тег
git tag -a v1.1.0 -m "Release v1.1.0"

# 4. Запушьте тег
git push origin v1.1.0
```

---

## ❓ Вопросы?

- 📖 Прочитайте [AGENT.md](./AGENT.md) для общих принципов
- 🏗️ Смотрите [ARCHITECTURE.md](./ARCHITECTURE.md) для архитектуры
- 🗺️ Проверьте [ROADMAP.md](./ROADMAP.md) для плана разработки
- 💬 Откройте Issue на GitHub для обсуждения

---

*Последнее обновление: 22 февраля 2026*
