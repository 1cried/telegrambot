import subprocess
import pyperclip
import platform
import asyncio
import hashlib
import ctypes
import pyautogui
import time
from ctypes import cast, POINTER, wintypes
import psutil
import socket
import sys
import os
from datetime import datetime

from aiogram.filters import Command
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from PIL import ImageGrab

# Определяем правильный путь к директории (для exe и для обычного запуска)
def get_base_dir():
    """Получить директорию, где находится скрипт/exe"""
    if getattr(sys, 'frozen', False):
        # Запущен как exe
        return os.path.dirname(sys.executable)
    else:
        # Запущен как скрипт
        return os.path.dirname(os.path.abspath(__file__))

# Сохраняем базовую директорию
BASE_DIR = get_base_dir()

from app.database import db
from app.keyboards import *
from app.config import config

# Глобальные переменные из bot.py
try:
    from app.bot import bot_instance, monitoring_task
except ImportError:
    bot_instance = None
    monitoring_task = None

# Состояния FSM
class NotificationState(StatesGroup):
    waiting_for_text = State()

class SleepState(StatesGroup):
    waiting_type = State()

class ClipboardState(StatesGroup):
    waiting_for_clipboard_text = State()

class TokenState(StatesGroup):
    waiting_for_token = State()

class NewPasswordState(StatesGroup):
    waiting_new_password = State()

class BlockExeState(StatesGroup):
    waiting_for_exe_name = State()

class AddSteamState(StatesGroup):
    waiting_for_steam_game = State()

class DownloadState(StatesGroup):
    waiting_for_link = State()

class NotesState(StatesGroup):
    waiting_for_note = State()
    waiting_for_type = State()

class YouTubeState(StatesGroup):
    waiting_for_url = State()
    waiting_for_quality = State()

# Менеджер мониторинга
monitoring_manager = {
    'clipboard': {
        'enabled': False,
        'target_chat_id': None,
        'last_content': '',
        'last_hash': '',
        'task': None
    },
    'programs': {
        'enabled': False,
        'blocked_exes': [],
        'task': None
    }
}

async def monitor_clipboard(bot):
    """Мониторинг буфера обмена"""
    
    while True:
        if not monitoring_manager['clipboard']['enabled']:
            break
        
        target_chat_id = monitoring_manager['clipboard']['target_chat_id']
        if not target_chat_id:
            await asyncio.sleep(5)
            continue
        
        try:
            current = pyperclip.paste()
        except:
            await asyncio.sleep(2)
            continue
        
        if not isinstance(current, str):
            await asyncio.sleep(0.5)
            continue
        
        current = current.strip()
        if not current:
            await asyncio.sleep(0.5)
            continue
        
        current_hash = hashlib.md5(current.encode('utf-8', errors='ignore')).hexdigest()
        
        if current_hash != monitoring_manager['clipboard']['last_hash']:
            try:
                db.add_clipboard(current, source='monitoring')
            except:
                pass
            
            display_text = current[:1500] + "...\n\n[текст обрезан]" if len(current) > 1500 else current
            
            try:
                await bot.send_message(
                    target_chat_id, 
                    f"📋 **Новый буфер обмена:**\n\n{display_text}"
                )
            except:
                pass
            
            monitoring_manager['clipboard']['last_content'] = current
            monitoring_manager['clipboard']['last_hash'] = current_hash
        
        await asyncio.sleep(1)

async def start_monitoring(bot):
    """Запуск мониторинга (буфер обмена)"""
    await monitor_clipboard(bot)

def play_no_sound():
    """Воспроизвести звук no.wav"""
    try:
        import winsound
        # Пробуем разные пути
        possible_paths = [
            os.path.join(BASE_DIR, "app", "no.wav"),
            os.path.join(BASE_DIR, "no.wav"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "no.wav"),
            "app/no.wav",
            "no.wav"
        ]
        sound_path = None
        for path in possible_paths:
            if os.path.exists(path):
                sound_path = path
                break
        
        print(f"[DEBUG] Trying to play sound...")
        if sound_path:
            print(f"[DEBUG] Sound file found at: {sound_path}")
            winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
        else:
            print(f"[DEBUG] Sound file NOT found in any location")
    except Exception as e:
        print(f"[DEBUG] Error playing sound: {e}")

# Глобальная переменная для управления видео
video_process = {'process': None, 'paused': False, 'pid': None, 'player': None}

def play_video_file(video_path):
    """Воспроизвести видео файл - использует Windows Media Player через COM"""
    try:
        # Останавливаем предыдущее видео
        stop_video()
        
        # Пробуем использовать WMP через COM
        try:
            import win32com.client
            wmp = win32com.client.Dispatch("WMPlayer.OCX")
            wmp.URL = video_path
            wmp.controls.play()
            video_process['player'] = wmp
            video_process['paused'] = False
            video_process['pid'] = None
            return True
        except Exception as e:
            print(f"WMP COM failed: {e}")
        
        # Способ 2: Через Windows Media Player напрямую
        wmp_path = r"C:\Program Files (x86)\Windows Media Player\wmplayer.exe"
        if os.path.exists(wmp_path):
            # Запускаем с параметром /play /close
            proc = subprocess.Popen([wmp_path, "/play", "/close", video_path], 
                         creationflags=subprocess.CREATE_NO_WINDOW, 
                         shell=False)
            video_process['process'] = proc
            video_process['pid'] = proc.pid
            video_process['paused'] = False
            return True
        
        # Способ 3: Через VLC если установлен
        vlc_paths = [
            r"C:\Program Files\VideoLAN\VLC\vlc.exe",
            r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe"
        ]
        for vlc_path in vlc_paths:
            if os.path.exists(vlc_path):
                # Используем интерфейс управления VLC
                proc = subprocess.Popen([vlc_path, "--no-video-title-show", "--quiet", "--rc-client", video_path],
                             creationflags=subprocess.CREATE_NO_WINDOW,
                             shell=False)
                video_process['process'] = proc
                video_process['pid'] = proc.pid
                video_process['paused'] = False
                return True
        
        # Способ 4: Через системный плеер (os.startfile)
        import ctypes
        SW_MINIMIZE = 6
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), SW_MINIMIZE)
        os.startfile(video_path)
        
        video_process['paused'] = False
        video_process['pid'] = None
        return True
    except Exception as e:
        print(f"Error playing video: {e}")
        # Фоллбек на os.startfile
        try:
            os.startfile(video_path)
            return True
        except:
            return False

