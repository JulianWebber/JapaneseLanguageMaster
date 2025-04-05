"""
Spaced Repetition System for Japanese language learning.

This module provides functionality for creating and managing a spaced repetition
system to optimize learning and review of Japanese grammar patterns, vocabulary,
and kanji.
"""

import streamlit as st
import pandas as pd
import math
import datetime
import json
import os
from database import get_db, UserProgress
from datetime import datetime, timedelta
import uuid
import random
import plotly.express as px
import numpy as np

class SpacedRepetitionItem:
    """
    Represents an item in the spaced repetition system.
    """
    
    def __init__(self, item_id, item_type, content, english, notes=None, tags=None):
        """
        Initialize a spaced repetition item.
        
        Args:
            item_id: Unique identifier for the item
            item_type: Type of item (e.g., "vocabulary", "kanji", "grammar")
            content: The Japanese content to learn
            english: English translation or meaning
            notes: Optional notes about the item
            tags: Optional tags for categorizing items
        """
        self.item_id = item_id
        self.item_type = item_type
        self.content = content
        self.english = english
        self.notes = notes or ""
        self.tags = tags or []
        
        # Spaced repetition data
        self.ease_factor = 2.5  # Initial ease factor
        self.interval = 0       # Initial interval in days
        self.last_reviewed = None
        self.next_review = datetime.now().date()
        self.review_count = 0
        self.history = []
    
    def review(self, quality):
        """
        Review this item and update its scheduling.
        
        Args:
            quality: Quality of recall, from 0 (complete failure) to 5 (perfect recall)
            
        Returns:
            New interval in days
        """
        # Record this review
        review_data = {
            "date": datetime.now().date().isoformat(),
            "quality": quality,
            "ease_factor": self.ease_factor,
            "interval": self.interval
        }
        
        self.history.append(review_data)
        self.review_count += 1
        self.last_reviewed = datetime.now().date()
        
        # Update ease factor (SM-2 algorithm)
        self.ease_factor = max(1.3, self.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))
        
        # Calculate new interval
        if quality < 3:
            # If quality is too low, reset interval
            self.interval = 1
        elif self.interval == 0:
            # First successful review
            self.interval = 1
        elif self.interval == 1:
            # Second successful review
            self.interval = 6
        else:
            # Subsequent reviews
            self.interval = math.ceil(self.interval * self.ease_factor)
        
        # Set next review date
        self.next_review = datetime.now().date() + timedelta(days=self.interval)
        
        return self.interval
    
    def to_dict(self):
        """
        Convert the item to a dictionary for serialization.
        
        Returns:
            Dictionary representation of the item
        """
        return {
            "item_id": self.item_id,
            "item_type": self.item_type,
            "content": self.content,
            "english": self.english,
            "notes": self.notes,
            "tags": self.tags,
            "ease_factor": self.ease_factor,
            "interval": self.interval,
            "last_reviewed": self.last_reviewed.isoformat() if self.last_reviewed else None,
            "next_review": self.next_review.isoformat(),
            "review_count": self.review_count,
            "history": self.history
        }
    
    @classmethod
    def from_dict(cls, data):
        """
        Create an item from a dictionary.
        
        Args:
            data: Dictionary with item data
            
        Returns:
            SpacedRepetitionItem instance
        """
        item = cls(
            item_id=data["item_id"],
            item_type=data["item_type"],
            content=data["content"],
            english=data["english"],
            notes=data.get("notes", ""),
            tags=data.get("tags", [])
        )
        
        # Restore spaced repetition data
        item.ease_factor = data.get("ease_factor", 2.5)
        item.interval = data.get("interval", 0)
        item.last_reviewed = datetime.fromisoformat(data["last_reviewed"]) if data.get("last_reviewed") else None
        item.next_review = datetime.fromisoformat(data["next_review"]).date()
        item.review_count = data.get("review_count", 0)
        item.history = data.get("history", [])
        
        return item

