from aiogram import F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.commands import *
from app.database import db
from app.keyboards import *

async def handle_video_buttons(message: types.Message):
    """Управление медиаплеером - простой способ через pyautogui"""
    import pyautogui
    
    if message.text == "Предыдущий ⏮️":
        pyautogui.press('prevtrack')
        await message.answer("⏮️ Предыдущий трек")
    
    elif message.text == "Пауза ⏯️":
        pyautogui.press('playpause')
        await message.answer("⏯️ Пауза/Продолжить")
    
    elif message.text == "Следующий ⏭️":
        pyautogui.press('nexttrack')
        await message.answer("⏭️ Следующий трек")
    
    elif message.text == "Тише 🔉":
        pyautogui.press('volumedown')
        await message.answer("🔉 Тише")
    
    elif message.text == "Громче 🔊":
        pyautogui.press('volumeup')
        await message.answer("🔊 Громче")
    
    elif message.text == "Выкл звук 🔇":
        pyautogui.press('volumemute')
        await message.answer("🔇 Выкл звук")


def register_handlers(dp):
    """Регистрация всех обработчиков"""
    
    # ==================== COMMAND HANDLERS (должны быть первыми!) ====================
    dp.message.register(cmd_test_monitoring, Command("test_monitor"))
    dp.message.register(cmd_change_password, Command("password"))
    dp.message.register(cmd_check_admin, Command("check_admin"))
    dp.message.register(cmd_screenshot, Command("screenshot"))
    dp.message.register(cmd_set_admin, Command("set_admin"))
    dp.message.register(cmd_clipboard, Command("clipboard"))
    dp.message.register(cmd_processes, Command("processes"))
    dp.message.register(cmd_set_token, Command("set_token"))
    dp.message.register(cmd_download,  Command("download"))
    dp.message.register(cmd_shutdown,  Command("shutdown"))
    dp.message.register(cmd_sleep_menu,Command("sleep"))
    dp.message.register(cmd_restart, Command("restart"))
    dp.message.register(cmd_start, Command("start"))
    dp.message.register(cmd_notes, Command("notes"))
    dp.message.register(cmd_lock, Command("lock"))
    
    # ==================== CALLBACK HANDLERS ====================
    dp.message.register(cmd_block_programs, Command("block"))
    dp.message.register(cmd_unblock_programs, Command("unblock"))
    dp.message.register(cmd_run_programs, Command("run"))
    dp.callback_query.register(handle_process_callback, F.data.startswith(("process_", "kill_", "front_", "processes_")))
    dp.callback_query.register(handle_programs_callback, F.data.startswith(("run_", "toggle_fav_", "toggle_block_", "programs_", "program_delete_")))
    dp.callback_query.register(handle_block_running_callback, F.data.startswith("block_running_"))
    dp.callback_query.register(handle_block_programs_callback, F.data.startswith(("block_", "block_programs_", "unblock_")))
    dp.callback_query.register(handle_bot_shutdown_callback, F.data.startswith("bot_shutdown_"))
    dp.callback_query.register(handle_shutdown_callback, F.data.startswith("shutdown_"))
    dp.callback_query.register(handle_restart_callback, F.data.startswith("restart_"))
    dp.callback_query.register(handle_system_callback, F.data.startswith("system_"))
    dp.callback_query.register(handle_notes_callback, F.data.startswith("notes_"))
    dp.callback_query.register(handle_video_callback, F.data.startswith("video_"))
    dp.callback_query.register(handle_autoclicker_callback, F.data.startswith("autoclick_"))
    
    # Автокликер - текстовый ввод
    from app.commands import AutoClickerState, handle_autoclicker_input
    dp.message.register(handle_autoclicker_input, AutoClickerState.waiting_for_coords)
    dp.message.register(handle_autoclicker_input, AutoClickerState.waiting_for_clicks)
    
    # ==================== TEXT MESSAGE HANDLERS ====================
    dp.message.register(cmd_download, F.text == "Скачать 📥")
    dp.message.register(handle_download_link, DownloadState.waiting_for_link)
    dp.message.register(cmd_shutdown, F.text == "Выключить 🔴")
    dp.message.register(cmd_monitor_off, F.text == "Выключить монитор 🖥️")
    dp.message.register(cmd_set_clipboard, F.text == "Добавить в буфер 📥")
    dp.message.register(cmd_monitor_on, F.text == "Включить монитор 📱")
    dp.message.register(cmd_hybrid_sleep, F.text == "Гибридный сон 🔋")
    dp.message.register(cmd_lock, F.text == "Заблокировать 🔒")
    dp.message.register(cmd_restart_pc, F.text == "Перезагрузить 🔄")
    dp.message.register(cmd_shutdown_bot, F.text == "Выкл бота 🛑")
    dp.message.register(cmd_structure, F.text == "Структура 📁")
    dp.message.register(cmd_clipboard, F.text == "Буфер обмена 📋")
    dp.message.register(cmd_notify, F.text == "Уведомление 📝")
    dp.message.register(cmd_sleep_menu, F.text == "Сон 💤")
    dp.message.register(cmd_hibernate, F.text == "Гибернация 🛌")
    dp.message.register(cmd_processes, F.text == "Процессы ⚙️")
    dp.message.register(cmd_run_programs, F.text == "Программы 🖥️")
    dp.message.register(cmd_system_menu, F.text == "Система 🖥️")
    dp.message.register(cmd_back, F.text == "Назад ↩️")
    dp.message.register(cmd_monitor_on, F.text == "Включить монитор 📱")
    dp.message.register(cmd_restart_bot, F.text == "Перезапустить 🔄")
    dp.message.register(cmd_screenshot, F.text == "Скриншот 📸")
    dp.message.register(cmd_commands, F.text == "Команды ⚡")
    dp.message.register(cmd_change_password, F.text == "Сменить пароль 🔑")
    dp.message.register(toggle_monitoring, F.text == "Включить отслеживание 🔍")
    dp.message.register(toggle_monitoring, F.text == "Выключить отслеживание 🛑")
    
    # Обработчики кнопок меню программ
    dp.message.register(cmd_favorites, F.text == "Избранное 🖥️")
    dp.message.register(handle_add_program_button, F.text == "Добавить программу ➕")
    dp.message.register(handle_add_steam_button, F.text == "Добавить Steam игру 🎮")
    dp.message.register(handle_delete_program_button, F.text == "Удалить программу 🗑️")
    
    # Обработчики кнопок
    dp.message.register(cmd_favorites, F.text == "Добавить избранное ➕")
    dp.message.register(cmd_block_programs, F.text == "Блокировка программ 🚫")
    dp.message.register(cmd_notes, F.text == "Мои заметки 📝")
    
    # Автокликер
    from app.commands import cmd_autoclicker
    dp.message.register(cmd_autoclicker, F.text == "Автокликер 🖱️")
    dp.message.register(cmd_show_ideas, F.text == "Идеи 💡")
    dp.message.register(cmd_show_tasks, F.text == "Задачи 📋")
    dp.message.register(cmd_add_task, F.text == "Новая задача ➕")
    dp.message.register(cmd_add_idea, F.text == "Новая идея ➕")
    dp.message.register(cmd_video_menu, F.text == "Видео 🎬")
    dp.message.register(cmd_video_menu, F.text == "Видео плеер 🎬")
    dp.message.register(handle_video_buttons, F.text == "Предыдущий ⏮️")
    dp.message.register(handle_video_buttons, F.text == "Пауза ⏯️")
    dp.message.register(handle_video_buttons, F.text == "Следующий ⏭️")
    dp.message.register(handle_video_buttons, F.text == "Громче 🔊")
    dp.message.register(handle_video_buttons, F.text == "Тише 🔉")
    # Новые кнопки
    dp.message.register(handle_video_buttons, F.text == "Предыдущий ⏮️")
    dp.message.register(handle_video_buttons, F.text == "Пауза ⏯️")
    dp.message.register(handle_video_buttons, F.text == "Следующий ⏭️")
    dp.message.register(handle_video_buttons, F.text == "Тише 🔉")
    dp.message.register(handle_video_buttons, F.text == "Громче 🔊")
    dp.message.register(handle_video_buttons, F.text == "Выкл звук 🔇")

    

    
    # ==================== COMMAND HANDLERS ====================
    dp.message.register(cmd_start, Command("start"))
    dp.message.register(cmd_shutdown, Command("shutdown"))
    dp.message.register(cmd_restart, Command("restart"))
    dp.message.register(cmd_lock, Command("lock"))
    dp.message.register(cmd_download, Command("download"))
    dp.message.register(cmd_set_admin, Command("set_admin"))
    dp.message.register(cmd_check_admin, Command("check_admin"))
    dp.message.register(cmd_test_monitoring, Command("test_monitor"))
    dp.message.register(cmd_sleep_menu, Command("sleep"))
    dp.message.register(cmd_set_token, Command("set_token"))
    dp.message.register(cmd_notes, Command("notes"))
    dp.message.register(cmd_screenshot, Command("screenshot"))
    dp.message.register(cmd_clipboard, Command("clipboard"))
    dp.message.register(cmd_processes, Command("processes"))
    dp.message.register(cmd_change_password, Command("password"))
    
    # ==================== STATE HANDLERS ====================
    dp.message.register(handle_notification, NotificationState.waiting_for_text)
    dp.message.register(handle_set_clipboard, ClipboardState.waiting_for_clipboard_text)
    dp.message.register(handle_set_token, TokenState.waiting_for_token)
    dp.message.register(handle_new_password, NewPasswordState.waiting_new_password)
    dp.message.register(handle_block_exe_input, BlockExeState.waiting_for_exe_name)
    dp.message.register(handle_steam_game_input, AddSteamState.waiting_for_steam_game)
    dp.message.register(handle_note_input, NotesState.waiting_for_note)
    
    # Дополнительные состояния
    dp.message.register(handle_add_program_input, AddProgramState.waiting_for_program)
    
    # Обработка запуска программ по кнопке из избранного
    dp.message.register(handle_run_program_from_button)

