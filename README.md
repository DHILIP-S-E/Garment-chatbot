# Indian Dress Chatbot Web App

A smart chatbot interface for Indian dress enthusiasts built using Streamlit, Gemini Pro API, and SQLite database with 100+ Indian dress entries.

## Features

- Smart chatbot interface built in Streamlit for Indian dress recommendations
- Gemini Pro API handles conversation in a natural and culturally-aware way
- SQLite database with 100+ traditional and modern Indian dresses
- When a user asks questions like "I'm attending an Indian wedding, what should I wear?":
  - Gemini API responds with culturally appropriate recommendations
  - The app checks the SQLite DB for matching garments
  - Displays matching garments with images, prices, and buy links

## Garment Database Includes

- 100+ traditional and modern Indian dresses
- Categories: Saree, Lehenga, Salwar Kameez, Kurta Pajama, Sherwani, Dhoti, etc.
- Attributes: name, category, fabric, price, size, availability, image_url, buy_link, region, occasion

## Streamlit UI Features

- User input chat box
- Sidebar with chat history
- Dropdown filters for garment category and occasion
- Product cards with images and buy links
- Streamlit Cloud deployment ready

## Technical Structure

- `main.py` — Streamlit frontend and app logic
- `db.py` — SQLite database interactions for Indian dress lookup
- `gemini_chat.py` — Gemini Pro API integration with Indian cultural context
- `utils.py` — Helper functions (formatting, chat memory, product cards)
- `test_app.py` — Unit tests for the application

## Setup and Installation

1. Clone this repository
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
3. Set up your Gemini API key:
   - Copy `.env.example` to `.env`
   - Add your Gemini API key to the `.env` file
   ```
   GEMINI_API_KEY=your_api_key_here
   ```
4. Run the app:
   ```
   streamlit run main.py
   ```

## Running Tests

To run the unit tests:
```
python -m unittest test_app.py
```

## Usage

1. Type your Indian dress-related questions in the text input field
2. Use the category and occasion filters in the sidebar to browse specific garment types
3. View your chat history in the sidebar
4. The app will provide recommendations based on your queries and display matching garments with images and buy links

## Example Queries

- "I'm attending an Indian wedding, what should I wear?"
- "Can you suggest a traditional outfit for Diwali celebration?"
- "What's a good formal wear for men in South Indian style?"
- "Show me silk sarees for wedding occasions"
- "I need a comfortable kurta pajama for summer"

## Deployment

This app is fully deployable on Streamlit Cloud:

1. Push your code to a GitHub repository
2. Log in to [Streamlit Cloud](https://streamlit.io/cloud)
3. Create a new app pointing to your repository
4. Add your Gemini API key as a secret in the Streamlit Cloud settings

## License

MIT

