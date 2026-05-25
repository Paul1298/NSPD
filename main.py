from pprint import pprint

from pynspd import Nspd, NspdFeature

from data_provider import search_area


# from nspd.data_provider import search_area
from geo_processor import get_distance_direction
from plotting import plot_features
from report_generator import generate_report


def main(kad_id, radius_meters=100):
    # 1. Подключение к NSPD
    with Nspd() as nspd:  # Инициализация клиента

        # 2. Получение данных о целевом участке
        target_feat = nspd.find(kad_id)
        # target_geometry = loads(target_feat.get_geometry())
        target_permission = nspd.tab_permission_type(target_feat)
        print(target_permission)

        # 3. Создание области поиска
        search_circle = search_area(target_feat, radius_meters)

        # 4. Поиск соседних участков
        neighbor_feats = nspd.search_in_contour(
            search_circle,
            NspdFeature.by_title("Земельные участки из ЕГРН"),
        )
        cns = [i.properties.options.cad_num for i in neighbor_feats]

        print(f"Соседи в радиусе {radius_meters}м. : {len(cns)}\n", '\n'.join(cns))
        # print(cns)

        # neighbor_feats = [
        #     feat for feat in neighbor_feats
        #     if feat.properties.options.cad_num != '50:58:0000000:12'
        # ]

        # Добавляем визуализацию
        plot_features(target_feat, neighbor_feats, search_circle, radius_meters)

        # 5. Обработка найденных участков
        # processed_neighbors = []
        # for neighbor_feat in neighbor_feats:
        #     if neighbor_feat.properties.options.cad_num == kad_id:
        #         continue  # Пропускаем сам целевой участок
        #
        #     # Получаем полную информацию о соседе
        #     # neighbor_details = nspd.find(neighbor_feat.kad_num)
        #     dist, direction = get_distance_direction(target_feat, neighbor_feat)
        #
        #     # Здесь будет логика определения направления и расстояния
        #     # Пока что заглушка
        #     processed_neighbors.append({
        #         'kad_id': neighbor_feat.properties.options.cad_num,
        #         'permission': nspd.tab_permission_type(neighbor_feat),
        #         'direction': direction,
        #         'distance': dist
        #     })
        #
        # pprint(processed_neighbors)

        # 6. Генерация отчета
        # generate_report(target_feat, processed_neighbors)


if __name__ == "__main__":
    # Пример использования
    main('50:58:0020204:50', radius_meters=175)
    # main('58:29:3007008:13', radius_meters=90)
