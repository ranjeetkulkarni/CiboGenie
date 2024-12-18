# Cibo-Genie

CiboGenie is a cutting-edge, AI-powered application that transforms traditional food analysis into an interactive, insightful experience. Whether you're a foodie, health-conscious individual, or professional in the food industry, CiboGenie provides structured and actionable breakdowns of food items, helping you make informed decisions about what you eat.

With integration to **Wikipedia**, **Google Search**, and advanced **AI models**, **CiboGenie** offers detailed insights on:

- 🥗 **Food Ingredients**: In-depth analysis of food components.
- ⚖️ **Safe Consumption Guidelines**: Ensures safe and healthy food consumption.
- 🍎 **Healthier Alternatives**: Recommends healthier substitutes to improve your diet.
- 🔍 **Product Comparisons**: Compares the food you're consuming with similar products in the market.
- 🏪 **Nearby Shop Recommendations**: Finds local stores where you can purchase the food item.

---

### **Features** 

- 🥗 **Food Analysis**: Provides a comprehensive breakdown of food ingredients, health considerations, and consumption guidelines.
- 🤖 **AI-Powered Recommendations**: Suggests healthier substitutes and analyzes food items based on nutrition and quality.
- 🏪 **Nearest Shops Finder**: Allows users to input their location and find the nearest shops that sell the given food item.
- 🌐 **Multi-Source Data Gathering**: Utilizes data from Wikipedia, Google, and other credible sources to provide well-rounded insights.
- 🔧 **Customizable**: Designed to adapt to specific food items, ensuring tailored recommendations.


---

## Technologies Used

- *Python*: Core programming language for the application logic.
- *Streamlit*: For building the user interface and interactive dashboard.
- *TensorFlow*: For machine learning-based recommendations and food analysis.
- *SERP API*: To gather relevant data from Google Search and to find nearby shops using location-based queries.
- *Wikipedia API*: To fetch detailed summaries and information about food items.
- *Groq API*: For natural language processing and generating insights.
- *Google Maps API*: For location-based services, including finding nearby stores.

---

## Installation

### Prerequisites
Before running CiboGenie, ensure you have the following:
- Python 3.x
- An active API Key for accessing Google, Wikipedia, and other data sources

### Steps to Set Up

1. *Clone the repository:*
    bash
    git clone https://github.com/your-username/CiboGenie.git
    cd CiboGenie
    

2. *Create and activate a virtual environment:*
    bash
    python -m venv cibogenv
    source cibogenv/bin/activate   # On Windows, use cibogenv\Scripts\activate
    

3. *Install the required dependencies:*
    bash
    pip install -r requirements.txt
    

4. *Set up the environment variables for API keys:*
    - Create a .env file in the project root and add your keys:
      env
      GOOGLE_API_KEY=your_google_api_key
      GROQ_API_KEY=your_groq_api_key
      GOOGLE_MAPS_API_KEY=your_google_maps_api_key
      

5. *Run the application:*
    bash
    streamlit run app.py
    

6. *Open the local URL* (usually [http://localhost:8501](http://localhost:8501)) in your browser to start using CiboGenie.

---

## Usage

1. *Enter a Food Item*: Type a food item (e.g., "Coke") into the input field.
2. *Get Detailed Insights*: Receive a structured, actionable breakdown, including:
    - Ingredients List
    - Safe Consumption Guidelines
    - Healthier Substitutes
    - Comparison with Similar Products
    - Special Health Considerations
3. *Add Your Location*: Input your location (city or area) to find the nearest shops where you can purchase the food item.
4. *Explore Further*: Browse through recommendations for better alternatives and dietary tips.

---

## Screenshots

### Main Dashboard
**Pizza**

![Main Dashboard](images/dashboard.jpg)

### Food Analysis Results
**Pepsi Cold Drink**

![Food Analysis](images/food_analysis.jpg)

### Shop Locator
**Pizza**

![Nearest Shops](images/shop_locator2.jpg)

---

## Contributing

We welcome contributions to make CiboGenie even better! Here’s how you can help:

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Submit a pull request

---

## License

## License

This project is licensed under the **GNU General Public License** (GPL) **Version 3, 29 June 2007**. See the [LICENSE](LICENSE) file for details.


---

## Contact

For any inquiries or feedback, feel free to reach out:

- *Email*: ranjeetkulkarni2505@gmail.com
- *Email*: iit2023064@iiita.ac.in
- *GitHub*: [CiboGenie Repository](https://github.com/ranjeetkulkarni/CiboGenie)

---

Thank you for using CiboGenie! We hope it makes your food analysis journey both insightful and exciting.