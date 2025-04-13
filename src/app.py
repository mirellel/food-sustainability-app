import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# load data
food_consumption = pd.read_csv("/data/Luke_Maa_Ravtase_03_20250413-163420.csv")
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
products = st.multiselect("Select meat types", options=food_consumption.columns[1:], default=['Meat', 'Milk', 'Eggs'])

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

