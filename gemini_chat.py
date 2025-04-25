import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class GeminiChatbot:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set in environment variables")
        
        # Validate API key format
        if not isinstance(api_key, str) or not api_key.startswith('AI'):
            raise ValueError("Invalid GEMINI_API_KEY format. Key should be a string starting with 'AI'")
            
        try:
            genai.configure(api_key=api_key)
            
            # Test the API key by making a simple request
            test_model = genai.GenerativeModel('gemini-2.0-flash')
            test_model.generate_content("test")
        except Exception as e:
            raise ValueError(f"Failed to initialize Gemini API: {str(e)}")
        
        # Configure the model
        generation_config = {
            "temperature": float(os.getenv("GEMINI_TEMPERATURE", 0.7)),
            "top_p": float(os.getenv("GEMINI_TOP_P", 0.8)),
            "top_k": int(os.getenv("GEMINI_TOP_K", 40)),
            "max_output_tokens": int(os.getenv("GEMINI_MAX_OUTPUT_TOKENS", 2048)),
        }
        
        # Initialize the model with proper safety settings
        safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
        ]
        
        try:
            self.model = genai.GenerativeModel(
                model_name="gemini-2.5-flash-preview-04-17",
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            self.chat = self.model.start_chat(history=[])
        except Exception as e:
            raise ValueError(f"Failed to initialize chat model: {str(e)}")
    
    def suggest_garment(self, user_query):
        """
        Use Gemini to suggest a suitable garment based on the user's query.
        
        Args:
            user_query (str): The user's query about what to wear
            
        Returns:
            tuple: (suggestion_text, suggested_garments)
                - suggestion_text: Gemini's response with garment suggestions
                - suggested_garments: List of specific garment types mentioned in the response
        """
        try:
            # Clean up the query text first
            cleaned_query = self._clean_query(user_query)
            
            # Create a prompt for Gemini to suggest garments
            prompt = f"""You are an expert in Indian ethnic wear fashion.
            The user is asking: "{user_query}"
            
            Please suggest appropriate Indian garments for this situation. Be specific about:
            1. The exact type of garment (e.g., Dhoti, Saree, Lehenga, Kurta Pajama, etc.)
            2. Why this garment would be appropriate for the occasion/context
            3. Any styling tips or accessories that would complement the outfit
            
            Format your response in a conversational way, but make sure to clearly mention specific garment types.
            """
            
            response = self.model.generate_content(prompt)
            if not response.text:
                return "I'm sorry, I couldn't generate a suggestion at this time.", []
            
            suggestion_text = response.text
            
            # Extract mentioned garment types from the response
            extraction_prompt = f"""
            From the following fashion advice, extract ONLY the specific Indian garment types mentioned:
            
            {suggestion_text}
            
            Return ONLY a JSON array of strings with the garment types (e.g., ["Dhoti", "Kurta", "Saree"]).
            Include only the main garment categories like: Saree, Lehenga, Kurta Pajama, Sherwani, Dhoti, Salwar Kameez, etc.
            Do not include accessories or general terms.
            """
            
            extraction_response = self.model.generate_content(extraction_prompt)
            if not extraction_response.text:
                return suggestion_text, []
                
            # Clean and parse the response
            garments_text = extraction_response.text.strip()
            if garments_text.startswith("```json"):
                garments_text = garments_text[7:-3]  # Remove ```json and ``` markers
                
            try:
                import json
                suggested_garments = json.loads(garments_text)
                return suggestion_text, suggested_garments
            except json.JSONDecodeError:
                return suggestion_text, []
                
        except Exception as e:
            print(f"Error suggesting garment: {e}")
            return "I encountered an error while processing your request. Please try again.", []
        
    def generate_response(self, user_query, relevant_garments=None):
        """
        Generate a response to the user's query, including product information if available.
        
        Args:
            user_query (str): The user's query
            relevant_garments (pandas.DataFrame): Dataframe of relevant garments from the database
            
        Returns:
            str: The formatted response including Gemini's suggestion and product information
        """
        try:
            # Clean up the query text first
            cleaned_query = self._clean_query(user_query)
            
            # Create context from relevant garments if available
            context = ""
            if relevant_garments is not None and not relevant_garments.empty:
                context = """Based on our available inventory, here are some relevant garments:\n"""
                for _, garment in relevant_garments.iterrows():
                    context += f"- {garment['name']} ({garment['category']}) - {garment['fabric_type']}, "
                    context += f"₹{garment['price']:.2f}, Available in {garment['sizes']}\n"
                    context += f"  Suitable for: {garment['occasion']} occasions, {garment['region']} region\n"
                    
                prompt = f"""You are an expert in Indian ethnic wear fashion.
                The original user query was: "{user_query}"
                The cleaned query is: "{cleaned_query}"
                
                Context: {context}
                
                Provide a helpful response that:
                1. References the actual garments from our inventory
                2. Explains why these options would work well
                3. Gives styling tips specific to these items
                4. If relevant, suggests occasions where these would be appropriate
                5. If the original query had typos or was unclear, acknowledge that you understood what they meant
                
                DO NOT include product images or links in the main response text.
                Keep the response natural and conversational."""
                
                response = self.model.generate_content(prompt)
                if response.text:
                    response_text = response.text
                    
                    # Always add formatted product details section at the end
                    response_text += "\n\n---\n\n## Available Products:\n"
                    for _, garment in relevant_garments.iterrows():
                        response_text += f"\n### {garment['name']}\n"
                        if garment.get('image_url'):
                            response_text += f"![{garment['name']}]({garment['image_url']})\n"
                        response_text += f"- **Price:** ₹{garment['price']:.2f}\n"
                        response_text += f"- **Fabric:** {garment['fabric_type']}\n"
                        response_text += f"- **Sizes:** {garment['sizes']}\n"
                        response_text += f"- **Occasion:** {garment['occasion']}\n"
                        response_text += f"- **Region:** {garment['region']}\n"
                        if garment.get('buy_link'):
                            response_text += f"\n[🛍️ Buy Now]({garment['buy_link']})\n"
                        response_text += "\n---\n"
                    
                    return response_text
                    
            else:
                # First, get a garment suggestion from Gemini
                suggestion_text, _ = self.suggest_garment(user_query)
                
                # No matches found, provide the suggestion with a note
                prompt = f"""You are an expert in Indian ethnic wear fashion.
                The original user query was: "{user_query}"
                The cleaned query is: "{cleaned_query}"
                
                Unfortunately, we don't have exact matches in our current inventory.
                
                Please provide:
                1. If the query had typos, acknowledge that you understood what they meant
                2. A brief explanation of why we couldn't find exact matches
                3. General advice about Indian ethnic wear related to their query
                4. Alternative suggestions they might consider
                5. Tips for what to look for when shopping
                
                Keep it helpful and encouraging, but make it clear we're giving general advice since we don't have exact matches."""
                
                response = self.model.generate_content(prompt)
                if response.text:
                    return "No matching items found in our collection, but here's a suggestion...\n\n" + suggestion_text
                    
            return "I apologize, but I couldn't generate a response. Please try rephrasing your question."
            
        except Exception as e:
            print(f"Error generating response: {e}")
            return f"I encountered an error while processing your request. Please try again. Error: {str(e)}"

    def _clean_query(self, query):
        """Clean up the query by correcting common misspellings."""
        # Split query into words
        words = query.lower().split()
        
        # Common misspellings and their corrections
        corrections = {
            'sker': 'search',
            'eith': 'with',
            'chst': 'chat',
            'bot': 'bot',
            'sare': 'saree',
            'lhnga': 'lehenga',
            'dhti': 'dhoti',
            'kurtha': 'kurta',
            'pajma': 'pajama',
            'shrvani': 'sherwani',
            'nehru': 'nehru',
            'jkt': 'jacket',
            'slwr': 'salwar',
            'kamez': 'kameez',
            'ctn': 'cotton',
            'slk': 'silk',
            'weding': 'wedding',
            'festval': 'festival',
            'casuall': 'casual',
            'formall': 'formal',
            'pty': 'party'
        }
        
        # Clean words one by one
        cleaned_words = []
        for word in words:
            # Check if word needs correction
            if word in corrections:
                cleaned_words.append(corrections[word])
            else:
                # Use fuzzy matching for other words
                from difflib import get_close_matches
                all_known_words = list(corrections.values())
                matches = get_close_matches(word, all_known_words, n=1, cutoff=0.6)
                if matches:
                    cleaned_words.append(matches[0])
                else:
                    cleaned_words.append(word)
        
        return ' '.join(cleaned_words)
    
    def extract_search_criteria(self, user_query):
        """
        Extract search criteria from user query for database filtering.
        Also includes garment suggestions from Gemini.
        """
        try:
            # Clean the query first
            cleaned_query = self._clean_query(user_query)
            
            # Get garment suggestions from Gemini
            _, suggested_garments = self.suggest_garment(user_query)
            
            # Ask the model to analyze the query for search criteria
            analysis_prompt = f"""
            Analyze this query for Indian garment search criteria:
            Original query: "{user_query}"
            Cleaned query: "{cleaned_query}"
            
            Extract these fields if present:
            - gender (Men/Women)
            - category (Saree/Lehenga/Kurta/etc.)
            - occasion (Wedding/Festival/Casual/etc.)
            - fabric_type
            - region (North/South/East/West)
            
            Format: JSON only
            """
            
            response = self.model.generate_content(analysis_prompt)
            if not response.text:
                # If no criteria extracted, use suggested garments as categories
                criteria = {}
                if suggested_garments:
                    criteria["category"] = suggested_garments[0]  # Use the first suggested garment
                return criteria
                
            # Clean and parse the response
            criteria_text = response.text.strip()
            if criteria_text.startswith("```json"):
                criteria_text = criteria_text[7:-3]  # Remove ```json and ``` markers
                
            try:
                import json
                criteria = json.loads(criteria_text)
                
                # Remove empty values
                criteria = {k: v for k, v in criteria.items() if v}
                
                # If no category was found but we have suggested garments, use them
                if "category" not in criteria and suggested_garments:
                    criteria["category"] = suggested_garments[0]  # Use the first suggested garment
                    
                return criteria
            except json.JSONDecodeError:
                # If JSON parsing fails, use suggested garments as categories
                criteria = {}
                if suggested_garments:
                    criteria["category"] = suggested_garments[0]  # Use the first suggested garment
                return criteria
                
        except Exception as e:
            print(f"Error extracting search criteria: {e}")
            return {}

# For testing purposes
if __name__ == "__main__":
    chatbot = GeminiChatbot()
    
    # Test response generation
    response = chatbot.generate_response("I need a t-shirt for summer")
    print(response)