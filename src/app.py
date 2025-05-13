import os
import streamlit as st
import pandas as pd
import altair as alt
from fetch_data import fetch_food_consumption

# change background to mint green
st.markdown("""
    <style>
    .stApp {
        background-color: #f5fdf4;  /* soft mint green */
    }
    </style>
    """, unsafe_allow_html=True)

if 'show_intro' not in st.session_state:
    st.session_state.show_intro = True

# show an info card  when opening the application
if st.session_state.show_intro:
    with st.expander("ℹ️ Welcome to the Food Emissions App! (click to hide)", expanded=True):
        st.markdown("""
        👋 **Welcome!** This app helps you explore food consumption and related greenhouse gas (GHG) emissions.
        
        ### 🧭 Tabs Overview:
        - **Food Consumption**: See trends in food consumption over time.
        - **Emissions of Food Products**: View GHG emissions per kilogram of food items.
        - **Your Diet Calculator**: Estimate your own diet’s weekly and annual emissions.

        🔍 Use filters and sliders to explore the data. Colors indicate emission intensity (green = low, red = high).
        """)
        if st.button("❌ Close This Message"):
            st.session_state.show_intro = False

# define tabs
tab1, tab2, tab3 = st.tabs(["📊 Food Consumption", "🌍 Food Emissions", "🧮 Your Diet Emissions"])

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
            color=alt.Color('Food:N', legend=alt.Legend(title='Food'),
                            scale=alt.Scale(scheme='viridis')),
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
    tab1.markdown("### Per-Food Min and Max Consumption")

    for food in products:
        food_data = df_long[df_long['Food'] == food]
        min_val = food_data['Consumption'].min()
        max_val = food_data['Consumption'].max()
        min_year = food_data.loc[food_data['Consumption'].idxmin(), 'Year']
        max_year = food_data.loc[food_data['Consumption'].idxmax(), 'Year']

        col1, col2 = tab1.columns(2)
        col1.metric(f"{food} - Lowest", f"{min_val:.1f} kg", f"({min_year})")
        col2.metric(f"{food} - Highest", f"{max_val:.1f} kg", f"({max_year})")


# --- tab 2 setup ---
current_dir = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(current_dir, 'data', 'greenhouse-gas-emissions-per-kilogram-of-food.csv')
data_path_2 = os.path.join(current_dir, 'data', 'greenhouse-gas-emissions-per-kilogram-of-food-product.csv')


# load data
emissions_of_food = pd.read_csv(data_path)
emissions_of_food_2 = pd.read_csv(data_path_2)

# rename columns for simplification
emissions_of_food = (
    emissions_of_food
    .drop(columns=['Year'])
    .rename(columns={
        'Emissions per kilogram': 'ghg_emission',
        'Entity': 'food'
    })
)

# rename columns for simplification
emissions_of_food_2 = (
    emissions_of_food_2
    .drop(columns=['Year'])
    .rename(columns={
        'GHG emissions per kilogram (Poore & Nemecek, 2018)': 'ghg_emission',
        'Entity': 'food'
    })
)
# round to 2 decimal places
emissions_of_food['ghg_emission'] = emissions_of_food['ghg_emission'].round(2)

new_rows = emissions_of_food_2[~emissions_of_food_2['food'].isin(emissions_of_food['food'])]

# now concatenate the new rows
combined_food_emissions = pd.concat([emissions_of_food, new_rows], ignore_index=True)
combined_food_emissions = combined_food_emissions.sort_values(by='food').reset_index(drop=True)

