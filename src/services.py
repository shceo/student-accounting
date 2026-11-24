"""
services.py — СЛОЙ ЛОГИКИ (средний слой программы).

Простыми словами: этот файл — "строгий секретарь деканата". Прежде чем
что-то записать в базу, он проверяет, что данные правильные:
ФИО не пустое, номер зачётки не повторяется, оценка от 2 до 5 и т.д.

Если данные неправильные — он "поднимает ошибку" ValueError с понятным
текстом. Интерфейс (ui.py) эту ошибку ловит и показывает пользователю.

Этот файл НЕ знает SQL (за это отвечает database.py)
и НЕ печатает на экран (за это отвечает ui.py).
"""

import datetime

# Границы оценок. Вынесены в константы: если в вузе другая шкала,
# достаточно поменять два числа здесь (и CHECK в database.py).
MIN_GRADE = 2
MAX_GRADE = 5

# Максимальная длина текстовых полей (чтобы таблица на экране не "разъезжалась").
MAX_NAME_LENGTH = 100
MAX_GROUP_LENGTH = 20
MAX_RECORD_BOOK_LENGTH = 20
MAX_SUBJECT_LENGTH = 60


def clean_text(text):
    """Убирает лишние пробелы: '  Иванов   Иван ' -> 'Иванов Иван'."""
    # split() режет строку по пробелам, join() склеивает обратно через один пробел.
    return " ".join(str(text).split())


def to_int(value, field_name):
    """Превращает введённый текст в целое число или сообщает об ошибке."""
    try:
        return int(str(value).strip())
    except ValueError:
        # Пользователь ввёл буквы или пустую строку вместо числа.
        raise ValueError(field_name + " — это должно быть целое число.")


class StudentService:
    """Все действия программы: добавить, найти, изменить, удалить, оценить."""

    def __init__(self, db):
        # Запоминаем объект базы данных, чтобы потом обращаться к нему.
        self.db = db

    # ------------------------------------------------------------------
    # Проверка данных студента (используется при добавлении и изменении)
    # ------------------------------------------------------------------
    def _check_student_data(self, full_name, group_name, record_book, except_id=None):
        """Проверяет поля студента и возвращает их в "причёсанном" виде."""
        full_name = clean_text(full_name)
        group_name = clean_text(group_name)
        record_book = clean_text(record_book)

        # --- ФИО ---
        if full_name == "":
            raise ValueError("ФИО не может быть пустым.")
        if len(full_name) > MAX_NAME_LENGTH:
            raise ValueError("ФИО слишком длинное (максимум %d символов)." % MAX_NAME_LENGTH)
        # any(...) вернёт True, если хотя бы один символ — цифра.
        if any(symbol.isdigit() for symbol in full_name):
            raise ValueError("В ФИО не должно быть цифр.")

        # --- Группа ---
        if group_name == "":
            raise ValueError("Название группы не может быть пустым.")
        if len(group_name) > MAX_GROUP_LENGTH:
            raise ValueError("Название группы слишком длинное (максимум %d символов)." % MAX_GROUP_LENGTH)

        # --- Номер зачётной книжки ---
        if record_book == "":
            raise ValueError("Номер зачётной книжки не может быть пустым.")
        if len(record_book) > MAX_RECORD_BOOK_LENGTH:
            raise ValueError("Номер зачётной книжки слишком длинный (максимум %d символов)." % MAX_RECORD_BOOK_LENGTH)
        # Номер зачётки должен быть уникальным — по нему отличают студентов-тёзок.
        if self.db.record_book_exists(record_book, except_id):
            raise ValueError("Студент с номером зачётной книжки '%s' уже есть в базе." % record_book)

        return full_name, group_name, record_book

    # ------------------------------------------------------------------
    # Студенты
    # ------------------------------------------------------------------
    def add_student(self, full_name, group_name, record_book):
        """Функция 1. Добавляет студента. Возвращает его ID."""
        full_name, group_name, record_book = self._check_student_data(
            full_name, group_name, record_book
        )
        return self.db.insert_student(full_name, group_name, record_book)

    def get_all_students(self):
        """Функция 2. Возвращает список всех студентов."""
        return self.db.get_all_students()

    def find_students(self, text):
        """Функция 3. Ищет студентов по части ФИО, группы или номера зачётки."""
        text = clean_text(text)
        if text == "":
            raise ValueError("Введите текст для поиска.")
        return self.db.find_students(text)

    def get_student(self, student_id):
        """Возвращает студента по ID. Если такого нет — ошибка."""
        student_id = to_int(student_id, "ID студента")
        student = self.db.get_student(student_id)
        if student is None:
            raise ValueError("Студент с ID %d не найден." % student_id)
        return student

    def update_student(self, student_id, full_name, group_name, record_book):
        """Функция 4. Изменяет данные студента."""
        student = self.get_student(student_id)  # заодно проверили, что он существует
        full_name, group_name, record_book = self._check_student_data(
            full_name, group_name, record_book, except_id=student["id"]
        )
        self.db.update_student(student["id"], full_name, group_name, record_book)

    def delete_student(self, student_id):
        """Функция 5. Удаляет студента вместе с его оценками."""
        student = self.get_student(student_id)
        self.db.delete_student(student["id"])

    # ------------------------------------------------------------------
    # Оценки
    # ------------------------------------------------------------------
    def add_grade(self, student_id, subject, grade):
        """Функция 6. Выставляет студенту оценку по предмету."""
        student = self.get_student(student_id)

        subject = clean_text(subject)
        if subject == "":
            raise ValueError("Название предмета не может быть пустым.")
        if len(subject) > MAX_SUBJECT_LENGTH:
            raise ValueError("Название предмета слишком длинное (максимум %d символов)." % MAX_SUBJECT_LENGTH)

        grade = to_int(grade, "Оценка")
        if grade < MIN_GRADE or grade > MAX_GRADE:
            raise ValueError("Оценка должна быть от %d до %d." % (MIN_GRADE, MAX_GRADE))

        # Дату ставим автоматически — сегодняшнюю, в виде '2026-11-24'.
        today = datetime.date.today().isoformat()
        return self.db.insert_grade(student["id"], subject, grade, today)

    def get_grades(self, student_id):
        """Функция 7. Возвращает оценки студента и его средний балл.

        Результат — пара (список оценок, средний балл).
        Если оценок нет, средний балл равен None ("ничего").
        """
        student = self.get_student(student_id)
        grades = self.db.get_grades(student["id"])

        if len(grades) == 0:
            return grades, None

        # Средний балл = сумма всех оценок / их количество.
        total = sum(row["grade"] for row in grades)
        average = round(total / len(grades), 2)
        return grades, average
