from django import forms


class AnalysisForm(forms.Form):
    kad_ids = forms.CharField(
        label='Кадастровые номера',
        widget=forms.Textarea(attrs={
            'rows': 6,
            'placeholder': '86:14:0101002:715\n50:58:0020204:50',
        }),
        help_text='По одному номеру на строку. Можно через запятую или точку с запятой.',
    )
    radius_meters = forms.IntegerField(
        label='Радиус поиска (м)',
        min_value=10,
        max_value=5000,
        initial=100,
        help_text='Допустимый диапазон: от 10 до 5000 метров',
    )
    area_limit = forms.IntegerField(
        label='Мин. площадь ЗУ (м²)',
        min_value=0,
        max_value=100,
        initial=5,
        help_text='Участки меньшей площади будут исключены (0 — без ограничений)',
    )
    min_intersection_percent = forms.IntegerField(
        label='Порог пересечения сектора (%)',
        min_value=1,
        max_value=100,
        initial=25,
        help_text='Допустимый диапазон: от 1% до 100%',
    )
    draw_plots = forms.BooleanField(
        label='Создать визуализацию участков',
        required=False,
        initial=False,
        help_text='Если отмечено, для каждого участка будет создан график',
    )
    draw_kad = forms.BooleanField(
        label='Показывать кадастровые номера на графиках',
        required=False,
        initial=False,
        help_text='Добавить подписи кадастровых номеров на графиках',
    )

    def clean_kad_ids(self):
        text = self.cleaned_data['kad_ids']
        kad_ids = []
        for line in text.replace(',', '\n').replace(';', '\n').splitlines():
            kad_id = line.strip()
            if kad_id and not kad_id.startswith('#'):
                kad_ids.append(kad_id)
        if not kad_ids:
            raise forms.ValidationError('Введите хотя бы один кадастровый номер.')
        return kad_ids
