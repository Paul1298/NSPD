import configparser
from pynspd import Nspd
from data_provider import search_area, process_target, process_neighbors
from plotting import plot_features
from report_generator import generate_report


# 1. Добавляем новый аргумент в функцию main
def main(kad_id, radius_meters, draw_plot_flag):
    print(f"Запускаем анализ для участка {kad_id} с радиусом {radius_meters} м...")

    with Nspd() as nspd:
        target_feat = nspd.find(kad_id)
        if not target_feat:
            print(f"Ошибка: Участок с кадастровым номером {kad_id} не найден.")
            return

        target, crs_4326_to_utm, crs_utm_to_4326 = process_target(target_feat)

        # 3. Создание области поиска
        search_circle_utm = search_area(target, radius_meters)

        # 4. Поиск соседних участков
        processed_neighbors = process_neighbors(target, search_circle_utm, nspd.search_in_contour, crs_4326_to_utm,
                                                crs_utm_to_4326)

        # 2. Оборачиваем вызов отрисовки в условный блок
        if draw_plot_flag:
            print("Подготовка и отображение графика...")
            plot_features(target, processed_neighbors, search_circle_utm, radius_meters)
        else:
            print("Этап визуализации пропущен согласно настройкам в config.ini.")

        print("Генерация текстового отчета...")
        generate_report(target, processed_neighbors)

    print("Анализ успешно завершен!")


if __name__ == "__main__":
    config = configparser.ConfigParser()

    try:
        config.read('config.ini', encoding='utf-8')

        kad_to_process = config['Settings']['kad_id']
        radius_to_process = config.getint('Settings', 'radius_meters')

        # 3. Читаем булевый флаг с помощью getboolean()
        should_draw_plot = config.getboolean('Settings', 'draw_plot')

    except FileNotFoundError:
        print("Ошибка: Файл конфигурации 'config.ini' не найден!")
        exit()
    except KeyError as e:
        print(f"Ошибка: В файле 'config.ini' отсутствует необходимый параметр: {e}")
        exit()
    except ValueError as e:
        print(f"Ошибка в значении параметра в 'config.ini': {e}")
        exit()
    except Exception as e:
        print(f"Произошла ошибка при чтении файла конфигурации: {e}")
        exit()

    # 4. Передаем новый флаг в main
    main(kad_to_process, radius_to_process, should_draw_plot)