class SpacedRepetitionSystem:
    """
    Manages a collection of items for spaced repetition review.
    """
    
    def __init__(self, session_id):
        """
        Initialize the spaced repetition system.
        
        Args:
            session_id: User's session ID
        """
        self.session_id = session_id
        self.items = {}
        self.load_items()
    
    def add_item(self, item_type, content, english, notes=None, tags=None):
        """
        Add a new item to the system.
        
        Args:
            item_type: Type of item (e.g., "vocabulary", "kanji", "grammar")
            content: The Japanese content to learn
            english: English translation or meaning
            notes: Optional notes about the item
            tags: Optional tags for categorizing items
            
        Returns:
            The created item
        """
        item_id = str(uuid.uuid4())
        item = SpacedRepetitionItem(item_id, item_type, content, english, notes, tags)
        self.items[item_id] = item
        self.save_items()
        return item
    
    def get_item(self, item_id):
        """
        Get an item by ID.
        
        Args:
            item_id: The item's unique identifier
            
        Returns:
            The item, or None if not found
        """
        return self.items.get(item_id)
    
    def update_item(self, item_id, content=None, english=None, notes=None, tags=None):
        """
        Update an item's content.
        
        Args:
            item_id: The item's unique identifier
            content: New Japanese content (optional)
            english: New English translation (optional)
            notes: New notes (optional)
            tags: New tags (optional)
            
        Returns:
            True if successful, False if item not found
        """
        item = self.get_item(item_id)
        if not item:
            return False
        
        if content is not None:
            item.content = content
        if english is not None:
            item.english = english
        if notes is not None:
            item.notes = notes
        if tags is not None:
            item.tags = tags
        
        self.save_items()
        return True
    
    def delete_item(self, item_id):
        """
        Delete an item from the system.
        
        Args:
            item_id: The item's unique identifier
            
        Returns:
            True if deleted, False if not found
        """
        if item_id in self.items:
            del self.items[item_id]
            self.save_items()
            return True
        return False
    
    def review_item(self, item_id, quality):
        """
        Review an item and update its schedule.
        
        Args:
            item_id: The item's unique identifier
            quality: Quality of recall (0-5)
            
        Returns:
            The new interval, or None if item not found
        """
        item = self.get_item(item_id)
        if not item:
            return None
        
        interval = item.review(quality)
        self.save_items()
        return interval
    
    def get_due_items(self, count=10, item_type=None, tags=None):
        """
        Get items due for review.
        
        Args:
            count: Maximum number of items to return
            item_type: Optional filter by item type
            tags: Optional filter by tags
            
        Returns:
            List of due items, sorted by priority
        """
        today = datetime.now().date()
        due_items = []
        
        for item in self.items.values():
            # Check if due for review
            if item.next_review <= today:
                # Apply filters
                if item_type and item.item_type != item_type:
                    continue
                
                if tags and not any(tag in item.tags for tag in tags):
                    continue
                
                due_items.append(item)
        
        # Sort by overdue days and then by ease factor (prioritize harder items)
        due_items.sort(key=lambda x: ((today - x.next_review).days, x.ease_factor))
        
        return due_items[:count]
    
    def get_items_by_type(self, item_type):
        """
        Get items of a specific type.
        
        Args:
            item_type: Type of items to retrieve
            
        Returns:
            List of items of the specified type
        """
        return [item for item in self.items.values() if item.item_type == item_type]
    
    def get_items_by_tags(self, tags):
        """
        Get items with specific tags.
        
        Args:
            tags: List of tags to filter by
            
        Returns:
            List of items with any of the specified tags
        """
        return [item for item in self.items.values() if any(tag in item.tags for tag in tags)]
    
    def get_review_forecast(self, days=30):
        """
        Forecast reviews for the coming days.
        
        Args:
            days: Number of days to forecast
            
        Returns:
            Dictionary with dates as keys and counts as values
        """
        today = datetime.now().date()
        forecast = {(today + timedelta(days=i)).isoformat(): 0 for i in range(days)}
        
        for item in self.items.values():
            next_review = item.next_review
            days_until = (next_review - today).days
            
            if 0 <= days_until < days:
                forecast[next_review.isoformat()] += 1
        
        return forecast
    
    def get_statistics(self):
        """
        Calculate statistics about the spaced repetition system.
        
        Returns:
            Dictionary with various statistics
        """
        if not self.items:
            return {
                "total_items": 0,
                "items_by_type": {},
                "total_reviews": 0,
                "average_ease": 0,
                "review_success_rate": 0,
                "daily_items": []
            }
        
        # Count items by type
        items_by_type = {}
        for item in self.items.values():
            if item.item_type not in items_by_type:
                items_by_type[item.item_type] = 0
            items_by_type[item.item_type] += 1
        
        # Count total reviews
        total_reviews = sum(item.review_count for item in self.items.values())
        
        # Calculate average ease factor
        average_ease = sum(item.ease_factor for item in self.items.values()) / len(self.items)
        
        # Calculate review success rate
        success_reviews = 0
        for item in self.items.values():
            for review in item.history:
                if review["quality"] >= 3:
                    success_reviews += 1
        
        review_success_rate = success_reviews / total_reviews if total_reviews > 0 else 0
        
        # Count items by review date
        today = datetime.now().date()
        daily_items = []
        
        for i in range(30):
            date = today - timedelta(days=i)
            daily_count = 0
            
            for item in self.items.values():
                for review in item.history:
                    review_date = datetime.fromisoformat(review["date"]).date()
                    if review_date == date:
                        daily_count += 1
                        break
            
            daily_items.append({
                "date": date.isoformat(),
                "count": daily_count
            })
        
        return {
            "total_items": len(self.items),
            "items_by_type": items_by_type,
            "total_reviews": total_reviews,
            "average_ease": average_ease,
            "review_success_rate": review_success_rate,
            "daily_items": daily_items
        }
    
    def save_items(self):
        """
        Save items to session state.
        """
        # Save to session state
        if "srs_items" not in st.session_state:
            st.session_state.srs_items = {}
        
        # Save items for this user
        items_dict = {item_id: item.to_dict() for item_id, item in self.items.items()}
        st.session_state.srs_items[self.session_id] = items_dict
    
    def load_items(self):
        """
        Load items from session state.
        """
        if "srs_items" not in st.session_state:
            st.session_state.srs_items = {}
        
        # Load items for this user
        if self.session_id in st.session_state.srs_items:
            items_dict = st.session_state.srs_items[self.session_id]
            self.items = {item_id: SpacedRepetitionItem.from_dict(item_data) 
                         for item_id, item_data in items_dict.items()}
        else:
            self.items = {}
    
    def import_items(self, items_data):
        """
        Import items from a list of dictionaries.
        
        Args:
            items_data: List of dictionaries with item data
            
        Returns:
            Number of items imported
        """
        imported_count = 0
        
        for item_data in items_data:
            # Validate required fields
            if not all(key in item_data for key in ["content", "english", "item_type"]):
                continue
            
            # Create a new ID to avoid collisions
            item_id = str(uuid.uuid4())
            
            # Create and add the item
            item = SpacedRepetitionItem(
                item_id=item_id,
                item_type=item_data["item_type"],
                content=item_data["content"],
                english=item_data["english"],
                notes=item_data.get("notes", ""),
                tags=item_data.get("tags", [])
            )
            
            self.items[item_id] = item
            imported_count += 1
        
        if imported_count > 0:
            self.save_items()
            
        return imported_count

    def export_items(self):
        """
        Export items as a list of dictionaries.
        
        Returns:
            List of item dictionaries
        """
        return [item.to_dict() for item in self.items.values()]
    
    def bulk_add_items(self, items_list):
        """
        Add multiple items at once.
        
        Args:
            items_list: List of dictionaries with item data
            
        Returns:
            Number of items added
        """
        added_count = 0
        
        for item_data in items_list:
            # Validate required fields
            if not all(key in item_data for key in ["content", "english", "item_type"]):
                continue
            
            # Add the item
            self.add_item(
                item_type=item_data["item_type"],
                content=item_data["content"],
                english=item_data["english"],
                notes=item_data.get("notes", ""),
                tags=item_data.get("tags", [])
            )
            
            added_count += 1
        
        return added_count