# ==================== CALLBACK HANDLERS ====================

async def handle_process_callback(callback: types.CallbackQuery):
    """Обработка колбэков процессов"""
    data = callback.data
    
    if data.startswith("kill_"):
        parts = data.split("_")
        if len(parts) >= 3:
            pid = int(parts[1])
            process_name = "_".join(parts[2:])
            
            try:
                import psutil
                proc = psutil.Process(pid)
                proc.terminate()
                await callback.answer(f"Процесс {process_name} завершен")
                await cmd_processes(callback.message)
            except Exception as e:
                await callback.answer(f"Ошибка завершения процесса: {e}")
    
    elif data.startswith("front_"):
        parts = data.split("_")
        if len(parts) >= 3:
            pid = int(parts[1])
            process_name = "_".join(parts[2:])
            
            try:
                if bring_to_front(pid):
                    await callback.answer(f"Процесс {process_name} выведен на передний план")
                else:
                    await callback.answer("Не удалось вывести процесс на передний план")
            except Exception as e:
                await callback.answer(f"Ошибка вывода процесса: {e}")
    
    elif data.startswith("process_"):
        # Показать информацию о процессе или меню действий
        parts = data.split("_")
        if len(parts) >= 2:
            pid = int(parts[1])
            process_name = "_".join(parts[2:]) if len(parts) > 2 else ""
            
            keyboard = process_keyboard(pid, process_name)
            await callback.message.edit_text(
                f"⚙️ **Процесс:** {process_name}\n🆔 PID: {pid}",
                reply_markup=keyboard
            )
            await callback.answer()
    
    elif data.startswith("processes_"):
        if data == "processes_refresh":
            await cmd_processes(callback.message)
            await callback.answer("Список процессов обновлен")
        elif data.startswith("processes_page_"):
            page = int(data.split("_")[-1])
            try:
                # Получаем список процессов заново
                import psutil
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
                
                keyboard = processes_keyboard(processes, page)
                await callback.message.edit_text(
                    f"⚙️ **Активные процессы (страница {page + 1}):**\n\n"
                    f"Всего: {len(processes)} процессов",
                    reply_markup=keyboard
                )
            except Exception as e:
                await callback.answer(f"Ошибка: {e}")
        else:
            await callback.answer("Действие с процессами")
    
    else:
        await callback.answer("Обработка процесса")

