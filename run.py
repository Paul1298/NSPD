import sys
import webbrowser
import threading
import time
import uvicorn
from pathlib import Path


def open_browser():
    """Открывает браузер через 1.5 секунды после запуска сервера"""
    time.sleep(1.5)
    webbrowser.open("http://127.0.0.1:8000")


if __name__ == '__main__':
    # Запускаем открытие браузера в отдельном потоке
    threading.Thread(target=open_browser, daemon=True).start()

    # Настраиваем логирование проще для .exe
    if getattr(sys, 'frozen', False):
        # Если запущено из .exe - отключаем colorama и упрощаем логи
        import logging

        logging.basicConfig(level=logging.INFO)

        uvicorn.run(
            "nspd_site.asgi:application",
            host="127.0.0.1",
            port=8000,
            log_level="info",
            log_config=None  # Отключаем сложную конфигурацию логирования
        )
    else:
        # Обычный запуск
        uvicorn.run("nspd_site.asgi:application", host="127.0.0.1", port=8000)