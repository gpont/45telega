# 🚀 Telegram MCP Server Setup Guide for Windows + WSL + Kiro IDE

**Полная инструкция по подключению 45telega MCP сервера к Kiro IDE на Windows через WSL**

---

## 📋 Обзор

Данная инструкция описывает **проверенный рабочий способ** подключения Telegram MCP сервера к Kiro IDE на Windows с использованием WSL. Основана на реальном опыте решения проблем и успешной интеграции.

### ✅ Что будет работать после настройки:
- Полный доступ к Telegram API через MCP
- 45+ инструментов для работы с Telegram
- Отправка/получение сообщений
- Управление чатами и каналами
- Поиск по сообщениям
- Загрузка медиа файлов

---

## 🔧 Системные требования

### Обязательные компоненты:
- **Windows 11** с WSL2
- **Kiro IDE** (последняя версия)
- **Ubuntu** в WSL (рекомендуется)
- **Python 3.8+** в WSL
- **Telegram API credentials** (API ID, API Hash)

### Проверка готовности системы:
```bash
# Проверка WSL
wsl --version

# Проверка Python в WSL
wsl python3 --version

# Проверка доступности pip
wsl python3 -m pip --version
```

---

## 📦 Установка 45telega в WSL

### Шаг 1: Установка через uv (рекомендуется)
```bash
# В WSL терминале
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc

# Установка 45telega
uv tool install 45telega
```

### Шаг 2: Проверка установки
```bash
# Проверяем, что 45telega установлен
~/.local/bin/45telega --help

# Проверяем путь установки
which 45telega
ls -la ~/.local/bin/45telega
```

---

## 🔑 Настройка Telegram API

### Получение API credentials:
1. Перейдите на https://my.telegram.org/apps
2. Войдите в свой аккаунт Telegram
3. Создайте новое приложение
4. Сохраните **API ID** и **API Hash**

### Авторизация в Telegram:
```bash
# В WSL терминале
~/.local/bin/45telega sign-in \
  --api-id YOUR_API_ID \
  --api-hash YOUR_API_HASH \
  --phone-number +7XXXXXXXXXX
```

**Альтернативно - QR авторизация:**
```bash
~/.local/bin/45telega qr-login \
  --api-id YOUR_API_ID \
  --api-hash YOUR_API_HASH
```

### Проверка сессии:
```bash
# Проверяем, что сессия создана
ls -la ~/.local/state/mcp-telegram/
file ~/.local/state/mcp-telegram/mcp_telegram_session.session
```

---

## ⚙️ Настройка MCP в Kiro IDE

### Создание wrapper скрипта

**Создайте файл `telegram_mcp_wrapper.py` в корне проекта:**

```python
#!/usr/bin/env python3
"""
Telegram MCP Server Wrapper for Windows + WSL + Kiro IDE
"""
import sys
import os

# Add the mcp_telegram module to Python path
sys.path.insert(0, '/mnt/c/Users/YOUR_USERNAME/.kiro/45telega/45telega/src')

# Set environment variables
os.environ.setdefault('TELEGRAM_API_ID', 'YOUR_API_ID')
os.environ.setdefault('TELEGRAM_API_HASH', 'YOUR_API_HASH')
os.environ.setdefault('TELEGRAM_PHONE', '+7XXXXXXXXXX')

if __name__ == "__main__":
    from mcp_telegram.server import run_mcp_server
    import asyncio
    asyncio.run(run_mcp_server())
```

### Конфигурация MCP

**Добавьте в `.kiro/settings/mcp.json`:**

```json
{
  "mcpServers": {
    "telegram": {
      "command": "wsl",
      "args": [
        "/mnt/c/Users/YOUR_USERNAME/.kiro/telegram_env/bin/python", 
        "/mnt/c/Users/YOUR_USERNAME/.kiro/telegram_mcp_wrapper.py"
      ],
      "env": {
        "TELEGRAM_API_ID": "YOUR_API_ID",
        "TELEGRAM_API_HASH": "YOUR_API_HASH",
        "TELEGRAM_PHONE": "+7XXXXXXXXXX",
        "FASTMCP_LOG_LEVEL": "ERROR",
        "PYTHONPATH": "/mnt/c/Users/YOUR_USERNAME/.kiro/45telega/45telega/src"
      },
      "timeout": 120000,
      "disabled": false,
      "autoApprove": [
        "GetMe",
        "GetChats",
        "SendMessage",
        "GetChatInfo",
        "GetChatMembers",
        "SendFile",
        "SearchMessages"
      ]
    }
  }
}
```

---

## 🔄 Активация и тестирование

### Перезапуск MCP сервера:
1. В Kiro IDE найдите панель MCP серверов
2. Переподключите сервер "telegram"
3. Или перезапустите Kiro IDE полностью

### Тестирование подключения:
```javascript
// В Kiro IDE
mcp_telegram_GetMe()
// Должно вернуть информацию о вашем аккаунте

mcp_telegram_GetChats({limit: 5})
// Должно показать список ваших чатов
```

---

## 🚨 Решение проблем

### Проблема: "Connection closed" (MCP error -32000)

**Причины и решения:**

1. **Неправильный путь к Python:**
   ```json
   // ❌ Неправильно
   "command": "python"
   
   // ✅ Правильно  
   "command": "wsl",
   "args": ["/mnt/c/Users/USERNAME/.kiro/telegram_env/bin/python", "..."]
   ```

