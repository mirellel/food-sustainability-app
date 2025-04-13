import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests

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

# load data
food_consumption = fetch_food_consumption()
food_consumption = food_consumption.infer_objects(copy=False)

# define min and max years for filtering
min_year = int(food_consumption['Year'].min())
max_year = int(food_consumption['Year'].max())


# make data numeric and interpolate
for col in food_consumption.columns[1:]:
    food_consumption[col] = pd.to_numeric(food_consumption[col], errors='coerce')

food_consumption = food_consumption.interpolate(method='linear')

# app
st.title("📊 Finnish Food Consumption Over Time")
st.subheader("Explore food consumption trends")

# dropdown menu, default values meat milk and eggs
products = st.multiselect("Select food types", options=food_consumption.columns[1:], default=['Milk', 'Meat', 'Eggs'])

# slider for filtering years
year_range = st.slider("Select Year Range",
                       min_value=min_year,
                       max_value=max_year,
                       value=(1950, max_year))
filtered_data = food_consumption[(food_consumption['Year'] >= year_range[0]) & (food_consumption['Year'] <= year_range[1])]

# plot data
fig, ax = plt.subplots(figsize=(10, 5))
for product in products:
    ax.plot(filtered_data['Year'], filtered_data[product], label=product)

ax.set_title("Food Consumption Over Time")
ax.set_xlabel("Year")
ax.set_ylabel("kg/person/year")
ax.legend()
ax.grid(True)

st.pyplot(fig)

