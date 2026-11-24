"""
main.py — ТОЧКА ВХОДА. С этого файла запускается программа.

Запуск:   python3 main.py      (в Windows:  python main.py)

Здесь мы "собираем" программу из трёх частей (слоёв), как конструктор:

    ui.py (меню)  ->  services.py (проверки)  ->  database.py (SQLite)

Каждый слой общается только с соседним нижним слоем.
"""

from database import Database
from services import StudentService
import ui


def main():
    # 1. Подключаемся к базе данных (файл students.db создаётся автоматически).
    db = Database()

    # 2. Создаём слой логики и отдаём ему базу данных.
    service = StudentService(db)

    # 3. Запускаем меню и отдаём ему слой логики.
    try:
        ui.run(service)
    finally:
        # finally выполняется в любом случае — даже если случилась ошибка.
        # Так подключение к базе будет закрыто всегда.
        db.close()


# Эта проверка означает: "выполнять main() только если файл запустили напрямую,
# а не подключили через import из другого файла".
if __name__ == "__main__":
    main()