2. **Отсутствие wrapper файла:**
   - Убедитесь, что `telegram_mcp_wrapper.py` существует
   - Проверьте права доступа к файлу

3. **Неправильные пути в PYTHONPATH:**
   ```bash
   # Проверьте структуру проекта
   ls -la /mnt/c/Users/USERNAME/.kiro/45telega/45telega/src/mcp_telegram/
   ```

### Проблема: "Module not found"

**Решение:**
```bash
# Проверьте виртуальное окружение
source /mnt/c/Users/USERNAME/.kiro/telegram_env/bin/activate
python -c "import mcp_telegram; print('OK')"

# Если модуль не найден, переустановите
cd /mnt/c/Users/USERNAME/.kiro/45telega
pip install -e .
```

### Проблема: "Session not found"

**Решение:**
```bash
# Проверьте сессию
ls -la ~/.local/state/mcp-telegram/

# Если сессии нет, создайте заново
~/.local/bin/45telega sign-in --api-id YOUR_ID --api-hash YOUR_HASH --phone +7XXX
```

---

## 📊 Диагностические команды

### Полная диагностика системы:
```bash
# Проверка WSL
wsl --version
wsl --list --verbose

# Проверка 45telega
wsl ~/.local/bin/45telega --help
wsl ls -la ~/.local/bin/45telega

# Проверка сессии
wsl ls -la ~/.local/state/mcp-telegram/

# Проверка Python окружения
wsl /mnt/c/Users/USERNAME/.kiro/telegram_env/bin/python --version

# Тест импорта модуля
wsl /mnt/c/Users/USERNAME/.kiro/telegram_env/bin/python -c "
import sys
sys.path.insert(0, '/mnt/c/Users/USERNAME/.kiro/45telega/45telega/src')
import mcp_telegram
print('✅ Module import successful')
"
```

---

## 🎯 Альтернативные конфигурации

### Вариант 1: Inline Python код
```json
{
  "command": "wsl",
  "args": [
    "/mnt/c/Users/USERNAME/.kiro/telegram_env/bin/python", 
    "-c", 
    "import sys; sys.path.insert(0, '/mnt/c/Users/USERNAME/.kiro/45telega/45telega/src'); from mcp_telegram import app; app(['run'])"
  ]
}
```

### Вариант 2: Bash wrapper
```json
{
  "command": "wsl",
  "args": [
    "bash", 
    "-c", 
    "cd ~/.local/share/45telega && ~/.local/bin/45telega run"
  ]
}
```

### Вариант 3: Прямой вызов (если установлен глобально)
```json
{
  "command": "wsl",
  "args": ["~/.local/bin/45telega", "run"]
}
```

---

## 🔐 Безопасность

### Рекомендации:
1. **Не коммитьте API credentials в Git:**
   ```bash
   echo ".kiro/settings/mcp.json" >> .gitignore
   ```

2. **Используйте переменные окружения:**
   ```bash
   # В ~/.bashrc или ~/.profile
   export TELEGRAM_API_ID="your_id"
   export TELEGRAM_API_HASH="your_hash"
   ```

3. **Ограничьте autoApprove список:**
   - Включайте только безопасные операции чтения
   - Исключайте операции отправки/удаления

---

## ✅ Проверочный чек-лист

### Перед началом:
- [ ] WSL2 установлен и работает
- [ ] Ubuntu дистрибутив настроен
- [ ] Python 3.8+ доступен в WSL
- [ ] Kiro IDE установлен

### После установки 45telega:
- [ ] `~/.local/bin/45telega --help` работает
- [ ] Telegram API credentials получены
- [ ] Авторизация в Telegram выполнена
- [ ] Файл сессии создан и не пустой

### После настройки MCP:
- [ ] `telegram_mcp_wrapper.py` создан
- [ ] `.kiro/settings/mcp.json` обновлен
- [ ] Пути в конфигурации корректны
- [ ] MCP сервер переподключен в Kiro

### Финальная проверка:
- [ ] `mcp_telegram_GetMe()` возвращает данные пользователя
- [ ] `mcp_telegram_GetChats()` показывает список чатов
- [ ] Отправка тестового сообщения работает

---

## 🆘 Получение помощи

### Если ничего не работает:

1. **Запустите диагностику:**
   ```bash
   # Создайте и запустите диагностический скрипт
   python mcp_telegram_diagnostic.py
   ```

2. **Проверьте логи Kiro IDE:**
   - Найдите панель MCP серверов
   - Посмотрите сообщения об ошибках

3. **Создайте минимальный тест:**
   ```bash
   # Тест wrapper скрипта
   wsl /mnt/c/Users/USERNAME/.kiro/telegram_env/bin/python telegram_mcp_wrapper.py --help
   ```

### Полезные ресурсы:
- [45telega GitHub](https://github.com/sergekostenchuk/45telega)
- [Kiro MCP Documentation](https://docs.kiro.ai/mcp)
- [Telegram API Documentation](https://core.telegram.org/api)

---

## 📝 История изменений

**v1.0 (14 августа 2025)**
- Первая версия инструкции
- Основана на реальном опыте решения проблем
- Протестирована на Windows 11 + WSL2 + Kiro IDE

**Автор:** Kiro AI Assistant  
**Статус:** Проверено и работает ✅