with tab2:
    tab2.title("🥦 Emissions of Food Products")
    tab2.subheader("CO₂‑eq emissions per kilogram of food 🌍")

    # top emitters for defaults
    selected = tab2.multiselect(
        "Select food items to display",
        options=combined_food_emissions['food'].unique(),
        default= ['Coffee', 'Beef (beef herd)', 'Avocados', 'Bread', 'Eggs', 'Milk']
    )

    filtered = combined_food_emissions[combined_food_emissions['food'].isin(selected)]

    # bar chart
    chart = (
        alt.Chart(filtered)
        .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            x=alt.X('ghg_emission:Q', title='GHG (kg CO₂‑eq per kg)'),
            y=alt.Y('food:N', sort='-x', title='Food'),
            color=alt.Color(
                'ghg_emission:Q',
                    scale=alt.Scale(
                    domain=[combined_food_emissions['ghg_emission'].min(), combined_food_emissions['ghg_emission'].max()],

                    range=['#6fbf73', '#EF2F06']  # green to red
                ),
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
    
    # show reference point for emissions
    tab2.markdown("### 🌍 Emissions Reference Points")
    tab2.markdown(
        """
        To help interpret GHG emissions, here are some typical reference values:

        - 🚌 **1 km by diesel bus** ≈ 0.105 kg CO₂‑eq  
        - ✈️ **1 km of air travel (economy passenger)** ≈ 0.133 kg CO₂‑eq  
        - 🍌 **1 banana** ≈ 0.08 kg CO₂‑eq  
        - 📦 **1 delivery by van (urban)** ≈ 0.5–1.0 kg CO₂‑eq
        These can help place food emissions in context.
        """)

# --- tab 3 setup ---
with tab3:
    tab3.title("🧮 Your Diet Emissions Calculator")
    tab3.subheader("Estimate your weekly CO₂‑eq emissions from food 🌱")

    food_options = combined_food_emissions['food'].unique()

    if 'diet_quantities' not in st.session_state:
        st.session_state.diet_quantities = {}

    selected_foods = st.multiselect(
        "Choose foods to include in your weekly diet:",
        options=food_options,
        default=list(st.session_state.diet_quantities.keys())
    )

    for food in list(st.session_state.diet_quantities.keys()):
        if food not in selected_foods:
            del st.session_state.diet_quantities[food]

    st.markdown("### 🍽️ Enter Weekly Quantities")
    cols = st.columns(2)

    for i, food in enumerate(selected_foods):
        with cols[i % 2]:
            qty = st.number_input(
                f"{food} (kg/week)", min_value=0.0, step=0.1,
                format="%.2f", key=f"qty_{food}",
                value=st.session_state.diet_quantities.get(food, 0.0)
            )
            st.session_state.diet_quantities[food] = qty

    if st.button("🔍 Calculate Emissions"):
        results = []
        for food, amount in st.session_state.diet_quantities.items():
            emission_factor = combined_food_emissions.loc[
                combined_food_emissions['food'] == food, 'ghg_emission'
            ].values[0]
            weekly_emissions = amount * emission_factor
            results.append({'food': food, 'weekly_kg_CO2': weekly_emissions})

        result_df = pd.DataFrame(results)
        total_weekly = result_df['weekly_kg_CO2'].sum()
        total_annual = total_weekly * 52

        col1, col2 = st.columns(2)
        col1.metric("🌿 Weekly Emissions", f"{total_weekly:.2f} kg CO₂‑eq")
        col2.metric("🌍 Annual Emissions", f"{total_annual:.2f} kg CO₂‑eq")

        chart = (
            alt.Chart(result_df)
            .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
            .encode(
                x=alt.X('weekly_kg_CO2:Q', title='Weekly Emissions (kg CO₂‑eq)'),
                y=alt.Y('food:N', sort='-x'),
                color=alt.Color(
                    'weekly_kg_CO2:Q',
                    scale=alt.Scale(range=['#6fbf73', '#EF2F06']),
                    legend=alt.Legend(title='Emission Intensity')
                ),
                tooltip=[
                    alt.Tooltip('food:N', title='Food'),
                    alt.Tooltip('weekly_kg_CO2:Q', title='Weekly CO₂‑eq', format='.2f')
                ]
            )
            .properties(height=400)
        )

        st.altair_chart(chart, use_container_width=True)
