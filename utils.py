import pandas as pd
import streamlit as st
from datetime import datetime
import re
import requests
from PIL import Image
from io import BytesIO
from difflib import get_close_matches

def format_price(price):
    """Format price with currency symbol."""
    return f"${price:.2f}"

def format_chat_message(role, content, timestamp=None):
    """Format chat messages for display."""
    if timestamp is None:
        timestamp = datetime.now().strftime("%H:%M")
        
    if role == "user":
        return {
            "role": "user",
            "content": content,
            "timestamp": timestamp,
            "avatar": "👤"
        }
    else:
        return {
            "role": "assistant",
            "content": content,
            "timestamp": timestamp,
            "avatar": "🤖"
        }

def initialize_session_state():
    """Initialize session state variables if they don't exist."""
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
        
    if "selected_category" not in st.session_state:
        st.session_state.selected_category = "All"
        
    if "garment_data" not in st.session_state:
        st.session_state.garment_data = None

def display_chat_message(message):
    """Display a formatted chat message in the Streamlit UI."""
    role = message["role"]
    content = message["content"]
    timestamp = message.get("timestamp", "")
    avatar = message.get("avatar", "")
    
    if role == "user":
        st.markdown(f"""
        <div style="display: flex; align-items: flex-start; margin-bottom: 10px;">
            <div style="background-color: #e0e0e0; border-radius: 20px; padding: 10px 15px; max-width: 80%; margin-left: auto;">
                <p style="margin: 0;">{content}</p>
                <p style="margin: 0; font-size: 0.8em; text-align: right; color: #666;">{timestamp} {avatar}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # For assistant messages, use two containers: one for the message and one for products
        st.markdown(f"""
        <div style="display: flex; align-items: flex-start; margin-bottom: 10px;">
            <div style="background-color: #f0f7ff; border-radius: 20px; padding: 10px 15px; max-width: 80%;">
                <div style="margin-bottom: 10px;">
        """, unsafe_allow_html=True)
        
        # Split content into main message and product section
        if "---\n\n## Available Products:" in content:
            main_message, products_section = content.split("---\n\n## Available Products:", 1)
            # Render main message
            st.markdown(main_message)
            # Render products section with proper image rendering
            st.markdown(f"## Available Products:{products_section}")
        else:
            # If no product section, render the whole content
            st.markdown(content)
            
        # Close the message container
        st.markdown(f"""
                </div>
                <p style="margin: 0; font-size: 0.8em; text-align: right; color: #666;">{timestamp} {avatar}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

def display_garment_results(garments_df):
    """Display garment search results in a formatted way with images and buy links."""
    if garments_df.empty:
        st.warning("No matching garments found.")
        return
    
    # Custom CSS for product cards
    st.markdown("""
    <style>
    .product-card {
        border: 1px solid #ddd;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 25px;
        background: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .product-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    .product-image {
        width: 100%;
        max-width: 300px;
        margin: 0 auto;
        display: block;
        border-radius: 8px;
        object-fit: cover;
        aspect-ratio: 3/4;
    }
    .buy-button {
        background-color: #FF4B4B;
        color: white !important;
        padding: 10px 20px;
        border-radius: 25px;
        text-decoration: none;
        display: inline-block;
        margin-top: 15px;
        text-align: center;
        width: 100%;
        font-weight: bold;
        transition: background-color 0.2s ease;
    }
    .buy-button:hover {
        background-color: #FF3333;
        text-decoration: none;
    }
    .price-tag {
        font-size: 1.4em;
        font-weight: bold;
        color: #FF4B4B;
        margin: 15px 0;
    }
    .product-title {
        font-size: 1.3em;
        font-weight: bold;
        color: #333;
        margin: 10px 0;
        min-height: 3em;
    }
    .product-details {
        margin: 15px 0;
        color: #555;
    }
    .availability-badge {
        display: inline-block;
        padding: 5px 10px;
        border-radius: 15px;
        font-size: 0.9em;
        margin: 10px 0;
    }
    .availability-badge.in-stock {
        background-color: #e6f4ea;
        color: #1e8e3e;
    }
    .availability-badge.out-of-stock {
        background-color: #fce8e6;
        color: #d93025;
    }
    @media (max-width: 768px) {
        .product-card {
            margin: 10px 0;
        }
        .product-title {
            font-size: 1.1em;
            min-height: auto;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Create responsive columns - 2 on desktop, 1 on mobile
    for i in range(0, len(garments_df), 2):
        cols = st.columns([1, 1])
        for j in range(2):
            if i + j < len(garments_df):
                garment = garments_df.iloc[i + j]
                with cols[j]:
                    st.markdown("""
                    <div class="product-card">
                    """, unsafe_allow_html=True)
                    
                    # Display image with proper handling of missing/invalid URLs
                    image_url = garment.get("image_url", "")
                    if image_url:
                        try:
                            # Validate image URL with proper error handling
                            is_valid, error_msg = validate_image_url(image_url)
                            if is_valid:
                                st.image(
                                    image_url,
                                    use_container_width=True,
                                    caption=garment["name"],
                                    output_format="auto"
                                )
                            else:
                                st.error(f"Invalid image: {error_msg}")
                                st.image(
                                    "https://placehold.co/300x400/lightgray/darkgray?text=Image+Not+Available",
                                    use_container_width=True,
                                    caption=garment["name"]
                                )
                        except Exception as e:
                            st.error(f"Error loading image: {str(e)}")
                            st.image(
                                "https://placehold.co/300x400/lightgray/darkgray?text=Error+Loading+Image",
                                use_container_width=True,
                                caption=garment["name"]
                            )
                    else:
                        st.image(
                            "https://placehold.co/300x400/lightgray/darkgray?text=No+Image",
                            use_container_width=True,
                            caption=garment["name"]
                        )
                    
                    # Product name as header
                    st.markdown(f'<div class="product-title">{garment["name"]}</div>', unsafe_allow_html=True)
                    
                    # Price with special styling
                    st.markdown(f'<div class="price-tag">{format_price(garment["price"])}</div>', unsafe_allow_html=True)
                    
                    # Availability badge
                    if garment["available"]:
                        st.markdown('<div class="availability-badge in-stock">✓ In Stock</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="availability-badge out-of-stock">✕ Out of Stock</div>', unsafe_allow_html=True)
                    
                    # Product details
                    st.markdown(f"""
                    <div class="product-details">
                        <strong>Category:</strong> {garment['category']}<br>
                        <strong>Fabric:</strong> {garment['fabric_type']}<br>
                        <strong>Sizes:</strong> {garment['sizes']}<br>
                        <strong>Gender:</strong> {garment['gender']}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Display occasion if available
                    if occasion := garment.get("occasion"):
                        st.markdown(f'<div class="product-details"><strong>Occasion:</strong> {occasion}</div>', 
                                  unsafe_allow_html=True)
                    
                    # Display region if available
                    if region := garment.get("region"):
                        st.markdown(f'<div class="product-details"><strong>Region:</strong> {region}</div>', 
                                  unsafe_allow_html=True)
                    
                    # Description
                    if description := garment.get("description"):
                        st.markdown(f'<div class="product-details"><em>{description}</em></div>', 
                                  unsafe_allow_html=True)
                    
                    # Buy/View button
                    if buy_link := garment.get("buy_link"):
                        st.markdown(f'''
                            <a href="{buy_link}" target="_blank" class="buy-button">
                                🛍️ Buy Now / View Details
                            </a>
                        ''', unsafe_allow_html=True)
                    else:
                        st.info("🔍 Product link not available")
                    
                    st.markdown("</div>", unsafe_allow_html=True)

def extract_keywords(text):
    """Extract potential search keywords from user input with fuzzy matching."""
    # List of common Indian garment-related keywords
    garment_keywords = [
        # Indian garment types
        "saree", "sari", "lehenga", "choli", "salwar", "kameez", "kurta", "pajama",
        "sherwani", "dhoti", "lungi", "anarkali", "churidar", "patiala", "ghagra",
        "dupatta", "turban", "pagri", "nehru jacket", "bandhgala", "jodhpuri",
        
        # Fabrics
        "silk", "cotton", "banarasi", "chiffon", "georgette", "chanderi", "khadi",
        "linen", "brocade", "crepe", "organza", "tussar", "kanjivaram", "patola",
        "bandhani", "phulkari", "zari", "gota", "pashmina",
        
        # Occasions
        "wedding", "festival", "diwali", "holi", "eid", "pongal", "navratri", "durga puja",
        "casual", "formal", "party", "sangeet", "mehendi", "reception",
        
        # Regions
        "north indian", "south indian", "east indian", "west indian", "punjabi", "gujarati",
        "rajasthani", "bengali", "kashmiri", "maharashtrian", "tamil", "kerala",
        
        # Gender
        "men", "women", "unisex", "kids", "children"
    ]
    
    # Split the input text into words and clean them
    words = re.findall(r'\b\w+\b', text.lower())
    
    # Find fuzzy matches for each word
    found_keywords = []
    for word in words:
        matches = get_fuzzy_matches(word, garment_keywords)
        found_keywords.extend(matches)
    
    return list(set(found_keywords))  # Remove duplicates

def parse_query_for_filters(query):
    """Parse user query to extract potential filter criteria with fuzzy matching."""
    filters = {}
    words = re.findall(r'\b\w+\b', query.lower())
    
    # Gender detection with fuzzy matching
    gender_terms = {
        "men": ["men", "mens", "man", "gents", "male"],
        "women": ["women", "womens", "woman", "ladies", "female"],
        "unisex": ["unisex", "universal", "anyone"]
    }
    
    for word in words:
        for gender, terms in gender_terms.items():
            if any(get_fuzzy_matches(word, terms, cutoff=0.8)):
                filters["gender"] = gender.capitalize()
                break
    
    # Occasion detection with fuzzy matching
    occasion_terms = {
        "Wedding": ["wedding", "shaadi", "marriage", "vivah"],
        "Festival": ["festival", "diwali", "holi", "navratri", "puja", "celebration"],
        "Casual": ["casual", "daily", "regular", "everyday"],
        "Formal": ["formal", "office", "business", "work"],
        "Party": ["party", "celebration", "function", "event"]
    }
    
    for word in words:
        for occasion, terms in occasion_terms.items():
            if any(get_fuzzy_matches(word, terms, cutoff=0.8)):
                filters["occasion"] = occasion
                break
    
    # Region detection with fuzzy matching
    region_terms = {
        "North": ["north", "punjabi", "rajasthani", "kashmiri", "delhi"],
        "South": ["south", "tamil", "kerala", "karnataka", "andhra"],
        "East": ["east", "bengali", "oriya", "assam", "bengal"],
        "West": ["west", "gujarati", "marathi", "maharashtrian", "goa"]
    }
    
    for word in words:
        for region, terms in region_terms.items():
            if any(get_fuzzy_matches(word, terms, cutoff=0.8)):
                filters["region"] = region
                break
    
    # Fabric detection with fuzzy matching
    fabrics = {
        "Silk": ["silk", "resham"],
        "Cotton": ["cotton", "suti"],
        "Georgette": ["georgette", "jorjet"],
        "Chiffon": ["chiffon", "shifon"],
        "Banarasi": ["banarasi", "banaras"],
        "Chanderi": ["chanderi"],
        "Khadi": ["khadi", "khaddar"],
        "Linen": ["linen"],
        "Brocade": ["brocade", "broket"],
        "Crepe": ["crepe", "krep"],
        "Organza": ["organza"],
        "Tussar": ["tussar", "tussah", "tasar"],
        "Kanjivaram": ["kanjivaram", "kanjeevaram", "kanchipuram"]
    }
    
    for word in words:
        for fabric, terms in fabrics.items():
            if any(get_fuzzy_matches(word, terms, cutoff=0.8)):
                filters["fabric_type"] = fabric
                break
    
    # Category detection with fuzzy matching
    categories = {
        "Saree": ["saree", "sari", "shari"],
        "Lehenga": ["lehenga", "lehnga", "lehenga choli"],
        "Salwar Kameez": ["salwar", "kameez", "salvar", "kamij"],
        "Kurta": ["kurta", "kurti"],
        "Sherwani": ["sherwani", "shirwani"],
        "Dhoti": ["dhoti", "dhuti", "doti"],
        "Indo-Western": ["indo western", "fusion"],
        "Nehru Jacket": ["nehru", "nehru jacket", "bandh gala"],
        "Vesti": ["vesti", "lungi", "mundu"]
    }
    
    for word in words:
        for category, terms in categories.items():
            if any(get_fuzzy_matches(word, terms, cutoff=0.8)):
                filters["category"] = category
                break
    
    return filters

def get_fuzzy_matches(word, word_list, cutoff=0.6):
    """Get fuzzy matches for a word from a list of words."""
    matches = get_close_matches(word.lower(), [w.lower() for w in word_list], n=3, cutoff=cutoff)
    return [w for w in word_list if w.lower() in matches]

def format_db_results_for_display(df):
    """Format database results for display in chat."""
    if df.empty:
        return "I couldn't find any matching garments in our inventory."
    
    result = "Here are some items that might interest you:\n\n"
    
    for _, row in df.iterrows():
        availability = "In Stock" if row["available"] else "Out of Stock"
        result += f"• **{row['name']}** - {format_price(row['price'])} ({availability})\n"
        result += f"  {row['description']}\n"
        
        # Add occasion if available
        if "occasion" in row and row["occasion"]:
            result += f"  Occasion: {row['occasion']}\n"
            
        result += f"  Sizes: {row['sizes']}\n"
        
        # Add buy link if available
        if "buy_link" in row and row["buy_link"]:
            result += f"  [View/Buy]({row['buy_link']})\n"
            
        result += "\n"
        
    return result

def validate_image_url(url):
    """Validate if a URL points to a valid image."""
    try:
        # Check if URL is empty
        if not url:
            return False, "Image URL cannot be empty"
            
        # Check file extension
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        has_valid_extension = any(url.lower().endswith(ext) for ext in valid_extensions)
        if not has_valid_extension:
            return False, f"URL must end with one of: {', '.join(valid_extensions)}"
        
        try:
            # Verify image accessibility with increased timeout and headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, timeout=10, headers=headers, verify=False)
            if response.status_code == 200:
                try:
                    # Try to open the image to verify it's valid
                    image = Image.open(BytesIO(response.content))
                    return True, None
                except:
                    return False, "Invalid image format"
            return False, f"Failed to access image (Status: {response.status_code})"
        except requests.RequestException as e:
            return False, f"Network error: {str(e)}"
    except Exception as e:
        return False, str(e)



