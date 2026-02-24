from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def main_keyboard(monitoring=False):
    """Главное меню"""
    monitor_text = "Выключить отслеживание 🛑" if monitoring else "Включить отслеживание 🔍"
    
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Скриншот📸"), KeyboardButton(text="Уведомление📝")],
            [KeyboardButton(text="Буфер обмена📋"), KeyboardButton(text="Добавить в буфер📥"), KeyboardButton(text=monitor_text)],
            [KeyboardButton(text="Процессы⚙️"), KeyboardButton(text="Программы🖥️")],
            [KeyboardButton(text="Скачать📥"), KeyboardButton(text="Команды⚡")],
            [KeyboardButton(text="Предыдущий ⏮️"), KeyboardButton(text="Пауза ⏯️"), KeyboardButton(text="Следующий ⏭️")],
            [KeyboardButton(text="Тише 🔉"), KeyboardButton(text="Громче 🔊"), KeyboardButton(text="Выкл звук 🔇")],
            [KeyboardButton(text="📋 Задачи"), KeyboardButton(text="➕ Новая задача"), KeyboardButton(text="➕ Новая идея"), KeyboardButton(text="💡 Идеи")],
            [KeyboardButton(text="Система🖥️"), KeyboardButton(text="🚫 Блокировка программ")],
            [KeyboardButton(text="Выключить компьютер🔴"), KeyboardButton(text="Перезагрузить ПК🔄"), KeyboardButton(text="Сон💤"), KeyboardButton(text="Заблокировать🔒")],
            [KeyboardButton(text="Сменить пароль🔑")],
            [KeyboardButton(text="Выкл бота🛑"), KeyboardButton(text="Перезапустить бота🔄"), KeyboardButton(text="Структура📁")]
        ],
        resize_keyboard=True
    )

def confirm_keyboard(confirm_callback, cancel_callback, confirm_text="✅ Да", cancel_text="❌ Отмена"):
    """Универсальная клавиатура подтверждения"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=confirm_text, callback_data=confirm_callback),
                InlineKeyboardButton(text=cancel_text, callback_data=cancel_callback)
            ]
        ]
    )

def shutdown_keyboard():
    return confirm_keyboard("shutdown_confirm", "shutdown_cancel", "✅ Да, выключить", "❌ Отмена")

def restart_pc_keyboard():
    return confirm_keyboard("restart_pc_confirm", "restart_pc_cancel", "✅ Да, перезагрузить", "❌ Отмена")

def shutdown_bot_keyboard():
    return confirm_keyboard("bot_shutdown_confirm", "bot_shutdown_cancel", "✅ Да, выключить", "❌ Отмена")

def restart_bot_keyboard():
    return confirm_keyboard("restart_confirm", "restart_cancel", "🔄 Да, перезагрузить", "❌ Отмена")

def system_menu_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🖥️ Полная сводка", callback_data="system_all")],
            [InlineKeyboardButton(text="⚙️ CPU", callback_data="system_cpu")],
            [InlineKeyboardButton(text="🧠 RAM", callback_data="system_ram")],
            [InlineKeyboardButton(text="💾 Диски", callback_data="system_disk")],
            [InlineKeyboardButton(text="🌐 Сеть", callback_data="system_network")],
            [InlineKeyboardButton(text="🎮 GPU", callback_data="system_gpu")],
            [InlineKeyboardButton(text="🖥️ ОС", callback_data="system_os")]
        ]
    )

def programs_menu_keyboard():
    """Главное меню программ - с избранным и кнопками управления (Inline)"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🖥️ Избранное", callback_data="programs_favorites")],
            [InlineKeyboardButton(text="➕ Добавить программу", callback_data="programs_add")],
            [InlineKeyboardButton(text="🎮 Добавить Steam игру", callback_data="programs_add_steam")],
            [InlineKeyboardButton(text="🗑️ Удалить программу", callback_data="programs_delete_select")]
        ]
    )