async def handle_programs_callback(callback: types.CallbackQuery, state: FSMContext):
    """Обработка колбэков программ"""
    data = callback.data
    
    try:
        if data.startswith("run_"):
            program_id = int(data.split("_")[1])
            try:
                success = await run_program(program_id, callback.message)
                if success:
                    await callback.answer("Программа запущена")
                    await callback.message.edit_text("✅ Программа запущена")
                else:
                    await callback.answer("Ошибка запуска программы")
            except Exception as e:
                await callback.answer(f"Ошибка: {e}")
        
        elif data.startswith("toggle_block_"):
            parts = data.split("_")
            view_type = parts[2]
            program_id = int(parts[3])
            
            try:
                db.toggle_program_blocked(program_id)
                await callback.answer("Блокировка переключена")
                if view_type == "favorites":
                    programs = db.get_programs()
                    keyboard = programs_list_keyboard(programs, "favorites")
                    await callback.message.edit_text("🖥️ **Доступные программы:**", reply_markup=keyboard)
                elif view_type == "blocked":
                    programs = db.get_programs(include_blocked=True)
                    programs = [p for p in programs if 'b' in p.get('type', '')]
                    keyboard = programs_list_keyboard(programs, "blocked")
                    await callback.message.edit_text("🚫 **Заблокированные программы:**", reply_markup=keyboard)
            except Exception as e:
                await callback.answer(f"Ошибка: {e}")
        
        elif data == "programs_favorites":
            # Показываем все доступные программы (без заблокированных)
            programs = db.get_programs()
            if programs:
                keyboard = favorites_keyboard(programs)
                await callback.message.edit_text("🖥️ **Доступные программы:**", reply_markup=keyboard)
            else:
                await callback.message.edit_text(
                    "🖥️ **Программы:**\n\n"
                    "Программ пока нет.\n"
                    "Нажмите '➕ Добавить' для добавления.",
                    reply_markup=programs_menu_keyboard()
                )
                await callback.answer()
        
        elif data == "programs_all":
            programs = db.get_programs()
            if programs:
                keyboard = all_programs_keyboard(programs)
                await callback.message.edit_text(
                    "🖥️ **Все программы:**\n\n"
                    f"Всего: {len(programs)} программ",
                    reply_markup=keyboard
                )
            else:
                await callback.message.edit_text(
                    "🖥️ **Программы:**\n\n"
                    "Программ пока нет.\n"
                    "Нажмите '➕ Добавить' для добавления.",
                    reply_markup=programs_menu_keyboard()
                )
            await callback.answer()
        
        elif data.startswith("toggle_fav_"):
            # Убираем функционал избранного - просто показываем сообщение
            await callback.answer("Избранное больше не используется")
            
            # Обновляем список
            all_programs = db.get_programs()
            keyboard = all_programs_keyboard(all_programs)
            await callback.message.edit_text(
                "🖥️ **Все программы:**\n\n"
                f"Всего: {len(all_programs)} программ",
                reply_markup=keyboard
            )
        
        elif data == "programs_back" or data == "programs_menu":
            try:
                await callback.message.edit_text(
                    "🖥️ **Управление программами:**", 
                    reply_markup=programs_menu_keyboard()
                )
            except:
                await callback.message.answer(
                    "🖥️ **Управление программами:**", 
                    reply_markup=programs_menu_keyboard()
                )
        
        elif data == "programs_add":
            await state.set_state(AddProgramState.waiting_for_program)
            await callback.message.edit_text(
                "➕ **Добавить программу:**\n\n"
                "Введите название и путь через запятую"
            )
            await callback.answer()
        
        elif data == "programs_add_steam":
            from app.commands import AddSteamState
            await state.set_state(AddSteamState.waiting_for_steam_game)
            await callback.message.edit_text(
                "🎮 **Добавить Steam игру:**\n\n"
                "Введите: Название, AppID"
            )
            await callback.answer()
        
        elif data == "programs_delete_select":
            programs = db.get_programs()
            if programs:
                keyboard = delete_program_keyboard(programs)
                await callback.message.edit_text(
                    "🗑️ **Удалить программу:**\n\n"
                    "Нажмите на программу для удаления",
                    reply_markup=keyboard
                )
            else:
                await callback.message.edit_text(
                    "🗑️ **Удалить программу:**\n\n"
                    "Нет программ для удаления",
                    reply_markup=programs_menu_keyboard()
                )
            await callback.answer()
        
        elif data.startswith("program_delete_"):
            program_id = int(data.split("_")[-1])
            try:
                db.delete_program(program_id)
                await callback.answer("Программа удалена")
                # Показываем список программ после удаления
                programs = db.get_programs()
                if programs:
                    keyboard = delete_program_keyboard(programs)
                    await callback.message.edit_text(
                        "🗑️ **Удалить программу:**\n\n"
                        "Нажмите на программу для удаления",
                        reply_markup=keyboard
                    )
                else:
                    await callback.message.edit_text(
                        "🗑️ **Удалить программу:**\n\n"
                        "Нет программ для удаления",
                        reply_markup=programs_menu_keyboard()
                    )
            except Exception as e:
                await callback.answer(f"Ошибка: {e}")
        
        else:
            await callback.answer("Действие с программами")
            
    except Exception as e:
        await callback.answer(f"Ошибка: {e}", show_alert=True)