def pause_video():
    """Приостановить воспроизведение - использует Windows Media Player COM"""
    try:
        # Пробуем использовать WMP через COM
        try:
            import win32com.client
            wmp = video_process.get('player')
            if wmp:
                wmp.controls.pause()
                video_process['paused'] = True
                return True
            
            # Пробуем подключиться к уже запущенному WMP
            wmp = win32com.client.Dispatch("WMPlayer.OCX")
            if wmp.URL:
                wmp.controls.pause()
                video_process['player'] = wmp
                video_process['paused'] = True
                return True
        except Exception as e:
            print(f"WMP COM pause failed: {e}")
        
        # Способ 2: Пробуем приостановить процесс через Windows API
        if video_process.get('pid'):
            try:
                import ctypes
                from ctypes import wintypes
                
                PROCESS_ALL_ACCESS = 0x1F0FFF
                pid = video_process['pid']
                
                kernel32 = ctypes.windll.kernel32
                kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
                kernel32.OpenProcess.restype = wintypes.HANDLE
                
                handle = kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
                if handle:
                    try:
                        ntdll = ctypes.windll.ntdll
                        ntdll.NtSuspendProcess.argtypes = [wintypes.HANDLE]
                        ntdll.NtSuspendProcess.restype = wintypes.NTSTATUS
                        result = ntdll.NtSuspendProcess(handle)
                        if result >= 0:
                            kernel32.CloseHandle(handle)
                            video_process['paused'] = True
                            return True
                    except:
                        pass
                    kernel32.CloseHandle(handle)
            except Exception as e:
                print(f"Process suspend failed: {e}")
        
        # Способ 3: Ищем окно и отправляем пробел
        try:
            import win32gui
            import win32con
            import win32api
            
            def find_video_window(hwnd, windows):
                title = win32gui.GetWindowText(hwnd)
                class_name = win32gui.GetClassName(hwnd)
                if any(x in title.lower() for x in ['video', 'vlc', 'wmplayer', 'media player', 'mpc', 'player', 'фильм', 'кино']) or \
                   any(x in class_name.lower() for x in ['vlc', 'wmplayer', 'player', 'mpc', 'applicationframewindow']):
                    windows.append(hwnd)
                return True
            
            windows = []
            win32gui.EnumWindows(find_video_window, windows)
            
            if windows:
                hwnd = windows[0]
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.SetForegroundWindow(hwnd)
                time.sleep(0.1)
                win32api.keybd_event(0x20, 0, 0, 0)
                win32api.keybd_event(0x20, 0, win32con.KEYEVENTF_KEYUP, 0)
                video_process['paused'] = True
                return True
        except ImportError:
            pass
        
        # Фоллбек: PowerShell
        try:
            subprocess.Popen(
                ['powershell', '-Command', 
                 'Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait(" ")'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            video_process['paused'] = True
            return True
        except:
            pass
        
        pyautogui.press('space')
        video_process['paused'] = True
        return True
    except Exception as e:
        print(f"Error pause: {e}")
        return False

def resume_video():
    """Продолжить воспроизведение - использует Windows Media Player COM"""
    try:
        # Пробуем использовать WMP через COM
        try:
            import win32com.client
            wmp = video_process.get('player')
            if wmp:
                wmp.controls.play()
                video_process['paused'] = False
                return True
            
            # Пробуем подключиться к уже запущенному WMP
            wmp = win32com.client.Dispatch("WMPlayer.OCX")
            if wmp.URL:
                wmp.controls.play()
                video_process['player'] = wmp
                video_process['paused'] = False
                return True
        except Exception as e:
            print(f"WMP COM resume failed: {e}")
        
        # Способ 2: Пробуем возобновить процесс через Windows API
        if video_process.get('pid'):
            try:
                import ctypes
                from ctypes import wintypes
                
                PROCESS_ALL_ACCESS = 0x1F0FFF
                pid = video_process['pid']
                
                kernel32 = ctypes.windll.kernel32
                kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
                kernel32.OpenProcess.restype = wintypes.HANDLE
                
                handle = kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
                if handle:
                    try:
                        ntdll = ctypes.windll.ntdll
                        ntdll.NtResumeProcess.argtypes = [wintypes.HANDLE]
                        ntdll.NtResumeProcess.restype = wintypes.NTSTATUS
                        result = ntdll.NtResumeProcess(handle)
                        if result >= 0:
                            kernel32.CloseHandle(handle)
                            video_process['paused'] = False
                            return True
                    except:
                        pass
                    kernel32.CloseHandle(handle)
            except Exception as e:
                print(f"Process resume failed: {e}")
        
        # Способ 3: Ищем окно и отправляем пробел
        try:
            import win32gui
            import win32con
            import win32api
            
            def find_video_window(hwnd, windows):
                title = win32gui.GetWindowText(hwnd)
                class_name = win32gui.GetClassName(hwnd)
                if any(x in title.lower() for x in ['video', 'vlc', 'wmplayer', 'media player', 'mpc', 'player', 'фильм', 'кино']) or \
                   any(x in class_name.lower() for x in ['vlc', 'wmplayer', 'player', 'mpc', 'applicationframewindow']):
                    windows.append(hwnd)
                return True
            
            windows = []
            win32gui.EnumWindows(find_video_window, windows)
            
            if windows:
                hwnd = windows[0]
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.SetForegroundWindow(hwnd)
                time.sleep(0.1)
                win32api.keybd_event(0x20, 0, 0, 0)
                win32api.keybd_event(0x20, 0, win32con.KEYEVENTF_KEYUP, 0)
                video_process['paused'] = False
                return True
        except ImportError:
            pass
        
        # Фоллбек: PowerShell
        try:
            subprocess.Popen(
                ['powershell', '-Command', 
                 'Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait(" ")'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            video_process['paused'] = False
            return True
        except:
            pass
        
        pyautogui.press('space')
        video_process['paused'] = False
        return True
    except Exception as e:
        print(f"Error resume: {e}")
        return False

def stop_video():
    """Остановить видео - закрываем плееры"""
    try:
        # Останавливаем WMP COM
        try:
            wmp = video_process.get('player')
            if wmp:
                wmp.controls.stop()
                video_process['player'] = None
        except:
            pass
        
        subprocess.run('taskkill /F /IM wmplayer.exe 2>nul', shell=True)
        subprocess.run('taskkill /F /IM mpv.exe 2>nul', shell=True)
        subprocess.run('taskkill /F /IM vlc.exe 2>nul', shell=True)
        video_process['process'] = None
        video_process['pid'] = None
        video_process['paused'] = False
        return True
    except:
        return False

def volume_up():
    """Увеличить громкость - использует pyautogui"""
    try:
        pyautogui.press('volumeup')
        return True
    except:
        return False

def volume_down():
    """Уменьшить громкость - использует pyautogui"""
    try:
        pyautogui.press('volumedown')
        return True
    except:
        return False

def volume_mute():
    """Выключить/включить звук - использует pyautogui"""
    try:
        pyautogui.press('volumemute')
        return True
    except:
        return False

# Глобальная переменная для текущего видео
current_video_index = {'index': 0, 'videos': []}

def get_video_list():
    """Получить список доступных видео"""
    # Пробуем разные пути
    possible_video_dirs = [
        os.path.join(BASE_DIR, "assets", "screamers"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "screamers"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "screamers"),
    ]
    
    videos = []
    video_dir = None
    
    for vdir in possible_video_dirs:
        if os.path.exists(vdir):
            video_dir = vdir
            for f in sorted(os.listdir(vdir)):
                if f.endswith('.mp4'):
                    videos.append(os.path.join(vdir, f))
            break
    
    return videos

def play_next_video():
    """Воспроизвести следующее видео"""
    global current_video_index
    videos = get_video_list()
    
    if not videos:
        return False
    
    # Обновляем индекс
    current_video_index['videos'] = videos
    current_video_index['index'] = (current_video_index['index'] + 1) % len(videos)
    
    # Воспроизводим видео
    return play_video_file(videos[current_video_index['index']])

def play_prev_video():
    """Воспроизвести предыдущее видео"""
    global current_video_index
    videos = get_video_list()
    
    if not videos:
        return False
    
    # Обновляем индекс
    current_video_index['videos'] = videos
    current_video_index['index'] = (current_video_index['index'] - 1) % len(videos)
    
    # Воспроизводим видео
    return play_video_file(videos[current_video_index['index']])

async def cmd_video_menu(message: types.Message):
    """Меню видео - показывает доступные видео для воспроизведения"""
    from app.keyboards import video_menu_keyboard, volume_keyboard
    
    # Проверяем наличие видео файлов
    # Пробуем разные пути
    possible_video_dirs = [
        os.path.join(BASE_DIR, "assets", "screamers"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "screamers"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "screamers"),
    ]
    
    videos = []
    video_dir = None
    
    for vdir in possible_video_dirs:
        if os.path.exists(vdir):
            video_dir = vdir
            for f in sorted(os.listdir(vdir)):
                if f.endswith('.mp4'):
                    videos.append(f)
            break
    
    if videos:
        await message.answer(
            "🎬 Видео плеер\n\nВыберите видео для воспроизведения:\n\n🔊 Управление громкостью:",
            reply_markup=video_menu_keyboard()
        )
        # Отправляем клавиатуру громкости отдельным сообщением
        await message.answer("🔊 Громкость:", reply_markup=volume_keyboard())
    else:
        await message.answer(
            "🎬 Видео плеер\n\nВидео файлы не найдены в папке assets/screamers\n\n🔊 Управление громкостью:",
            reply_markup=volume_keyboard()
        )

def set_volume(level: int):
    """Установить громкость (0-100)"""
    try:
        # Используем PowerShell для установки громкости
        # level должен быть от 0 до 100
        level = max(0, min(100, level))
        
        # Сначала получаем текущее устройство воспроизведения по умолчанию
        script = f'''
Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public class Audio {{
    [DllImport(\"user32.dll\")]
    public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, UIntPtr dwExtraInfo);
    public const byte VK_VOLUME_UP = 0xAF;
    public const byte VK_VOLUME_DOWN = 0xAE;
    public const uint KEYEVENTF_KEYUP = 0x0002;
}}
"@
        
        # Устанавливаем громкость через COM интерфейс
        $shell = New-Object -ComObject WScript.Shell
        # Попробуем использовать nircmd если установлен
        $nircmd = "C:\\Windows\\System32\\nircmd.exe"
        if (Test-Path $nircmd) {{
            & $nircmd setsysvolume {int(level * 655.35)}
        }} else {{
            # Используем PowerShell для установки громкости
            Add-Type -AssemblyName System.Sound
            [System.Media.SystemSounds]::Beep.Play()
        }}
        '''
        
        # Более простой способ - использовать PowerShell с Windows Core Audio API
        ps_script = f'''
$targetVol = {level}
Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public class Audio{{
    [DllImport(\"user32.dll\")]
    public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, UIntPtr dwExtraInfo);
}}
"@
        '''
        
        # Используем более надёжный способ через pycaw или direct COM
        # Пока просто отправляем нажатия клавиш
        return True
    except Exception as e:
        print(f"[DEBUG] Error setting volume: {e}")
        return False

async def cmd_volume_menu(message: types.Message):
    """Меню управления громкостью"""
    from app.keyboards import volume_keyboard
    await message.answer(
        "🔊 **Управление громкостью**\n\nВыберите действие:",
        reply_markup=volume_keyboard()
    )

async def monitor_blocked_programs(bot):
    """Мониторинг заблокированных программ"""
    while True:
        if not monitoring_manager['programs']['enabled']:
            break
        
        blocked_exes = monitoring_manager['programs']['blocked_exes']
        if not blocked_exes:
            await asyncio.sleep(2)
            continue
        
        try:
            for proc in psutil.process_iter(['name']):
                try:
                    proc_name = proc.info['name'].lower()
                    for blocked in blocked_exes:
                        if blocked.lower() in proc_name:
                            proc.terminate()
                            play_no_sound()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except:
            pass
        
        await asyncio.sleep(1)



async def cmd_start(message: types.Message, state: FSMContext):
    """Старт"""
    await state.clear()
    
    monitoring_status = db.load_monitoring_status('clipboard')
    monitoring_manager['clipboard']['enabled'] = monitoring_status['enabled']
    monitoring_manager['clipboard']['target_chat_id'] = monitoring_status['chat_id'] or message.chat.id
    
    await message.answer(
        "🤖 **Бот запущен!**",
        reply_markup=main_keyboard(monitoring_manager['clipboard']['enabled'])
    )

async def cmd_screenshot(message: types.Message):
    """Скриншот"""
    import tempfile
    import uuid
    try:
        from app.screen_protection import allow_screenshot
        allow_screenshot()
        
        await asyncio.sleep(0.1)
        
        screenshot = ImageGrab.grab()
        
        temp_dir = tempfile.gettempdir()
        filename = f"screenshot_{uuid.uuid4().hex}.png"
        filepath = os.path.join(temp_dir, filename)
        
        screenshot.save(filepath)
        
        await message.answer_photo(
            types.FSInputFile(filepath)
        )
        
        os.remove(filepath)
        
    except Exception as e:
        await message.answer(f"❌ Ошибка скриншота: {e}")

async def cmd_clipboard(message: types.Message):
    """Буфер обмена"""
    try:
        current = pyperclip.paste()
        if current and isinstance(current, str):
            current = current.strip()
            if len(current) > 4000:
                current = current[:4000] + "...\n\n[текст обрезан]"
            
            await message.answer(
                f"📋 **Текущий буфер обмена:**\n\n{current}",
                reply_markup=main_keyboard(monitoring_manager['clipboard']['enabled'])
            )
            
            db.add_clipboard(current, source='manual')
        else:
            await message.answer("📋 Буфер обмена пуст или содержит не текст")
            
    except Exception as e:
        await message.answer(f"❌ Ошибка чтения буфера: {e}")

async def cmd_set_clipboard(message: types.Message, state: FSMContext):
    """Добавить текст в буфер обмена"""
    await state.set_state(ClipboardState.waiting_for_clipboard_text)
    await message.answer("📝 Введите текст для добавления в буфер обмена:", reply_markup=types.ReplyKeyboardRemove())

async def handle_set_clipboard(message: types.Message, state: FSMContext):
    """Обработка текста для буфера обмена"""
    current_state = await state.get_state()
    
    if current_state != ClipboardState.waiting_for_clipboard_text:
        return
    
    text = message.text.strip()
    
    if not text:
        await message.answer("❌ Текст не может быть пустым!")
        await state.clear()
        return
    
    try:
        import pyperclip
        pyperclip.copy(text)
        await message.answer(f"✅ Текст добавлен в буфер обмена!", reply_markup=main_keyboard())
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}", reply_markup=main_keyboard())
    
    await state.clear()

async def toggle_monitoring(message: types.Message):
    """Переключить мониторинг"""
    from app.bot import bot_instance, monitoring_task
    
    monitoring_manager['clipboard']['enabled'] = not monitoring_manager['clipboard']['enabled']
    
    if monitoring_manager['clipboard']['enabled']:
        monitoring_manager['clipboard']['target_chat_id'] = message.chat.id
        
        if monitoring_task is None or monitoring_task.done():
            import asyncio
            monitoring_task = asyncio.create_task(start_monitoring(bot_instance))
    
    status = "✅ ВКЛЮЧЕН" if monitoring_manager['clipboard']['enabled'] else "❌ ВЫКЛЮЧЕН"
    
    db.save_monitoring_status(
        'clipboard', 
        monitoring_manager['clipboard']['enabled'],
        monitoring_manager['clipboard']['target_chat_id']
    )
    
    await message.answer(
        f"📋 Мониторинг буфера: {status}",
        reply_markup=main_keyboard(monitoring_manager['clipboard']['enabled'])
    )

# ==================== СИСТЕМНЫЕ КОМАНДЫ ====================

async def cmd_shutdown(message: types.Message):
    """Выключение компьютера"""
    keyboard = shutdown_keyboard()
    await message.answer(
        "🔴 **Выключение компьютера**\n\n"
        "Вы уверены, что хотите выключить компьютер?",
        reply_markup=keyboard
    )

async def cmd_restart_pc(message: types.Message):
    """Перезагрузка компьютера"""
    from app.keyboards import restart_pc_keyboard
    keyboard = restart_pc_keyboard()
    
    await message.answer(
        "🔄 **Перезагрузка компьютера**\n\n"
        "Вы уверены, что хотите перезагрузить компьютер?",
        reply_markup=keyboard
    )

async def cmd_restart(message: types.Message):
    """Перезапуск бота"""
    await message.answer("🔄 Перезапускаю бота...")
    
    try:
        import sys
        import os
        
        os.execv(sys.executable, [sys.executable] + sys.argv)
        
    except Exception as e:
        await message.answer(f"❌ Ошибка перезапуска: {e}")

async def cmd_lock(message: types.Message):
    """Блокировка компьютера"""
    try:
        ctypes.windll.user32.LockWorkStation()
        await message.answer("🔒 Компьютер заблокирован")
    except Exception as e:
        await message.answer(f"❌ Ошибка блокировки: {e}")

async def cmd_sleep_menu(message: types.Message):
    """Меню сна"""
    await message.answer(
        "💤 **Выберите режим сна:**",
        reply_markup=sleep_menu_keyboard()
    )

async def cmd_hibernate(message: types.Message):
    """Гибернация"""
    try:
        # Включаем гибернацию
        subprocess.run("powercfg /hibernate on", shell=True)
        
        # Пробуем через ctypes
        try:
            import ctypes
            # SetSuspendState(Hibernate=1, ForceCritical=0, DisableWakeEvent=0)
            result = ctypes.windll.PowrProf.SetSuspendState(1, 0, 0)
            
            if result:
                await message.answer("🛌 Переход в гибернацию...", reply_markup=main_keyboard())
            else:
                # Метод 2: через shutdown
                subprocess.run("shutdown /h /t 1", shell=True)
                await message.answer("🛌 Переход в гибернацию...", reply_markup=main_keyboard())
                
        except Exception as e:
            # Метод 2: через shutdown
            subprocess.run("shutdown /h /t 1", shell=True)
            await message.answer("🛌 Переход в гибернацию...", reply_markup=main_keyboard())
            
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

async def cmd_sleep(message: types.Message):
    """Сон"""
    try:
        # Отключаем гибернацию
        subprocess.run("powercfg /hibernate off", shell=True)
        
        # Используем ctypes для перехода в сон (S3)
        # SetSuspendState(Hibernate, ForceCritical, DisableWakeEvent)
        # Hibernate=0 - обычный сон (не гибернация)
        # ForceCritical=0 - не принудительно
        # DisableWakeEvent=0 - разрешить события пробуждения
        
        # Пробуем через PowerSetings (требуется UAC)
        try:
            # Метод 1: через ctypes
            import ctypes
            from ctypes import wintypes
            
            # Определяем константы для SetSuspendState
            ES_CONTINUOUS = 0x80000000
            ES_SYSTEM_REQUIRED = 0x00000001
            
            # Вызываем SetSuspendState
            # Параметры: Hibernate (0=сон), ForceCritical (0=нет), DisableWakeEvent (0=разрешено)
            result = ctypes.windll.PowrProf.SetSuspendState(0, 0, 0)
            
            if result:
                await message.answer("💤 Переход в режим сна...", reply_markup=main_keyboard())
            else:
                # Метод 2: если первый не сработал - пробуем через командную строку
                subprocess.run("rundll32.exe powrprof.dll,SetSuspendState", shell=True)
                await message.answer("💤 Переход в режим сна...", reply_markup=main_keyboard())
                
        except Exception as e:
            # Метод 2: через subprocess
            subprocess.run("rundll32.exe powrprof.dll,SetSuspendState", shell=True)
            await message.answer("💤 Переход в режим сна...", reply_markup=main_keyboard())
            
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

async def cmd_monitor_off(message: types.Message):
    """Выключить монитор"""
    try:
        import win32api
        import win32con
        win32api.SendMessage(0xFFFF, win32con.WM_SYSCOMMAND, win32con.SC_MONITORPOWER, 2)
        await message.answer("🖥️ Монитор выключен", reply_markup=main_keyboard())
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

async def cmd_monitor_on(message: types.Message):
    """Включить монитор"""
    try:
        import win32api
        import win32con
        win32api.SendMessage(0xFFFF, win32con.WM_SYSCOMMAND, win32con.SC_MONITORPOWER, -1)
        await message.answer("📱 Монитор включен", reply_markup=main_keyboard())
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

# ==================== ПРОЦЕССЫ ====================

def bring_to_front(pid):
    """Вывести процесс на передний план"""
    try:
        import win32gui
        import win32con
        import win32process
        
        def enum_windows_callback(hwnd, pid_list):
            _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
            if found_pid in pid_list:
                pid_list.remove(found_pid)
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.SetForegroundWindow(hwnd)
            return True
        
        win32gui.EnumWindows(enum_windows_callback, [pid])
        return True
    except:
        return False

async def cmd_processes(message: types.Message):
    """Список процессов"""
    try:
        processes = []
        seen_names = set()
        
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                pid = proc.info['pid']
                name = proc.info['name']
                
                if name.lower() in ['system', 'system idle process', 'svchost.exe']:
                    continue
                
                # Пропускаем дубликаты по имени
                if name.lower() in seen_names:
                    continue
                seen_names.add(name.lower())
                
                processes.append((pid, name))
                
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        processes.sort(key=lambda x: x[1].lower())
        
        if processes:
            keyboard = processes_keyboard(processes)
            await message.answer(
                "⚙️ **Активные процессы:**\n\n"
                f"Всего: {len(processes)} процессов",
                reply_markup=keyboard
            )
        else:
            await message.answer("⚙️ Активные процессы не найдены")
            
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

async def cmd_system_menu(message: types.Message):
    """Меню системы"""
    keyboard = system_menu_keyboard()
    await message.answer(
        "🖥️ **Информация о системе:**\n\n"
        "Выберите раздел:",
        reply_markup=keyboard
    )


# ==================== СИСТЕМНАЯ ИНФОРМАЦИЯ ====================

async def show_full_system_info(message: types.Message):
    """Полная сводка по системе"""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.5)
        cpu_count = psutil.cpu_count()
        
        mem = psutil.virtual_memory()
        mem_used_gb = mem.used / (1024**3)
        mem_total_gb = mem.total / (1024**3)
        
        net_io = psutil.net_io_counters()
        
        response = "🖥️ **ПОЛНАЯ СВОДКА**\n"
        response += "══════════════════════\n\n"
        response += f"⚙️ CPU: {cpu_count} ядер, {cpu_percent}% загрузки\n"
        response += f"🧠 RAM: {mem.percent}% ({mem_used_gb:.1f}/{mem_total_gb:.1f} ГБ)\n"
        
        disk_count = 0
        for partition in psutil.disk_partitions()[:3]:
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disk_count += 1
                drive = partition.device[0] if partition.device else "?"
                response += f"💾 {drive}: {usage.percent}% "
            except:
                pass
        
        if disk_count > 0:
            response += "\n"
        
        response += f"🌐 Сеть: ↑{net_io.bytes_sent/(1024**2):.0f}MB ↓{net_io.bytes_recv/(1024**2):.0f}MB\n"
        response += f"🖥️ ОС: {platform.system()} {platform.release()}\n"
        
        uptime = datetime.fromtimestamp(psutil.boot_time())
        response += f"⏱️ Запуск: {uptime.strftime('%d.%m %H:%M')}"
        
        await message.answer(response)
        
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")


async def show_detailed_cpu(message: types.Message):
    """Детальная информация о процессоре"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
        cpu_freq = psutil.cpu_freq()
        cpu_count = psutil.cpu_count()
        cpu_count_logical = psutil.cpu_count(logical=True)
        
        response = "⚙️ **ПРОЦЕССОР - ДЕТАЛЬНО**\n"
        response += "══════════════════════════\n\n"
        response += f"Ядра: {cpu_count} физических, {cpu_count_logical} логических\n"
        
        if cpu_freq:
            response += f"Частота: {cpu_freq.current:.0f} MHz (макс: {cpu_freq.max:.0f} MHz)\n\n"
        
        response += "📊 **Загрузка по ядрам:**\n"
        
        for i, percent in enumerate(cpu_percent, 1):
            bar_length = 10
            filled = int(bar_length * percent / 100)
            bar = '█' * filled + '░' * (bar_length - filled)
            
            if i <= 8:
                if i % 2 == 1:
                    response += "  "
                response += f"Ядро {i:2d}: [{bar}] {percent:3.0f}%  "
                if i % 2 == 0:
                    response += "\n"
        
        if len(cpu_percent) > 8:
            response += f"\n... и еще {len(cpu_percent)-8} ядер\n"
        
        avg_load = sum(cpu_percent) / len(cpu_percent)
        response += f"\n📈 Средняя загрузка: {avg_load:.1f}%"
        
        await message.answer(response)
        
    except Exception as e:
        await message.answer(f"❌ Ошибка CPU: {e}")


async def show_detailed_ram(message: types.Message):
    """Детальная информация о памяти"""
    try:
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        total_gb = mem.total / (1024**3)
        used_gb = mem.used / (1024**3)
        free_gb = mem.free / (1024**3)
        available_gb = mem.available / (1024**3)
        
        response = "🧠 **ОПЕРАТИВНАЯ ПАМЯТЬ**\n"
        response += "════════════════════════\n\n"
        response += f"📊 Всего: {total_gb:.1f} ГБ\n"
        response += f"📈 Использовано: {used_gb:.1f} ГБ ({mem.percent}%)\n"
        response += f"📉 Свободно: {free_gb:.1f} ГБ\n"
        response += f"✅ Доступно: {available_gb:.1f} ГБ\n\n"
        
        bar_length = 20
        filled = int(bar_length * mem.percent / 100)
        bar = '█' * filled + '░' * (bar_length - filled)
        response += f"[{bar}] {mem.percent}%\n\n"
        
        if swap.total > 0:
            swap_total_gb = swap.total / (1024**3)
            swap_used_gb = swap.used / (1024**3)
            response += f"💽 **SWAP (файл подкачки):**\n"
            response += f"Использовано: {swap_used_gb:.1f}/{swap_total_gb:.1f} ГБ ({swap.percent}%)"
        
        await message.answer(response)
        
    except Exception as e:
        await message.answer(f"❌ Ошибка RAM: {e}")


async def show_detailed_disk(message: types.Message):
    """Детальная информация о дисках"""
    try:
        response = "💾 **ДИСКИ И ХРАНИЛИЩЕ**\n"
        response += "══════════════════════\n\n"
        
        for partition in psutil.disk_partitions():
            try:
                if 'cdrom' in partition.opts or partition.fstype == '':
                    continue
                
                usage = psutil.disk_usage(partition.mountpoint)
                total_gb = usage.total / (1024**3)
                used_gb = usage.used / (1024**3)
                free_gb = usage.free / (1024**3)
                percent = usage.percent
                
                drive_name = partition.device
                if partition.mountpoint and partition.mountpoint != '/':
                    drive_name = f"{partition.device} ({partition.mountpoint})"
                
                response += f"📁 **{drive_name}**\n"
                response += f"Файловая система: {partition.fstype}\n"
                response += f"Размер: {total_gb:.1f} ГБ\n"
                response += f"Использовано: {used_gb:.1f} ГБ ({percent}%)\n"
                response += f"Свободно: {free_gb:.1f} ГБ\n"
                
                bar_length = 15
                filled = int(bar_length * percent / 100)
                bar = '█' * filled + '░' * (bar_length - filled)
                response += f"[{bar}] {percent}%\n\n"
                
            except:
                continue
        
        if response.count("📁") == 0:
            response += "❌ Нет доступных дисков для отображения"
        
        await message.answer(response)
        
    except Exception as e:
        await message.answer(f"❌ Ошибка дисков: {e}")


async def show_detailed_network(message: types.Message):
    """Детальная информация о сети"""
    try:
        hostname = socket.gethostname()
        try:
            local_ip = socket.gethostbyname(hostname)
        except:
            local_ip = "не определен"
        
        net_io = psutil.net_io_counters()
        sent_mb = net_io.bytes_sent / (1024**2)
        recv_mb = net_io.bytes_recv / (1024**2)
        
        connections = psutil.net_connections(kind='inet')
        tcp_established = len([c for c in connections if c.status == 'ESTABLISHED'])
        tcp_listen = len([c for c in connections if c.status == 'LISTEN'])
        
        response = "🌐 **СЕТЕВАЯ ИНФОРМАЦИЯ**\n"
        response += "══════════════════════\n\n"
        response += f"🖥️ Имя ПК: {hostname}\n"
        response += f"📍 Локальный IP: {local_ip}\n\n"
        response += "📊 **Статистика трафика:**\n"
        response += f"📤 Отправлено: {sent_mb:.1f} MB\n"
        response += f"📥 Получено: {recv_mb:.1f} MB\n"
        response += f"📦 Пакетов отправлено: {net_io.packets_sent}\n"
        response += f"📦 Пакетов получено: {net_io.packets_recv}\n\n"
        response += f"🔗 **Соединения:**\n"
        response += f"TCP ESTABLISHED: {tcp_established}\n"
        response += f"TCP LISTEN: {tcp_listen}\n"
        response += f"Всего соединений: {len(connections)}"
        
        await message.answer(response)
        
    except Exception as e:
        await message.answer(f"❌ Ошибка сети: {e}")


async def show_detailed_gpu(message: types.Message):
    """Детальная информация о видеокарте"""
    try:
        response = "🎮 **ВИДЕОКАРТА**\n"
        response += "═══════════════════\n\n"
        
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            
            if gpus:
                for i, gpu in enumerate(gpus, 1):
                    response += f"**GPU #{i}: {gpu.name}**\n"
                    response += f"Загрузка: {gpu.load*100:.1f}%\n"
                    response += f"Температура: {gpu.temperature:.0f}°C\n"
                    response += f"Память: {gpu.memoryUsed:.0f}/{gpu.memoryTotal:.0f} MB ({gpu.memoryUtil*100:.0f}%)\n"
                    
                    bar_length = 15
                    filled = int(bar_length * gpu.load)
                    bar = '█' * filled + '░' * (bar_length - filled)
                    response += f"[{bar}] {gpu.load*100:.0f}%\n\n"
            else:
                response += "❌ Видеокарты не найдены\n"
                
        except ImportError:
            response += "⚠️ Установите GPUtil для детальной информации:\n"
            response += "`pip install gputil`\n\n"
            response += "Используется системная информация..."
        
        await message.answer(response)
        
    except Exception as e:
        await message.answer(f"❌ Ошибка GPU: {e}")


async def show_detailed_os(message: types.Message):
    """Детальная информация об ОС"""
    try:
        import getpass
        
        uptime = datetime.fromtimestamp(psutil.boot_time())
        now = datetime.now()
        uptime_delta = now - uptime
        
        days = uptime_delta.days
        hours = uptime_delta.seconds // 3600
        minutes = (uptime_delta.seconds % 3600) // 60
        
        username = getpass.getuser()
        
        response = "🖥️ **ОПЕРАЦИОННАЯ СИСТЕМА**\n"
        response += "════════════════════════\n\n"
        response += f"Система: {platform.system()} {platform.release()}\n"
        response += f"Версия: {platform.version()}\n"
        response += f"Архитектура: {platform.architecture()[0]}\n"
        response += f"Процессор: {platform.processor()}\n\n"
        response += f"⏱️ **Время работы системы:**\n"
        response += f"Запуск: {uptime.strftime('%d.%m.%Y %H:%M:%S')}\n"
        response += f"Прошло: {days} дн., {hours} ч., {minutes} мин.\n\n"
        response += f"👤 **Пользователь:** {username}\n"
        response += f"📁 Рабочий каталог: {os.getcwd()}"
        
        await message.answer(response)
        
    except Exception as e:
        await message.answer(f"❌ Ошибка ОС: {e}")

# ==================== ПРОГРАММЫ ====================

async def cmd_programs(message: types.Message):
    """Меню программ - показывает все доступные программы"""
    try:
        # Получаем программы без заблокированных (по умолчанию)
        all_programs = db.get_programs()
        
        if all_programs:
            keyboard = all_programs_keyboard(all_programs)
            await message.answer(
                "🖥️ **Доступные программы:**\n\n"
                f"Всего: {len(all_programs)} программ",
                reply_markup=keyboard
            )
        else:
            await message.answer(
                "🖥️ **Программы:**\n\n"
                "Программ пока нет.\n"
                "Нажмите '➕ Добавить' для добавления.",
                reply_markup=programs_menu_keyboard()
            )
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")


async def cmd_favorites(message: types.Message):
    """Избранные программы - показывает все доступные программы кнопками"""
    from app.keyboards import favorites_with_buttons_keyboard, programs_menu_keyboard
    
    try:
        programs = db.get_programs()
        if programs:
            await message.answer(
                "🖥️ **ИЗБРАННОЕ**\n\n"
                "Нажмите на программу для запуска:",
                reply_markup=favorites_with_buttons_keyboard(programs)
            )
        else:
            await message.answer(
                "🖥️ **ИЗБРАННОЕ**\n\n"
                "Пока нет избранных программ.",
                reply_markup=programs_menu_keyboard()
            )
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")


async def run_program(program_id: int, message: types.Message = None):
    """Запуск программы"""
    try:
        # Получаем программу напрямую из базы
        cursor = db.conn.cursor()
        cursor.execute('SELECT id, name, path, type FROM programs WHERE id = ?', (program_id,))
        row = cursor.fetchone()
        
        if not row:
            return False
        
        program_name = row[1]
        program_path = row[2] or ''
        program_type = row[3] or ''
        
        # Проверяем, не заблокирована ли программа
        if 'b' in program_type or 'l' in program_type:
            return False
        
        # Для Steam игр - запускаем по AppID
        if 'steam' in program_type:
            app_id = program_path if program_path else program_name
            if app_id:
                # Используем start для открытия URL в Windows
                subprocess.Popen(f'start "" "steam://run/{app_id}"', shell=True)
                if message:
                    await message.answer(
                        f"✅ **{program_name} запущена!**",
                        reply_markup=main_keyboard(monitoring_manager['clipboard']['enabled'])
                    )
                return True
        
        # Для обычных программ - запускаем по пути
        if program_path:
            if os.path.exists(program_path):
                subprocess.Popen(program_path, shell=True)
            else:
                # Пробуем как команду
                subprocess.Popen(f'start "" "{program_path}"', shell=True)
        else:
            # Фоллбек - запускаем по имени (как команду)
            subprocess.Popen(f'start "" "{program_name}"', shell=True)
        
        if message:
            await message.answer(
                f"✅ **{program_name} запущена!**",
                reply_markup=main_keyboard(monitoring_manager['clipboard']['enabled'])
            )
        return True
        
    except Exception as e:
        print(f"Ошибка запуска программы: {e}")
        return False


# ==================== УВЕДОМЛЕНИЯ ====================

async def cmd_notify(message: types.Message, state: FSMContext):
    """Отправить уведомление"""
    await state.set_state(NotificationState.waiting_for_text)
    await message.answer(
        "✏️ **Введите текст уведомления:**",
        reply_markup=types.ReplyKeyboardRemove()
    )

async def handle_notification(message: types.Message, state: FSMContext):
    """Обработка уведомления"""
    text = message.text.strip()
    
    if not text:
        await message.answer("❌ Текст не может быть пустым")
        await state.clear()
        return
    
    try:
        from win10toast import ToastNotifier
        toaster = ToastNotifier()
        toaster.show_toast(
            "",
            text,
            duration=3,
            threaded=True
        )
        await message.answer(
            f"✅ Уведомление отправлено:\n\n{text}",
            reply_markup=main_keyboard(monitoring_manager['clipboard']['enabled'])
        )
    except:
        try:
            import win32api
            import win32con
            win32api.MessageBox(0, text, "Уведомление от бота", win32con.MB_OK | win32con.MB_ICONINFORMATION)
            await message.answer(
                f"✅ Уведомление показано:\n\n{text}",
                reply_markup=main_keyboard(monitoring_manager['clipboard']['enabled'])
            )
        except:
            await message.answer("⚠️ Не удалось показать уведомление")
    
    await state.clear()

# ==================== ЗАГРУЗКА ====================

def get_ffmpeg_location():
    """Найти путь к FFmpeg"""
    import shutil
    ffmpeg_path = shutil.which('ffmpeg')
    if ffmpeg_path:
        return os.path.dirname(ffmpeg_path)
    return None

def detect_link_type(text):
    """Определить тип ссылки"""
    text_lower = text.lower()
    
    youtube_patterns = ['youtube.com', 'youtu.be', 'ytube']
    tiktok_patterns = ['tiktok.com', 'vm.tiktok', 'tiktok.com']
    
    for pattern in youtube_patterns:
        if pattern in text_lower:
            return 'youtube'
    
    for pattern in tiktok_patterns:
        if pattern in text_lower:
            return 'tiktok'
    
    return None


async def cmd_download(message: types.Message, state: FSMContext):
    """Скачать"""
    await state.set_state(DownloadState.waiting_for_link)
    await message.answer("📥 Отправь ссылку:", reply_markup=types.ReplyKeyboardRemove())


async def handle_download_link(message: types.Message, state: FSMContext):
    """Ссылка"""
    link = message.text.strip()
    
    if not link:
        await message.answer("❌")
        return
    
    link_type = detect_link_type(link)
    
    if link_type == 'youtube':
        await download_youtube(message, link)
    elif link_type == 'tiktok':
        await download_tiktok(message, link)
    else:
        await message.answer("❌ Неизвестная ссылка", reply_markup=main_keyboard(monitoring_manager['clipboard']['enabled']))
    
    await state.clear()


async def download_youtube(message: types.Message, url: str):
    """YouTube - скачивает видео"""
    import tempfile
    import uuid
    await message.answer("⏳ Загрузка с YouTube...\nЭто может занять несколько минут...")
    
    temp_dir = tempfile.gettempdir()
    video_path = os.path.join(temp_dir, f"youtube_{uuid.uuid4().hex}.mp4")
    
    # Пробуем найти FFmpeg
    ffmpeg_location = get_ffmpeg_location()
    
    try:
        from yt_dlp import YoutubeDL
        
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': video_path,
            'quiet': True,
            'no_warnings': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            },
            'extractor_retries': 3,
            'fragment_retries': 3,
            'nocheckcertificate': True,
        }
        
        # Добавляем FFmpeg если найден
        if ffmpeg_location:
            ydl_opts['ffmpeg_location'] = ffmpeg_location
        
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'YouTube Video')
        
        # Проверяем существование файла
        if os.path.exists(video_path):
            file_size = os.path.getsize(video_path)
            file_size_mb = file_size / (1024 * 1024)
            
            MAX_SIZE_MB = 50
            
            if file_size_mb > MAX_SIZE_MB:
                # Пробуем качество 720p
                os.remove(video_path)
                video_path = os.path.join(temp_dir, f"youtube_{uuid.uuid4().hex}.mp4")
                ydl_opts['format'] = 'best[height<=720][ext=mp4]/best[ext=mp4]/best'
                ydl_opts['outtmpl'] = video_path
                with YoutubeDL(ydl_opts) as ydl2:
                    info = ydl2.extract_info(url, download=True)
                
                if os.path.exists(video_path):
                    file_size = os.path.getsize(video_path)
                    file_size_mb = file_size / (1024 * 1024)
                    if file_size_mb > MAX_SIZE_MB:
                        os.remove(video_path)
                        await message.answer(
                            "⚠️ Видео слишком большое\n\n"
                            f"Размер: {file_size_mb:.1f} MB\n"
                            "Telegram Premium: до 2GB\n\n"
                            "Попробуйте короткое видео или купите Premium"
                        )
                        return
                    await message.answer_video(
                        types.FSInputFile(video_path),
                        caption=f"🎬 {title} (720p)",
                    )
                    os.remove(video_path)
            else:
                await message.answer_video(
                    types.FSInputFile(video_path),
                    caption=f"🎬 {title}",
                )
                os.remove(video_path)
        else:
            await message.answer("❌ Не удалось загрузить видео")
                
    except Exception as e:
        error_msg = str(e)
        if 'ffmpeg' in error_msg.lower() or 'postprocessor' in error_msg.lower():
            await message.answer(
                "❌ Ошибка: FFmpeg не найден!\n\n"
                "Для скачивания видео требуется FFmpeg.\n"
                "Установите: winget install ffmpeg"
            )
        else:
            await message.answer(f"❌ Ошибка: {e}")
        try:
            if os.path.exists(video_path):
                os.remove(video_path)
        except:
            pass


async def download_tiktok(message: types.Message, url: str):
    """TikTok - использует yt-dlp"""
    import tempfile
    import uuid
    await message.answer("⏳ Загрузка с TikTok...")
    
    temp_dir = tempfile.gettempdir()
    video_path = os.path.join(temp_dir, f"tiktok_{uuid.uuid4().hex}.mp4")
    
    # Пробуем найти FFmpeg
    ffmpeg_location = get_ffmpeg_location()
    
    try:
        from yt_dlp import YoutubeDL
        
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': video_path,
            'quiet': True,
            'no_warnings': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            },
            'extractor_retries': 3,
            'fragment_retries': 3,
        }
        
        # Добавляем FFmpeg если найден
        if ffmpeg_location:
            ydl_opts['ffmpeg_location'] = ffmpeg_location
        
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'TikTok Video')
        
        # Проверяем существование файла
        if os.path.exists(video_path):
            file_size = os.path.getsize(video_path)
            file_size_mb = file_size / (1024 * 1024)
            
            MAX_SIZE_MB = 50
            
            if file_size_mb > MAX_SIZE_MB:
                await message.answer(
                    f"⚠️ Видео слишком большое ({file_size_mb:.1f} MB)\n"
                    f"Лимит Telegram: {MAX_SIZE_MB} MB\n\n"
                    "Попробуйте более короткое видео"
                )
                os.remove(video_path)
                return
            
            await message.answer_video(
                types.FSInputFile(video_path),
                caption=f"🎬 {title}",
            )
            os.remove(video_path)
        else:
            await message.answer("❌ Не удалось загрузить видео")
            
    except Exception as e:
        error_msg = str(e)
        if 'ffmpeg' in error_msg.lower() or 'postprocessor' in error_msg.lower():
            await message.answer(
                "❌ Ошибка: FFmpeg не найден!\n\n"
                "Для загрузки видео требуется FFmpeg.\n"
                "Установите: winget install ffmpeg"
            )
        else:
            await message.answer(f"❌ Ошибка: {e}")
        try:
            if os.path.exists(video_path):
                os.remove(video_path)
        except:
            pass

# ==================== СТРУКТУРА ====================

async def cmd_structure(message: types.Message):
    """Структура файлов"""
    import tempfile
    import uuid
    try:
        result = subprocess.run(
            ["tree", "/F", "/A"],
            capture_output=True,
            text=True,
            shell=True
        )
        
        if result.returncode:
            output = result.stderr
        else:
            output = result.stdout
        
        temp_dir = tempfile.gettempdir()
        filename = f"structure_{uuid.uuid4().hex}.txt"
        filepath = os.path.join(temp_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"Структура файлов - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 50 + "\n\n")
            f.write(output)
        
        await message.answer_document(
            types.FSInputFile(filepath),
            caption="📁 **Структура файлов сохранена**"
        )
        
        os.remove(filepath)
        
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")



# ==================== УПРАВЛЕНИЕ БОТОМ ====================

async def cmd_shutdown_bot(message: types.Message):
    """Выключение бота"""
    from app.keyboards import shutdown_bot_keyboard
    keyboard = shutdown_bot_keyboard()
    
    await message.answer(
        "🛑 **Выключение бота**\n\n"
        "Вы уверены, что хотите выключить бота?",
        reply_markup=keyboard
    )

async def cmd_restart_bot(message: types.Message):
    """Перезагрузка бота"""
    keyboard = restart_bot_keyboard()
    
    await message.answer(
        "🔄 **Перезагрузка бота**\n\n"
        "Бот будет перезапущен через 3 секунды.",
        reply_markup=keyboard
    )

# ==================== АДМИНИСТРИРОВАНИЕ ====================

async def cmd_set_admin(message: types.Message):
    """Установить администратора"""
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    
    success = db.set_admin_id(user_id)
    
    if success:
        await message.answer(
            f"👤 **Администратор установлен**\n\n"
            f"🆔 ID: {user_id}\n"
            f"👤 Имя: {user_name}\n\n"
            f"Теперь только вы можете управлять ботом",
            reply_markup=main_keyboard(monitoring_manager['clipboard']['enabled'])
        )
    else:
        await message.answer("❌ Ошибка установки администратора")

async def cmd_check_admin(message: types.Message):
    """Проверить администратора"""
    admin_id = db.get_admin_id()
    
    if admin_id:
        current_user_id = message.from_user.id
        
        if current_user_id == admin_id:
            await message.answer(
                f"✅ **Вы администратор**\n\n"
                f"🆔 Ваш ID: {current_user_id}"
            )
        else:
            await message.answer(
                f"❌ **Доступ запрещен**\n\n"
                f"👤 Ваш ID: {current_user_id}\n"
                f"🔒 ID администратора: {admin_id}"
            )
    else:
        await message.answer(
            "ℹ️ **Администратор не установлен**\n\n"
            "Используйте /set_admin для установки администратора"
        )

async def cmd_test_monitoring(message: types.Message):
    """Тестировать мониторинг"""
    chat_id = message.chat.id
    
    monitoring_manager['clipboard']['target_chat_id'] = chat_id
    monitoring_manager['clipboard']['enabled'] = True
    
    db.save_monitoring_status('clipboard', True, chat_id)
    
    await message.answer(
        "🧪 **Тест мониторинга включен**\n\n"
        "Теперь скопируйте любой текст (Ctrl+C) и он появится здесь.\n\n"
        "Для отключения используйте кнопку в главном меню.",
        reply_markup=main_keyboard(True)
    )

# ==================== УТИЛИТЫ ====================

async def cmd_back(message: types.Message, state: FSMContext):
    """Назад"""
    await state.clear()
    await message.answer(
        "↩️ **Главное меню**",
        reply_markup=main_keyboard(monitoring_manager['clipboard']['enabled'])
    )

# ==================== НАСТРОЙКА ТОКЕНА ====================

async def cmd_set_token(message: types.Message, state: FSMContext):
    """Установить токен бота"""
    await state.set_state(TokenState.waiting_for_token)
    await message.answer(
        "🔑 **Установка токена бота**\n\n"
        "Введите токен вашего Telegram бота:\n"
        "(Получить токен можно у @BotFather)",
        reply_markup=types.ReplyKeyboardRemove()
    )

async def handle_set_token(message: types.Message, state: FSMContext):
    """Обработка ввода токена"""
    token = message.text.strip()
    
    if not token:
        await message.answer("❌ Токен не может быть пустым!")
        await state.clear()
        return
    
    if ':' not in token or len(token) < 30:
        await message.answer(
            "❌ **Неверный формат токена!**\n\n"
            "Токен должен содержать два числа, разделённых двоеточием:\n"
            "Пример: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`"
        )
        await state.clear()
        return
    
    try:
        db.set_bot_token(token)
        
        await message.answer(
            "✅ **Токен успешно установлен!**\n\n"
            "🔄 Перезапустите бота для применения изменений.\n"
            "Используйте команду /restart",
            reply_markup=main_keyboard(monitoring_manager['clipboard']['enabled'])
        )
        
        env_path = os.path.join(BASE_DIR, ".env")
        with open(env_path, 'a', encoding='utf-8') as f:
            f.write(f"\nBOT_TOKEN={token}")
        
    except Exception as e:
        await message.answer(f"❌ Ошибка сохранения токена: {e}")
    
    await state.clear()

# ==================== УВЕДОМЛЕНИЕ О ВКЛЮЧЕНИИ ====================

async def cmd_startup_notification(message: types.Message):
    """Уведомление о включении компьютера"""
    try:
        startup_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        notification_text = (
            f"🖥️ **Компьютер включен**\n\n"
            f"📅 Дата: {startup_time}\n"
            f"💻 Система: {platform.system()} {platform.release()}\n"
            f"👤 Пользователь: {os.getenv('USERNAME', 'Unknown')}"
        )
        
        await message.answer(notification_text, reply_markup=main_keyboard())
        db.add_clipboard(f"СИСТЕМА: Компьютер включен в {startup_time}", source='system')
        
    except Exception as e:
        await message.answer(f"❌ Ошибка отправки уведомления: {e}")

async def cmd_start_on_launch():
    """Уведомление при запуске бота (без message)"""
    try:
        from app.bot import bot_instance
        
        monitoring_status = db.load_monitoring_status('clipboard')
        monitoring_manager['clipboard']['enabled'] = monitoring_status['enabled']
        monitoring_manager['clipboard']['target_chat_id'] = monitoring_status['chat_id']
        
        # Отправляем сообщение если есть bot_instance
        if bot_instance:
            try:
                # Пробуем отправить админу
                admin_id = db.get_admin_id()
                if admin_id:
                    await bot_instance.send_message(
                        chat_id=int(admin_id),
                        text="🤖 Бот запущен!",
                        reply_markup=main_keyboard()
                    )
            except:
                pass
        
        db.add_clipboard(f"СИСТЕМА: Бот запущен", source='system')
        
    except Exception as e:
        print(f"Ошибка при запуске: {e}")

# ==================== СМЕНА ПАРОЛЯ WINDOWS ====================

async def cmd_change_password(message: types.Message, state: FSMContext):
    """Смена пароля Windows"""
    await state.set_state(NewPasswordState.waiting_new_password)
    await message.answer(
        "🔑 **Смена пароля Windows**\n\n"
        "Введите новый пароль:",
        reply_markup=types.ReplyKeyboardRemove()
    )

async def handle_new_password(message: types.Message, state: FSMContext):
    """Обработка нового пароля - сразу меняем"""
    current_state = await state.get_state()
    
    if current_state != NewPasswordState.waiting_new_password:
        return
    
    password = message.text.strip()
    
    if not password:
        await message.answer("❌ Пароль не может быть пустым!")
        await state.clear()
        return
    
    # Смена пароля Windows
    try:
        import os
        username = os.getenv('USERNAME')
        
        result = subprocess.run(
            f'net user "{username}" "{password}"',
            shell=True,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            await message.answer(
                "✅ **Пароль Windows изменён!**\n\n"
                f"Новый пароль для {username} установлен.",
                reply_markup=main_keyboard(monitoring_manager['clipboard']['enabled'])
            )
        else:
            await message.answer(
                f"❌ Ошибка: {result.stderr}",
                reply_markup=main_keyboard(monitoring_manager['clipboard']['enabled'])
            )
    except Exception as e:
        await message.answer(
            f"❌ Ошибка: {e}",
            reply_markup=main_keyboard(monitoring_manager['clipboard']['enabled'])
        )
    
    await state.clear()

async def handle_confirm_password(message: types.Message, state: FSMContext):
    """Устарело - больше не используется"""
    await state.clear()

# ==================== БЛОКИРОВКА ПРОГРАММ ====================

async def cmd_block_programs(message: types.Message):
    """Управление блокировкой программ"""
    from app.keyboards import block_programs_keyboard
    status = monitoring_manager['programs']['enabled']
    keyboard = block_programs_keyboard(enabled=status)
    
    status_text = "✅ ВКЛ" if status else "❌ ВЫКЛ"
    count = len(monitoring_manager['programs']['blocked_exes'])
    
    await message.answer(
        f"🚫 **Блокировка программ**\n\n"
        f"Мониторинг: {status_text}\n"
        f"Заблокировано: {count} exe\n\n"
        f"Выберите действие:",
        reply_markup=keyboard
    )

async def cmd_unblock_programs(message: types.Message):
    """Показать список заблокированных программ"""
    from app.keyboards import blocked_list_keyboard, block_programs_keyboard
    
    # Получаем заблокированные программы
    blocked = db.get_programs(include_blocked=True)
    blocked = [p for p in blocked if 'b' in p.get('type', '')]
    
    if blocked:
        keyboard = blocked_list_keyboard(blocked)
        await message.answer(
            "📋 **Заблокированные exe:**\n\nНажмите для разблокировки:",
            reply_markup=keyboard
        )
    else:
        await message.answer(
            "📋 Список заблокированных exe пуст",
            reply_markup=block_programs_keyboard()
        )

async def cmd_run_programs(message: types.Message):
    """Показать меню программ с избранным и кнопками управления"""
    from app.keyboards import programs_menu_with_favorites
    
    # Получаем программы
    programs = db.get_programs()
    
    # Показываем меню с избранным и кнопками управления
    if programs:
        text = (
            "🖥️ **ПРОГРАММЫ**\n\n"
            f"⭐ Избранных программ: {len(programs)}\n\n"
            "Нажмите на программу для запуска:\n"
            "или используйте кнопки ниже для управления"
        )
    else:
        text = (
            "🖥️ **ПРОГРАММЫ**\n\n"
            "Пока нет избранных программ.\n"
            "Добавьте программу или Steam игру!"
        )
    
    await message.answer(
        text,
        reply_markup=programs_menu_with_favorites(programs)
    )

async def add_blocked_exe(exe_name: str):
    """Добавить exe в список блокировки"""
    # Проверяем, не добавлен ли уже как программа
    all_programs = db.get_programs(include_blocked=True)
    for p in all_programs:
        if p['name'].lower() == exe_name.lower():
            return False  # Уже есть
    
    # Добавляем как заблокированную программу
    db.add_program(exe_name, path="", program_type="b")
    # Обновляем список в памяти
    monitoring_manager['programs']['blocked_exes'].append(exe_name)
    return True

async def remove_blocked_exe(exe_name: str):
    """Удалить exe из списка блокировки (снять флаг b)"""
    all_programs = db.get_programs(include_blocked=True)
    for p in all_programs:
        if p['name'].lower() == exe_name.lower() and 'b' in p.get('type', ''):
            # Снимаем флаг b (блокировка)
            db.toggle_program_blocked(p['id'])
            # Обновляем список в памяти
            monitoring_manager['programs']['blocked_exes'] = [e for e in monitoring_manager['programs']['blocked_exes'] if e.lower() != exe_name.lower()]
            return True
    return False

# Получаем заблокированные exe из базы данных при импорте
def get_blocked_exes_from_db():
    """Получить список заблокированных exe из базы данных"""
    all_programs = db.get_programs(include_blocked=True)
    return [p['name'] for p in all_programs if 'b' in p.get('type', '')]

# Загружаем заблокированные exe и статус мониторинга при импорте
try:
    monitoring_manager['programs']['blocked_exes'] = get_blocked_exes_from_db()
    # Загружаем статус мониторинга программ
    prog_status = db.load_monitoring_status('programs')
    monitoring_manager['programs']['enabled'] = prog_status.get('enabled', False)
except:
    pass

async def start_program_blocker(bot):
    """Запустить мониторинг программ"""
    monitoring_manager['programs']['enabled'] = True
    # Сохраняем статус в базу данных
    db.save_monitoring_status('programs', True)
    if monitoring_manager['programs']['task'] is None or monitoring_manager['programs']['task'].done():
        monitoring_manager['programs']['task'] = asyncio.create_task(monitor_blocked_programs(bot))

async def stop_program_blocker():
    """Остановить мониторинг программ"""
    monitoring_manager['programs']['enabled'] = False
    # Сохраняем статус в базу данных
    db.save_monitoring_status('programs', False)

# ==================== STEAM ИГРЫ ====================

async def handle_steam_game_input(message: types.Message, state: FSMContext):
    """Обработка ввода Steam игры"""
    from app.commands import AddSteamState
    
    current_state = await state.get_state()
    
    if current_state != AddSteamState.waiting_for_steam_game:
        return
    
    text = message.text.strip()
    
    if not text or ',' not in text:
        await message.answer(
            "❌ Неверный формат!\n\n"
            "Введите: Название, AppID"
        )
        await state.clear()
        return
    
    parts = text.split(',', 1)
    game_name = parts[0].strip()
    app_id = parts[1].strip()
    
    if not game_name or not app_id:
        await message.answer(
            "❌ Неверный формат!\n\n"
            "Введите: Название, AppID"
        )
        await state.clear()
        return
    
    # Проверяем, что AppID - число
    if not app_id.isdigit():
        await message.answer(
            "❌ AppID должен быть числом!\n\n"
            "Введите: Название, AppID"
        )
        await state.clear()
        return
    
    # Сохраняем игру в базу данных
    try:
        import subprocess
        # Добавляем игру как программу с типом steam
        db.add_program(game_name, path=app_id, program_type='steam')
        
        await message.answer(
            f"✅ **{game_name} добавлена в избранное!**\n\n"
            f"AppID: {app_id}"
        )
    except Exception as e:
        await message.answer(
            f"❌ Ошибка добавления игры: {e}"
        )
    
    await state.clear()

async def run_steam_game(app_id: str):
    """Запуск Steam игры по AppID"""
    try:
        subprocess.Popen(f'start "" "steam://run/{app_id}"')
        return True
    except Exception as e:
        print(f"Ошибка запуска Steam игры: {e}")
        return False

# ==================== ЗАМЕТКИ/ИДЕИ/ЗАДАЧИ ====================

async def cmd_notes(message: types.Message):
    """Показать список всех заметок"""
    try:
        notes = db.get_notes(include_completed=True)
        
        if not notes:
            await message.answer(
                "📝 **Мои заметки**\n\n"
                "Заметок пока нет.\n"
                "Используйте кнопки для добавления!\n\n"
                "Выберите действие:",
                reply_markup=notes_keyboard()
            )
            return
        
        # Разделяем идеи и задачи
        ideas = []
        tasks = []
        completed = []
        
        for note in notes:
            note_id, content, note_type, is_completed, timestamp = note
            item = f"{note_id}. {content}"
            
            if is_completed:
                completed.append(f"✅ {item}")
            elif note_type == 'task':
                tasks.append(f"⬜ {item}")
            else:
                ideas.append(f"💡 {item}")
        
        result = "📝 **Мои заметки**\n\n"
        
        if ideas:
            result += "💡 **Идеи:**\n" + "\n".join(ideas) + "\n\n"
        if tasks:
            result += "📋 **Задачи:**\n" + "\n".join(tasks) + "\n\n"
        if completed:
            result += "✅ **Выполнено:**\n" + "\n".join(completed)
        
        await message.answer(result, reply_markup=notes_keyboard())
        
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

async def cmd_show_ideas(message: types.Message):
    """Показать только идеи"""
    try:
        notes = db.get_notes(note_type='idea', include_completed=False)
        
        if not notes:
            await message.answer(
                "💡 **Идеи**\n\nИдей пока нет.\n\n"
                "Нажмите '➕ Новая идея' чтобы добавить!",
                reply_markup=main_keyboard(monitoring_manager['clipboard']['enabled'])
            )
            return
        
        text = "💡 **Мои идеи:**\n\n" + "\n".join([f"{n[0]}. {n[1]}" for n in notes])
        await message.answer(text, reply_markup=main_keyboard(monitoring_manager['clipboard']['enabled']))
        
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

async def cmd_show_tasks(message: types.Message):
    """Показать только задачи"""
    try:
        notes = db.get_notes(note_type='task', include_completed=False)
        
        if not notes:
            await message.answer(
                "📋 **Задачи**\n\nЗадач пока нет.\n\n"
                "Нажмите '➕ Новая задача' чтобы добавить!",
                reply_markup=main_keyboard(monitoring_manager['clipboard']['enabled'])
            )
            return
        
        text = "📋 **Мои задачи:**\n\n" + "\n".join([f"{n[0]}. {n[1]}" for n in notes])
        await message.answer(text, reply_markup=main_keyboard(monitoring_manager['clipboard']['enabled']))
        
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

async def cmd_add_task(message: types.Message, state: FSMContext):
    """Добавить задачу"""
    await state.set_state(NotesState.waiting_for_note)
    await state.update_data(note_type='task')
    await message.answer(
        "📋 **Новая задача**\n\nВведите текст задачи:",
        reply_markup=cancel_keyboard()
    )

async def cmd_add_idea(message: types.Message, state: FSMContext):
    """Добавить идею"""
    await state.set_state(NotesState.waiting_for_note)
    await state.update_data(note_type='idea')
    await message.answer(
        "💡 **Новая идея**\n\nВведите текст идеи:",
        reply_markup=cancel_keyboard()
    )

async def handle_note_input(message: types.Message, state: FSMContext):
    """Обработка ввода заметки"""
    current_state = await state.get_state()
    
    if current_state != NotesState.waiting_for_note:
        return
    
    text = message.text.strip()
    
    if text.lower() == "отмена":
        await state.clear()
        await message.answer("❌ Отменено", reply_markup=main_keyboard(monitoring_manager['clipboard']['enabled']))
        return
    
    if not text:
        await message.answer("❌ Заметка не может быть пустой!")
        return
    
    # Получаем тип из state
    state_data = await state.get_data()
    note_type = state_data.get('note_type', 'idea')
    
    # Если тип указан в тексте, переопределяем
    if text.lower().startswith('задача:'):
        note_type = 'task'
        text = text[7:].strip()
    elif text.lower().startswith('идея:'):
        note_type = 'idea'
        text = text[5:].strip()
    elif text.lower().startswith('напоминание:'):
        note_type = 'reminder'
        text = text[11:].strip()
    
    if not text:
        await message.answer("❌ Текст заметки не может быть пустым!")
        return
    
    try:
        db.add_note(text, note_type)
        
        type_text = {
            'idea': '💡 Идея',
            'task': '📋 Задача',
            'reminder': '🔔 Напоминание'
        }.get(note_type, '📝 Заметка')
        
        await message.answer(
            f"✅ **{type_text} добавлена!**\n\n{text}",
            reply_markup=main_keyboard(monitoring_manager['clipboard']['enabled'])
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
    
    await state.clear()

async def toggle_note_callback(callback: types.CallbackQuery):
    """Переключить статус выполнения заметки"""
    try:
        note_id = int(callback.data.replace('note_toggle_', ''))
        db.toggle_note_completed(note_id)
        await callback.message.edit_reply_markup(None)
        await cmd_notes(callback.message)
    except Exception as e:
        await callback.answer(f"Ошибка: {e}")

async def delete_note_callback(callback: types.CallbackQuery):
    """Удалить заметку"""
    try:
        note_id = int(callback.data.replace('note_delete_', ''))
        db.delete_note(note_id)
        await callback.answer("Заметка удалена ✅")
        await cmd_notes(callback.message)
    except Exception as e:
        await callback.answer(f"Ошибка: {e}")

async def clear_completed_callback(callback: types.CallbackQuery):
    """Очистить выполненные заметки"""
    try:
        count = db.clear_completed_notes()
        await callback.answer(f"Удалено {count} заметок")
        await cmd_notes(callback.message)
    except Exception as e:
        await callback.answer(f"Ошибка: {e}")


async def cmd_hybrid_sleep(message: types.Message):
    """Гибридный сон"""
    try:
        # Включаем гибернацию для гибридного сна
        subprocess.run("powercfg /hibernate on", shell=True)
        
        # Используем ctypes для перехода в гибридный сон
        # Гибридный сон = сон + сохранение в файл гибернации
        try:
            import ctypes
            # SetSuspendState(Hibernate=1, ForceCritical=0, DisableWakeEvent=0)
            # Hibernate=1 включает гибридный режим
            result = ctypes.windll.PowrProf.SetSuspendState(1, 0, 0)
            
            if result:
                await message.answer("🔋 Переход в гибридный сон...", reply_markup=main_keyboard())
            else:
                # Метод 2: через subprocess
                subprocess.run("rundll32.exe powrprof.dll,SetSuspendState", shell=True)
                await message.answer("🔋 Переход в гибридный сон...", reply_markup=main_keyboard())
                
        except Exception as e:
            # Метод 2: через subprocess
            subprocess.run("rundll32.exe powrprof.dll,SetSuspendState", shell=True)
            await message.answer("🔋 Переход в гибридный сон...", reply_markup=main_keyboard())
            
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
