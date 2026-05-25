def generate_report(target_feat, neighbors):
    return
    # Формирование текстового отчета
    report = f"Отчет для участка {target_feat.kad_num}\n"
    report += f"Разрешенное использование: {target_feat.tab_permission_type()}\n\n"

    # Группировка и сортировка соседей по направлениям
    neighbors_by_direction = {}
    for neighbor in neighbors:
        if neighbor['direction'] not in neighbors_by_direction:
            neighbors_by_direction[neighbor['direction']] = []
        neighbors_by_direction[neighbor['direction']].append(neighbor)

    # Вывод для каждого направления
    for direction, direction_neighbors in neighbors_by_direction.items():
        report += f"{direction}:\n"
        for neighbor in direction_neighbors:
            report += (
                f"- на расстоянии {neighbor['distance']} м "
                f"расположен ЗУ с КН {neighbor['kad_id']}, "
                f"разрешенное использование – {neighbor['permission']}\n"
            )

    # Сохранение в файл
    with open('report.txt', 'w', encoding='utf-8') as f:
        f.write(report)

    print("Отчет сохранен в report.txt")
