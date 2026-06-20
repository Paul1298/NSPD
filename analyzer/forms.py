from django import forms


class AnalysisForm(forms.Form):
    kad_ids = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 6, 'placeholder': '86:14:0101002:715'}),
        required=False,
        help_text="По одному номеру на строку"
    )

    polygon_coordinates = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 6,
            'placeholder': '55.560255236, 37.892199320\n55.560271004, 37.892419993\n...'
        }),
        required=False,
        help_text="Координаты в формате: широта, долгота (по одной паре на строку). Полигон будет замкнут автоматически."
    )

    radius_meters = forms.IntegerField(initial=250, min_value=10, max_value=5000)
    area_limit = forms.IntegerField(initial=5, min_value=0)
    min_intersection_percent = forms.IntegerField(initial=15, min_value=1, max_value=100)
    draw_plots = forms.BooleanField(required=False)
    draw_kad = forms.BooleanField(required=False)
    merge_directions = forms.BooleanField(required=False, initial=True)

    def clean(self):
        cleaned_data = super().clean()
        kad_ids = cleaned_data.get('kad_ids', '').strip()
        polygon = cleaned_data.get('polygon_coordinates', '').strip()

        if not kad_ids and not polygon:
            raise forms.ValidationError("Введите либо кадастровые номера, либо координаты полигона.")

        # Парсинг полигона из построчного формата
        if polygon:
            try:
                coords = self._parse_polygon(polygon)
                cleaned_data['parsed_polygon'] = coords
            except ValueError as e:
                raise forms.ValidationError(f"Ошибка парсинга координат: {e}")

        return cleaned_data

    def _parse_polygon(self, text: str) -> list:
        """
        Парсит текст вида:
            55.560255236, 37.892199320
            55.560271004, 37.892419993
        в список координат [[lon, lat], [lon, lat], ...] (формат GeoJSON/Shapely)
        """
        coords = []
        lines = text.strip().split('\n')

        for line_num, line in enumerate(lines, start=1):
            line = line.strip()
            if not line:
                continue

            # Разделитель может быть запятой или пробелом
            parts = line.replace(',', ' ').split()

            if len(parts) != 2:
                raise ValueError(f"Строка {line_num}: ожидается 2 числа (широта, долгота), найдено {len(parts)}")

            try:
                lat = float(parts[0])
                lon = float(parts[1])
            except ValueError:
                raise ValueError(f"Строка {line_num}: не удалось преобразовать '{line}' в числа")

            # Валидация диапазонов
            if not (-90 <= lat <= 90):
                raise ValueError(f"Строка {line_num}: широта {lat} вне диапазона [-90, 90]")
            if not (-180 <= lon <= 180):
                raise ValueError(f"Строка {line_num}: долгота {lon} вне диапазона [-180, 180]")

            # Shapely/GeoJSON используют порядок [lon, lat]
            coords.append([lon, lat])

        if len(coords) < 3:
            raise ValueError(f"Для полигона нужно минимум 3 точки, введено {len(coords)}")

        # Автоматически замыкаем полигон, если нужно
        # По идее, ненужно, вроде полигон умеет и сам замыкаться)
        # if coords[0] != coords[-1]:
        #     coords.append(coords[0])

        return coords