import pandas as pd
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
# 1. Укажите путь к распакованной папке (замените на свой, если нужно)
# Предполагается, что скрипт лежит рядом с папкой CH_104_E1_4_9_7.5_LTEF
data_dir = '../../tmc/CH_104_E1_4_9_7.5_LTEF'

print("Чтение исходных файлов DAT...")
# Читаем данные. DATEX II файлы разделены точкой с запятой (;). Кодировка UTF-8.
df_points = pd.read_csv(os.path.join(data_dir, 'POINTS.DAT'), sep=';', encoding='utf-8')
df_names = pd.read_csv(os.path.join(data_dir, 'NAMES.DAT'), sep=';', encoding='utf-8')
df_roads = pd.read_csv(os.path.join(data_dir, 'ROADS.DAT'), sep=';', encoding='utf-8')

# Исправляем возможные проблемы с кодировкой в заголовке первой колонки
df_names = df_names.rename(columns=lambda x: x.replace('ï»¿', ''))
df_roads = df_roads.rename(columns=lambda x: x.replace('ï»¿', ''))
df_points = df_points.rename(columns=lambda x: x.replace('ï»¿', ''))

print("Сборка и обогащение данных...")
# Оставляем только нужные колонки из точек
df_tmc = df_points[['LCD', 'XCOORD', 'YCOORD', 'ROA_LCD', 'N1ID', 'CID', 'TABCD']].copy()

# 2. Присоединяем номера дорог из ROADS.DAT (по ключу ROA_LCD = LCD)
df_tmc = df_tmc.merge(
    df_roads[['LCD', 'ROADNUMBER']],
    left_on='ROA_LCD',
    right_on='LCD',
    how='left',
    suffixes=('', '_road')
)

# 3. Присоединяем текстовые названия из NAMES.DAT (по ключу N1ID = NID)
df_tmc = df_tmc.merge(
    df_names[['NID', 'NAME']],
    left_on='N1ID',
    right_on='NID',
    how='left'
)

# 4. Преобразуем координаты в нормальный GPS-формат (градусы WGS84)
# В стандарте TMC они умножены на 100 000
df_tmc['longitude'] = df_tmc['XCOORD'] / 100000.0
df_tmc['latitude'] = df_tmc['YCOORD'] / 100000.0

# 5. Приводим таблицу к итоговому, красивому виду
df_final = pd.DataFrame({
    'country_code': df_tmc['CID'],
    'table_number': df_tmc['TABCD'],
    'location_code': df_tmc['LCD'],
    'road_name': df_tmc['ROADNUMBER'],
    'description': df_tmc['NAME'],
    'latitude': df_tmc['latitude'],
    'longitude': df_tmc['longitude']
})

# Очищаем дубликаты на случай задвоений в исходниках
df_final = df_final.drop_duplicates(subset=['location_code'])

print(f"Подготовлено {len(df_final)} локаций. Образец данных:")
print(df_final.head())

load_dotenv()
# 6. Загрузка в базу данных PostgreSQL
print("\nСохранение в PostgreSQL...")
# Замените на свои данные для подключения!
# Формат: 'postgresql://пользователь:пароль@хост:порт/имя_базы'
db_url = f'postgresql://{os.getenv("POSTGRES_USER")}:{os.getenv("POSTGRES_PASSWORD")}@localhost:5432/{os.getenv("POSTGRES_DB")}'
engine = create_engine(db_url)

# Записываем таблицу (заменит существующую, если она уже есть)
df_final.to_sql('tmc_locations', engine, if_exists='replace', index=False)

print("Готово! Таблица tmc_locations успешно загружена в базу.")