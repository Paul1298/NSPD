import datetime


def generate_report(target, aoi_neighbors) -> str:
    """
    Формирует текстовый отчет, где каждый сосед упоминается только один раз
    с полным списком его направлений.

    Args:
        target: Словарь с данными о целевом участке.
        aoi_neighbors (list[dict]): Список словарей с данными о соседних участках.
    """
    # --- 1. Подготовка данных ---

    # Группируем соседей по каждому из их направлений.
    # Это все еще нужно, чтобы знать, какие соседи относятся к какой-либо дирекции.
    neighbors_by_direction = {}
    for neighbor in aoi_neighbors:
        directions = neighbor['direction'].split(', ')
        for direction in directions:
            if direction == 'не опознан':
                continue
            if direction not in neighbors_by_direction:
                neighbors_by_direction[direction] = []
            neighbors_by_direction[direction].append(neighbor)

    # Стандартный порядок обхода
    all_directions = [
        "с северной стороны", "с северо-восточной стороны", "с восточной стороны",
        "с юго-восточной стороны", "с южной стороны", "с юго-западной стороны",
        "с западной стороны", "с северо-западной стороны"
    ]

    report_lines = []

    # --- 2. Формирование шапки отчета ---
    target_kad_id = target["kad_id"]
    target_permission = target["permission"][0]  # Берем первый ВРИ, если их несколько
    target_address = target.get("address", "[адрес не указан]")

    report_lines.append("1.4. Краткая характеристика прилегающей к объекту ОНВ местности")
    report_lines.append(
        f"Объект ОНВ расположен по адресу: {target_address}, кадастровый номер земельного участка: {target_kad_id},"
        f" разрешенное использование: {target_permission}, и окружен:"
    )
    report_lines.append("")  # Пустая строка после шапки

    # --- 3. Основная логика формирования тела отчета ---

    # Сет для отслеживания уже добавленных в отчет соседей
    processed_neighbor_ids = set()

    # Итерируемся по каждому основному направлению, чтобы сформировать секции отчета
    for primary_direction in all_directions:

        # Получаем всех соседей, которые хоть как-то затрагивают это направление
        candidate_neighbors = neighbors_by_direction.get(primary_direction, [])

        # Фильтруем кандидатов, оставляя только тех, кого еще не добавили в отчет
        new_neighbors_for_this_direction = [
            n for n in candidate_neighbors if n['kad_id'] not in processed_neighbor_ids
        ]

        # Если для этого направления нет *новых* соседей, оно считается свободным
        if not new_neighbors_for_this_direction:
            report_lines.append(f"{primary_direction} – территории свободные от застройки.")
            continue

        # Сортируем новых соседей: сначала те, что只 в одном направлении, потом в нескольких.
        # Внутри каждой группы сортируем по расстоянию.
        new_neighbors_for_this_direction.sort(key=lambda n: (len(n['direction'].split(', ')), n['distance']))

        # Формируем строки отчета для этого направления
        direction_header = primary_direction
        for neighbor in new_neighbors_for_this_direction:
            # Полный список направлений для этого соседа
            all_dirs_for_neighbor = neighbor['direction']

            distance_str = f"на расстоянии {neighbor['distance']:.0f} м"
            if neighbor['distance'] < 1.0:
                distance_str = "вплотную к объекту ОНВ"

            # Создаем строку с ПОЛНЫМ списком направлений соседа
            full_report_line = (
                f"{all_dirs_for_neighbor} – {distance_str} расположен ЗУ с КН {neighbor['kad_id']},"
                f" разрешенное использование – {neighbor['permission'][0]}."
            )
            report_lines.append(full_report_line)

            # Важнейший шаг: отмечаем соседа как обработанного
            processed_neighbor_ids.add(neighbor['kad_id'])

    # --- 4. Финальная часть (сохранение) ---
    final_report_text = "\n".join(report_lines)

    # name = f'report_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
    name = f'report_test.txt'
    with open(name, 'w', encoding='utf-8') as f:
        f.write(final_report_text)

    print(f"Отчет сохранен в {name}")
    # Можно также вернуть сам текст для дальнейшего использования
    # return final_report_text