def programs_menu_with_favorites(programs):
    """Меню программ с избранными и кнопками управления (Inline)"""
    keyboard = []
    
    # Добавляем избранные программы если есть
    if programs:
        for prog in programs:
            icon = "🎮" if 'steam' in prog.get('type', '') else "🖥️"
            btn_text = f"{icon} {prog['name']}"
            if len(btn_text) > 30:
                btn_text = btn_text[:27] + "..."
            keyboard.append([InlineKeyboardButton(text=btn_text, callback_data=f"run_{prog['id']}")])
    
    # Кнопки управления
    keyboard.append([InlineKeyboardButton(text="➕ Добавить программу", callback_data="programs_add")])
    keyboard.append([InlineKeyboardButton(text="🎮 Добавить Steam игру", callback_data="programs_add_steam")])
    keyboard.append([InlineKeyboardButton(text="🗑️ Удалить программу", callback_data="programs_delete_select")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def favorites_with_buttons_keyboard(programs):
    """Клавиатура избранного с кнопками программ для запуска (ReplyKeyboardMarkup)"""
    keyboard = []
    
    # Добавляем программы кнопками
    for prog in programs:
        icon = "🎮" if 'steam' in prog.get('type', '') else "🖥️"
        btn_text = f"{icon} {prog['name']}"
        if len(btn_text) > 40:
            btn_text = btn_text[:37] + "..."
        keyboard.append([KeyboardButton(text=btn_text)])
    
    # Кнопки управления
    keyboard.append([KeyboardButton(text="➕ Добавить программу"), KeyboardButton(text="🎮 Добавить Steam игру")])
    keyboard.append([KeyboardButton(text="🗑️ Удалить программу")])
    
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def all_programs_keyboard(programs):
    """Клавиатура запуска программ - упрощённая версия"""
    keyboard = []
    
    # Если есть программы, показываем их
    if programs:
        # Группируем по типу: Steam игры и обычные программы
        steam_games = []
        regular_programs = []
        
        for prog in programs:
            if 'steam' in prog.get('type', ''):
                steam_games.append(prog)
            else:
                regular_programs.append(prog)
        
        # Сначала Steam игры
        for prog in steam_games:
            btn_text = f"🎮 {prog['name']}"
            if len(btn_text) > 40:
                btn_text = btn_text[:37] + "..."
            keyboard.append([
                InlineKeyboardButton(text=btn_text, callback_data=f"run_{prog['id']}")
            ])
        
        # Потом обычные программы
        for prog in regular_programs:
            btn_text = f"🖥️ {prog['name']}"
            if len(btn_text) > 40:
                btn_text = btn_text[:37] + "..."
            keyboard.append([
                InlineKeyboardButton(text=btn_text, callback_data=f"run_{prog['id']}")
            ])
    
    # Кнопки управления - показываем всегда
    keyboard.append([
        InlineKeyboardButton(text="➕ Добавить", callback_data="programs_add"),
        InlineKeyboardButton(text="🗑️ Удалить", callback_data="programs_delete_select")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def favorites_keyboard(programs):
    """Клавиатура избранного - теперь просто список программ"""
    keyboard = []
    for prog in programs:
        icon = "🎮" if 'steam' in prog.get('type', '') else "🖥️"
        btn_text = f"{icon} {prog['name']}"
        if len(btn_text) > 40:
            btn_text = btn_text[:37] + "..."
        keyboard.append([InlineKeyboardButton(text=btn_text, callback_data=f"run_{prog['id']}")])
    
    if not programs:
        keyboard.append([InlineKeyboardButton(text="ℹ️ Нет доступных программ", callback_data="programs_no_fav")])
    
    keyboard.append([
        InlineKeyboardButton(text="📁 Все программы", callback_data="programs_all")
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def programs_list_keyboard(programs, view_type):
    """Универсальная клавиатура списка программ"""
    keyboard = []
    
    # Группируем по типу
    steam_games = []
    regular_programs = []
    
    for prog in programs:
        if 'steam' in prog.get('type', ''):
            steam_games.append(prog)
        else:
            regular_programs.append(prog)
    
    # Steam игры
    for i, prog in enumerate(steam_games[:8], 1):
        btn_text = f"🎮 {prog['name']}"
        if len(btn_text) > 40:
            btn_text = btn_text[:37] + "..."
        keyboard.append([InlineKeyboardButton(text=f"{i}. {btn_text}", callback_data=f"run_{prog['id']}")])
    
    # Обычные программы
    start_num = len(steam_games) + 1
    for i, prog in enumerate(regular_programs[:8], start_num):
        btn_text = f"🖥️ {prog['name']}"
        if len(btn_text) > 40:
            btn_text = btn_text[:37] + "..."
        keyboard.append([InlineKeyboardButton(text=f"{i}. {btn_text}", callback_data=f"run_{prog['id']}")])
    
    if view_type == "commands":
        keyboard.append([InlineKeyboardButton(text="➕ Добавить команду", callback_data="programs_add_command")])
    else:
        keyboard.append([
            InlineKeyboardButton(text="➕ Добавить", callback_data="programs_add"),
            InlineKeyboardButton(text="🗑️ Удалить", callback_data="programs_delete_select")
        ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def delete_program_keyboard(programs):
    keyboard = []
    for prog in programs:
        icon = "🎮" if 'steam' in prog.get('type', '') else "🖥️"
        btn_text = f"{icon} {prog['name']}"
        if len(btn_text) > 40:
            btn_text = btn_text[:37] + "..."
        keyboard.append([InlineKeyboardButton(text=f"❌ {btn_text}", callback_data=f"program_delete_{prog['id']}")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def sleep_menu_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💤 Обычный сон")],
            [KeyboardButton(text="🔋 Гибридный сон")],
            [KeyboardButton(text="🛌 Гибернация")],
            [KeyboardButton(text="🖥️ Выключить монитор"), KeyboardButton(text="📱 Включить монитор")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def process_keyboard(pid, process_name):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔼 На передний план", callback_data=f"front_{pid}_{process_name}")],
            [InlineKeyboardButton(text="❌ Завершить", callback_data=f"kill_{pid}_{process_name}")]
        ]
    )

def block_programs_keyboard(enabled=False):
    """Клавиатура блокировки программ с переключателем"""
    toggle_text = "⏹️ Выключить мониторинг" if enabled else "▶️ Включить мониторинг"
    toggle_callback = "block_stop" if enabled else "block_start"
    
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить exe", callback_data="block_add_exe")],
            [InlineKeyboardButton(text="📋 Список заблокированных", callback_data="block_list")],
            [InlineKeyboardButton(text=toggle_text, callback_data=toggle_callback)]
        ]
    )

def blocked_list_keyboard(programs):
    """Клавиатура списка заблокированных программ с кнопками разблокировки"""
    keyboard = []
    for prog in programs:
        keyboard.append([
            InlineKeyboardButton(text=f"🔓 {prog['name']}", callback_data=f"unblock_{prog['id']}")
        ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def cancel_keyboard():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Отмена")]], resize_keyboard=True)

def video_menu_keyboard():
    """Меню управления видео"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎬 Страшилка 1", callback_data="video_play_1")],
            [InlineKeyboardButton(text="🎬 Страшилка 2", callback_data="video_play_2")],
            [InlineKeyboardButton(text="⏹️ Остановить видео", callback_data="video_stop")]
        ]
    )

def video_control_keyboard():
    """Клавиатура управления видеоплеером с паузой"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⏮️ Предыдущее", callback_data="video_prev"), InlineKeyboardButton(text="⏸️ Пауза", callback_data="video_pause"), InlineKeyboardButton(text="⏭️ Следующее", callback_data="video_next")],
            [InlineKeyboardButton(text="⏹️ Стоп", callback_data="video_stop"), InlineKeyboardButton(text="▶️ Продолжить", callback_data="video_resume")],
            [InlineKeyboardButton(text="🔊 Громкость +", callback_data="volume_up"), InlineKeyboardButton(text="🔉 Громкость -", callback_data="volume_down")]
        ]
    )

def volume_keyboard():
    """Клавиатура управления громкостью"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Предыдущий ⏮️"), KeyboardButton(text="Пауза ⏯️"), KeyboardButton(text="Следующий ⏭️")],
            [KeyboardButton(text="Тише 🔉"), KeyboardButton(text="Громче 🔊"), KeyboardButton(text="Выкл звук 🔇")]
        ],
        resize_keyboard=True
    )

def notes_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💡 Все идеи", callback_data="notes_ideas")],
            [InlineKeyboardButton(text="📋 Все задачи", callback_data="notes_tasks")],
            [InlineKeyboardButton(text="✅ Выполненные", callback_data="notes_completed")],
            [InlineKeyboardButton(text="🗑️ Очистить выполненные", callback_data="notes_clear")]
        ]
    )

def processes_keyboard(processes, page=0, per_page=16):
    keyboard = []
    start_idx = page * per_page
    end_idx = start_idx + per_page
    page_processes = processes[start_idx:end_idx]
    
    for i in range(0, len(page_processes), 4):
        row = []
        for j in range(4):
            idx = i + j
            if idx < len(page_processes):
                pid, name = page_processes[idx]
                btn_number = start_idx + idx + 1
                full_name = name[:-4] if name.lower().endswith('.exe') else name
                button_text = f"#{btn_number} {full_name}"
                if len(button_text) > 60:
                    button_text = button_text[:57] + "..."
                row.append(InlineKeyboardButton(text=button_text, callback_data=f"process_{pid}"))
        if row:
            keyboard.append(row)
    
    total_pages = (len(processes) + per_page - 1) // per_page
    pagination_row = []
    if total_pages > 1:
        if page > 0:
            pagination_row.append(InlineKeyboardButton(text="⬅️", callback_data=f"processes_page_{page-1}"))
        pagination_row.append(InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="processes_info"))
        if page < total_pages - 1:
            pagination_row.append(InlineKeyboardButton(text="➡️", callback_data=f"processes_page_{page+1}"))
    if pagination_row:
        keyboard.append(pagination_row)
    keyboard.append([InlineKeyboardButton(text="🔄 Обновить", callback_data="processes_refresh")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# Клавиатуры удалены - навигация через главное меню
