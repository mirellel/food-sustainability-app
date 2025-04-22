import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import altair as alt
from fetch_data import fetch_food_consumption

# define tabs
tab1, tab2 = st.tabs(["Food Consumption", "Food Emissions"])

# --- tab 1 setup ---
food_consumption = fetch_food_consumption().infer_objects(copy=False)
min_year = int(food_consumption['Year'].min())
max_year = int(food_consumption['Year'].max())
for col in food_consumption.columns[1:]:
    food_consumption[col] = pd.to_numeric(food_consumption[col], errors='coerce')
food_consumption = food_consumption.interpolate()


with tab1:
    tab1.title("📊 Finnish Food Consumption Over Time")
    tab1.subheader("Explore food consumption trends")

    products = tab1.multiselect(
        "Select food types",
        options=food_consumption.columns[1:],
        default=['Milk', 'Meat', 'Eggs']
    )
    year_range = tab1.slider(
        "Select Year Range",
        min_value=min_year,
        max_value=max_year,
        value=(1950, max_year)
    )

    fd = food_consumption[
        (food_consumption['Year'] >= year_range[0]) &
        (food_consumption['Year'] <= year_range[1])
    ]

    # Melt to long form
    df_long = fd.melt(id_vars='Year', value_vars=products,
                      var_name='Food', value_name='Consumption')

    line_chart = (
        alt.Chart(df_long)
        .mark_line(point=True, strokeWidth=2, interpolate='monotone')
        .encode(
            x=alt.X('Year:O', title='Year'),
            y=alt.Y('Consumption:Q', title='kg/person/year'),
            color=alt.Color('Food:N', legend=alt.Legend(title='Food')),
            tooltip=[
                alt.Tooltip('Year:O'),
                alt.Tooltip('Food:N'),
                alt.Tooltip('Consumption:Q', format='.1f')
            ]
        )
        .properties(width=700, height=400)
        .interactive()
    )

    tab1.altair_chart(line_chart, use_container_width=True)
    min_consumption = df_long['Consumption'].min()
    max_consumption = df_long['Consumption'].max()
    min_item = df_long.loc[df_long['Consumption'].idxmin(), ['Food', 'Year']]
    max_item = df_long.loc[df_long['Consumption'].idxmax(), ['Food', 'Year']]

    col1, col2 = tab1.columns(2)
    col1.metric("Lowest Consumption", 
                f"{min_item['Food']} ({min_item['Year']})", 
                f"{min_consumption:.1f} kg")
    col2.metric("Highest Consumption", 
                f"{max_item['Food']} ({max_item['Year']})", 
                f"{max_consumption:.1f} kg")

# --- tab 2 setup ---

# load data
emissions_of_food = pd.read_csv('data/greenhouse-gas-emissions-per-kilogram-of-food.csv')

# rename columns for simplification
emissions_of_food = (
    emissions_of_food
    .drop(columns=['Year'])
    .rename(columns={
        'Emissions per kilogram': 'ghg_emission',
        'Entity': 'food'
    })
)
# round to 2 decimal places
emissions_of_food['ghg_emission'] = emissions_of_food['ghg_emission'].round(2)

with tab2:
    tab2.title("🥦 Emissions of Food Products")
    tab2.subheader("CO₂‑eq emissions per kilogram of food")

    # top emitters for defaults
    top_emitters = (
        emissions_of_food
        .sort_values('ghg_emission', ascending=False)
        .head(8)['food']
        .tolist()
    )
    selected = tab2.multiselect(
        "Select food items to display",
        options=emissions_of_food['food'].unique(),
        default=top_emitters
    )

    filtered = emissions_of_food[emissions_of_food['food'].isin(selected)]

    # bar chart
    chart = (
        alt.Chart(filtered)
        .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            x=alt.X('ghg_emission:Q', title='GHG (kg CO₂‑eq per kg)'),
            y=alt.Y('food:N', sort='-x', title='Food'),
            color=alt.Color(
                'ghg_emission:Q',
                scale=alt.Scale(scheme='greens'),
                legend=alt.Legend(title='Emission Intensity')
            ),
            tooltip=[
                alt.Tooltip('food:N', title='Food'),
                alt.Tooltip('ghg_emission:Q', title='GHG (kg CO₂‑eq)', format='.2f')
            ]
        )
        .properties(height=500, width=700)
    )
    bars = chart
    text = bars.mark_text(
        align='left',
        dx=3  # shift text rightwards
    ).encode(
        text=alt.Text('ghg_emission:Q', format='.2f')
    )

    tab2.altair_chart((bars + text).configure_axis(
        labelFontSize=12, titleFontSize=14
    ).configure_legend(
        titleFontSize=13, labelFontSize=11
    ).configure_view(strokeOpacity=0), use_container_width=True)