async def handle_block_running_callback(callback: types.CallbackQuery):
    """Обработка блокировки запущенных программ"""
    await callback.answer("Блокировка запущенных программ")

async def handle_bot_shutdown_callback(callback: types.CallbackQuery):
    """Обработка выключения бота"""
    if callback.data == "bot_shutdown_confirm":
        await callback.message.edit_text("🛑 Бот выключается...")
        # Даем время отправить сообщение
        import asyncio
        await asyncio.sleep(0.5)
        # Принудительное завершение
        import os
        os._exit(0)
    elif callback.data == "bot_shutdown_cancel":
        await callback.message.edit_text("❌ Выключение отменено")
    else:
        await callback.answer("Действие с ботом")

async def handle_shutdown_callback(callback: types.CallbackQuery):
    """Обработка выключения компьютера"""
    if callback.data == "shutdown_confirm":
        await callback.message.edit_text("🔴 Компьютер выключается...")
        import subprocess
        subprocess.run("shutdown /s /t 3", shell=True)
    elif callback.data == "shutdown_cancel":
        await callback.message.edit_text("❌ Выключение отменено")
    else:
        await callback.answer("Действие выключения")

async def handle_restart_callback(callback: types.CallbackQuery):
    """Обработка перезагрузки"""
    if callback.data == "restart_confirm":
        await callback.message.edit_text("🔄 Компьютер перезагружается...")
        import subprocess
        subprocess.run("shutdown /r /t 3", shell=True)
    elif callback.data == "restart_cancel":
        await callback.message.edit_text("❌ Перезагрузка отменена")
    elif callback.data == "restart_pc_confirm":
        await callback.message.edit_text("🔄 Компьютер перезагружается...")
        import subprocess
        subprocess.run("shutdown /r /t 3", shell=True)
    elif callback.data == "restart_pc_cancel":
        await callback.message.edit_text("❌ Перезагрузка отменена")
    else:
        await callback.answer("Действие перезагрузки")

