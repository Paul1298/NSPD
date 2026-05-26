import datetime
import time


def generate_report(target, aoi_neighbors) -> str:
    """
    Формирует текстовый отчет в строгом соответствии с эталонным форматом.

    Args:
        target: Объект целевого участка.
        aoi_neighbors (list[dict]): Список словарей с данными о соседних участках.
    Returns:
        str: Готовый многострочный текстовый отчет.
    """
    # --- 1. Подготовка данных ---

    # Группируем соседей по каждому из их направлений
    neighbors_by_direction = {}
    for neighbor in aoi_neighbors:
        # Направление может быть составным, например "с южной стороны, с юго-западной стороны"
        directions = neighbor['direction'].split(', ')
        for direction in directions:
            if direction == 'не опознан':
                continue
            if direction not in neighbors_by_direction:
                neighbors_by_direction[direction] = []
            neighbors_by_direction[direction].append(neighbor)

    # Сортируем списки соседей внутри каждого направления по расстоянию
    for direction in neighbors_by_direction:
        neighbors_by_direction[direction].sort(key=lambda x: x['distance'])

    # Полный список всех возможных направлений для итерации, чтобы не пропустить пустые
    all_directions = [
        "с северной стороны", "с северо-восточной стороны", "с восточной стороны",
        "с юго-восточной стороны", "с южной стороны", "с юго-западной стороны",
        "с западной стороны", "с северо-западной стороны"
    ]

    report_lines = []

    # --- 2. Формирование шапки отчета ---
    target_kad_id = target["kad_id"]
    target_permission = target["permission"][0]
    # Попытка получить адрес из свойств, с запасным вариантом
    target_address = target["address"]

    report_lines.append("1.4. Краткая характеристика прилегающей к объекту ОНВ местности")
    report_lines.append(
        f"Объект ОНВ расположен по адресу: {target_address}, кадастровый номер земельного участка: {target_kad_id},"
        f" разрешенное использование: {target_permission}, и окружен:\n"
    )

    # --- 3. Формирование основного тела отчета ---

    # Чтобы объединять направления, если у них одинаковый список соседей (как в примере "с юго-западной, западной сторон")
    processed_directions = set()

    for i in range(len(all_directions)):
        direction = all_directions[i]

        if direction in processed_directions:
            continue

        # Находим соседей для текущего направления
        current_neighbors = neighbors_by_direction.get(direction)

        # --- Обработка пустых направлений ---
        if not current_neighbors:
            report_lines.append(f"{direction} – территории свободные от застройки.")
            continue

        # --- Поиск смежных направлений с тем же набором соседей ---
        combined_directions = [direction]
        for j in range(i + 1, len(all_directions)):
            next_direction = all_directions[j]
            if neighbors_by_direction.get(next_direction) == current_neighbors:
                combined_directions.append(next_direction)

        # Формируем заголовок направления (может быть составным)
        direction_str = ', '.join(combined_directions)

        # Добавляем в отчет по одному соседу на строку
        for neighbor in current_neighbors:
            distance_str = f"на расстоянии {neighbor['distance']:.0f} м"
            if neighbor['distance'] < 1.0:  # Если расстояние меньше метра, считаем "вплотную"
                distance_str = "вплотную к объекту ОНВ"

            report_lines.append(
                f"{direction_str} – {distance_str} расположен ЗУ с КН {neighbor['kad_id']},"
                f" разрешенное использование – {neighbor['permission'][0]}."
            )
            # Если у нас несколько соседей в одном направлении,
            # заголовок направления для следующих строк не повторяется
            direction_str = " " * (len(direction_str))  # Заменяем на пробелы

        # Отмечаем все обработанные направления, чтобы не повторяться
        for d in combined_directions:
            processed_directions.add(d)

    # --- 4. Добавление информации о жилых и спец. зонах (если она есть) ---
    # Тут должен быть код для поиска ближайшей жилой/нормируемой зоны,
    # сейчас просто добавим заглушки по аналогии с эталоном.
    # report_lines.append("Ближайшая жилая зона расположена ...")
    # report_lines.append("Ближайшая нормируемая территория ...")

    # return "\n".join(report_lines)

    # Сохранение в файл
    # name = f'report_{datetime.datetime.now().strftime("%H:%M:%S")}.txt'
    name = f'report_test.txt'
    with open(name, 'w', encoding='utf-8') as f:
        f.write("\n".join(report_lines))

    print(f"Отчет сохранен в {name}")
