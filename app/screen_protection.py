"""
Защита экрана от скриншотов
"""
import time
import threading
import subprocess
import ctypes
import ctypes.wintypes

SM_CXSCREEN = 0
SM_CYSCREEN = 1
HWND_TOPMOST = -1
SWP_SHOWWINDOW = 0x0040

black_screen_active = False
black_window_handle = None
user32 = None


class RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                 ("right", ctypes.c_long), ("bottom", ctypes.c_long)]


def wnd_proc(hwnd, msg, wparam, lparam):
    return ctypes.windll.user32.DefWindowProcW(hwnd, msg, wparam, lparam)


def create_black_window():
    """Создать черное окно поверх всех окон"""
    global black_screen_active, black_window_handle
    
    try:
        global user32
        user32 = ctypes.windll.user32
        
        width = user32.GetSystemMetrics(SM_CXSCREEN)
        height = user32.GetSystemMetrics(SM_CYSCREEN)
        
        wc = ctypes.wintypes.WNDCLASSEXW()
        wc.cbSize = ctypes.sizeof(ctypes.wintypes.WNDCLASSEXW)
        wc.lpfnWndProc = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_int, ctypes.c_uint, ctypes.c_int, ctypes.c_int)(wnd_proc)
        wc.hInstance = user32.GetModuleHandleW(None)
        wc.lpszClassName = "BlackScreenClass"
        wc.hbrBackground = ctypes.windll.gdi32.GetStockObject(0)
        wc.hCursor = None
        
        user32.RegisterClassExW(ctypes.byref(wc))
        
        hwnd = user32.CreateWindowExW(
            0x80 | 0x08, "BlackScreenClass", "",
            0x80000000 | 0x40000000 | 0x02000000,
            0, 0, width, height, None, None,
            user32.GetModuleHandleW(None), None
        )
        
        if not hwnd:
            return False
        
        black_window_handle = hwnd
        user32.ShowWindow(hwnd, 5)
        user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_SHOWWINDOW)
        user32.SetForegroundWindow(hwnd)
        black_screen_active = True
        return True
        
    except:
        return False


def close_black_window():
    """Закрыть черное окно"""
    global black_screen_active, black_window_handle
    
    try:
        if black_window_handle:
            user32.DestroyWindow(black_window_handle)
            black_window_handle = None
        black_screen_active = False
    except:
        pass


def show_black_screen():
    """Показать черное окно вместо скриншота"""
    global black_screen_active
    
    if not black_screen_active:
        threading.Thread(target=create_black_window, daemon=True).start()
        threading.Timer(0.3, close_black_window).start()


class ScreenProtector:
    def __init__(self):
        self.protection_active = False
        self.protection_thread = None
        self.screenshot_allowed = False
    
    def start_protection(self):
        if self.protection_active:
            return
        self.protection_active = True
        self.protection_thread = threading.Thread(target=self._protection_loop, daemon=True)
        self.protection_thread.start()
    
    def stop_protection(self):
        self.protection_active = False
    
    def _protection_loop(self):
        suspicious_names = ['teamviewer.exe', 'anydesk.exe', 'ammyy.exe', 'supremo.exe',
                          'screenrecorder.exe', 'snagit.exe', 'obs.exe', 'bandicam.exe',
                          'rdpclip.exe', 'mstsc.exe', 'vnc.exe']
        
        while self.protection_active:
            try:
                # CREATE_NO_WINDOW = 0x08000000 - скрывает консольное окно
                result = subprocess.run(['tasklist', '/fo', 'csv'], capture_output=True, text=True, creationflags=0x08000000)
                for line in result.stdout.split('\n'):
                    for name in suspicious_names:
                        if name.lower() in line.lower():
                            ctypes.windll.user32.LockWorkStation()
                            break
                time.sleep(1)
            except:
                time.sleep(5)


screen_protector = ScreenProtector()


def start_screen_protection():
    screen_protector.start_protection()


def stop_screen_protection():
    screen_protector.stop_protection()


def allow_screenshot():
    screen_protector.screenshot_allowed = True
    threading.Timer(1.0, lambda: setattr(screen_protector, 'screenshot_allowed', False)).start()