async def handle_system_callback(callback: types.CallbackQuery):
    """Обработка системных колбэков"""
    from app.commands import (
        show_full_system_info, show_detailed_cpu, show_detailed_ram,
        show_detailed_disk, show_detailed_network, show_detailed_gpu, show_detailed_os
    )
    
    data = callback.data
    
    if data == "system_all":
        await show_full_system_info(callback.message)
    elif data == "system_cpu":
        await show_detailed_cpu(callback.message)
    elif data == "system_ram":
        await show_detailed_ram(callback.message)
    elif data == "system_disk":
        await show_detailed_disk(callback.message)
    elif data == "system_network":
        await show_detailed_network(callback.message)
    elif data == "system_gpu":
        await show_detailed_gpu(callback.message)
    elif data == "system_os":
        await show_detailed_os(callback.message)
    
    await callback.answer()

async def handle_block_exe_input(message: types.Message, state: FSMContext):
    """Обработка ввода имени exe для блокировки"""
    from app.commands import BlockExeState, add_blocked_exe, monitoring_manager
    
    current_state = await state.get_state()
    
    if current_state != BlockExeState.waiting_for_exe_name:
        return
    
    exe_name = message.text.strip()
    
    if not exe_name:
        await message.answer("❌ Имя exe не может быть пустым!")
        return
    
    # Добавляем .exe если нет
    if not exe_name.lower().endswith('.exe'):
        exe_name = exe_name + ".exe"
    
    success = await add_blocked_exe(exe_name)
    
    if success:
        await message.answer(
            f"✅ **{exe_name} добавлен в список блокировки!**",
            reply_markup=main_keyboard(monitoring_manager['clipboard']['enabled'])
        )
    else:
        await message.answer(
            f"⚠️ {exe_name} уже в списке блокировки!",
            reply_markup=main_keyboard(monitoring_manager['clipboard']['enabled'])
        )
    
    await state.clear()


