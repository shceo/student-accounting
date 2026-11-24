"""
test_app.py — автоматические тесты программы.

Запуск:   python3 -m unittest -v test_app

Тест — это маленькая программа, которая сама вызывает функции приложения
и проверяет, что результат правильный. Каждая функция test_... — один тест.

Тесты работают с временной базой в оперативной памяти (":memory:"),
поэтому настоящий файл students.db они не трогают.
"""

import unittest

from database import Database
from services import StudentService


class StudentAppTests(unittest.TestCase):

    def setUp(self):
        # Выполняется ПЕРЕД каждым тестом: создаём чистую пустую базу.
        self.db = Database(":memory:")
        self.service = StudentService(self.db)

    def tearDown(self):
        # Выполняется ПОСЛЕ каждого теста: закрываем базу.
        self.db.close()

    # ---------- Добавление и просмотр ----------
    def test_add_and_show_student(self):
        new_id = self.service.add_student("Иванов Иван", "ПИ-101", "001")
        students = self.service.get_all_students()
        self.assertEqual(len(students), 1)
        self.assertEqual(students[0]["id"], new_id)
        self.assertEqual(students[0]["full_name"], "Иванов Иван")
        self.assertIsNone(students[0]["avg_grade"])  # оценок ещё нет

    def test_extra_spaces_are_removed(self):
        self.service.add_student("   Иванов    Иван  ", " ПИ-101 ", " 001 ")
        student = self.service.get_all_students()[0]
        self.assertEqual(student["full_name"], "Иванов Иван")
        self.assertEqual(student["group_name"], "ПИ-101")

    def test_empty_name_is_rejected(self):
        # assertRaises проверяет, что внутри блока with возникла ошибка.
        with self.assertRaises(ValueError):
            self.service.add_student("   ", "ПИ-101", "001")

    def test_name_with_digits_is_rejected(self):
        with self.assertRaises(ValueError):
            self.service.add_student("Иванов 123", "ПИ-101", "001")

    def test_duplicate_record_book_is_rejected(self):
        self.service.add_student("Иванов Иван", "ПИ-101", "001")
        with self.assertRaises(ValueError):
            self.service.add_student("Петров Пётр", "ПИ-102", "001")

    # ---------- Поиск ----------
    def test_search_ignores_letter_case(self):
        self.service.add_student("Иванов Иван", "ПИ-101", "001")
        self.service.add_student("Петрова Анна", "ИС-201", "002")
        self.assertEqual(len(self.service.find_students("ИВАН")), 1)   # по ФИО
        self.assertEqual(len(self.service.find_students("ис-2")), 1)   # по группе
        self.assertEqual(len(self.service.find_students("00")), 2)     # по зачётке
        self.assertEqual(len(self.service.find_students("Сидоров")), 0)

    def test_empty_search_is_rejected(self):
        with self.assertRaises(ValueError):
            self.service.find_students("  ")

    # ---------- Редактирование ----------
    def test_update_student(self):
        new_id = self.service.add_student("Иванов Иван", "ПИ-101", "001")
        # Номер зачётки оставляем прежним — это не должно считаться повтором.
        self.service.update_student(new_id, "Иванов Иван Иванович", "ПИ-102", "001")
        student = self.service.get_student(new_id)
        self.assertEqual(student["full_name"], "Иванов Иван Иванович")
        self.assertEqual(student["group_name"], "ПИ-102")

    def test_update_to_taken_record_book_is_rejected(self):
        self.service.add_student("Иванов Иван", "ПИ-101", "001")
        second_id = self.service.add_student("Петров Пётр", "ПИ-101", "002")
        with self.assertRaises(ValueError):
            self.service.update_student(second_id, "Петров Пётр", "ПИ-101", "001")

    def test_unknown_student_is_rejected(self):
        with self.assertRaises(ValueError):
            self.service.get_student(999)
        with self.assertRaises(ValueError):
            self.service.get_student("abc")  # не число

    # ---------- Оценки ----------
    def test_add_grades_and_average(self):
        new_id = self.service.add_student("Иванов Иван", "ПИ-101", "001")
        self.service.add_grade(new_id, "Математика", 5)
        self.service.add_grade(new_id, "Физика", "4")  # текст тоже принимается
        grades, average = self.service.get_grades(new_id)
        self.assertEqual(len(grades), 2)
        self.assertEqual(average, 4.5)
        # Средний балл в общем списке должен совпадать.
        self.assertEqual(self.service.get_all_students()[0]["avg_grade"], 4.5)

    def test_wrong_grade_is_rejected(self):
        new_id = self.service.add_student("Иванов Иван", "ПИ-101", "001")
        for bad_grade in (1, 6, 0, -3, "пять", ""):
            with self.assertRaises(ValueError):
                self.service.add_grade(new_id, "Математика", bad_grade)

    def test_grade_for_unknown_student_is_rejected(self):
        with self.assertRaises(ValueError):
            self.service.add_grade(999, "Математика", 5)

    # ---------- Удаление ----------
    def test_delete_student_removes_grades_too(self):
        new_id = self.service.add_student("Иванов Иван", "ПИ-101", "001")
        self.service.add_grade(new_id, "Математика", 5)
        self.service.delete_student(new_id)

        self.assertEqual(len(self.service.get_all_students()), 0)
        # Проверяем напрямую в базе, что "осиротевших" оценок не осталось.
        left = self.db.conn.execute("SELECT COUNT(*) FROM grades").fetchone()[0]
        self.assertEqual(left, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
