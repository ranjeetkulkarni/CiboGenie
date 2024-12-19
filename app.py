import streamlit as st
import os
import requests
import logging
import time
import PyPDF2
from sentence_transformers import SentenceTransformer
import faiss
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
logging.basicConfig(level=logging.INFO)

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

# Safe Summarization Function
def safe_summarize(content, token_limit=2000):
    """Summarize content to stay within token limits."""
    if count_tokens(content) > token_limit:
        summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
        return summarizer(content, max_length=300, min_length=50, do_sample=False)[0]['summary_text']
    return content

# Token Counting Function
def count_tokens(text):
    """Count the number of tokens in the input text."""
    enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))

# Extract Text from Multiple PDFs
def extract_text_from_pdfs(pdf_paths):
    text = ""
    for pdf_path in pdf_paths:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text()
    return text

# Generate Embeddings from Text
def generate_embeddings(text):
    model = SentenceTransformer('all-MiniLM-L6-v2')
    chunks = text.split("\n")  # Split by line or chunk text however required
    embeddings = model.encode(chunks)
    return chunks, embeddings

# Store Embeddings in FAISS Index
def create_faiss_index(embeddings):
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)  # Add embeddings to the index
    return index

# Search for Relevant PDF Content
def search_pdf(query, index, pdf_chunks):
    model = SentenceTransformer('all-MiniLM-L6-v2')
    query_embedding = model.encode([query])  # Encode the query
    D, I = index.search(query_embedding, k=3)  # Get top 3 closest results
    relevant_docs = [pdf_chunks[i] for i in I[0]]
    return relevant_docs

# Fetch Wikipedia Summary
def fetch_wikipedia_summary(topic):
    try:
        wiki_wiki = wikipediaapi.Wikipedia("en", user_agent="CiboGenie/1.0")
        page = wiki_wiki.page(topic)
        if page.exists():
            return page.summary
        else:
            return "No Wikipedia data found."
    except Exception as e:
        logging.error(f"Wikipedia API Error: {str(e)}")
        return "Error fetching data from Wikipedia."

# Fetch Google Results
def fetch_google_results(query):
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

# Combine Context from Wikipedia and Google
def hybrid_context_aggregation(wiki_summary, google_summary):
    combined_context = ""
    if wiki_summary and "No Wikipedia data" not in wiki_summary:
        combined_context = f"Wikipedia: {wiki_summary} "
    if google_summary and "No relevant Google search" not in google_summary:
        combined_context += f"Google Search: {google_summary} "
    return combined_context.strip() if combined_context.strip() else "Insufficient data from reliable sources."

# Google Maps API Integration for nearby places
gmaps = googlemaps.Client(key=GOOGLE_PLACES_API_KEY)

def fetch_nearby_places(food_item, user_location):
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
                location = place.get("geometry", {}).get("location", {})
                if not location:
                    continue
                top_places.append({
                    "name": place.get("name", "Unknown"),
                    "address": place.get("vicinity", "Address not available"),
                    "rating": place.get("rating", "No rating available"),
                    "distance": geodesic(
                        user_location,
                        (location.get("lat"), location.get("lng"))
                    ).km,
                    "geometry": {"location": location}
                })
            except Exception as inner_e:
                logging.warning(f"Error processing place: {str(inner_e)}")
        return top_places
    except Exception as e:
        logging.error(f"Google Places API Error: {str(e)}")
        return None

# Display Map with Nearby Places
def display_map(places, user_coordinates):
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
                popup=f"{place.get('name', 'Unknown')} - {place.get('rating', 'No rating')}\u2b50",
                icon=folium.Icon(color="green")
            ).add_to(m)
    st_folium(m, width=700, height=500)

# Build Prompt Template for Groq LLM
def build_prompt_template():
    """Build prompt template for Groq LLM."""
    prompt = ChatPromptTemplate.from_template(
        """
        Analyze the food item described below by providing a comprehensive, structured, and actionable breakdown. Focus on delivering precise and practical insights for each of the following aspects:

        1. **Ingredients List**: 
           - List all ingredients present in the food item, with quantities explicitly mentioned (5-10 ingredients max).
           - For each ingredient, provide a brief description of any associated health risks or hazards, including allergens or substances that may cause reactions in sensitive individuals.
        
        2. **Safe Consumption Guidelines**: 
           - Define the safe frequency of consumption for this food item on a monthly basis (e.g., how often it is safe to consume per month).
           - Specify the recommended serving size in grams, ensuring it is within safe nutritional limits. Consider general health guidelines, caloric intake, and any special dietary needs.
        
        3. **Healthier Substitutes**:
           - Suggest 2-3 healthier or more natural substitutes for the ingredients used in this food item, considering the flavor profile, texture, and overall nutritional value.
           - The substitutes should be commonly available in the Indian market.
        
        4. **Comparison with Similar Products**:
           - Compare this food item with 2-3 similar products in the market, highlighting strengths where it outperforms its competitors (e.g., better taste, superior nutritional content, better packaging).
           - Identify at least one or two areas where this product falls short compared to similar products (e.g., cost, nutritional deficiencies, environmental impact).
        
        5. **Special Considerations**:
           - Identify any dietary restrictions, health warnings, or conditions that require special attention (e.g., allergies, diabetes, hypertension).
           - Focus on any ingredients or aspects that may pose a risk to specific consumer groups, and suggest alternatives where applicable.
        
        6. **Other Facts**:
           - Provide any additional, relevant information about the product that hasn't been covered in the previous sections, with a focus on nutritional value, environmental impact, or unique features of the product.

        Context: {context}
        User Input: {input}

        Please provide a crisp and concise and structured analysis with clear, actionable insights based on the given input.
        """
    )
    return prompt