async def handle_block_programs_callback(callback: types.CallbackQuery, state: FSMContext):
    """Обработка колбэков блокировки программ"""
    from app.bot import bot_instance
    from app.commands import BlockExeState
    
    data = callback.data
    
    if data == "block_add_exe":
        await state.set_state(BlockExeState.waiting_for_exe_name)
        await callback.message.edit_text(
            "Введи название exe (например chrome.exe)"
        )
        await callback.answer()
    
    elif data == "block_list":
        blocked = db.get_programs(include_blocked=True)
        blocked = [p for p in blocked if 'b' in p.get('type', '')]
        if blocked:
            keyboard = blocked_list_keyboard(blocked)
            await callback.message.edit_text(
                "Список:",
                reply_markup=keyboard
            )
        else:
            await callback.message.edit_text(
                "Пусто",
                reply_markup=block_programs_keyboard()
            )
        await callback.answer()
    
    elif data.startswith("unblock_"):
        program_id = int(data.split("_")[1])
        try:
            # Получаем имя программы перед разблокировкой
            all_programs = db.get_programs(include_blocked=True)
            prog_name = ""
            for p in all_programs:
                if p['id'] == program_id and 'b' in p.get('type', ''):
                    prog_name = p['name']
                    break
            
            # Снимаем флаг b (разблокировка)
            db.toggle_program_blocked(program_id)
            
            # Обновляем список в памяти
            from app.commands import get_blocked_exes_from_db, monitoring_manager
            monitoring_manager['programs']['blocked_exes'] = get_blocked_exes_from_db()
            
            await callback.answer(f"{prog_name} разблокирован")
            
            # Показываем обновленный список
            blocked = db.get_programs(include_blocked=True)
            blocked = [p for p in blocked if 'b' in p.get('type', '')]
            if blocked:
                keyboard = blocked_list_keyboard(blocked)
                await callback.message.edit_text(
                    "Список:",
                    reply_markup=keyboard
                )
            else:
                await callback.message.edit_text(
                    "Пусто",
                    reply_markup=block_programs_keyboard()
                )
        except Exception as e:
            await callback.answer(f"Ошибка: {e}")
    
    elif data == "block_start":
        from app.commands import monitoring_manager, start_program_blocker
        await start_program_blocker(bot_instance)
        await callback.answer("Включено")
        status = monitoring_manager['programs']['enabled']
        count = len(monitoring_manager['programs']['blocked_exes'])
        keyboard = block_programs_keyboard(enabled=status)
        await callback.message.edit_text(
            f"Мониторинг: вкл\n"
            f"Заблокировано: {count}",
            reply_markup=keyboard
        )
    
    elif data == "block_stop":
        from app.commands import monitoring_manager, stop_program_blocker
        await stop_program_blocker()
        await callback.answer("Выключено")
        status = monitoring_manager['programs']['enabled']
        count = len(monitoring_manager['programs']['blocked_exes'])
        keyboard = block_programs_keyboard(enabled=status)
        await callback.message.edit_text(
            f"Мониторинг: выкл\n"
            f"Заблокировано: {count}",
            reply_markup=keyboard
        )
    
    elif data == "block_back":
        from app.commands import monitoring_manager
        await callback.message.edit_text(
            "Назад",
            reply_markup=main_keyboard(monitoring_manager['clipboard']['enabled'])
        )
        await callback.answer()
    
    else:
        await callback.answer("Блокировка программ")

