import sqlite3
import json
from datetime import datetime
from app.config import config

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(config.DATABASE_PATH, check_same_thread=False)
        self.init_tables()
    
    def init_tables(self):
        """Инициализация таблиц"""
        cursor = self.conn.cursor()
        
        # Таблица настроек
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        # Таблица буфера обмена
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clipboard (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                source TEXT DEFAULT 'manual'
            )
        ''')
        
        # Таблица программ (id, name, path, type с флагами: f-favourite, b-blocked)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS programs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                path TEXT,
                type TEXT DEFAULT ''
            )
        ''')
        
        # Таблица заметок/идей/задач
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                note_type TEXT DEFAULT 'idea',
                completed BOOLEAN DEFAULT 0,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()
        
        # Миграция: перенос blocked_exes из settings в programs
        self.migrate_blocked_exes()
    
    def migrate_blocked_exes(self):
        """Миграция: перенос blocked_exes из settings в programs (новая структура)"""
        blocked_list = self.load_blocked_exes()
        if blocked_list:
            cursor = self.conn.cursor()
            for exe_name in blocked_list:
                # Проверяем, не добавлен ли уже
                cursor.execute('SELECT id, type FROM programs WHERE name = ?', (exe_name,))
                result = cursor.fetchone()
                if result:
                    # Добавляем флаг b если его нет
                    prog_id, prog_type = result
                    if 'b' not in prog_type:
                        new_type = prog_type + 'b' if prog_type else 'b'
                        cursor.execute('UPDATE programs SET type = ? WHERE id = ?', (new_type, prog_id))
                else:
                    # Добавляем как заблокированную программу
                    cursor.execute('INSERT INTO programs (name, path, type) VALUES (?, ?, ?)', (exe_name, '', 'b'))
            self.conn.commit()
            # Удаляем старые данные из settings
            cursor.execute('DELETE FROM settings WHERE key = ?', ('blocked_exes',))
            self.conn.commit()
    
    def get_setting(self, key):
        """Получить настройку"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
        result = cursor.fetchone()
        return result[0] if result else None
    
    def set_setting(self, key, value):
        """Установить настройку"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)
        ''', (key, value))
        self.conn.commit()
    
    def get_bot_token(self):
        """Получить токен бота"""
        return self.get_setting('bot_token') or config.BOT_TOKEN
    
    def set_bot_token(self, token):
        """Установить токен бота"""
        return self.set_setting('bot_token', token)
    
    def get_admin_id(self):
        """Получить ID администратора"""
        admin_id = self.get_setting('admin_id')
        return int(admin_id) if admin_id else None
    
    def set_admin_id(self, admin_id):
        """Установить ID администратора"""
        return self.set_setting('admin_id', str(admin_id))
    
    def add_clipboard(self, content, source='manual'):
        """Добавить запись в буфер обмена"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO clipboard (content, source) VALUES (?, ?)
        ''', (content, source))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_clipboard_history(self, limit=50):
        """Получить историю буфера обмена"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT content, timestamp, source FROM clipboard 
            ORDER BY timestamp DESC LIMIT ?
        ''', (limit,))
        return cursor.fetchall()
    
    def save_monitoring_status(self, monitor_type, enabled, chat_id=None):
        """Сохранить статус мониторинга"""
        data = {
            'enabled': enabled,
            'chat_id': chat_id,
            'updated_at': datetime.now().isoformat()
        }
        self.set_setting(f'monitoring_{monitor_type}', json.dumps(data))
    
    def load_monitoring_status(self, monitor_type):
        """Загрузить статус мониторинга"""
        data = self.get_setting(f'monitoring_{monitor_type}')
        if data:
            try:
                parsed = json.loads(data)
                return {
                    'enabled': parsed.get('enabled', False),
                    'chat_id': parsed.get('chat_id')
                }
            except:
                pass
        return {'enabled': False, 'chat_id': None}
    
    def save_blocked_exes(self, blocked_list):
        """Сохранить список заблокированных exe"""
        self.set_setting('blocked_exes', json.dumps(blocked_list))
    
    def load_blocked_exes(self):
        """Загрузить список заблокированных exe"""
        data = self.get_setting('blocked_exes')
        if data:
            try:
                return json.loads(data)
            except:
                pass
        return []
    
    def add_program(self, name, path=None, program_type=''):
        """Добавить программу (type - флаги: f-favourite, b-blocked)"""
        cursor = self.conn.cursor()
        cursor.execute('INSERT INTO programs (name, path, type) VALUES (?, ?, ?)', (name, path, program_type))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_programs(self, program_type=None, include_blocked=False):
        """Получить программы (по умолчанию скрыты заблокированные и locked)"""
        query = "SELECT id, name, path, type FROM programs"
        conditions = []
        params = []
        
        if program_type:
            conditions.append("type LIKE ?")
            params.append(f'%{program_type}%')
        
        # По умолчанию исключаем заблокированные (b) и locked (l) программы
        if not include_blocked:
            conditions.append("(type IS NULL OR (type NOT LIKE '%b%' AND type NOT LIKE '%l%'))")
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        
        programs = []
        for row in cursor.fetchall():
            prog_type = row[3] or ''
            programs.append({
                'id': row[0],
                'name': row[1],
                'path': row[2],
                'type': prog_type
            })
        return programs
    
    def delete_program(self, program_id):
        """Удалить программу"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM programs WHERE id = ?', (program_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def toggle_program_favorite(self, program_id):
        """Переключить избранное (флаг f)"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT type FROM programs WHERE id = ?', (program_id,))
        result = cursor.fetchone()
        if result:
            prog_type = result[0] or ''
            if 'f' in prog_type:
                new_type = prog_type.replace('f', '')
            else:
                new_type = prog_type + 'f'
            cursor.execute('UPDATE programs SET type = ? WHERE id = ?', (new_type, program_id))
            self.conn.commit()
            return True
        return False
    
    def toggle_program_blocked(self, program_id):
        """Переключить блокировку (флаг b)"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT type FROM programs WHERE id = ?', (program_id,))
        result = cursor.fetchone()
        if result:
            prog_type = result[0] or ''
            if 'b' in prog_type:
                new_type = prog_type.replace('b', '')
            else:
                new_type = prog_type + 'b'
            cursor.execute('UPDATE programs SET type = ? WHERE id = ?', (new_type, program_id))
            self.conn.commit()
            return True
        return False
    
    # ==================== ЗАМЕТКИ ====================
    
    def add_note(self, content, note_type='idea'):
        """Добавить заметку/идею/задачу"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO notes (content, note_type) VALUES (?, ?)
        ''', (content, note_type))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_notes(self, note_type=None, include_completed=True):
        """Получить все заметки"""
        cursor = self.conn.cursor()
        
        query = 'SELECT id, content, note_type, completed, timestamp FROM notes'
        conditions = []
        params = []
        
        if note_type:
            conditions.append('note_type = ?')
            params.append(note_type)
        
        if not include_completed:
            conditions.append('completed = 0')
        
        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
        
        query += ' ORDER BY completed ASC, timestamp DESC'
        
        cursor.execute(query, params)
        return cursor.fetchall()
    
    def toggle_note_completed(self, note_id):
        """Переключить статус выполнения заметки"""
        cursor = self.conn.cursor()
        cursor.execute('UPDATE notes SET completed = NOT completed WHERE id = ?', (note_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def delete_note(self, note_id):
        """Удалить заметку"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM notes WHERE id = ?', (note_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def clear_completed_notes(self):
        """Удалить все выполненные заметки"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM notes WHERE completed = 1')
        self.conn.commit()
        return cursor.rowcount
    
    def set_password(self, password):
        """Установить пароль"""
        import hashlib
        hashed = hashlib.sha256(password.encode()).hexdigest()
        return self.set_setting('password', hashed)
    
    def get_password(self):
        """Получить хеш пароля"""
        return self.get_setting('password')
    
    def reset_password(self):
        """Сбросить пароль"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM settings WHERE key = ?', ('password',))
        self.conn.commit()
    
    def close(self):
        """Закрыть соединение"""
        self.conn.close()

# Глобальный экземпляр
db = Database()
