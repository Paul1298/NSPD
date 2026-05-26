import datetime
import time

def generate_report(target, neighbors):
    # Формирование текстового отчета
    report = f"Отчет для участка {target["kad_id"]}\n"
    report += f"Разрешенное использование: {target["permission"]}\n\n"

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
    name = f'report_{datetime.datetime.now().strftime("%H:%M:%S")}.txt'
    with open(name, 'w', encoding='utf-8') as f:
        f.write(report)

    print("Отчет сохранен в report.txt")