async def handle_notes_callback(callback: types.CallbackQuery, state: FSMContext):
    """Обработка колбэков заметок"""
    from app.commands import NotesState, cmd_notes
    
    data = callback.data
    
    if data == "notes_add":
        await state.set_state(NotesState.waiting_for_note)
        await callback.message.edit_text(
            "📝 **Добавить заметку:**\n\n"
            "Введите текст:\n"
            "• Просто текст = идея\n"
            "• задача: текст = задача\n"
            "• идея: текст = идея\n"
            "• напоминание: текст = напоминание"
        )
        await callback.answer()
    
    elif data == "notes_ideas":
        notes = db.get_notes(note_type='idea', include_completed=False)
        if notes:
            text = "💡 **Идеи:**\n\n" + "\n".join([f"{n[0]}. {n[1]}" for n in notes])
        else:
            text = "💡 Идей пока нет"
        await callback.message.edit_text(
            text
        )
        await callback.answer()
    
    elif data == "notes_tasks":
        notes = db.get_notes(note_type='task', include_completed=False)
        if notes:
            text = "📋 **Задачи:**\n\n" + "\n".join([f"{n[0]}. {n[1]}" for n in notes])
        else:
            text = "📋 Задач пока нет"
        await callback.message.edit_text(
            text
        )
        await callback.answer()
    
    elif data == "notes_completed":
        notes = db.get_notes(include_completed=True)
        completed = [n for n in notes if n[3]]
        if completed:
            text = "✅ **Выполненные:**\n\n" + "\n".join([f"{n[0]}. {n[1]}" for n in completed])
        else:
            text = "✅ Нет выполненных задач"
        await callback.message.edit_text(
            text
        )
        await callback.answer()
    
    elif data == "notes_clear":
        count = db.clear_completed_notes()
        await callback.answer(f"Удалено {count} заметок")
        await cmd_notes(callback.message)
    
    elif data == "notes_back":
        await callback.message.edit_text(
            "↩️ Возврат в главное меню",
            reply_markup=main_keyboard(monitoring_manager['clipboard']['enabled'])
        )
        await callback.answer()
    
    elif data.startswith("note_toggle_"):
        try:
            note_id = int(data.replace("note_toggle_", ""))
            db.toggle_note_completed(note_id)
            await callback.answer("Статус изменён")
            await cmd_notes(callback.message)
        except Exception as e:
            await callback.answer(f"Ошибка: {e}")
    
    elif data.startswith("note_delete_"):
        try:
            note_id = int(data.replace("note_delete_", ""))
            db.delete_note(note_id)
            await callback.answer("Заметка удалена")
            await cmd_notes(callback.message)
        except Exception as e:
            await callback.answer(f"Ошибка: {e}")
    
    else:
        await callback.answer("Заметки")


# ==================== ВИДЕО КОНТРОЛЬ ====================

async def handle_video_callback(callback: types.CallbackQuery):
    """Обработка колбэков видео"""
    from app.commands import play_video_file, stop_video, pause_video, resume_video, video_process, volume_up, volume_down, volume_mute, play_next_video, play_prev_video, get_video_list, current_video_index, BASE_DIR
    import os
    
    # Пробуем разные пути для видео
    possible_video_dirs = [
        os.path.join(BASE_DIR, "assets", "screamers"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "screamers"),
    ]
    
    video_dir = None
    for vdir in possible_video_dirs:
        if os.path.exists(vdir):
            video_dir = vdir
            break
    
    data = callback.data
    
    if data.startswith("video_play_"):
        video_num = data.split("_")[-1]
        if video_dir:
            video_path = os.path.join(video_dir, f"{video_num}.mp4")
        else:
            video_path = os.path.join(BASE_DIR, "assets", "screamers", f"{video_num}.mp4")
        
        if os.path.exists(video_path):
            success = play_video_file(video_path)
            if success:
                # Сохраняем индекс видео
                videos = get_video_list()
                for i, v in enumerate(videos):
                    if v == video_path:
                        current_video_index['index'] = i
                        current_video_index['videos'] = videos
                        break
                await callback.answer("▶️ Видео запущено")
                await callback.message.edit_text(
                    "🎬 Видео воспроизводится\n\n"
                    "Управление:",
                    reply_markup=video_control_keyboard()
                )
            else:
                await callback.answer("❌ Ошибка запуска видео")
        else:
            await callback.answer("❌ Видео файл не найден")
    
    elif data == "video_next":
        success = play_next_video()
        if success:
            await callback.answer("⏭️ Следующее видео")
            await callback.message.edit_text(
                "🎬 Следующее видео\n\n"
                "Управление:",
                reply_markup=video_control_keyboard()
            )
        else:
            await callback.answer("❌ Нет следующего видео")
    
    elif data == "video_prev":
        success = play_prev_video()
        if success:
            await callback.answer("⏮️ Предыдущее видео")
            await callback.message.edit_text(
                "🎬 Предыдущее видео\n\n"
                "Управление:",
                reply_markup=video_control_keyboard()
            )
        else:
            await callback.answer("❌ Нет предыдущего видео")
    
    elif data == "video_pause":
        success = pause_video()
        if success:
            await callback.answer("⏸️ Видео приостановлено")
        else:
            await callback.answer("❌ Не удалось приостановить")
    
    elif data == "video_resume":
        success = resume_video()
        if success:
            await callback.answer("▶️ Видео продолжается")
        else:
            await callback.answer("❌ Не удалось продолжить (перезапустите видео)")
    
    elif data == "video_stop":
        success = stop_video()
        await callback.answer("⏹️ Видео остановлено")
        await callback.message.edit_text(
            "⏹️ Видео остановлено",
            reply_markup=video_menu_keyboard()
        )
    
    elif data == "volume_up":
        volume_up()
        await callback.answer("🔊 Громкость увеличена")
    
    elif data == "volume_down":
        volume_down()
        await callback.answer("🔉 Громкость уменьшена")
    
    elif data == "volume_mute":
        volume_mute()
        await callback.answer("🔇 Звук выключен")
    
    elif data.startswith("volume_"):
        # Обработка установки конкретной громкости
        try:
            level = int(data.split("_")[1])
            await callback.answer(f"🔊 Громкость установлена на {level}%")
        except:
            await callback.answer("Ошибка установки громкости")
    
    else:
        await callback.answer("Видео")


