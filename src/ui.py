"""
ui.py — СЛОЙ ИНТЕРФЕЙСА (верхний слой программы).

Простыми словами: этот файл — "окошко в деканате". Он показывает меню,
спрашивает у пользователя данные и печатает ответы.

Сам он ничего не решает и не хранит: все просьбы передаёт в services.py
(объект service). Если service сообщает об ошибке (ValueError),
интерфейс просто показывает текст ошибки и возвращается в меню.
"""

# Границы оценок берём из слоя логики, чтобы подсказка на экране
# всегда совпадала с настоящим правилом проверки.
from services import MIN_GRADE, MAX_GRADE

MENU = """
========== УЧЁТ СТУДЕНТОВ ==========
 1. Добавить студента
 2. Показать всех студентов
 3. Найти студента
 4. Редактировать студента
 5. Удалить студента
 6. Выставить оценку
 7. Показать оценки студента
 0. Выход
====================================="""


# ----------------------------------------------------------------------
# Вспомогательные функции вывода
# ----------------------------------------------------------------------
def print_table(headers, rows):
    """Печатает аккуратную таблицу. headers — заголовки, rows — строки."""
    # Превращаем все значения в текст, чтобы можно было измерить их длину.
    rows = [[str(cell) for cell in row] for row in rows]

    # Ширина каждого столбца = длина самого длинного значения в нём.
    widths = []
    for i in range(len(headers)):
        longest = len(headers[i])
        for row in rows:
            if len(row[i]) > longest:
                longest = len(row[i])
        widths.append(longest)

    def make_line(cells):
        # ljust(n) дополняет текст пробелами справа до ширины n.
        return " | ".join(cells[i].ljust(widths[i]) for i in range(len(cells)))

    print(make_line(headers))
    print("-+-".join("-" * width for width in widths))  # линия под заголовком
    for row in rows:
        print(make_line(row))


def format_average(value):
    """Средний балл для показа: число или прочерк, если оценок ещё нет."""
    if value is None:
        return "—"
    return "%.2f" % value


def format_date(iso_date):
    """Дата из вида '2026-11-24' (так хранится в базе) в привычный '24.11.2026'."""
    year, month, day = iso_date.split("-")
    return day + "." + month + "." + year


def print_students(students):
    """Печатает список студентов таблицей."""
    if len(students) == 0:
        print("Список пуст.")
        return
    rows = []
    for s in students:
        rows.append([s["id"], s["full_name"], s["group_name"],
                     s["record_book"], format_average(s["avg_grade"])])
    print_table(["ID", "ФИО", "Группа", "№ зачётки", "Средний балл"], rows)
    print("Всего студентов:", len(students))


# ----------------------------------------------------------------------
# Действия меню. Каждая функция = один пункт меню.
# ----------------------------------------------------------------------
def action_add_student(service):
    """Пункт 1. Добавление студента."""
    print("\n--- Добавление студента ---")
    full_name = input("ФИО: ")
    group_name = input("Группа: ")
    record_book = input("Номер зачётной книжки: ")
    new_id = service.add_student(full_name, group_name, record_book)
    print("Готово! Студент добавлен, его ID =", new_id)


def action_show_all(service):
    """Пункт 2. Просмотр всех студентов."""
    print("\n--- Список студентов ---")
    print_students(service.get_all_students())


def action_find(service):
    """Пункт 3. Поиск студента."""
    print("\n--- Поиск студента ---")
    text = input("Введите часть ФИО, группы или номера зачётки: ")
    found = service.find_students(text)
    if len(found) == 0:
        print("Ничего не найдено.")
    else:
        print_students(found)


def action_edit(service):
    """Пункт 4. Редактирование студента."""
    print("\n--- Редактирование студента ---")
    student = service.get_student(input("ID студента: "))
    print("Нажмите Enter, чтобы оставить поле без изменений.")

    # Конструкция "input(...).strip() or старое_значение" работает так:
    # если пользователь ничего не ввёл (пустая строка), берём старое значение.
    full_name = input("ФИО [%s]: " % student["full_name"]).strip() or student["full_name"]
    group_name = input("Группа [%s]: " % student["group_name"]).strip() or student["group_name"]
    record_book = input("Номер зачётки [%s]: " % student["record_book"]).strip() or student["record_book"]

    service.update_student(student["id"], full_name, group_name, record_book)
    print("Готово! Данные студента обновлены.")


def action_delete(service):
    """Пункт 5. Удаление студента (с подтверждением)."""
    print("\n--- Удаление студента ---")
    student = service.get_student(input("ID студента: "))

    # Удаление нельзя отменить, поэтому переспрашиваем.
    answer = input("Удалить студента '%s' и все его оценки? (да/нет): " % student["full_name"])
    if answer.strip().lower() in ("да", "д", "yes", "y"):
        service.delete_student(student["id"])
        print("Готово! Студент удалён.")
    else:
        print("Удаление отменено.")


def action_add_grade(service):
    """Пункт 6. Выставление оценки."""
    print("\n--- Выставление оценки ---")
    student = service.get_student(input("ID студента: "))
    print("Студент:", student["full_name"], "(группа " + student["group_name"] + ")")
    subject = input("Предмет: ")
    grade = input("Оценка (от %d до %d): " % (MIN_GRADE, MAX_GRADE))
    service.add_grade(student["id"], subject, grade)
    print("Готово! Оценка выставлена.")


def action_show_grades(service):
    """Пункт 7. Просмотр оценок студента и среднего балла."""
    print("\n--- Оценки студента ---")
    student = service.get_student(input("ID студента: "))
    grades, average = service.get_grades(student["id"])

    print("Студент:", student["full_name"], "(группа " + student["group_name"] + ")")
    if len(grades) == 0:
        print("Оценок пока нет.")
        return
    rows = [[g["subject"], g["grade"], format_date(g["grade_date"])] for g in grades]
    print_table(["Предмет", "Оценка", "Дата"], rows)
    print("Средний балл:", format_average(average))


# Словарь "номер пункта -> функция". Удобнее, чем длинная цепочка if/elif:
# чтобы добавить новый пункт меню, достаточно дописать одну строку.
ACTIONS = {
    "1": action_add_student,
    "2": action_show_all,
    "3": action_find,
    "4": action_edit,
    "5": action_delete,
    "6": action_add_grade,
    "7": action_show_grades,
}


def run(service):
    """Главный цикл программы: показываем меню, пока пользователь не выберет 0."""
    while True:
        print(MENU)
        try:
            choice = input("Выберите пункт меню: ").strip()

            if choice == "0":
                print("До свидания!")
                break                       # выходим из цикла — программа завершается

            action = ACTIONS.get(choice)    # ищем функцию по номеру пункта
            if action is None:
                print("Ошибка: нет такого пункта. Введите число от 0 до 7.")
                continue                    # возвращаемся к показу меню

            action(service)                 # выполняем выбранное действие

        except ValueError as error:
            # Сюда попадают все ошибки проверки данных из services.py.
            # Программа не "падает", а показывает понятное сообщение.
            print("Ошибка:", error)

        except (EOFError, KeyboardInterrupt):
            # Пользователь нажал Ctrl+C / Ctrl+D — спокойно выходим.
            print("\nРабота программы завершена.")
            break
