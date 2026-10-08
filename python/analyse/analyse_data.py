import os
from dotenv import load_dotenv
import pandas as pd
import folium
from folium.plugins import HeatMap
from sqlalchemy import create_engine
load_dotenv()
# 1. Настройки подключения к вашей базе данных PostgreSQL
# Формат: postgresql://пользователь:пароль@хост:порт/имя_базы
db_url = f'postgresql://{os.getenv("POSTGRES_USER")}:{os.getenv("POSTGRES_PASSWORD")}@localhost:5432/{os.getenv("POSTGRES_DB")}'
engine = create_engine(db_url)

# 2. SQL-запрос для получения координат
# Мы берем только те инциденты, у которых удалось определить координаты
query = """
SELECT 
    start_loc.latitude, 
    start_loc.longitude
FROM 
    traffic_situations ts
JOIN 
    tmc_locations start_loc 
    ON (ts.location->'alert_c'->>'primary_location_code')::INT = start_loc.location_code
WHERE 
    start_loc.latitude IS NOT NULL 
    AND start_loc.longitude IS NOT NULL;
"""

print("Выгрузка данных из базы...")
df = pd.read_sql(query, engine)
print(f"Найдено инцидентов с координатами: {len(df)}")

# 3. Инициализация карты Folium
# Центрируем карту примерно по центру Швейцарии (широта 46.8, долгота 8.2)
# 'CartoDB positron' — это светлая и неброская подложка карты,
# на которой яркие пятна тепловой карты смотрятся контрастнее всего.
basemap_api_key = os.getenv("BASEMAP_API_KEY")

m = folium.Map(
    location=[46.8, 8.2],
    zoom_start=8,
    tiles=f'https://basemaps.cartocdn.com/light_all/{{z}}/{{x}}/{{y}}.png?key={basemap_api_key}',
    attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
)

# 4. Подготовка данных для тепловой карты
# HeatMap принимает на вход список списков: [[lat1, lon1], [lat2, lon2], ...]
heat_data = [[row['latitude'], row['longitude']] for index, row in df.iterrows()]

# 5. Настройка и добавление слоя тепловой карты
# radius - радиус "пятна" от одной точки (в пикселях)
# blur - степень размытия краев пятна
HeatMap(
    heat_data,
    radius=15,
    blur=10,
    min_opacity=0.3,
    gradient={0.2: 'blue', 0.4: 'lime', 0.6: 'yellow', 0.8: 'orange', 1.0: 'red'}
).add_to(m)

# 6. Сохранение результата в HTML-файл
output_file = '../../output/switzerland_traffic_heatmap.html'
m.save(output_file)

print(f"Готово! Тепловая карта сохранена в файл: {output_file}")
print("Просто откройте этот файл в любом веб-браузере (Chrome, Safari, Edge).")