# ==================== ДОПОЛНИТЕЛЬНЫЕ СОСТОЯНИЯ ====================

class AddProgramState(StatesGroup):
    waiting_for_program = State()


async def handle_add_program_input(message: types.Message, state: FSMContext):
    """Обработка ввода программы для добавления"""
    current_state = await state.get_state()
    
    if current_state != AddProgramState.waiting_for_program:
        return
    
    text = message.text.strip()
    
    if not text or ',' not in text:
        await message.answer(
            "❌ Неверный формат!\n\n"
            "Введите: Название, Путь"
        )
        await state.clear()
        return
    
    parts = text.split(',', 1)
    name = parts[0].strip()
    path = parts[1].strip() if len(parts) > 1 else ''
    
    if not name:
        await message.answer("❌ Название не может быть пустым!")
        await state.clear()
        return
    
    try:
        db.add_program(name, path=path, program_type='app')
        await message.answer(
            f"✅ **{name} добавлен в программы!**"
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка добавления: {e}")
    
    await state.clear()


async def handle_add_program_button(message: types.Message, state: FSMContext):
    """Обработка кнопки 'Добавить программу'"""
    from app.commands import AddProgramState
    await state.set_state(AddProgramState.waiting_for_program)
    await message.answer(
        "➕ **Добавить программу:**\n\n"
        "Введите название и путь к программе через запятую:\n"
        "Например: Блокнот, C:\\Windows\\notepad.exe"
    )


async def handle_add_steam_button(message: types.Message, state: FSMContext):
    """Обработка кнопки 'Добавить Steam игру'"""
    from app.commands import AddSteamState
    await state.set_state(AddSteamState.waiting_for_steam_game)
    await message.answer(
        "🎮 **Добавить Steam игру:**\n\n"
        "Введите название игры и AppID через запятую:\n"
        "Например: Dota 2, 570"
    )


async def handle_delete_program_button(message: types.Message):
    """Обработка кнопки 'Удалить программу' - показывает список для удаления"""
    from app.keyboards import delete_program_keyboard, programs_menu_keyboard
    
    programs = db.get_programs()
    if programs:
        await message.answer(
            "🗑️ **Удалить программу:**\n\n"
            "Нажмите на программу для удаления:",
            reply_markup=delete_program_keyboard(programs)
        )
    else:
        await message.answer(
            "🗑️ **Удалить программу:**\n\n"
            "Нет программ для удаления.",
            reply_markup=programs_menu_keyboard()
        )


async def handle_run_program_from_button(message: types.Message, state: FSMContext):
    """Обработка запуска программы по кнопке из избранного"""
    from app.commands import run_program
    from app.keyboards import favorites_with_buttons_keyboard, programs_menu_keyboard
    
    # Проверяем, что мы не в состоянии ввода
    current_state = await state.get_state()
    if current_state is not None:
        return
    
    # Получаем текст кнопки
    btn_text = message.text.strip()
    
    # Убираем иконку в начале
    if btn_text.startswith("🖥️ ") or btn_text.startswith("🎮 "):
        program_name = btn_text[2:].strip()
    else:
        return
    
    # Ищем программу в базе по имени
    programs = db.get_programs()
    for prog in programs:
        if prog['name'] == program_name:
            # Запускаем программу
            success = await run_program(prog['id'], message)
            programs = db.get_programs()
            if success:
                await message.answer(
                    f"✅ **{prog['name']} запущена!**",
                    reply_markup=favorites_with_buttons_keyboard(programs)
                )
            else:
                await message.answer(
                    f"❌ Не удалось запустить {prog['name']}",
                    reply_markup=favorites_with_buttons_keyboard(programs)
                )
            return
    
    # Программа не найдена
    await message.answer(
        f"❌ Программа '{program_name}' не найдена",
        reply_markup=programs_menu_keyboard()
    )


