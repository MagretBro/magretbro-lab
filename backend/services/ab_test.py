import numpy as np
import pandas as pd
from scipy import stats


def analyze_ab_test(
    df: pd.DataFrame,
    group_column: str,
    metric_column: str,
) -> dict:
    """
    Выполняет статистический анализ A/B-теста для бинарной метрики.

    Проверяет корректность входных данных, вычисляет конверсии,
    разницу конверсий, относительный прирост и проводит z-тест
    для двух пропорций.

    Параметры:
        df (pd.DataFrame): Датафрейм с данными эксперимента.
        group_column (str): Название столбца с группами (должно быть ровно два уникальных значения).
        metric_column (str): Название столбца с бинарной метрикой (только 0 и 1).

    Возвращает:
        dict: Словарь с результатами анализа A/B-теста.

    Возбуждает:
        ValueError: Если данные не проходят проверку.
    """
    # Проверка существования group_column
    if group_column not in df.columns:
        raise ValueError(f"Столбец '{group_column}' не найден в данных.")

    # Проверка существования metric_column
    if metric_column not in df.columns:
        raise ValueError(f"Столбец '{metric_column}' не найден в данных.")

    # Проверка отсутствия пропусков
    if df[group_column].isnull().any() or df[metric_column].isnull().any():
        raise ValueError("Данные содержат пропущенные значения.")

    # Проверка, что в группе ровно два уникальных значения
    unique_groups = df[group_column].unique()
    if len(unique_groups) != 2:
        raise ValueError(
            f"Ожидалось ровно два уникальных значения в столбце '{group_column}', "
            f"но найдено {len(unique_groups)}."
        )

    # Проверка, что метрика содержит только 0 и 1
    unique_metrics = df[metric_column].unique()
    if not set(unique_metrics).issubset({0, 1}):
        raise ValueError(
            f"Метрика должна содержать только значения 0 и 1, "
            f"но найдены значения: {unique_metrics}."
        )

    # Определение групп A и B
    group_a, group_b = sorted(unique_groups)

    # Подсчёт количества наблюдений
    n_a = int((df[group_column] == group_a).sum())
    n_b = int((df[group_column] == group_b).sum())

    # Подсчёт количества конверсий
    conversions_a = int(((df[group_column] == group_a) & (df[metric_column] == 1)).sum())
    conversions_b = int(((df[group_column] == group_b) & (df[metric_column] == 1)).sum())

    # Подсчёт conversion rate
    conversion_a = conversions_a / n_a
    conversion_b = conversions_b / n_b

    # Подсчёт absolute difference
    absolute_diff = conversion_b - conversion_a

    # Подсчёт relative uplift
    if conversion_a == 0:
        relative_uplift = float("inf") if conversion_b > 0 else 0.0
    else:
        relative_uplift = (conversion_b - conversion_a) / conversion_a

    # Z-test для двух пропорций
    p_pool = (conversions_a + conversions_b) / (n_a + n_b)
    se_pool = np.sqrt(p_pool * (1 - p_pool) * (1 / n_a + 1 / n_b))

    if se_pool == 0:
        z_statistic = 0.0
        p_value = 1.0
    else:
        z_statistic = (conversion_b - conversion_a) / se_pool
        p_value = 2 * (1 - stats.norm.cdf(abs(z_statistic)))

    # Определение значимости (на уровне alpha = 0.05)
    significant = p_value < 0.05

    return {
        "group_a": str(group_a),
        "group_b": str(group_b),
        "n_a": n_a,
        "n_b": n_b,
        "conversions_a": conversions_a,
        "conversions_b": conversions_b,
        "conversion_a": conversion_a,
        "conversion_b": conversion_b,
        "absolute_diff": absolute_diff,
        "relative_uplift": relative_uplift,
        "z_statistic": z_statistic,
        "p_value": p_value,
        "significant": significant,
    }
