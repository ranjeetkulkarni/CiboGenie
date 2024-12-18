import streamlit as st
import os
import requests
import logging
import time
from langchain_groq import ChatGroq
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import create_retrieval_chain
from langchain_core.prompts import ChatPromptTemplate
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import googlemaps
from dotenv import load_dotenv
import tiktoken
from bs4 import BeautifulSoup
import wikipediaapi
from transformers import pipeline
import folium
from streamlit_folium import st_folium

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SERP_API_KEY = os.getenv("SERP_API_KEY")
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

# Validate API Keys
if not GROQ_API_KEY or not SERP_API_KEY or not GOOGLE_PLACES_API_KEY:
    logging.error("One or more API keys are missing.")
    raise ValueError("One or more API keys are missing. Please check your environment variables.")
else:
    logging.info("API keys loaded successfully.")

# Initialize Groq LLM
llm = ChatGroq(groq_api_key=GROQ_API_KEY, model_name="llama3-8b-8192")


# Token Counting Function
def count_tokens(text):
    """Count the number of tokens in the input text."""
    enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))


# Safe Summarization Function
def safe_summarize(content, token_limit=2000):
    """Summarize content to stay within token limits."""
    if count_tokens(content) > token_limit:
        summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
        return summarizer(content, max_length=300, min_length=50, do_sample=False)[0]['summary_text']
    return content


# Wikipedia API Integration
def fetch_wikipedia_summary(topic):
    """Fetch a summary of a topic from Wikipedia."""
    try:
        wiki_wiki = wikipediaapi.Wikipedia("en", user_agent="CiboGenie/1.0 (ranjeetkulkarni2505@gmail.com)")
        page = wiki_wiki.page(topic)
        if page.exists():
            return page.summary
        else:
            return "No Wikipedia data found."
    except Exception as e:
        logging.error(f"Wikipedia API Error: {str(e)}")
        return "Error fetching data from Wikipedia."


# SerpAPI Integration
def fetch_google_results(query):
    """Fetch top search results using SerpAPI."""
    try:
        url = f"https://serpapi.com/search.json?q={query}&api_key={SERP_API_KEY}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            summaries = [result["snippet"] for result in data.get("organic_results", [])[:3]]
            return " ".join(summaries)
        else:
            logging.error(f"SerpAPI error: {response.status_code}")
            return "No relevant Google search data found."
    except Exception as e:
        logging.error(f"SerpAPI Error: {str(e)}")
        return "Error fetching data from SerpAPI."


# Google Places API Integration
gmaps = googlemaps.Client(key=GOOGLE_PLACES_API_KEY)


def fetch_nearby_places(food_item, user_location):
    """Fetch top 3 nearby stores/restaurants selling the given food item."""
    try:
        places = gmaps.places_nearby(
            location=user_location,
            keyword=food_item,
            radius=5000,  # Search radius in meters
            type="store"
        )
        results = places.get("results", [])
        top_places = []
        for place in results[:5]:
            try:
                # Extract geometry
                location = place.get("geometry", {}).get("location", {})
                if not location:
                    continue  # Skip if geometry or location is missing
                
                # Add geometry to the response for compatibility with display_map
                top_places.append({
                    "name": place.get("name", "Unknown"),
                    "address": place.get("vicinity", "Address not available"),
                    "rating": place.get("rating", "No rating available"),
                    "distance": geodesic(
                        user_location,
                        (location.get("lat"), location.get("lng"))
                    ).km,
                    "geometry": {"location": location}  # Include geometry for display_map
                })
            except Exception as inner_e:
                logging.warning(f"Error processing place: {str(inner_e)}")
        return top_places
    except Exception as e:
        logging.error(f"Google Places API Error: {str(e)}")
        return None


# Display Interactive Map
def display_map(places, user_coordinates):
    """Display a map with nearby places."""
    m = folium.Map(location=user_coordinates, zoom_start=13)
    folium.Marker(
        location=user_coordinates,
        popup="Your Location",
        icon=folium.Icon(color="blue")
    ).add_to(m)
    for place in places:
        location = place.get("geometry", {}).get("location", {})
        if location:
            folium.Marker(
                location=(location.get("lat"), location.get("lng")),
                popup=f"{place.get('name', 'Unknown')} - {place.get('rating', 'No rating')}⭐",
                icon=folium.Icon(color="green")
            ).add_to(m)
    st_folium(m, width=700, height=500)


