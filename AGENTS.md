# AGENTS.md

Анализатор прилегающей территории для раздела 1.4 ОВОС («Краткая характеристика прилегающей
к объекту ОНВ местности»). Тянет ЗУ из ЕГРН через НСПД (публичный API), режет окно поиска на
8 румбов, находит соседние участки, формирует DOCX/TXT-отчёт строго по эталонной формулировке.

## Запуск

```bash
.venv/bin/python main.py       # CLI, читает ./config.ini
.venv/bin/python run.py        # веб: uvicorn ASGI на 127.0.0.1:8000 + автооткрытие браузера
```

Всё ходит в **живой** НСПД. Офлайн-проверка невозможна, фикстур и моков нет.

Тестов, линтера, тайпчекера и CI в репозитории **нет**. Единственная проверка — ручной запуск.
`manage.py migrate/makemigrations` не имеет смысла: `DATABASES = {}` (`nspd_site/settings.py:60`),
моделей нет. Не придумывать команды `pytest`/`ruff` — их нечем запускать.

## То, что ломается молча

**CLI игнорирует `kad_id`, если в `config.ini` есть `[coordinates]`.**
`main.py:31` всегда передаёт `coordinates`, а `data_provider.py:19` — `if coordinates:`,
и полигон всегда выигрывает. В текущем `config.ini` заполнены `point_0..point_9`, поэтому
запуск анализирует захардкоженную московскую геометрию, а не `kad_id = 50:21:0060403:9494`.
Чтобы реально проверить КН — закомментировать секцию `[coordinates]`.

**`[coordinates]` требует непрерывной нумерации.** `main.py:83` — `while f'point_{i}' in config['coordinates']`:
пропуск индекса молча обрывает остальные точки. Координаты в ini записаны как `lat, lon`,
но добавляются как `(lon, lat)` (`main.py:85-89`).

**`draw_plot = yes` в CLI ничего не рисует.** `plotting.py:5` принудительно `matplotlib.use('Agg')`,
поэтому `plt.show()` — no-op с предупреждением. `plot_features_to_file` / `plot_features_from_wkt`
пишут PNG, но `plot_features_to_file` из CLI не вызывается никем.

**Пути относительные.** `report_generator.py:137` пишет в `reports/` относительно CWD, `main.py:70`
читает `config.ini` относительно CWD. Веб при этом читает/пишет `settings.REPORTS_DIR`
(= `BASE_DIR/reports`). Запуск CLI не из корня репозитория → отчёты не найдутся в веб-скачивании.

**Веб-режим «полигон» сейчас падает.** `analyzer/services.py:54` передаёт `nspd=None`,
а `services.py:165` вызывает `nspd.search_in_contour` → `AttributeError`.
Вдобавок для полигона `permission` — строка `"custom"` (`data_provider.py:24`), а
`report_generator.py:104,144` берёт `permission[0]` → в отчёт уйдёт символ `"c"`.

## Архитектура

CLI и веб — **два независимых входа в одно ядро** из модулей в корне:

```
config.ini / AnalysisForm
  → data_provider.process_target()   # dict цели + трансформы 4326 <-> UTM
  → data_provider.search_area()      # target["utm"].buffer(radius)
  → data_provider.process_neighbors()# НСПД search_in_contour + фильтры
       → geo_processor.get_direction_distance()  # 8 секторов, румб + мин. расстояние
  → report_generator.generate_report()  # docxtpl → reports/report_<КН>.docx
  → plotting.py (CLI: plt.show, веб: отложенный PNG по кнопке)
```

Веб-обвязка: `analyzer/` — Django-приложение без БД. POST → daemon-поток (`views.py:153`) →
логи пишутся в глобальный dict `log_sessions` → SSE `logs/<session_id>/` → `results/<session_id>/`
отдаёт готовый HTML-partial. Прогресс-бар в JS скрейпит лог по regex `/\[(\d+)%\]/`,
а `services.py:145-159` throttles до 5% (кроме `important=True`) — **формат логов менять нельзя**,
сломается прогресс-бар.

## Контракты, которые неявны

- **Строка направления — сквозной ключ соединения.** `get_direction_distance(merge_directions=True)`
  склеивает румбы в `"с южной стороны, с юго-западной стороны"`. Этот формат потом
  `split(', ')`-ится в `report_generator.py:49`, `data_provider.py:75` и используется как
  ключ группировки. Менять формат — значит править три места.
- **Отчёт = только секции.** `report_template.docx` использует исключительно `sections`.
  Передаваемые `target_kad_id` / `target_address` / `target_permission` в шаблоне не упомянуты.
  Тексты правятся в `report_generator.py`; `misc/etalon.txt` — эталон формулировок, не код.
  Шаблон `.docx` править руками осторожно: внутри 638 КБ стили Word, docxtpl их требует.
- **Все три дефолта `min_intersection_percent` разные**: `config.ini:28` = 5,
  `analyzer/forms.py:22` = 15, `index.html:55` = 40. Форма рендерится вручную сырым HTML,
  поэтому `initial=` из `forms.py` до браузера не доходит — побеждает значение в шаблоне.
- **Строка слоя НСПД — магическая:** `"Земельные участки из ЕГРН"` (`data_provider.py:95`).
- **Ошибка 597 / `TooBigContour`** при большом радиусе лечится `nspd.search_in_contour_iter()`
  (сам режет bbox на тайлы, дедуплицирует по md5). В коде проекта **не используется** —
  `process_neighbors` зовёт `search_in_contour` без обработки.
- Неиспользуемые, но релевантные вкладки `pynspd`: `tab_land_links` («Связанные ЗУ»),
  `tab_land_parts` («Части ЗУ») — вероятный источник данных о группе ЗУ, образующей один ОНВ.

## Ограничения геометрии

- Слой 36048 допускает `Union[MultiPolygon, Polygon, Point]`. `Point` (непривязанный ЗУ) и
  `MultiPolygon` ломают `.buffer`, `.area > 0` и `.exterior`. В CLI-ветке `plotting.py`
  нет защиты `get_polygons`, в веб-ветке она есть (`plotting.py:228`).
- Смежность участков определяется **расстоянием** (`geo_processor.py:102`, порог `< 1.0` м →
  «вплотную»), а не `touches()`/общей границей. `union`/`unary_union` в проекте нет нигде.
- Пакетный режим (список КН в `kad_ids`) — это N независимых анализов с N отчётами
  (`services.py:78-100`), а не один анализ группы участков. Не путать.
- CRS: `estimate_utm_crs()` вызывается на одно-строчном GeoDataFrame (`data_provider.py:42-47`).
  При добавлении нескольких целев ЗУ пересчёт зоны привязки нужно пересмотреть.

## Стиль

Русские комментарии, docstring-и, тексты логов и отчётов; эмодзи в логах веба (`▶️`, `📊`, `✅`).
Аннотации типов на сигнатурах функций. Комментарии в коде обильные — их принято писать.
