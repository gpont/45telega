# ruff: noqa: T201
from __future__ import annotations

from functools import cache
from getpass import getpass
from typing import Optional

from pydantic_settings import BaseSettings
from telethon import TelegramClient  # type: ignore[import-untyped]
from telethon.errors.rpcerrorlist import SessionPasswordNeededError  # type: ignore[import-untyped]
from telethon.tl.types import User  # type: ignore[import-untyped]
from xdg_base_dirs import xdg_state_home  # type: ignore[import-error]

from .qr_auth import QRAuthHandler


class TelegramSettings(BaseSettings):
    api_id: str
    api_hash: str
    
    # Rate Limiter настройки
    rate_limit_enabled: bool = True
    global_rate_limit: int = 30
    chat_rate_limit: int = 1
    group_rate_limit: int = 20
    resolve_daily_limit: int = 200

    class Config:
        env_prefix = "TELEGRAM_"
        env_file = ".env"
        extra = "ignore"  # Игнорируем ВСЕ переменные кроме TELEGRAM_*
        case_sensitive = False  # Разрешаем любой регистр для совместимости
        env_nested_delimiter = "__"  # Для вложенных настроек используем __


async def connect_to_telegram(
    api_id: str, 
    api_hash: str, 
    phone_number: Optional[str] = None,
    use_qr: bool = False
) -> None:
    """
    Универсальная функция авторизации с поддержкой QR и phone методов
    
    Args:
        api_id: Telegram API ID
        api_hash: Telegram API Hash
        phone_number: Номер телефона (опциональный при QR)
        use_qr: Использовать QR авторизацию
    """
    if use_qr:
        await qr_login_to_telegram(api_id, api_hash)
    else:
        if phone_number is None:
            raise ValueError("Phone number is required for phone authentication")
        await phone_login_to_telegram(api_id, api_hash, phone_number)


async def logout_from_telegram() -> None:
    user_session = create_client()
    await user_session.connect()
    await user_session.log_out()
    print("You are now logged out from Telegram.")


@cache
def create_client(
    api_id: str | None = None,
    api_hash: str | None = None,
    session_name: str = "mcp_telegram_session",
) -> TelegramClient:
    if api_id is not None and api_hash is not None:
        config = TelegramSettings(api_id=api_id, api_hash=api_hash)
    else:
        config = TelegramSettings()
    
    # Инициализируем глобальный Rate Limiter с настройками
    from .rate_limiter import create_rate_limiter_from_settings, get_rate_limiter
    
    # Создаем или обновляем глобальный rate limiter
    rate_limiter = create_rate_limiter_from_settings(
        global_limit=config.global_rate_limit,
        chat_limit=config.chat_rate_limit,
        group_limit=config.group_rate_limit,
        resolve_daily_limit=config.resolve_daily_limit,
        enabled=config.rate_limit_enabled
    )
    
    state_home = xdg_state_home() / "mcp-telegram"
    state_home.mkdir(parents=True, exist_ok=True)
    
    # Настраиваем клиент с учетом rate limiter
    flood_sleep_threshold = 0 if config.rate_limit_enabled else 60
    
    return TelegramClient(
        state_home / session_name, 
        config.api_id, 
        config.api_hash, 
        base_logger="telethon",
        flood_sleep_threshold=flood_sleep_threshold  # 0 если используем rate limiter, иначе 60
    )


async def phone_login_to_telegram(api_id: str, api_hash: str, phone_number: str) -> None:
    """
    Авторизация через номер телефона (существующая логика)
    
    Args:
        api_id: Telegram API ID
        api_hash: Telegram API Hash  
        phone_number: Номер телефона с кодом страны
    """
    user_session = create_client(api_id=api_id, api_hash=api_hash)
    await user_session.connect()

    result = await user_session.send_code_request(phone_number)
    code = input("Enter login code: ")
    try:
        await user_session.sign_in(
            phone=phone_number,
            code=code,
            phone_code_hash=result.phone_code_hash,
        )
    except SessionPasswordNeededError:
        password = getpass("Enter 2FA password: ")
        await user_session.sign_in(password=password)

    user = await user_session.get_me()
    if isinstance(user, User):
        print(f"Hey {user.username}! You are connected!")
    else:
        print("Connected!")
    print("You can now use the mcp-telegram server.")


async def qr_login_to_telegram(api_id: str, api_hash: str) -> None:
    """
    QR авторизация с интеграцией в MCP архитектуру
    
    Args:
        api_id: Telegram API ID
        api_hash: Telegram API Hash
    """
    user_session = create_client(api_id=api_id, api_hash=api_hash)
    
    # Получаем rate limiter для интеграции
    from .rate_limiter import get_rate_limiter
    rate_limiter = get_rate_limiter()
    
    # Создаем QR handler
    qr_handler = QRAuthHandler(user_session, rate_limiter)
    
    # Запускаем QR авторизацию (ASCII в терминале + PNG файл)
    success = await qr_handler.authenticate(method="both")
    
    if success:
        print("\n✅ QR авторизация завершена успешно!")
        print("🎯 Теперь можно использовать 45telega MCP сервер")
    else:
        print("\n❌ QR авторизация не удалась")
        print("💡 Попробуйте phone авторизацию:")
        print(f"uv run 45telega sign-in --api-id {api_id} --api-hash {api_hash} --phone-number +7XXX")