def render_spaced_repetition_ui():
    """
    Render the UI for the spaced repetition system.
    """
    st.title("📚 Spaced Repetition System")
    
    st.markdown("""
    This system helps you learn Japanese more efficiently by scheduling reviews at optimal intervals.
    Items you find difficult will appear more frequently, while items you know well will appear less often.
    """)
    
    # Initialize the SRS
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    
    srs = SpacedRepetitionSystem(st.session_state.session_id)
    
    # Create tabs
    tabs = st.tabs(["Today's Reviews", "Add Items", "Browse Items", "Statistics", "Settings"])
    
    # Today's Reviews tab
    with tabs[0]:
        st.header("Today's Reviews")
        
        # Get due items
        due_items = srs.get_due_items()
        
        if not due_items:
            st.success("🎉 You're all caught up! No reviews due today.")
            
            # Show next reviews
            st.subheader("Upcoming Reviews")
            forecast = srs.get_review_forecast(7)
            days = list(forecast.keys())
            counts = list(forecast.values())
            
            if sum(counts) > 0:
                # Format dates more nicely
                formatted_days = [datetime.fromisoformat(day).strftime("%a, %b %d") for day in days]
                
                # Create a bar chart
                fig = px.bar(
                    x=formatted_days,
                    y=counts,
                    labels={"x": "Date", "y": "Items"},
                    title="Upcoming reviews in the next 7 days"
                )
                st.plotly_chart(fig)
            else:
                st.info("No upcoming reviews in the next 7 days.")
            
            # Option to add new items
            st.markdown("---")
            st.markdown("Ready to learn more? [Add new items](#add-items) to your collection.")
        else:
            # Show the first due item
            current_item = due_items[0]
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**Items remaining today:** {len(due_items)}")
            
            with col2:
                st.markdown(f"**Item type:** {current_item.item_type.capitalize()}")
            
            # Review card
            st.markdown("""
            <style>
            .review-card {
                background-color: #f9f9f9;
                padding: 20px;
                border-radius: 10px;
                border-left: 5px solid #4169e1;
                margin: 20px 0;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Display the item to review
            st.markdown("<div class='review-card'>", unsafe_allow_html=True)
            
            st.subheader("Review this item:")
            st.markdown(f"<h1 style='text-align: center; font-family: \"Noto Serif JP\", serif;'>{current_item.content}</h1>", unsafe_allow_html=True)
            
            # Hide the answer initially
            if "show_answer" not in st.session_state:
                st.session_state.show_answer = False
            
            if st.button("Show Answer", key="show_answer_btn"):
                st.session_state.show_answer = True
            
            if st.session_state.show_answer:
                st.markdown(f"<h3 style='text-align: center;'>{current_item.english}</h3>", unsafe_allow_html=True)
                
                if current_item.notes:
                    st.markdown(f"<p><em>Notes:</em> {current_item.notes}</p>", unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Only show rating options if answer is visible
            if st.session_state.show_answer:
                st.markdown("### How well did you remember this?")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if st.button("Again (0)", key="rating_0"):
                        srs.review_item(current_item.item_id, 0)
                        st.session_state.show_answer = False
                        st.rerun()
                
                with col2:
                    if st.button("Hard (3)", key="rating_3"):
                        interval = srs.review_item(current_item.item_id, 3)
                        st.success(f"Next review in {interval} day{'s' if interval != 1 else ''}")
                        st.session_state.show_answer = False
                        st.rerun()
                
                with col3:
                    if st.button("Good (4)", key="rating_4"):
                        interval = srs.review_item(current_item.item_id, 4)
                        st.success(f"Next review in {interval} day{'s' if interval != 1 else ''}")
                        st.session_state.show_answer = False
                        st.rerun()
                
                with col4:
                    if st.button("Easy (5)", key="rating_5"):
                        interval = srs.review_item(current_item.item_id, 5)
                        st.success(f"Next review in {interval} day{'s' if interval != 1 else ''}")
                        st.session_state.show_answer = False
                        st.rerun()
    
    # Add Items tab
    with tabs[1]:
        st.header("Add New Items")
        
        # Create tabs for different ways to add items
        add_tabs = st.tabs(["Add Single Item", "Bulk Add", "Import"])
        
        # Add Single Item tab
        with add_tabs[0]:
            st.subheader("Add a Single Item")
            
            # Form for adding a new item
            with st.form("add_item_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    content = st.text_area(
                        "Japanese Content",
                        placeholder="Enter Japanese text to learn",
                        key="new_item_content"
                    )
                
                with col2:
                    english = st.text_area(
                        "English Meaning",
                        placeholder="Enter English translation or meaning",
                        key="new_item_english"
                    )
                
                item_type = st.selectbox(
                    "Item Type",
                    ["vocabulary", "kanji", "grammar", "sentence", "phrase"],
                    key="new_item_type"
                )
                
                notes = st.text_area(
                    "Notes (Optional)",
                    placeholder="Add any notes, hints, or context",
                    key="new_item_notes"
                )
                
                tags = st.text_input(
                    "Tags (Optional, comma-separated)",
                    placeholder="e.g., JLPT N5, food, verbs",
                    key="new_item_tags"
                )
                
                submit = st.form_submit_button("Add Item")
                
                if submit:
                    if content and english:
                        # Process tags
                        tags_list = [tag.strip() for tag in tags.split(",")] if tags else []
                        
                        # Add the item
                        srs.add_item(
                            item_type=item_type,
                            content=content,
                            english=english,
                            notes=notes,
                            tags=tags_list
                        )
                        
                        st.success(f"Added new {item_type} item: {content}")
                        
                        # Clear the form
                        st.session_state.new_item_content = ""
                        st.session_state.new_item_english = ""
                        st.session_state.new_item_notes = ""
                        st.session_state.new_item_tags = ""
                    else:
                        st.warning("Please enter both Japanese content and English meaning.")
        
        # Bulk Add tab
        with add_tabs[1]:
            st.subheader("Bulk Add Items")
            st.markdown("Add multiple items at once, one per line.")
            
            st.markdown("""
            **Format**: Japanese content | English meaning | Type | Notes (optional) | Tags (optional, comma-separated)
            
            **Example**:
            ```
            私は学生です | I am a student | sentence | Basic self-introduction | JLPT N5, grammar
            本 | book | vocabulary | | JLPT N5, nouns
            ```
            """)
            
            bulk_text = st.text_area(
                "Enter items (one per line)",
                height=200,
                placeholder="私は学生です | I am a student | sentence | Basic self-introduction | JLPT N5, grammar\n本 | book | vocabulary | | JLPT N5, nouns",
                key="bulk_add_text"
            )
            
            if st.button("Add Items", key="bulk_add_btn"):
                if bulk_text:
                    lines = bulk_text.strip().split("\n")
                    items_to_add = []
                    
                    for line in lines:
                        parts = [part.strip() for part in line.split("|")]
                        
                        if len(parts) >= 3:
                            # Extract data from the line
                            content = parts[0]
                            english = parts[1]
                            item_type = parts[2]
                            notes = parts[3] if len(parts) > 3 else ""
                            tags = [tag.strip() for tag in parts[4].split(",")] if len(parts) > 4 and parts[4].strip() else []
                            
                            # Add to the list
                            items_to_add.append({
                                "content": content,
                                "english": english,
                                "item_type": item_type,
                                "notes": notes,
                                "tags": tags
                            })
                    
                    # Add all the items
                    added_count = srs.bulk_add_items(items_to_add)
                    st.success(f"Added {added_count} items successfully!")
                else:
                    st.warning("Please enter some items to add.")
        
        # Import tab
        with add_tabs[2]:
            st.subheader("Import Items")
            st.markdown("Import items from a CSV file.")
            
            st.markdown("""
            **Expected CSV format**:
            - Required columns: `content`, `english`, `item_type`
            - Optional columns: `notes`, `tags`
            """)
            
            # Using file uploader
            uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])
            
            if uploaded_file is not None:
                try:
                    # Read the CSV file
                    df = pd.read_csv(uploaded_file)
                    
                    # Check required columns
                    required_columns = ["content", "english", "item_type"]
                    if not all(col in df.columns for col in required_columns):
                        st.error(f"CSV file must contain these columns: {', '.join(required_columns)}")
                    else:
                        st.write(f"Found {len(df)} items in the CSV file.")
                        
                        # Preview the data
                        st.dataframe(df.head())
                        
                        if st.button("Import Items", key="import_items_btn"):
                            # Convert DataFrame to list of dictionaries
                            items_data = df.to_dict(orient="records")
                            
                            # Import the items
                            imported_count = srs.import_items(items_data)
                            st.success(f"Imported {imported_count} items successfully!")
                except Exception as e:
                    st.error(f"Error importing CSV file: {str(e)}")
    
    # Browse Items tab
    with tabs[2]:
        st.header("Browse Items")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            filter_type = st.selectbox(
                "Filter by Type",
                ["All"] + sorted(set(item.item_type for item in srs.items.values())),
                key="browse_filter_type"
            )
        
        with col2:
            # Get all tags from all items
            all_tags = sorted(set(tag for item in srs.items.values() for tag in item.tags))
            filter_tag = st.selectbox(
                "Filter by Tag",
                ["All"] + all_tags,
                key="browse_filter_tag"
            )
        
        with col3:
            sort_by = st.selectbox(
                "Sort by",
                ["Next Review", "Last Reviewed", "Ease Factor", "Type"],
                key="browse_sort_by"
            )
        
        # Apply filters
        filtered_items = list(srs.items.values())
        
        if filter_type != "All":
            filtered_items = [item for item in filtered_items if item.item_type == filter_type]
        
        if filter_tag != "All":
            filtered_items = [item for item in filtered_items if filter_tag in item.tags]
        
        # Apply sorting
        if sort_by == "Next Review":
            filtered_items.sort(key=lambda x: x.next_review)
        elif sort_by == "Last Reviewed":
            filtered_items.sort(key=lambda x: x.last_reviewed or datetime.min.date(), reverse=True)
        elif sort_by == "Ease Factor":
            filtered_items.sort(key=lambda x: x.ease_factor)
        elif sort_by == "Type":
            filtered_items.sort(key=lambda x: x.item_type)
        
        # Display items
        if not filtered_items:
            st.info("No items match your filters.")
        else:
            st.write(f"Showing {len(filtered_items)} items")
            
            # Display as expandable sections
            for i, item in enumerate(filtered_items):
                with st.expander(f"{item.content} - {item.english}", expanded=False):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"**Type:** {item.item_type}")
                        st.markdown(f"**Tags:** {', '.join(item.tags)}")
                        st.markdown(f"**Notes:** {item.notes}")
                    
                    with col2:
                        st.markdown(f"**Reviews:** {item.review_count}")
                        st.markdown(f"**Ease Factor:** {item.ease_factor:.2f}")
                        st.markdown(f"**Next Review:** {item.next_review.strftime('%Y-%m-%d')}")
                    
                    # Edit and delete buttons
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Use a unique key for each item's edit button
                        if st.button("Edit", key=f"edit_btn_{item.item_id}"):
                            st.session_state.edit_item_id = item.item_id
                            st.session_state.edit_content = item.content
                            st.session_state.edit_english = item.english
                            st.session_state.edit_notes = item.notes
                            st.session_state.edit_tags = ", ".join(item.tags)
                    
                    with col2:
                        # Use a unique key for each item's delete button
                        if st.button("Delete", key=f"delete_btn_{item.item_id}"):
                            srs.delete_item(item.item_id)
                            st.success(f"Deleted item: {item.content}")
                            st.rerun()
            
            # Edit dialog
            if hasattr(st.session_state, "edit_item_id"):
                st.markdown("---")
                st.subheader("Edit Item")
                
                with st.form("edit_item_form"):
                    content = st.text_area("Japanese Content", value=st.session_state.edit_content)
                    english = st.text_area("English Meaning", value=st.session_state.edit_english)
                    notes = st.text_area("Notes", value=st.session_state.edit_notes)
                    tags = st.text_input("Tags (comma-separated)", value=st.session_state.edit_tags)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.form_submit_button("Save Changes"):
                            # Process tags
                            tags_list = [tag.strip() for tag in tags.split(",")]
                            
                            # Update the item
                            srs.update_item(
                                st.session_state.edit_item_id,
                                content=content,
                                english=english,
                                notes=notes,
                                tags=tags_list
                            )
                            
                            st.success("Item updated successfully!")
                            
                            # Clear edit state
                            del st.session_state.edit_item_id
                            del st.session_state.edit_content
                            del st.session_state.edit_english
                            del st.session_state.edit_notes
                            del st.session_state.edit_tags
                            
                            st.rerun()
                    
                    with col2:
                        if st.form_submit_button("Cancel"):
                            # Clear edit state
                            del st.session_state.edit_item_id
                            del st.session_state.edit_content
                            del st.session_state.edit_english
                            del st.session_state.edit_notes
                            del st.session_state.edit_tags
                            
                            st.rerun()
    
    # Statistics tab
    with tabs[3]:
        st.header("Learning Statistics")
        
        # Get statistics
        stats = srs.get_statistics()
        
        if stats["total_items"] == 0:
            st.info("Add some items to see your statistics here.")
        else:
            # Display top-level statistics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Items", stats["total_items"])
            
            with col2:
                st.metric("Total Reviews", stats["total_reviews"])
            
            with col3:
                st.metric("Average Ease", f"{stats['average_ease']:.2f}")
            
            with col4:
                st.metric("Success Rate", f"{stats['review_success_rate'] * 100:.1f}%")
            
            # Items by type
            st.subheader("Items by Type")
            
            if stats["items_by_type"]:
                fig = px.pie(
                    names=list(stats["items_by_type"].keys()),
                    values=list(stats["items_by_type"].values()),
                    title="Items by Type"
                )
                st.plotly_chart(fig)
            
            # Daily activity
            st.subheader("Review Activity")
            
            if stats["daily_items"]:
                # Sort by date (ascending)
                sorted_data = sorted(stats["daily_items"], key=lambda x: x["date"])
                
                fig = px.line(
                    x=[datetime.fromisoformat(item["date"]).strftime("%m-%d") for item in sorted_data],
                    y=[item["count"] for item in sorted_data],
                    labels={"x": "Date", "y": "Items Reviewed"},
                    title="Daily Review Activity"
                )
                st.plotly_chart(fig)
            
            # Review forecast
            st.subheader("Upcoming Reviews")
            
            forecast = srs.get_review_forecast(14)  # Next 14 days
            
            if sum(forecast.values()) > 0:
                # Format dates more nicely
                formatted_days = [datetime.fromisoformat(day).strftime("%m-%d") for day in forecast.keys()]
                
                fig = px.bar(
                    x=formatted_days,
                    y=list(forecast.values()),
                    labels={"x": "Date", "y": "Items Due"},
                    title="Review Forecast (Next 14 Days)"
                )
                st.plotly_chart(fig)
            else:
                st.info("No upcoming reviews in the next 14 days.")
    
    # Settings tab
    with tabs[4]:
        st.header("Settings")
        
        export_expander = st.expander("Export/Import Data", expanded=False)
        with export_expander:
            st.subheader("Export Data")
            st.markdown("Export your SRS data to a file for backup or transfer.")
            
            if st.button("Export to JSON", key="export_json_btn"):
                # Export the data
                export_data = srs.export_items()
                
                # Convert to JSON
                export_json = json.dumps(export_data, indent=2)
                
                # Create a download link
                st.download_button(
                    label="Download JSON File",
                    data=export_json,
                    file_name="srs_data.json",
                    mime="application/json"
                )
            
            st.markdown("---")
            
            st.subheader("Import Data")
            st.markdown("""
            Import SRS data from a JSON file. This will **add** to your current items.
            
            **Note:** To replace all items, delete your existing items first.
            """)
            
            uploaded_file = st.file_uploader("Upload JSON file", type=["json"])
            
            if uploaded_file is not None:
                try:
                    # Load the JSON data
                    import_data = json.load(uploaded_file)
                    
                    # Validate the data
                    if not isinstance(import_data, list):
                        st.error("Invalid JSON format. Expected a list of items.")
                    else:
                        st.write(f"Found {len(import_data)} items in the JSON file.")
                        
                        if st.button("Import Items", key="import_json_btn"):
                            # Import the items
                            imported_count = srs.import_items(import_data)
                            st.success(f"Imported {imported_count} items successfully!")
                except json.JSONDecodeError:
                    st.error("Invalid JSON file. Please upload a valid JSON file.")
                except Exception as e:
                    st.error(f"Error importing JSON file: {str(e)}")
        
        reset_expander = st.expander("Reset Data", expanded=False)
        with reset_expander:
            st.subheader("⚠️ Reset All Data")
            st.warning("""
            This will delete all your SRS items and reset your progress.
            This action cannot be undone.
            """)
            
            # Using a confirmation checkbox
            reset_confirmation = st.checkbox("I understand that this will delete all my SRS data", key="reset_confirm")
            
            if reset_confirmation:
                if st.button("Reset All Data", key="reset_btn"):
                    # Reset the data
                    srs.items = {}
                    srs.save_items()
                    st.success("All SRS data has been reset.")
                    st.rerun()

def generate_example_items():
    """
    Generate some example items for the SRS demo.
    
    Returns:
        List of item dictionaries
    """
    return [
        {
            "content": "私",
            "english": "I, me",
            "item_type": "vocabulary",
            "notes": "First-person pronoun",
            "tags": ["JLPT N5", "pronouns"]
        },
        {
            "content": "本",
            "english": "book",
            "item_type": "vocabulary",
            "notes": "",
            "tags": ["JLPT N5", "nouns"]
        },
        {
            "content": "食べる",
            "english": "to eat",
            "item_type": "vocabulary",
            "notes": "Ichidan verb",
            "tags": ["JLPT N5", "verbs"]
        },
        {
            "content": "学校",
            "english": "school",
            "item_type": "vocabulary",
            "notes": "",
            "tags": ["JLPT N5", "nouns", "places"]
        },
        {
            "content": "日本語を勉強しています",
            "english": "I am studying Japanese",
            "item_type": "sentence",
            "notes": "Uses te-form + imasu for ongoing action",
            "tags": ["JLPT N5", "grammar", "te-form"]
        },
        {
            "content": "昨日映画を見ました",
            "english": "I watched a movie yesterday",
            "item_type": "sentence",
            "notes": "Past tense form",
            "tags": ["JLPT N5", "grammar", "past tense"]
        },
        {
            "content": "明日",
            "english": "tomorrow",
            "item_type": "vocabulary",
            "notes": "Time expression",
            "tags": ["JLPT N5", "time"]
        },
        {
            "content": "高い",
            "english": "expensive, high",
            "item_type": "vocabulary",
            "notes": "i-adjective",
            "tags": ["JLPT N5", "adjectives"]
        },
        {
            "content": "～てください",
            "english": "please do ~",
            "item_type": "grammar",
            "notes": "Polite request form",
            "tags": ["JLPT N5", "grammar", "requests"]
        },
        {
            "content": "行きましょう",
            "english": "let's go",
            "item_type": "phrase",
            "notes": "Volitional form for suggesting an action",
            "tags": ["JLPT N5", "grammar", "volitional"]
        }
    ]