"""
database.py — СЛОЙ ДАННЫХ (самый нижний слой программы).

Простыми словами: этот файл — "кладовщик". Он один умеет разговаривать
с базой данных SQLite на языке SQL. Остальные части программы SQL не знают,
они просто просят: "сохрани студента", "дай список", "удали запись".

Здесь НЕТ проверок вроде "оценка от 2 до 5" — это работа файла services.py.
Здесь НЕТ print() и input() — это работа файла ui.py.
"""

import os
import sqlite3

# Файл базы данных лежит в той же папке, что и программа.
# os.path.abspath(__file__) — полный путь к этому файлу,
# os.path.dirname(...)      — папка, в которой он лежит.
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "students.db")

# Общая часть запроса "студент + его средний балл".
# LEFT JOIN нужен, чтобы в список попали и студенты БЕЗ оценок
# (обычный JOIN таких студентов просто выбросил бы).
SELECT_STUDENTS = """
    SELECT s.id,
           s.full_name,
           s.group_name,
           s.record_book,
           ROUND(AVG(g.grade), 2) AS avg_grade,      -- средний балл
           COUNT(g.id)            AS grades_count    -- сколько оценок
    FROM students AS s
    LEFT JOIN grades AS g ON g.student_id = s.id
"""


def _to_lower(text):
    """Переводит текст в нижний регистр: 'ИВАНОВ' -> 'иванов'.

    Зачем это нужно: встроенная в SQLite функция LOWER() понимает только
    английские буквы. Чтобы поиск "иванов" находил "Иванов", мы даём
    базе данных свою функцию, написанную на Python.
    """
    if text is None:
        return None
    return str(text).lower()


class Database:
    """Класс для работы с базой данных. Один объект = одно подключение."""

    def __init__(self, db_path=DB_PATH):
        # Подключаемся к файлу базы. Если файла нет — SQLite создаст его сам.
        self.conn = sqlite3.connect(db_path)

        # Row позволяет обращаться к столбцам по имени: row["full_name"],
        # а не по номеру row[1]. Так код легче читать.
        self.conn.row_factory = sqlite3.Row

        # Включаем проверку связей между таблицами (внешние ключи).
        # В SQLite она по умолчанию выключена, без неё не сработает
        # автоматическое удаление оценок вместе со студентом.
        self.conn.execute("PRAGMA foreign_keys = ON")

        # Регистрируем нашу функцию под именем py_lower —
        # теперь её можно вызывать прямо внутри SQL-запросов.
        self.conn.create_function("py_lower", 1, _to_lower)

        # Создаём таблицы, если программа запущена в первый раз.
        self.create_tables()

    # ------------------------------------------------------------------
    # Создание таблиц
    # ------------------------------------------------------------------
    def create_tables(self):
        """Создаёт две таблицы: students (студенты) и grades (оценки)."""

        # Таблица студентов.
        # id          — уникальный номер, база выдаёт его сама (AUTOINCREMENT)
        # NOT NULL    — поле обязательно для заполнения
        # UNIQUE      — у двух студентов не может быть одинаковой зачётки
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name   TEXT NOT NULL,
                group_name  TEXT NOT NULL,
                record_book TEXT NOT NULL UNIQUE
            )
        """)

        # Таблица оценок.
        # student_id  — к какому студенту относится оценка (связь "один ко многим":
        #               у одного студента много оценок)
        # ON DELETE CASCADE — если удалить студента, его оценки удалятся сами
        # CHECK       — база сама не пропустит оценку вне диапазона 2..5
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS grades (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                subject    TEXT    NOT NULL,
                grade      INTEGER NOT NULL CHECK (grade BETWEEN 2 AND 5),
                grade_date TEXT    NOT NULL,
                FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE
            )
        """)

        # commit() — "сохранить изменения на диск".
        self.conn.commit()

    # ------------------------------------------------------------------
    # Студенты
    # ------------------------------------------------------------------
    def insert_student(self, full_name, group_name, record_book):
        """Добавляет студента и возвращает его новый ID."""
        # Знаки вопроса — это "места для подстановки". Мы НЕ склеиваем
        # текст запроса из строк пользователя, а передаём значения отдельно.
        # Так нельзя сломать базу хитрым вводом (защита от SQL-инъекций).
        cursor = self.conn.execute(
            "INSERT INTO students (full_name, group_name, record_book) VALUES (?, ?, ?)",
            (full_name, group_name, record_book),
        )
        self.conn.commit()
        return cursor.lastrowid  # ID только что добавленной строки

    def get_all_students(self):
        """Возвращает список всех студентов со средним баллом."""
        sql = SELECT_STUDENTS + " GROUP BY s.id ORDER BY s.group_name, s.full_name"
        return self.conn.execute(sql).fetchall()

    def find_students(self, text):
        """Ищет студентов, у которых ФИО, группа или номер зачётки содержат text."""
        # instr(строка, кусок) возвращает позицию куска в строке или 0, если его нет.
        # И строку из базы, и текст поиска приводим к нижнему регистру,
        # поэтому "ИВАН", "иван" и "Иван" ищутся одинаково.
        sql = SELECT_STUDENTS + """
            WHERE instr(py_lower(s.full_name),   ?) > 0
               OR instr(py_lower(s.group_name),  ?) > 0
               OR instr(py_lower(s.record_book), ?) > 0
            GROUP BY s.id
            ORDER BY s.group_name, s.full_name
        """
        text = text.lower()
        return self.conn.execute(sql, (text, text, text)).fetchall()

    def get_student(self, student_id):
        """Возвращает одного студента по ID или None, если такого нет."""
        sql = SELECT_STUDENTS + " WHERE s.id = ? GROUP BY s.id"
        return self.conn.execute(sql, (student_id,)).fetchone()

    def record_book_exists(self, record_book, except_id=None):
        """Проверяет, занят ли номер зачётки другим студентом.

        except_id — ID студента, которого не надо учитывать. Нужно при
        редактировании: свой собственный номер зачётки "занятым" не считается.
        """
        row = self.conn.execute(
            "SELECT id FROM students WHERE record_book = ?", (record_book,)
        ).fetchone()
        if row is None:
            return False            # такого номера в базе нет
        return row["id"] != except_id

    def update_student(self, student_id, full_name, group_name, record_book):
        """Изменяет данные студента."""
        self.conn.execute(
            "UPDATE students SET full_name = ?, group_name = ?, record_book = ? WHERE id = ?",
            (full_name, group_name, record_book, student_id),
        )
        self.conn.commit()

    def delete_student(self, student_id):
        """Удаляет студента. Его оценки удаляются автоматически (CASCADE)."""
        self.conn.execute("DELETE FROM students WHERE id = ?", (student_id,))
        self.conn.commit()

    # ------------------------------------------------------------------
    # Оценки
    # ------------------------------------------------------------------
    def insert_grade(self, student_id, subject, grade, grade_date):
        """Добавляет оценку студенту и возвращает ID новой записи."""
        cursor = self.conn.execute(
            "INSERT INTO grades (student_id, subject, grade, grade_date) VALUES (?, ?, ?, ?)",
            (student_id, subject, grade, grade_date),
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_grades(self, student_id):
        """Возвращает все оценки одного студента (сначала старые, потом новые)."""
        return self.conn.execute(
            "SELECT id, subject, grade, grade_date FROM grades "
            "WHERE student_id = ? ORDER BY grade_date, id",
            (student_id,),
        ).fetchall()

    # ------------------------------------------------------------------
    def close(self):
        """Закрывает подключение к базе данных."""
        self.conn.close()
