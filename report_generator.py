import datetime
import os.path
from docxtpl import DocxTemplate


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


def generate_report(
        target,
        neighbours,
        merge_directions=True,
        output_format='docx',  # 'txt' или 'docx'
        template_path='report_template.docx',
) -> tuple[str, str]:
    """
    Формирует отчет в формате TXT или DOCX.
    """
    # --- 1. Подготовка ---
    # Разобьём каждого соседа как отдельного

    aoi_neighbors = []
    for neighbor in neighbours:
        for direction, distance in neighbor["dir_dist"]:
            fake_neighbour = neighbor.copy()
            fake_neighbour['direction'] = direction
            fake_neighbour['distance'] = distance
            aoi_neighbors.append(fake_neighbour)

    neighbors_by_direction = {}
    for neighbor in aoi_neighbors:
        directions = neighbor['direction'].split(', ')
        for direction in directions:
            if direction == 'не опознано':
                continue
            if direction not in neighbors_by_direction:
                neighbors_by_direction[direction] = []
            neighbors_by_direction[direction].append(neighbor)

    all_directions = [
        "с северной стороны", "с северо-восточной стороны", "с восточной стороны",
        "с юго-восточной стороны", "с южной стороны", "с юго-западной стороны",
        "с западной стороны", "с северо-западной стороны"
    ]

    # --- 2. Формируем секции для отчета ---
    sections = []  # Список секций для docxtpl
    report_lines = []  # Список строк для txt
    processed_neighbor_ids = set()

    for primary_direction in all_directions:
        candidate_neighbors = neighbors_by_direction.get(primary_direction, [])
        new_neighbors = [n for n in candidate_neighbors if n['kad_id'] not in processed_neighbor_ids]

        if not new_neighbors:
            # Территория свободна
            if not any(primary_direction in n['direction'] for n_id in processed_neighbor_ids
                       for n in aoi_neighbors if n['kad_id'] == n_id):
                sections.append({
                    'type': 'free',
                    'direction': primary_direction,
                })
                report_lines.append(f"{primary_direction} – территории, свободные от застройки.")
            continue

        # Группируем соседей по полной строке направлений
        groups = {}
        for neighbor in new_neighbors:
            key = neighbor['direction']
            if key not in groups:
                groups[key] = []
            groups[key].append(neighbor)

        sorted_group_keys = sorted(groups.keys(), key=lambda k: (len(k.split(', ')), k))

        for full_direction_str in sorted_group_keys:
            neighbor_list = groups[full_direction_str]
            neighbor_list.sort(key=lambda n: n['distance'])

            # Подготовка данных для docxtpl
            neighbors_data = []
            for neighbor in neighbor_list:
                distance_str = f"на расстоянии {neighbor['distance']:.0f} м"
                if neighbor['distance'] < 1.0:
                    distance_str = "вплотную к объекту ОНВ"

                permission_str = neighbor['permission'][0] if neighbor.get('permission') else "не определено"

                neighbors_data.append({
                    'kad_id': neighbor['kad_id'],
                    'distance_str': distance_str,
                    'permission': permission_str,
                })

                # Для TXT
                full_direction_str_formatted = format_direction_string(full_direction_str)
                if len(neighbors_data) == 1:
                    line = (
                        f"\n{full_direction_str_formatted} – {distance_str} расположен ЗУ с КН {neighbor['kad_id']},"
                        f" разрешенное использование – {permission_str}."
                    )
                else:
                    line = (
                        f"– {distance_str} расположен ЗУ с КН {neighbor['kad_id']},"
                        f" разрешенное использование – {permission_str}."
                    )
                report_lines.append(line)

            # Добавляем секцию для docxtpl
            sections.append({
                'type': 'neighbor_group',
                'direction_formatted': format_direction_string(full_direction_str),
                'neighbors': neighbors_data,
            })

            if merge_directions:
                processed_neighbor_ids.add(neighbor_list[0]['kad_id'])

    # --- 3. Сохранение ---
    filename_base = f"reports{os.path.sep}report_{target['kad_id'].replace(':', '_')}"

    if output_format == 'docx':
        # Подготовка контекста для docxtpl
        context = {
            'target_kad_id': target['kad_id'],
            'target_address': target.get('address', '[адрес не указан]'),
            'target_permission': target['permission'][0] if target.get('permission') else '[не определено]',
            'sections': sections,
        }

        # Рендеринг шаблона
        tpl = DocxTemplate(template_path)
        tpl.render(context)

        filename = filename_base + '.docx'
        tpl.save(filename)
        final_report_text = "\n".join(report_lines)  # Для логирования
    else:
        # TXT формат (как было)
        final_report_text = "\n".join(report_lines)
        filename = filename_base + '.txt'
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(final_report_text)

    print(f"Отчет сохранен в {filename}")
    return filename, final_report_text