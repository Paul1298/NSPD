import datetime


def format_direction_string(full_direction_str: str) -> str:
    """
    Преобразует строку вида "с южной стороны, с юго-западной стороны"
    в "с южной, юго-западной сторон".
    Если направление одно, оставляет его без изменений ("с южной стороны").
    """
    # Разделяем строку на отдельные направления
    parts = full_direction_str.split(', ')

    # Если направление всего одно, ничего не меняем
    if len(parts) <= 1:
        return full_direction_str

    # Извлекаем "ядро" каждого направления (без "с " и " стороны")
    cores = [p.removeprefix("с ").removesuffix(" стороны") for p in parts]

    # Собираем новую строку: "с" + "ядра через запятую" + "сторон"
    return f"с {', '.join(cores)} сторон"


def generate_report(target, aoi_neighbors) -> str:
    """
    Формирует отчет, группируя соседей с одинаковым набором направлений.
    Каждый сосед упоминается только один раз.

    Args:
        target: Словарь с данными о целевом участке.
        aoi_neighbors (list[dict]): Список словарей с данными о соседних участках.
    """
    # --- 1. Подготовка ---
    neighbors_by_direction = {}
    for neighbor in aoi_neighbors:
        directions = neighbor['direction'].split(', ')
        for direction in directions:
            if direction == 'не опознано': continue
            if direction not in neighbors_by_direction:
                neighbors_by_direction[direction] = []
            neighbors_by_direction[direction].append(neighbor)

    all_directions = [
        "с северной стороны", "с северо-восточной стороны", "с восточной стороны",
        "с юго-восточной стороны", "с южной стороны", "с юго-западной стороны",
        "с западной стороны", "с северо-западной стороны"
    ]

    report_lines = []

    # --- 2. Шапка отчета ---
    # target_kad_id = target["kad_id"]
    # target_permission = target["permission"][0]
    # target_address = target.get("address", "[адрес не указан]")
    #
    # report_lines.append("1.4. Краткая характеристика прилегающей к объекту ОНВ местности")
    # report_lines.append(
    #     f"Объект ОНВ расположен по адресу: {target_address}, кадастровый номер земельного участка: {target_kad_id},"
    #     f" разрешенное использование: {target_permission}, и окружен:"
    # )
    # # report_lines.append("")

    # --- 3. Основная логика с группировкой ---
    processed_neighbor_ids = set()

    for primary_direction in all_directions:
        candidate_neighbors = neighbors_by_direction.get(primary_direction, [])
        new_neighbors = [n for n in candidate_neighbors if n['kad_id'] not in processed_neighbor_ids]

        if not new_neighbors:
            # Проверяем, было ли уже что-то выведено для этого направления косвенно.
            # Если нет, то территория свободна.
            if not any(primary_direction in n['direction'] for n_id in processed_neighbor_ids for n in aoi_neighbors if
                       n['kad_id'] == n_id):
                report_lines.append(f"{primary_direction} – территории свободные от застройки.")
            continue

        # Группируем новых соседей по их ПОЛНОЙ строке направлений
        groups = {}
        for neighbor in new_neighbors:
            key = neighbor['direction']
            if key not in groups:
                groups[key] = []
            groups[key].append(neighbor)

        # Сортируем ключи групп (строки направлений), чтобы вывод был консистентным
        sorted_group_keys = sorted(groups.keys(), key=lambda k: (len(k.split(', ')), k))

        for full_direction_str in sorted_group_keys:
            neighbor_list = groups[full_direction_str]
            # Сортируем соседей внутри каждой группы по расстоянию
            neighbor_list.sort(key=lambda n: n['distance'])

            # Формируем строки для этой группы
            for i, neighbor in enumerate(neighbor_list):
                distance_str = f"на расстоянии {neighbor['distance']:.0f} м"
                if neighbor['distance'] < 1.0:
                    distance_str = "вплотную к объекту ОНВ"

                permission_str = neighbor['permission'][0] if neighbor.get('permission') else "не определено"

                full_direction_str = format_direction_string(full_direction_str)
                if i == 0:
                    # Первая строка в группе получает полный заголовок
                    line = (
                        f"\n{full_direction_str} – {distance_str} расположен ЗУ с КН {neighbor['kad_id']},"
                        f" разрешенное использование – {permission_str}."
                    )
                else:
                    # Последующие строки получают отступ вместо заголовка
                    # Это создает визуальный блок, как в эталоне
                    # indent = " " * len(full_direction_str)
                    line = (
                        f"– {distance_str} расположен ЗУ с КН {neighbor['kad_id']},"
                        f" разрешенное использование – {permission_str}."
                    )

                report_lines.append(line)
                processed_neighbor_ids.add(neighbor['kad_id'])

    # --- 4. Сохранение ---
    final_report_text = "\n".join(report_lines)

    name = f'report_{target["kad_id"].replace(":", "_")}.txt'
    # name = f'report_test.txt'
    with open(name, 'w', encoding='utf-8') as f:
        f.write(final_report_text)
    print(f"Отчет сохранен в {name}")
