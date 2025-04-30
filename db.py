import sqlite3
import os
import pandas as pd

class GarmentDatabase:
    _instance = None
    _cache = {}
    
    def __new__(cls, db_path="garment_database.db"):
        if cls._instance is None:
            cls._instance = super(GarmentDatabase, cls).__new__(cls)
            cls._instance.db_path = db_path
            cls._instance.conn = None
            cls._instance.cursor = None
            cls._instance.connect()
            cls._instance.create_tables()
        return cls._instance

    def __init__(self, db_path="garment_database.db"):
        """Initialize the database connection."""
        self.db_path = db_path

    def connect(self):
        """Connect to the SQLite database with optimized settings."""
        try:
            self.conn = sqlite3.connect(
                self.db_path, 
                check_same_thread=False,
                isolation_level="IMMEDIATE",
                timeout=30
            )
            # Performance optimizations
            self.conn.execute("PRAGMA cache_size = -2000")  # Use 2MB of cache
            self.conn.execute("PRAGMA temp_store = MEMORY")  # Store temp tables in memory
            self.conn.execute("PRAGMA synchronous = NORMAL")  # Faster writes with good safety
            self.conn.execute("PRAGMA journal_mode = WAL")  # Use Write-Ahead Logging
            self.conn.execute("PRAGMA foreign_keys = ON")
            self.conn.execute("PRAGMA busy_timeout = 5000")
            
            self.cursor = self.conn.cursor()
            print(f"Connected to database: {self.db_path}")
        except sqlite3.Error as e:
            print(f"Database connection error: {e}")
            raise
            
    def reconnect_if_needed(self):
        """Reconnect to database if connection was lost."""
        try:
            # Test connection
            self.conn.execute("SELECT 1")
        except (sqlite3.OperationalError, sqlite3.ProgrammingError):
            print("Database connection lost, reconnecting...")
            self.connect()
            
    def execute_with_retry(self, query, params=None, max_retries=3):
        """Execute a query with automatic retry on connection failure."""
        for attempt in range(max_retries):
            try:
                self.reconnect_if_needed()
                if params is None:
                    return self.cursor.execute(query)
                return self.cursor.execute(query, params)
            except sqlite3.Error as e:
                if attempt == max_retries - 1:  # Last attempt
                    raise
                print(f"Database error, retrying... ({e})")
                self.connect()  # Try to reconnect
            
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            print("Database connection closed.")
            
    def create_tables(self):
        """Create necessary tables if they don't exist."""
        try:
            # Drop existing tables first to ensure clean initialization
            self.cursor.execute('DROP TABLE IF EXISTS garments')
            self.cursor.execute('DROP TABLE IF EXISTS chat_history')
            
            # Create garments table
            self.cursor.execute('''
            CREATE TABLE garments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                fabric_type TEXT NOT NULL,
                sizes TEXT NOT NULL,
                price REAL NOT NULL,
                available BOOLEAN NOT NULL,
                description TEXT,
                gender TEXT,
                season TEXT,
                image_url TEXT,
                buy_link TEXT,
                region TEXT,
                occasion TEXT
            )
            ''')
            
            # Create chat_history table
            self.cursor.execute('''
            CREATE TABLE chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_message TEXT NOT NULL,
                bot_response TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            self.conn.commit()
            
            # Always populate initial data after creating tables
            self.populate_sample_data()
                
        except sqlite3.Error as e:
            print(f"Error creating tables: {e}")
            raise
            
    def populate_sample_data(self):
        """Populate the database with sample Indian garment data."""
        sample_garments = [
            # Sarees
            ("Banarasi Silk Saree", "Saree", "Silk", "Free Size", 149.99, True, 
             "Elegant Banarasi silk saree with gold zari work", "Women", "All", 
             "https://placehold.co/400x500/silk/white/png?text=Banarasi+Silk+Saree", 
             "https://www.amazon.com/banarasi-silk-saree", "North", "Wedding"),
            
            ("Kanjivaram Silk Saree", "Saree", "Silk", "Free Size", 199.99, True, 
             "Traditional South Indian Kanjivaram silk saree with temple border", "Women", "All", 
             "https://placehold.co/400x500/gold/white/png?text=Kanjivaram+Silk+Saree", 
             "https://www.amazon.com/kanjivaram-silk-saree", "South", "Wedding"),
            
            ("Cotton Handloom Saree", "Saree", "Cotton", "Free Size", 59.99, True, 
             "Comfortable cotton handloom saree for daily wear", "Women", "Summer", 
             "https://placehold.co/400x500/lightblue/white/png?text=Cotton+Handloom+Saree", 
             "https://www.amazon.com/cotton-handloom-saree", "East", "Casual"),
            
            ("Georgette Printed Saree", "Saree", "Georgette", "Free Size", 45.99, True, 
             "Lightweight georgette saree with modern prints", "Women", "All", 
             "https://placehold.co/400x500/pink/white/png?text=Georgette+Printed+Saree", 
             "https://www.amazon.com/georgette-printed-saree", "West", "Casual"),
            
            # Lehengas
            ("Bridal Lehenga Choli", "Lehenga", "Velvet", "S,M,L,XL", 299.99, True, 
             "Heavy embroidered bridal lehenga with zari and stonework", "Women", "Winter", 
             "https://placehold.co/400x500/red/white/png?text=Bridal+Lehenga+Choli", 
             "https://www.amazon.com/bridal-lehenga-choli", "North", "Wedding"),
            
            ("Silk Lehenga Choli", "Lehenga", "Silk", "S,M,L", 149.99, True, 
             "Festive silk lehenga with golden embroidery", "Women", "All", 
             "https://placehold.co/400x500/maroon/white/png?text=Silk+Lehenga+Choli", 
             "https://www.amazon.com/silk-lehenga-choli", "West", "Festival"),
            
            ("Cotton Chaniya Choli", "Lehenga", "Cotton", "S,M,L,XL", 79.99, True, 
             "Traditional Gujarati style chaniya choli for Navratri", "Women", "All", 
             "https://placehold.co/400x500/orange/white/png?text=Cotton+Chaniya+Choli", 
             "https://www.amazon.com/cotton-chaniya-choli", "West", "Festival"),
            
            # Salwar Kameez
            ("Anarkali Salwar Suit", "Salwar Kameez", "Georgette", "S,M,L,XL,XXL", 89.99, True, 
             "Floor length Anarkali suit with embroidered bodice", "Women", "All", 
             "https://placehold.co/400x500/teal/white/png?text=Anarkali+Salwar+Suit", 
             "https://www.amazon.com/anarkali-salwar-suit", "North", "Party"),
            
            ("Punjabi Patiala Suit", "Salwar Kameez", "Cotton", "S,M,L,XL", 69.99, True, 
             "Traditional Punjabi Patiala suit with printed dupatta", "Women", "Summer", 
             "https://placehold.co/400x500/yellow/white/png?text=Punjabi+Patiala+Suit", 
             "https://www.amazon.com/punjabi-patiala-suit", "North", "Casual"),
            
            ("Straight Cut Salwar Suit", "Salwar Kameez", "Crepe", "S,M,L,XL", 79.99, True, 
             "Elegant straight cut salwar suit for formal occasions", "Women", "All", 
             "https://placehold.co/400x500/navy/white/png?text=Straight+Cut+Salwar", 
             "https://www.amazon.com/straight-cut-salwar-suit", "North", "Formal"),
            
            # Kurta Pajama (Men)
            ("Silk Kurta Pajama", "Kurta Pajama", "Silk", "38,40,42,44", 89.99, True, 
             "Traditional silk kurta pajama for special occasions", "Men", "All", 
             "https://placehold.co/400x500/beige/black/png?text=Silk+Kurta+Pajama", 
             "https://www.amazon.com/silk-kurta-pajama", "North", "Wedding"),
            
            ("Cotton Kurta Pajama", "Kurta Pajama", "Cotton", "38,40,42,44,46", 49.99, True, 
             "Comfortable cotton kurta pajama for daily wear", "Men", "Summer", 
             "https://placehold.co/400x500/white/black/png?text=Cotton+Kurta+Pajama", 
             "https://www.amazon.com/cotton-kurta-pajama", "North", "Casual"),
            
            ("Embroidered Kurta Pajama", "Kurta Pajama", "Cotton Blend", "38,40,42,44", 69.99, True, 
             "Kurta with intricate embroidery for festive occasions", "Men", "All", 
             "https://placehold.co/400x500/green/white/png?text=Embroidered+Kurta", 
             "https://www.amazon.com/embroidered-kurta-pajama", "North", "Festival"),
            
            # Sherwani
            ("Wedding Sherwani", "Sherwani", "Silk", "38,40,42,44", 249.99, True, 
             "Royal wedding sherwani with heavy embroidery", "Men", "Winter", 
             "https://placehold.co/400x500/darkred/white/png?text=Wedding+Sherwani", 
             "https://www.amazon.com/wedding-sherwani", "North", "Wedding"),
            
            ("Indo-Western Sherwani", "Sherwani", "Polyester Blend", "38,40,42,44,46", 149.99, True, 
             "Modern Indo-Western sherwani for reception", "Men", "All", 
             "https://placehold.co/400x500/gray/white/png?text=Indo+Western+Sherwani", 
             "https://www.amazon.com/indo-western-sherwani", "North", "Party"),
            
            # Dhoti
            ("Traditional Dhoti", "Dhoti", "Cotton", "Free Size", 29.99, True, 
             "Pure cotton traditional dhoti", "Men", "All", 
             "https://placehold.co/400x500/white/black/png?text=Traditional+Dhoti", 
             "https://www.amazon.com/traditional-dhoti", "South", "Festival"),
            
            ("Silk Dhoti", "Dhoti", "Silk", "Free Size", 39.99, True, 
             "Premium silk dhoti for special occasions", "Men", "All", 
             "https://placehold.co/400x500/ivory/black/png?text=Silk+Dhoti", 
             "https://www.amazon.com/silk-dhoti", "South", "Wedding"),
            
            # Nehru Jacket
            ("Silk Nehru Jacket", "Nehru Jacket", "Silk", "38,40,42,44", 79.99, True, 
             "Elegant silk Nehru jacket for formal occasions", "Men", "All", 
             "https://placehold.co/400x500/black/white/png?text=Silk+Nehru+Jacket", 
             "https://www.amazon.com/silk-nehru-jacket", "North", "Formal"),
            
            ("Printed Nehru Jacket", "Nehru Jacket", "Cotton Blend", "38,40,42,44,46", 59.99, True, 
             "Stylish printed Nehru jacket for festive wear", "Men", "All", 
             "https://placehold.co/400x500/purple/white/png?text=Printed+Nehru+Jacket", 
             "https://www.amazon.com/printed-nehru-jacket", "North", "Festival"),
            
            # Indo-Western
            ("Indo-Western Gown", "Indo-Western", "Georgette", "S,M,L,XL", 119.99, True, 
             "Fusion Indo-Western gown for reception", "Women", "All", 
             "https://placehold.co/400x500/rose/white/png?text=Indo+Western+Gown", 
             "https://www.amazon.com/indo-western-gown", "North", "Party"),
            
            ("Indo-Western Suit", "Indo-Western", "Crepe", "S,M,L,XL", 99.99, True, 
             "Modern Indo-Western suit for women", "Women", "All", 
             "https://placehold.co/400x500/coral/white/png?text=Indo+Western+Suit", 
             "https://www.amazon.com/indo-western-suit", "North", "Party"),
            
            # Vesti (South Indian dhoti)
            ("Traditional Vesti", "Vesti", "Cotton", "Free Size", 24.99, True, 
             "Traditional South Indian vesti/dhoti", "Men", "All", 
             "https://placehold.co/400x500/cream/black/png?text=Traditional+Vesti", 
             "https://www.amazon.com/traditional-vesti", "South", "Festival"),
            
            ("Silk Vesti", "Vesti", "Silk", "Free Size", 34.99, True, 
             "Premium silk vesti for temple visits and special occasions", "Men", "All", 
             "https://placehold.co/400x500/gold/black/png?text=Silk+Vesti", 
             "https://www.amazon.com/silk-vesti", "South", "Wedding")
        ]
        
        try:
            self.cursor.executemany('''
            INSERT INTO garments (name, category, fabric_type, sizes, price, available, description, gender, season, image_url, buy_link, region, occasion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', sample_garments)
            
            self.conn.commit()
            print(f"Added {len(sample_garments)} sample Indian garments to the database.")
        except sqlite3.Error as e:
            print(f"Error populating sample data: {e}")
            
    def _get_cached_query(self, query, params=None):
        """Get cached query result if available."""
        cache_key = f"{query}:{str(params)}"
        cached_result = self._cache.get(cache_key)
        # Check if cached result exists and is not None
        if cached_result is not None:
            if isinstance(cached_result, pd.DataFrame):
                if not cached_result.empty:
                    return cached_result
            else:
                return cached_result
        return None

    def _set_cached_query(self, query, params, result, timeout=300):
        """Cache query result with timeout."""
        if result is not None:
            cache_key = f"{query}:{str(params)}"
            self._cache[cache_key] = result
            # Schedule cache cleanup after timeout
            import threading
            threading.Timer(timeout, lambda: self._cache.pop(cache_key, None)).start()

    def get_all_garments(self, use_cache=True):
        """Retrieve all garments from the database with optional caching."""
        if use_cache:
            cached = self._get_cached_query("SELECT * FROM garments")
            if cached is not None:
                return cached
            
        try:
            query = "SELECT * FROM garments"
            df = pd.read_sql_query(query, self.conn)
            if use_cache and not df.empty:
                self._set_cached_query("SELECT * FROM garments", None, df)
            return df
        except sqlite3.Error as e:
            print(f"Error retrieving garments: {e}")
            return pd.DataFrame()

    def get_garments_by_category(self, category):
        """Retrieve garments filtered by category with caching."""
        cache_key = f"category_{category}"
        cached = self._get_cached_query(cache_key)
        if cached is not None:
            return cached
            
        try:
            query = "SELECT * FROM garments WHERE category = ?"
            df = pd.read_sql_query(query, self.conn, params=(category,))
            if not df.empty:
                self._set_cached_query(cache_key, (category,), df)
            return df
        except sqlite3.Error as e:
            print(f"Error retrieving garments by category: {e}")
            return pd.DataFrame()

    def search_garments(self, search_term):
        """Search garments with optimized query."""
        try:
            search_pattern = f"%{search_term}%"
            # Use INDEXED columns for faster search
            query = """
            SELECT * FROM garments 
            WHERE name LIKE ? 
            OR category LIKE ?
            OR description LIKE ?
            """
            params = (search_pattern, search_pattern, search_pattern)
            df = pd.read_sql_query(query, self.conn, params=params)
            return df
        except sqlite3.Error as e:
            print(f"Error searching garments: {e}")
            return pd.DataFrame()
            
    def get_garments_by_criteria(self, criteria):
        """
        Get garments matching specific criteria.
        
        Args:
            criteria (dict): Dictionary of criteria to filter by
                            (e.g., {'gender': 'Men', 'season': 'Summer'})
        
        Returns:
            pandas.DataFrame: Matching garments
        """
        try:
            conditions = []
            params = []
            
            for key, value in criteria.items():
                if value:
                    conditions.append(f"{key} LIKE ?")
                    params.append(f"%{value}%")
            
            if not conditions:
                return self.get_all_garments()
                
            query = f"SELECT * FROM garments WHERE {' AND '.join(conditions)}"
            df = pd.read_sql_query(query, self.conn, params=params)
            return df
        except sqlite3.Error as e:
            print(f"Error retrieving garments by criteria: {e}")
            return pd.DataFrame()
            
    def get_all_categories(self):
        """Get list of all unique garment categories."""
        try:
            query = "SELECT DISTINCT category FROM garments ORDER BY category"
            df = pd.read_sql_query(query, self.conn)
            return df['category'].tolist()
        except sqlite3.Error as e:
            print(f"Error retrieving categories: {e}")
            return []
            
    def save_chat_history(self, user_message, bot_response):
        """Save chat interaction to history."""
        try:
            self.execute_with_retry('''
            INSERT INTO chat_history (user_message, bot_response)
            VALUES (?, ?)
            ''', (user_message, bot_response))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error saving chat history: {e}")
            
    def get_recent_chat_history(self, limit=10):
        """Retrieve recent chat history."""
        try:
            query = f"SELECT * FROM chat_history ORDER BY timestamp DESC LIMIT {limit}"
            return pd.read_sql_query(query, self.conn)
        except sqlite3.Error as e:
            print(f"Error retrieving chat history: {e}")
            return pd.DataFrame()
            
    def update_garment(self, garment_id, field_name, new_value):
        """Update a single field for a specific garment."""
        try:
            if field_name == 'image_url':
                print(f"Updating image for garment {garment_id} with new path: {new_value}")  # Debug print
                
                # Start a transaction
                self.conn.execute("BEGIN EXCLUSIVE TRANSACTION")
                
                try:
                    # Execute update
                    query = "UPDATE garments SET image_url = ? WHERE id = ?"
                    self.execute_with_retry(query, (new_value, garment_id))
                    
                    # Force commit the transaction
                    self.conn.commit()
                    
                    # Verify the update
                    verify_query = "SELECT image_url FROM garments WHERE id = ?"
                    self.cursor.execute(verify_query, (garment_id,))
                    result = self.cursor.fetchone()
                    
                    if result and result[0] == new_value:
                        print(f"Successfully verified image update for garment {garment_id}")  # Debug print
                        return True, None
                    else:
                        print(f"Failed to verify image update for garment {garment_id}")  # Debug print
                        return False, "Failed to verify update"
                        
                except Exception as e:
                    self.conn.rollback()
                    print(f"Error during image update: {str(e)}")  # Debug print
                    return False, str(e)
            else:
                # Handle other fields normally
                query = f"UPDATE garments SET {field_name} = ? WHERE id = ?"
                self.execute_with_retry(query, (new_value, garment_id))
                self.conn.commit()
                return True, None
                
        except Exception as e:
            print(f"Error updating garment: {str(e)}")  # Debug print
            return False, str(e)
            
    def get_garment_by_id(self, garment_id):
        """Get a single garment by its ID."""
        try:
            query = "SELECT * FROM garments WHERE id = ?"
            df = pd.read_sql_query(query, self.conn, params=(garment_id,))
            return None if df.empty else df.iloc[0].to_dict()  # Return as dictionary
        except sqlite3.Error as e:
            print(f"Error retrieving garment: {e}")
            return None
            
    def update_image_url(self, garment_id, new_image_url):
        """Update image URL for a specific garment with proper validation."""
        try:
            # Start transaction
            self.conn.execute("BEGIN EXCLUSIVE TRANSACTION")
            
            try:
                # Clear any cached queries that might contain this garment
                self._cache.clear()
                
                # Get current garment data including old image URL
                current_garment = self.get_garment_by_id(garment_id)
                if current_garment is None:
                    self.conn.rollback()
                    return False, "Garment not found"
                
                # Store old image path for cleanup
                old_image_url = current_garment.get('image_url')
                
                # Execute update with retry
                query = "UPDATE garments SET image_url = ? WHERE id = ?"
                self.execute_with_retry(query, (new_image_url, garment_id))
                
                # Force commit to ensure changes are written
                self.conn.commit()
                
                # Verify the update was successful
                verify_query = "SELECT image_url FROM garments WHERE id = ?"
                self.cursor.execute(verify_query, (garment_id,))
                result = self.cursor.fetchone()
                
                if result and result[0] == new_image_url:
                    # Clean up old image if it exists and is different
                    if old_image_url and old_image_url != new_image_url and old_image_url.startswith('static/'):
                        try:
                            old_image_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), old_image_url)
                            if os.path.exists(old_image_path):
                                os.remove(old_image_path)
                        except Exception as e:
                            print(f"Warning: Failed to delete old image {old_image_url}: {e}")
                    
                    return True, None
                else:
                    self.conn.rollback()
                    return False, "Failed to verify update"
                    
            except Exception as e:
                self.conn.rollback()
                return False, str(e)
                
        except Exception as e:
            if 'BEGIN EXCLUSIVE TRANSACTION' in str(e):
                return False, "Database is locked, please try again"
            return False, str(e)

    def bulk_update_garment(self, garment_id, updates):
        """Update multiple fields for a specific garment in one transaction."""
        try:
            valid_fields = [
                'name', 'category', 'fabric_type', 'sizes', 'price',
                'available', 'description', 'gender', 'season',
                'image_url', 'buy_link', 'region', 'occasion'
            ]
            
            # Validate all field names first
            invalid_fields = [field for field in updates.keys() if field not in valid_fields]
            if invalid_fields:
                raise ValueError(f"Invalid field names: {', '.join(invalid_fields)}")
            
            # Special handling for image URL
            if 'image_url' in updates:
                success, error = self.update_image_url(garment_id, updates['image_url'])
                if not success:
                    return False, f"Image URL update failed: {error}"
                del updates['image_url']  # Remove from general updates
                
            if not updates:  # If only image_url was updated or no updates
                return True, None
                
            # Handle remaining updates
            # Start transaction
            self.conn.execute("BEGIN EXCLUSIVE TRANSACTION")
            
            try:
                # Get current values to check for actual changes
                current_values = self.get_garment_by_id(garment_id)
                if current_values is None:
                    raise ValueError(f"No garment found with ID {garment_id}")
                
                # Filter out unchanged values and prepare updates
                real_updates = {k: v for k, v in updates.items() 
                              if current_values[k] != v}
                
                if not real_updates:
                    self.conn.rollback()
                    return True, None  # No changes needed
                
                # Build and execute the update query
                set_clause = ", ".join([f"{field} = ?" for field in real_updates.keys()])
                query = f"UPDATE garments SET {set_clause} WHERE id = ?"
                
                values = list(real_updates.values()) + [garment_id]
                self.execute_with_retry(query, values)
                
                # Verify the update
                updated_values = self.get_garment_by_id(garment_id)
                if all(updated_values[k] == v for k, v in real_updates.items()):
                    self.conn.commit()
                    return True, None
                else:
                    self.conn.rollback()
                    return False, "Update verification failed"
                    
            except Exception as e:
                self.conn.rollback()
                raise e
                
        except Exception as e:
            if 'BEGIN EXCLUSIVE TRANSACTION' in str(e):
                return False, "Database is locked, please try again"
            return False, str(e)