# Build Prompt Template
def build_prompt_template():
    """Build prompt template for Groq LLM."""
    prompt = ChatPromptTemplate.from_template(
        """
        Analyze the food item described below by providing a thorough, structured, and actionable breakdown. Focus on the following aspects:

        1. **Ingredients List**: Provide a serial list of all ingredients in the food item (5-10 items max)
        2. **Safe Consumption Guidelines**: Specify the safe frequency of consumption per month (in terms of time) and suggest the safe quantity to be consumed per serving, measured explicitly in grams.
        3. **Better Substitutes**: Suggest 2-3 healthier or more natural substitutes for the ingredients used in this food item that are readily available in the Indian market, keeping similar taste and texture in mind.
        4. **Comparison with Similar Products**: Compare this food item with other similar products in the food industry, identifying strengths where this product performs better (e.g., flavor, nutritional profile, packaging) and weaknesses (both 1-2)
        5. **Special Considerations**: Highlight any major dietary restrictions or health warnings, with a focus on common allergens and conditions requiring caution (e.g., diabetes, hypertension).

        Context: {context}
        User Input: {input}
        Please provide a crisp and concise and structured analysis with clear, actionable insights based on the given input.
        """
    )
    return prompt


# Streamlit UI
import streamlit as st

# Custom logo and title with the logo placed ahead of the title
import streamlit as st

# Custom logo and title with increased size
import streamlit as st

# Custom logo and title with increased size
import streamlit as st

# Custom logo and title with increased size
# Display the image using st.image()


# Custom title with larger size
# Embed an SVG custom symbol using markdown
st.markdown("""
    <div style="display: flex; align-items: center;">
        <h1 style="font-size: 50px; margin-right: 10px;">Cibo-Genie</h1>
        <img src="images/logo.png" width="100" style="margin-right: 10px;">
    </div>
""", unsafe_allow_html=True)


# Add a short description below the title
st.markdown("""
    🍴 **Cibo-Genie** is your intelligent food assistant! It helps you analyze ingredients, find nearby stores, 
    and make healthier food choices. Just enter the food item or brand name, and let Cibo-Genie provide you 
    with detailed insights and recommendations! 🥗
""")




# Sidebar: Location input
st.sidebar.header("Configuration")
location_input = st.sidebar.text_input("Enter your location (e.g., 'New Delhi, India'):", key="location_input")

# Main content: Food item input and analysis
food_input = st.text_input("Enter a food item or brand name (e.g., 'Coca-Cola drink'):", key="food_input")

if food_input:
    try:
        start = time.process_time()

        # Fetch data from Wikipedia
        wiki_summary = fetch_wikipedia_summary(food_input)
        logging.debug(f"Wikipedia Summary: {wiki_summary}")

        # Fetch data from Google (SerpAPI)
        google_summary = fetch_google_results(food_input)
        logging.debug(f"Google Search Summary: {google_summary}")

        # Summarize content if too long
        content = f"{wiki_summary} {google_summary}"
        content = safe_summarize(content, token_limit=2000)
        logging.debug(f"Summarized Content: {content}")

        # Build prompt
        prompt = build_prompt_template()
        context = {"context": content, "input": food_input}

        # Format and pass context properly
        formatted_prompt = prompt.format_prompt(**context).to_string()

        # Query Groq
        response = llm.invoke(formatted_prompt)
        logging.debug(f"Groq Response: {response}")

        # Extract only the content part of the response
        content = getattr(response, "content", "No content available.")

        # Display the food analysis
        st.subheader("Analysis Result:")
        st.write(content)

        end = time.process_time()
        elapsed_time = end - start
        logging.info(f"Processing time: {elapsed_time:.2f} seconds.")

    except Exception as e:
        logging.error(f"Error occurred: {str(e)}")
        st.error("An error occurred. Please check the logs for more details.")
else:
    st.warning("Please enter a food item.")

# If location input is given, fetch nearby places
if location_input:
    geolocator = Nominatim(user_agent="ingredient-analysis")
    user_location = geolocator.geocode(location_input)
    if user_location:
        user_coordinates = (user_location.latitude, user_location.longitude)
        # Fetch nearby places
        nearby_places = fetch_nearby_places(food_input, user_coordinates)
        if nearby_places:
            st.sidebar.subheader("Nearby Stores/Restaurants:")
            for i, place in enumerate(nearby_places, 1):
                st.sidebar.write(f"**{i}. {place['name']}**")
                st.sidebar.write(f"   - Address: {place['address']}")
                st.sidebar.write(f"   - Rating: {place['rating']}")
                st.sidebar.write(f"   - Distance: {place['distance']:.2f} km")
            display_map(nearby_places, user_coordinates)
        else:
            st.sidebar.warning("No nearby stores/restaurants found.")
    else:
        st.sidebar.warning("Location not found. Please check your input.")