# Streamlit Interface
st.markdown("""
    <div style="display: flex; align-items: center;">
        <h1 style="font-size: 50px; margin-right: 10px;">Cibo-Genie</h1>
        
    </div>
""", unsafe_allow_html=True)

# Add a short description below the title
st.markdown("""
    🍴 **Cibo-Genie** is your intelligent food assistant! It helps you analyze ingredients, find nearby stores, 
    and make healthier food choices. Just enter the food item or brand name, and let Cibo-Genie provide you 
    with detailed insights and recommendations! 🥗
""")

# Sidebar: Location Input
st.sidebar.header("Configuration")
location_input = st.sidebar.text_input("Enter your location (e.g., 'New Delhi, India'):", key="location_input")

# Main Content
st.subheader("Food Analysis and General Questions")

# Small Input Field: Food Analysis
food_input = st.text_input("Enter a food item for detailed analysis (e.g., 'Coca-Cola drink'):", key="food_input")

# Larger Input Field: General Questions
# Larger Input Field: General Questions
general_query = st.text_area("Have a general food-related question? Ask here:", key="general_query")

# If user provides a food item for analysis
if food_input:
    try:
        start_time = time.process_time()

        # Fetch relevant context from Wikipedia and Google using RAG
        wiki_summary = fetch_wikipedia_summary(food_input)
        google_summary = fetch_google_results(food_input)

        # Combine context from Wikipedia and Google
        content = hybrid_context_aggregation(wiki_summary, google_summary)

        # Extract PDF Content
        pdf_paths = ["food_guide1.pdf", "food_guide2.pdf"]
        pdf_text = extract_text_from_pdfs(pdf_paths)
        pdf_chunks, pdf_embeddings = generate_embeddings(pdf_text)
        pdf_index = create_faiss_index(pdf_embeddings)

        # Search relevant content in PDFs
        pdf_search_results = search_pdf(food_input, pdf_index, pdf_chunks)
        content += f" PDF Search Results: {', '.join(pdf_search_results)}"

        # Summarize content to fit within token limit
        content = safe_summarize(content, token_limit=3000)

        # Build prompt and query the LLM
        prompt = build_prompt_template()
        context = {"context": content, "input": food_input}
        formatted_prompt = prompt.format_prompt(**context).to_string()

        response = llm.invoke(formatted_prompt)
        analysis_result = getattr(response, "content", "No content available.")

        # Display the analysis result
        st.subheader("Detailed Analysis Result:")
        st.write(analysis_result)

        elapsed_time = time.process_time() - start_time
        logging.info(f"Processing time: {elapsed_time:.2f} seconds.")

    except Exception as e:
        logging.error(f"Error during food analysis: {str(e)}")
        st.error("An error occurred while analyzing the food item.")

# If user provides a general query
if general_query:
    try:
        start_time = time.process_time()

        # Fetch context from Wikipedia and Google
        wiki_summary = fetch_wikipedia_summary(general_query)
        google_summary = fetch_google_results(general_query)

        # Combine context and summarize if needed
        content = hybrid_context_aggregation(wiki_summary, google_summary)
        content = safe_summarize(content, token_limit=2000)

        # Use the LLM to answer the general question
        general_prompt = ChatPromptTemplate.from_template(
            """
            Analyze the following query in a concise and comprehensive manner. Provide actionable insights, 
            useful examples, and references when applicable.
            
            Context: {context}
            User Query: {query}
            
            Please respond with structured, user-friendly information.
            """
        )
        context = {"context": content, "query": general_query}
        formatted_prompt = general_prompt.format_prompt(**context).to_string()

        response = llm.invoke(formatted_prompt)
        general_response = getattr(response, "content", "No content available.")

        # Display the response
        st.subheader("Response to Your Question:")
        st.write(general_response)

        elapsed_time = time.process_time() - start_time
        logging.info(f"Processing time: {elapsed_time:.2f} seconds.")

    except Exception as e:
        logging.error(f"Error during general query processing: {str(e)}")
        st.error("An error occurred while processing your query.")

# Sidebar: Location-Based Suggestions
if location_input:
    try:
        geolocator = Nominatim(user_agent="ingredient-analysis")
        user_location = geolocator.geocode(location_input)

        if user_location:
            user_coordinates = (user_location.latitude, user_location.longitude)
            # Fetch nearby places
            nearby_places = fetch_nearby_places(food_input, user_coordinates) if food_input else []

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
    except Exception as e:
        logging.error(f"Error during location-based suggestions: {str(e)}")
        st.sidebar.error("An error occurred while fetching location-based suggestions.")

