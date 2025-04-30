import streamlit as st
import pandas as pd
from db import GarmentDatabase
import os
from dotenv import load_dotenv
from utils import validate_image_url, save_uploaded_image

load_dotenv()

def image_upload_modal(selected_id, db, garments_df):
    """Display a modal for handling image uploads."""
    with st.form(key=f"image_upload_form_{selected_id}"):
        st.subheader("Upload New Image")
        
        # Use a unique key for each instance of file uploader
        upload_key = f"uploader_{selected_id}"
        uploaded_file = st.file_uploader(
            "Choose an image file",
            type=['png', 'jpg', 'jpeg', 'gif', 'webp'],
            key=upload_key
        )
        
        preview_col1, preview_col2 = st.columns([1, 1])
        with preview_col1:
            if uploaded_file:
                st.image(uploaded_file, caption="New Image Preview", width=200)
            else:
                st.write("No new image selected")
                
        with preview_col2:
            current_image = garments_df.loc[selected_id, 'image_url']
            if current_image and current_image.startswith('static/'):
                try:
                    st.image(current_image, caption="Current Image", width=200)
                except:
                    st.image("https://placehold.co/200x200?text=Error+Loading+Image", width=200)
            else:
                st.image("https://placehold.co/200x200?text=No+Image", width=200)
        
        submit_button = st.form_submit_button("Save Image")
        
        if submit_button and uploaded_file:
            with st.spinner("Saving image..."):
                # Save the file locally
                file_path, error = save_uploaded_image(uploaded_file)
                if error:
                    st.error(f"Error saving image: {error}")
                    return False
                else:
                    # Update the database with new image URL
                    success, error = db.update_image_url(selected_id, file_path)
                    if success:
                        st.success("✅ Image saved successfully!")
                        # Use session state to signal reload instead of modifying widget state
                        st.session_state['reload_required'] = True
                        return True
                    else:
                        st.error(f"Error updating database: {error}")
                        return False
        return False

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
            
            # Image upload section
            st.subheader("Product Image")
            image_col1, image_col2 = st.columns([2, 1])
            with image_col1:
                uploaded_file = st.file_uploader(
                    "Upload Product Image*", 
                    type=['png', 'jpg', 'jpeg', 'gif', 'webp'],
                    help="Upload product image (supported formats: PNG, JPG, JPEG, GIF, WEBP)"
                )
                if "last_uploaded_image" not in st.session_state:
                    st.session_state.last_uploaded_image = None
            
            with image_col2:
                if uploaded_file:
                    try:
                        # Show preview of uploaded image
                        st.image(uploaded_file, caption="Image Preview", width=200)
                        # Save locally when file is selected
                        if uploaded_file != st.session_state.last_uploaded_image:
                            with st.spinner("Saving image..."):
                                file_path, error = save_uploaded_image(uploaded_file)
                                if error:
                                    st.error(error)
                                    file_path = None
                                else:
                                    st.success("Image saved successfully!")
                                    st.session_state.last_uploaded_image = uploaded_file
                                    st.session_state.current_image_url = file_path
                    except Exception as e:
                        st.error(f"Error processing image: {str(e)}")
                        file_path = None
                else:
                    st.image("https://placehold.co/200x200?text=No+Image", width=200)
                    file_path = None
            
            buy_link = st.text_input("Buy Link", help="Link to purchase the product")
            
            submit_button = st.form_submit_button("Add Garment")
            
            if submit_button:
                if not all([name, category, fabric_type, sizes, price, file_path]):
                    st.error("Please fill in all required fields marked with *")
                else:
                    # Validate image URL before saving
                    is_valid, error_msg = validate_image_url(file_path)
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
                                description, gender, season, file_path, buy_link, region, occasion
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
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            search_term = st.text_input("Search garments", help="Search by name, category, or description")
        with col2:
            filter_category = st.selectbox("Filter by Category", ["All"] + db.get_all_categories())
        with col3:
            filter_occasion = st.selectbox("Filter by Occasion", ["All", "Wedding", "Festival", "Casual", "Formal", "Party"])
        
        # Always reload data from database
        garments_df = db.get_all_garments() if not search_term else db.search_garments(search_term)

        # Apply category filter
        if filter_category != "All":
            garments_df = garments_df[garments_df['category'] == filter_category]

        # Apply occasion filter
        if filter_occasion != "All":
            garments_df = garments_df[garments_df['occasion'] == filter_occasion]
        
        if not garments_df.empty:
            # Display as editable dataframe with image upload support
            edited_df = st.data_editor(
                garments_df.set_index('id'),
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
                    "image_url": st.column_config.ImageColumn(
                        "Product Image",
                        help="Click to upload a new image or paste an image URL",
                        width="medium"
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
                },
                num_rows="dynamic"
            )
            
            # Save changes button
            changes_detected = False
            last_save_state = st.session_state.get('last_save_state', {})
            
            # Check for changes in the data editor
            if not edited_df.equals(garments_df.set_index('id')):
                changes_detected = True
            
            # Check for changes in uploaded files
            if "last_uploaded_files" not in st.session_state:
                st.session_state.last_uploaded_files = {}

            # Save changes button with dynamic state
            if st.button("Save Changes", type="primary", disabled=not changes_detected):
                with st.spinner("Saving changes..."):
                    try:
                        updates_made = False
                        error_count = 0
                        
                        # Handle data editor changes
                        changes = edited_df.compare(garments_df.set_index('id'))
                        if not changes.empty:
                            for idx in changes.index:
                                row = edited_df.loc[idx]
                                changed_fields = changes.xs(idx).index.get_level_values(0).unique()
                                
                                # Prepare updates
                                updates = {}
                                for field in changed_fields:
                                    new_value = row[field]
                                    if field == 'image_url':
                                        is_valid, error_msg = validate_image_url(new_value)
                                        if not is_valid:
                                            st.error(f"Invalid image URL for {row['name']}: {error_msg}")
                                            error_count += 1
                                            continue
                                    updates[field] = new_value
                                
                                if updates:  # Only proceed if we have valid updates
                                    try:
                                        success, error = db.bulk_update_garment(idx, updates)
                                        if success:
                                            updates_made = True
                                        else:
                                            st.error(f"Error updating {row['name']}: {error}")
                                            error_count += 1
                                    except Exception as e:
                                        st.error(f"Error updating {row['name']}: {str(e)}")
                                        error_count += 1
                        
                        if updates_made:
                            if error_count == 0:
                                st.success("All changes saved successfully!")
                                # Update last save state
                                st.session_state.last_save_state = edited_df.to_dict()
                                # Clear any upload states
                                st.session_state.last_uploaded_files = {}
                            else:
                                st.warning(f"Some changes were saved, but {error_count} errors occurred.")
                            st.rerun()  # Force UI refresh
                        else:
                            if error_count > 0:
                                st.error("No changes were saved due to errors.")
                            else:
                                st.info("No changes detected to save.")
                                
                    except Exception as e:
                        st.error(f"Error saving changes: {str(e)}")

            # Update image upload modal section
            st.divider()
            st.subheader("Image Management")
            image_col1, image_col2 = st.columns([3, 1])

            with image_col1:
                selected_id = st.selectbox(
                    "Select Product to Update Image", 
                    edited_df.index.tolist(),
                    format_func=lambda x: f"{x}: {edited_df.loc[x, 'name']}"
                )

            with image_col2:
                if st.button("📷 Upload Image", type="primary"):
                    st.session_state.show_upload_modal = True
                    st.session_state.selected_product_id = selected_id

            # Show upload modal if triggered
            if st.session_state.get("show_upload_modal", False):
                modal_result = image_upload_modal(
                    st.session_state.selected_product_id,
                    db,
                    edited_df
                )
                if modal_result:
                    # Clear modal state and refresh
                    del st.session_state.show_upload_modal
                    st.rerun()

            # Show current image
            if selected_id:
                current_image = edited_df.loc[selected_id, 'image_url']
                if current_image and current_image.startswith('static/'):
                    st.image(current_image, caption="Current Product Image", width=300)
                else:
                    st.image("https://placehold.co/300x400?text=No+Image", caption="No image available")
        else:
            st.info("No garments found. Add some garments using the 'Add New Garment' tab.")

if __name__ == "__main__":
    admin_page()