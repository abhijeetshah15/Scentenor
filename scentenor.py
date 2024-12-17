import streamlit as st
import requests
import pandas as pd
from openai import OpenAI

# OpenWeatherMap API Key
weather_api_key = st.secrets["WEATHER_API_KEY"]

# Title with branding
st.title("🌟 Scentenor Recommender 🌟")

# Initialize session state
if "perfume_list" not in st.session_state:
    st.session_state.perfume_list = []

# Layout for Weather Input
with st.container():
    st.subheader("🌦️ Weather Details")
    city = st.text_input("Enter your City:", placeholder="e.g., Ahmedabad")

    # Initialize variables with default values
    temp, humidity, weather_desc = None, None, ""

    try:
        if city:
            # Fetch weather data
            weather_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={weather_api_key}&units=metric"
            weather_data = requests.get(weather_url).json()

            if weather_data.get("cod") == 200:
                temp = weather_data["main"]["temp"]
                humidity = weather_data["main"]["humidity"]
                weather_desc = weather_data["weather"][0]["description"]
            else:
                temp, humidity, weather_desc = 25.0, 50, ""  # Reset to defaults
    except Exception:
        temp, humidity, weather_desc = 25.0, 50, ""  # Reset to defaults

    col1, col2 = st.columns(2)
    with col1:
        temp = st.number_input("Temperature (°C):", value=temp, step=0.1)
    with col2:
        humidity = st.number_input("Humidity (%):", value=humidity, step=1)

    weather_desc = st.text_input(
        "Weather Description:", value=weather_desc if weather_desc else "", placeholder="e.g., cool and breezy"
    )

st.markdown("---")

# File Upload Section
with st.container():
    st.subheader("📂 Upload Your Perfume List")
    uploaded_file = st.file_uploader("Upload CSV or XLSX file:")
    perfume_list = []

    if uploaded_file:
        try:
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            elif uploaded_file.name.endswith(".xlsx"):
                df = pd.read_excel(uploaded_file, engine='openpyxl')

            # Handle case-insensitive column matching for 'perfumes'
            df.columns = df.columns.str.lower()
            if "perfumes" in df.columns:
                perfume_list = df["perfumes"].dropna().tolist()
                st.session_state.perfume_list = perfume_list
                st.success("Perfume list uploaded successfully!")
                with st.expander("Click to view your uploaded perfume list"):
                    for perfume in perfume_list:
                        st.write(f"- {perfume}")
            else:
                st.error("The uploaded file must contain a column named 'perfumes'.")
        except Exception as e:
            st.error(f"Error reading the file: {e}")
    else:
        perfume_list = st.session_state.perfume_list

st.markdown("---")

# Optional Fragrance Type and Age Input
with st.container():
    st.subheader("🌸 Optional Preferences")
    fragrance_type = st.selectbox(
        "Choose a Fragrance Type (optional):", 
        ["None", "Floral", "Woody", "Citrus", "Fresh", "Oriental", "Spicy", "Aquatic"]
    )

    age_group = st.text_input(
        "Add an age group for recommendation (optional):",
        placeholder="e.g., 50-year-old, teen, adult"
    )

st.markdown("---")

# Event and Recommendation
with st.container():
    st.subheader("🎉 Event Details & Recommendation")
    event = st.text_input(
        "Describe your event (optional, e.g., 'formal dinner at 7 PM'):",
        placeholder="e.g., Outdoor wedding in the evening (optional)"
    )

    if st.button("✨ Get Recommendation ✨"):
        if len(perfume_list) > 0:
            # Formulate the ChatGPT query
            message = f"""
            My shop has these perfumes: {', '.join(perfume_list)}. 
            I want to recommend perfumes to a customer going to {event if event else 'an unknown event'}.
            The weather in {city} is {weather_desc} ({temp}°C, {humidity}% humidity).
            Recommend perfumes from the list based on the following:
            - (Optional) Weather: adjust for temperature and humidity.
            - (Optional) Event type: consider the formality or setting.
            - Fragrance Type (optional): {fragrance_type if fragrance_type != "None" else "No specific fragrance type"}.
            - Age Group (optional): {age_group if age_group else "No specific age group"}.

            Carefully analyze the list and avoid random suggestions. Provide a comprehensive list of recommended perfumes, and include:
            1. The recommended perfumes.
            2. A brief reason for each choice.
            3. Application tips for each recommended perfume.
            """

            # ChatGPT API Call
            client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": """
                    You are a professional perfume consultant. Your job is to analyze the provided list of perfumes and carefully recommend the most suitable perfumes based on:
                    - Weather conditions (optional: temperature, humidity, general description).
                    - Event type (optional: formal, casual, outdoor, etc.).
                    - Optional fragrance type preference.
                    - Optional age group.
                    Avoid random recommendations and give thoughtful, tailored advice. Provide a comprehensive list of recommendations, and avoid limiting the response to a small number of options.
                    """},
                    {"role": "user", "content": message}
                ]
            )

            recommendation = response.choices[0].message.content

            # Display the recommendation
            st.success("🎁 Here's your recommendation:")
            st.write(recommendation)
        else:
            st.error("Please ensure the perfume list is provided.")