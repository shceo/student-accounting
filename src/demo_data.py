"""
demo_data.py — заполняет базу учебными (выдуманными) данными для показа.

Запуск:   python3 demo_data.py

Скрипт нужен только для удобства на защите: чтобы не вводить студентов
вручную. Если в базе уже есть студенты, он ничего не делает,
поэтому запускать его повторно безопасно.
"""

from database import Database
from services import StudentService

# Выдуманные студенты: (ФИО, группа, номер зачётки)
STUDENTS = [
    ("Иванов Иван Иванович", "ПИ-101", "2024-001"),
    ("Петрова Анна Сергеевна", "ПИ-101", "2024-002"),
    ("Сидоров Алексей Петрович", "ПИ-102", "2024-003"),
    ("Каримова Диана Рустамовна", "ПИ-102", "2024-004"),
    ("Смирнов Олег Игоревич", "ИС-201", "2023-015"),
]

# Оценки: (номер студента по порядку в списке выше, предмет, оценка)
GRADES = [
    (0, "Математика", 5),
    (0, "Программирование", 4),
    (1, "Математика", 4),
    (1, "Программирование", 5),
    (1, "Английский язык", 5),
    (2, "Математика", 3),
    (3, "Программирование", 5),
]


def main():
    db = Database()
    service = StudentService(db)

    if len(service.get_all_students()) > 0:
        print("В базе уже есть студенты — учебные данные не добавлены.")
    else:
        ids = []
        for full_name, group_name, record_book in STUDENTS:
            ids.append(service.add_student(full_name, group_name, record_book))
        for index, subject, grade in GRADES:
            service.add_grade(ids[index], subject, grade)
        print("Добавлено студентов: %d, оценок: %d." % (len(STUDENTS), len(GRADES)))

    db.close()


if __name__ == "__main__":
    main()
