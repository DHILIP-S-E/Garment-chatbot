import unittest
import os
import pandas as pd
from db import GarmentDatabase
import utils
import tempfile
from unittest.mock import patch, MagicMock

class TestGarmentApp(unittest.TestCase):
    
    def setUp(self):
        # Create a temporary database for testing
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db').name
        self.db = GarmentDatabase(db_path=self.temp_db)
        
    def tearDown(self):
        # Close database connection
        self.db.close()
        # Remove temporary database file
        if os.path.exists(self.temp_db):
            os.remove(self.temp_db)
    
    def test_database_initialization(self):
        """Test that the database is properly initialized with sample data."""
        garments = self.db.get_all_garments()
        self.assertGreater(len(garments), 0, "Database should be populated with sample data")
        
        categories = self.db.get_all_categories()
        self.assertGreater(len(categories), 0, "Categories should be available")
        
        # Check for Indian dress categories
        indian_categories = ["Saree", "Lehenga", "Kurta Pajama", "Sherwani", "Dhoti"]
        for category in indian_categories:
            self.assertIn(category, categories, f"{category} should be in the categories")
    
    def test_search_functionality(self):
        """Test the search functionality of the database."""
        # Search for wedding clothes
        wedding_clothes = self.db.get_garments_by_criteria({"occasion": "Wedding"})
        self.assertGreater(len(wedding_clothes), 0, "Should find wedding clothes")
        
        # Search for men's clothes
        mens_clothes = self.db.get_garments_by_criteria({"gender": "Men"})
        self.assertGreater(len(mens_clothes), 0, "Should find men's clothes")
        
        # Search by category
        category = "Saree"  # Use a specific Indian dress category
        category_clothes = self.db.get_garments_by_category(category)
        self.assertGreater(len(category_clothes), 0, f"Should find clothes in category {category}")
        
        # Search by region
        north_clothes = self.db.get_garments_by_criteria({"region": "North"})
        self.assertGreater(len(north_clothes), 0, "Should find North Indian clothes")
    
    def test_chat_history(self):
        """Test saving and retrieving chat history."""
        # Save a chat interaction
        self.db.save_chat_history("What should I wear to an Indian wedding?", 
                                 "For an Indian wedding, you could consider a Banarasi Silk Saree or a Wedding Sherwani depending on your gender.")
        
        # Retrieve chat history
        history = self.db.get_recent_chat_history()
        self.assertEqual(len(history), 1, "Should have one chat history entry")
        self.assertEqual(history.iloc[0]["user_message"], "What should I wear to an Indian wedding?")
    
    def test_utils_functions(self):
        """Test utility functions."""
        # Test price formatting
        self.assertEqual(utils.format_price(149.99), "$149.99")
        
        # Test query parsing
        filters = utils.parse_query_for_filters("I need a silk saree for a wedding")
        self.assertEqual(filters.get("fabric_type"), "Silk")
        self.assertEqual(filters.get("category"), "Saree")
        self.assertEqual(filters.get("occasion"), "Wedding")
        
        # Test keyword extraction
        keywords = utils.extract_keywords("I need a silk saree for a wedding")
        self.assertIn("silk", keywords)
        self.assertIn("saree", keywords)
        self.assertIn("wedding", keywords)
        
        # Test display formatting
        test_df = pd.DataFrame({
            "name": ["Banarasi Silk Saree"],
            "category": ["Saree"],
            "fabric_type": ["Silk"],
            "sizes": ["Free Size"],
            "price": [149.99],
            "available": [True],
            "description": ["Elegant Banarasi silk saree"],
            "gender": ["Women"],
            "season": ["All"],
            "image_url": ["https://example.com/image.jpg"],
            "buy_link": ["https://example.com/buy"],
            "region": ["North"],
            "occasion": ["Wedding"]
        })
        
        result = utils.format_db_results_for_display(test_df)
        self.assertIn("Banarasi Silk Saree", result)
        self.assertIn("$149.99", result)
        self.assertIn("Wedding", result)
        self.assertIn("https://example.com/buy", result)
    
    @patch('gemini_chat.GeminiChatbot')
    def test_garment_suggestion_feature(self, MockChatbot):
        """Test the garment suggestion feature."""
        # Mock the chatbot's suggest_garment method
        mock_chatbot = MockChatbot.return_value
        mock_chatbot.suggest_garment.return_value = (
            "For a wedding, you can wear a dhoti which is a traditional Indian garment. It's elegant and appropriate for formal occasions.",
            ["Dhoti"]
        )
        
        # Mock the extract_search_criteria method
        mock_chatbot.extract_search_criteria.return_value = {"category": "Dhoti", "occasion": "Wedding"}
        
        # Test that the suggestion includes the garment type
        suggestion_text, suggested_garments = mock_chatbot.suggest_garment("I'm going to a wedding, what should I wear?")
        self.assertIn("dhoti", suggestion_text.lower())
        self.assertEqual(suggested_garments, ["Dhoti"])
        
        # Test that the search criteria includes the suggested garment
        search_criteria = mock_chatbot.extract_search_criteria("I'm going to a wedding, what should I wear?")
        self.assertEqual(search_criteria.get("category"), "Dhoti")
        
        # Test that we can find the suggested garment in the database
        dhoti_garments = self.db.search_garments("Dhoti")
        self.assertGreater(len(dhoti_garments), 0, "Should find dhoti garments in the database")
        
        # Test with a garment that doesn't exist in the database
        mock_chatbot.suggest_garment.return_value = (
            "For a beach party, you can wear a Hawaiian shirt which is colorful and casual.",
            ["Hawaiian shirt"]
        )
        
        # This should return an empty dataframe since Hawaiian shirts aren't in our Indian garment database
        hawaiian_garments = self.db.search_garments("Hawaiian shirt")
        self.assertEqual(len(hawaiian_garments), 0, "Should not find Hawaiian shirts in the database")
    
    def test_search_garments_function(self):
        """Test the search_garments function of the database."""
        # Search for a specific garment type
        dhoti_garments = self.db.search_garments("Dhoti")
        self.assertGreater(len(dhoti_garments), 0, "Should find dhoti garments")
        
        # Verify that all returned garments are of the Dhoti category
        for _, garment in dhoti_garments.iterrows():
            self.assertEqual(garment["category"], "Dhoti", "All returned garments should be Dhotis")
        
        # Search for a non-existent garment
        nonexistent_garments = self.db.search_garments("Tuxedo")
        self.assertEqual(len(nonexistent_garments), 0, "Should not find tuxedos in the database")

if __name__ == "__main__":
    unittest.main()

