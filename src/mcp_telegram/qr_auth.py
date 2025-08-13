"""
QR Authentication module for 45telega MCP Server
Интеграция QR авторизации в архитектуру MCP с Rate Limiter поддержкой
"""
import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

import qrcode
from getpass import getpass
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, TimeoutError


class QRAuthHandler:
    """Обработчик QR авторизации интегрированный в MCP архитектуру"""
    
    def __init__(self, client: TelegramClient, rate_limiter=None):
        self.client = client
        self.rate_limiter = rate_limiter
        self.max_attempts = 3
        self.qr_timeout = 60  # Таймаут для каждого QR кода
        self.temp_files = []  # Список временных файлов для очистки
    
    async def authenticate(self, method: str = "terminal") -> bool:
        """
        Основной метод QR авторизации
        
        Args:
            method: "terminal" для ASCII QR, "file" для PNG, "both" для обоих
            
        Returns:
            True если авторизация успешна
        """
        print("🔐 Запуск QR авторизации...")
        
        try:
            await self.client.connect()
            
            # Проверяем, не авторизованы ли мы уже
            if await self.client.is_user_authorized():
                me = await self.client.get_me()
                print(f"✅ Уже авторизован как {me.first_name}")
                if me.username:
                    print(f"🔗 Username: @{me.username}")
                return True
            
            # Инициируем QR login
            print("📱 Создание QR кода для авторизации...")
            qr_login = await self.client.qr_login()
            
            attempt = 1
            
            while attempt <= self.max_attempts:
                print(f"\n🔄 Попытка {attempt}/{self.max_attempts}")
                print(f"⏰ QR код истекает: {qr_login.expires}")
                
                # Отображаем QR код
                await self._display_qr(qr_login.url, method)
                
                print("\n👆 Отсканируйте QR код в Telegram для авторизации")
                print("⏳ Ожидание сканирования...")
                
                try:
                    # Ожидаем авторизацию
                    result = await qr_login.wait(timeout=self.qr_timeout)
                    
                    if result:
                        # Успешная авторизация
                        me = await self.client.get_me()
                        print(f"\n🎉 Успешная авторизация!")
                        print(f"👤 Имя: {me.first_name} {me.last_name or ''}")
                        if me.username:
                            print(f"🔗 Username: @{me.username}")
                        print(f"🆔 ID: {me.id}")
                        
                        # Cleanup временных файлов
                        await self._cleanup_temp_files()
                        return True
                
                except TimeoutError:
                    print("⏰ Время ожидания истекло")
                    
                    if attempt < self.max_attempts:
                        print("🔄 Создание нового QR кода...")
                        await qr_login.recreate()
                        attempt += 1
                    else:
                        print("❌ Превышено максимальное количество попыток")
                        break
                
                except SessionPasswordNeededError:
                    print("🔐 Требуется пароль 2FA...")
                    success = await self._handle_2fa()
                    if success:
                        await self._cleanup_temp_files()
                    return success
            
            print("\n❌ QR авторизация не удалась")
            print("💡 Попробуйте phone авторизацию:")
            print("uv run 45telega sign-in --api-id X --api-hash Y --phone-number +7XXX")
            return False
            
        except Exception as e:
            print(f"❌ Ошибка QR авторизации: {e}")
            return False
        
        finally:
            await self._cleanup_temp_files()
    
    async def _display_qr(self, qr_url: str, method: str) -> None:
        """Отображение QR кода в выбранном формате"""
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_url)
        qr.make(fit=True)
        
        if method in ["terminal", "both"]:
            print("\n" + "="*50)
            print("📱 QR КОД ДЛЯ СКАНИРОВАНИЯ:")
            print("="*50)
            qr.print_ascii(invert=True)
            print("="*50)
        
        if method in ["file", "both"]:
            # Создаем PNG файл
            img = qr.make_image(fill_color="black", back_color="white")
            qr_file = Path("telegram_qr_auth.png")
            img.save(qr_file)
            self.temp_files.append(qr_file)  # Добавляем в список для очистки
            print(f"💾 QR код сохранен в файл: {qr_file.absolute()}")
            
            # Пытаемся открыть файл автоматически
            try:
                if sys.platform == "darwin":  # macOS
                    os.system(f"open {qr_file}")
                elif sys.platform == "linux":
                    os.system(f"xdg-open {qr_file}")
                elif sys.platform == "win32":
                    os.system(f"start {qr_file}")
            except Exception:
                pass
    
    async def _handle_2fa(self) -> bool:
        """Обработка двухфакторной авторизации"""
        print("🔐 Для завершения авторизации нужен пароль 2FA")
        
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                password = getpass(f"Введите пароль 2FA (попытка {attempt + 1}/{max_attempts}): ")
                
                if not password:
                    print("❌ Пароль не может быть пустым")
                    continue
                
                await self.client.sign_in(password=password)
                
                me = await self.client.get_me()
                print(f"✅ Авторизация с 2FA завершена!")
                print(f"👤 {me.first_name}")
                if me.username:
                    print(f"🔗 Username: @{me.username}")
                return True
                
            except Exception as e:
                print(f"❌ Неверный пароль: {e}")
                if attempt == max_attempts - 1:
                    print("❌ Превышено количество попыток ввода пароля")
        
        return False
    
    async def _cleanup_temp_files(self) -> None:
        """Очистка временных файлов"""
        for file_path in self.temp_files:
            try:
                if file_path.exists():
                    file_path.unlink()
            except Exception:
                pass
        self.temp_files.clear()