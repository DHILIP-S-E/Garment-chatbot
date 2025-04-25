import streamlit as st
import pandas as pd
from db import GarmentDatabase
import os
from dotenv import load_dotenv
from utils import validate_image_url

load_dotenv()

def admin_page():
    st.title("👔 Garment Admin Panel")
    
    # Initialize database
    db = GarmentDatabase()
    
    # Store edited data in session state
    if "edited_data" not in st.session_state:
        st.session_state.edited_data = None
    
    # Tabs for different admin functions
    tab1, tab2 = st.tabs(["Add New Garment", "Edit Existing Garments"])
    
    with tab1:
        st.header("Add New Garment")
        with st.form("add_garment_form", clear_on_submit=True):
            # Basic Information
            name = st.text_input("Product Name*", help="Enter the name of the garment")
            category = st.selectbox("Category*", [
                "Saree", "Lehenga", "Salwar Kameez", "Kurta Pajama", 
                "Sherwani", "Dhoti", "Nehru Jacket", "Indo-Western", "Vesti"
            ])
            
            # Description and Details
            col1, col2 = st.columns(2)
            with col1:
                fabric_type = st.text_input("Fabric Type*", help="E.g., Cotton, Silk, etc.")
                sizes = st.text_input("Available Sizes*", help="E.g., S,M,L,XL or 38,40,42")
                price = st.number_input("Price*", min_value=0.0, format="%.2f")
                gender = st.selectbox("Gender", ["Men", "Women", "Unisex"])
            
            with col2:
                season = st.selectbox("Season", ["All", "Summer", "Winter", "Monsoon"])
                region = st.selectbox("Region", ["North", "South", "East", "West"])
                occasion = st.selectbox("Occasion", [
                    "Wedding", "Festival", "Casual", "Formal", "Party"
                ])
                available = st.checkbox("Available in Stock", value=True)
            
            description = st.text_area("Description", help="Detailed description of the garment")
            
            # Image URL with live preview
            image_col1, image_col2 = st.columns([2, 1])
            with image_col1:
                image_url = st.text_input(
                    "Image URL*", 
                    help="Link to product image (must end with .jpg, .jpeg, .png, .gif, or .webp)"
                )
            with image_col2:
                if image_url:
                    is_valid, error_msg = validate_image_url(image_url)
                    if is_valid:
                        st.image(image_url, caption="Image Preview", width=200)
                    else:
                        st.error(error_msg)
                        st.image("https://via.placeholder.com/200x200?text=Invalid+Image", width=200)
                else:
                    st.image("https://via.placeholder.com/200x200?text=No+Image", width=200)
            
            buy_link = st.text_input("Buy Link", help="Link to purchase the product")
            
            submit_button = st.form_submit_button("Add Garment")
            
            if submit_button:
                if not all([name, category, fabric_type, sizes, price, image_url]):
                    st.error("Please fill in all required fields marked with *")
                else:
                    # Validate image URL before saving
                    is_valid, error_msg = validate_image_url(image_url)
                    if not is_valid:
                        st.error(f"Invalid image URL: {error_msg}")
                    else:
                        try:
                            # Insert into database
                            db.cursor.execute('''
                            INSERT INTO garments (
                                name, category, fabric_type, sizes, price, available,
                                description, gender, season, image_url, buy_link, region, occasion
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                name, category, fabric_type, sizes, price, available,
                                description, gender, season, image_url, buy_link, region, occasion
                            ))
                            db.conn.commit()
                            st.success("Garment added successfully!")
                            
                            # Clear form (by rerunning the app)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error adding garment: {str(e)}")
    
    with tab2:
        st.header("Edit Existing Garments")
        
        # Search and filter options
        col1, col2 = st.columns([2, 1])
        with col1:
            search_term = st.text_input("Search garments", help="Search by name, category, or description")
        with col2:
            filter_category = st.selectbox("Filter by Category", ["All"] + db.get_all_categories())
        
        # Get and display garments
        if search_term or filter_category != "All":
            if filter_category != "All":
                garments_df = db.get_garments_by_category(filter_category)
                if search_term:
                    garments_df = garments_df[
                        garments_df['name'].str.contains(search_term, case=False) |
                        garments_df['description'].str.contains(search_term, case=False)
                    ]
            else:
                garments_df = db.search_garments(search_term)
        else:
            garments_df = db.get_all_garments()
        
        if not garments_df.empty:
            # Display as editable dataframe
            edited_df = st.data_editor(
                garments_df,
                hide_index=True,
                key="garment_editor",
                disabled=["id"],
                column_config={
                    "id": st.column_config.NumberColumn(
                        "ID",
                        help="Unique identifier",
                        disabled=True
                    ),
                    "price": st.column_config.NumberColumn(
                        "Price",
                        help="Product price",
                        min_value=0,
                        max_value=10000,
                        step=0.01,
                        format="$%.2f"
                    ),
                    "available": st.column_config.CheckboxColumn(
                        "In Stock",
                        help="Is the product available?"
                    ),
                    "image_url": st.column_config.TextColumn(
                        "Image URL",
                        help="Product image URL (must end with .jpg, .jpeg, .png, .gif, or .webp)",
                        required=True,
                        max_chars=500,
                        default=""
                    ),
                    "buy_link": st.column_config.LinkColumn(
                        "Buy Link"
                    ),
                    "description": st.column_config.TextColumn(
                        "Description",
                        help="Product description",
                        max_chars=500,
                        width="large"
                    )
                }
            )
            
            # Store edited data in session state
            st.session_state.edited_data = edited_df
            
            # Display image previews
            st.subheader("Image Previews")
            preview_cols = st.columns(4)
            
            for i, (_, row) in enumerate(edited_df.iterrows()):
                col = preview_cols[i % 4]
                with col:
                    with st.container():
                        image_url = row['image_url']
                        st.markdown(f"##### {row['name']}")
                        
                        if image_url:
                            try:
                                # Validate image URL
                                is_valid, error_msg = validate_image_url(image_url)
                                if is_valid:
                                    st.image(image_url, use_container_width=True)
                                    # Check if this is an updated image
                                    if (garments_df is not None and 
                                        row['id'] in garments_df.index and 
                                        image_url != garments_df.loc[row['id'], 'image_url']):
                                        st.caption("(Updated)")
                                else:
                                    st.error(f"Invalid image: {error_msg}")
                                    st.image("https://placehold.co/300x400/lightgray/darkgray/png?text=Invalid+Image",
                                           use_container_width=True)
                            except Exception as e:
                                st.error(f"Error loading image: {str(e)}")
                                st.image("https://placehold.co/300x400/lightgray/darkgray/png?text=Error+Loading+Image",
                                       use_container_width=True)
                        else:
                            st.image("https://placehold.co/300x400/lightgray/darkgray/png?text=No+Image",
                                   use_container_width=True)
            
            # Save changes button
            if st.button("Save Changes", type="primary"):
                try:
                    changes = edited_df.compare(garments_df)
                    if not changes.empty:
                        updates_made = False
                        error_count = 0
                        
                        for idx in changes.index:
                            row = edited_df.loc[idx]
                            changed_fields = changes.xs(idx).index.get_level_values(0).unique()
                            
                            # Prepare updates
                            updates = {
                                field: row[field]
                                for field in changed_fields
                            }
                            
                            # Validate image URL if it was changed
                            if 'image_url' in updates:
                                is_valid, error_msg = validate_image_url(updates['image_url'])
                                if not is_valid:
                                    st.error(f"Invalid image URL for {row['name']}: {error_msg}")
                                    error_count += 1
                                    continue
                            
                            # Apply updates
                            success, error = db.bulk_update_garment(row['id'], updates)
                            if success:
                                updates_made = True
                            else:
                                st.error(f"Error updating {row['name']}: {error}")
                                error_count += 1
                        
                        if updates_made:
                            if error_count == 0:
                                st.success("All changes saved successfully!")
                            else:
                                st.warning(f"Some changes were saved, but {error_count} errors occurred.")
                            st.rerun()
                        else:
                            st.error("No changes were saved due to errors.")
                    else:
                        st.info("No changes detected.")
                        
                except Exception as e:
                    st.error(f"Error saving changes: {str(e)}")
        else:
            st.info("No garments found. Add some garments using the 'Add New Garment' tab.")

if __name__ == "__main__":
    admin_page()