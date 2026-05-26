from pprint import pprint

from pynspd import Nspd, NspdFeature

from data_provider import search_area, process_target, process_neighbors

from geo_processor import get_distance_direction
from plotting import plot_features
from report_generator import generate_report



def main(kad_id, radius_meters=100):
    # 1. Подключение к NSPD
    with Nspd() as nspd:  # Инициализация клиента
        # 2. Получение данных о целевом участке
        target_feat = nspd.find(kad_id)
        target, crs_4326_to_utm, crs_utm_to_4326 = process_target(target_feat)

        # 3. Создание области поиска
        search_circle_utm = search_area(target, radius_meters)

        # 4. Поиск соседних участков
        processed_neighbors = process_neighbors(target, search_circle_utm, nspd.search_in_contour, crs_4326_to_utm, crs_utm_to_4326)

        # Добавляем визуализацию
        # plot_features(target, processed_neighbors, search_circle_utm, radius_meters)

        # 6. Генерация отчета
        generate_report(target, processed_neighbors)


if __name__ == "__main__":
    # Пример использования
    main('50:58:0020204:50', radius_meters=175)
    # main('58:29:3007008:13', radius_meters=90)
