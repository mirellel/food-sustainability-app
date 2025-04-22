import requests
import pandas as pd

# get data through API
LUKE_API_URL = "https://statdb.luke.fi:443/PxWeb/api/v1/en/LUKE/02%20Maatalous/08%20Muut/02%20Ravintotase/03_Elintarvikkeiden_kulutus_50.px"

def fetch_food_consumption():
    query = {
        "query": [
            {
                "code": "Vuosi",
                "selection": {
                    "filter": "item",
                    "values": [str(year) for year in range(1950, 2024)]
                }
            },
            {
                "code": "Elintarvike",
                "selection": {
                    "filter": "item",
                    "values":["Vilja","Peruna","Maito","Liha","Kala","Vehnä","Ruis","Ohra","Kaura","Riisi","Naudanliha","Sianliha","Siipikarjanliha","Kananmunat","Tilamaito","Täysmaito","Kevytmaito","Rasvaton maito","Piimä","Jogurtti","Juusto","Voi"],
                    "valueTexts":["Cereals","Potatoes","Milk","Meat","Fish","Wheat","Rye","Barley","Oats","Rice","Beef and veal","Pork","Poultry meat","Eggs","Farm milk","Whole milk","Low-fat milk","Skimmed milk","Sour milk","Yoghurt","Cheese","Butter"]
                }
            }
        ],
        "response": {
            "format": "json"
        }
    }

    response = requests.post(LUKE_API_URL, json=query)
    response.raise_for_status()
    data_json = response.json()

    records = []
    for item in data_json['data']:
        year = item['key'][0]
        product = item['key'][1]
        value = item['values'][0]
        records.append({"Year": int(year), product: float(value) if value != ".." else None})

    df = pd.DataFrame(records)
    df = df.groupby("Year").first().reset_index()
    # rename values to english
    english_names = ["Cereals","Potatoes","Milk","Meat","Fish","Wheat","Rye","Barley","Oats","Rice","Beef and veal","Pork","Poultry meat","Eggs","Farm milk","Whole milk","Low-fat milk","Skimmed milk","Sour milk","Yoghurt","Cheese","Butter"]
    rename_dict = dict(zip(df.columns[1:], english_names))
    df = df.rename(columns=rename_dict)
    return df