import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from japanese_badges import get_badge_info, categorize_badges, get_next_badge

def create_streak_chart(current_streak, longest_streak):
    """Create an animated streak progress chart"""
    fig = go.Figure()

    # Add current streak bar
    fig.add_trace(go.Bar(
        x=['Current Streak'],
        y=[current_streak],
        name='Current Streak',
        marker_color='#FF9900',
        text=[f'{current_streak} days'],
        textposition='auto',
    ))

    # Add longest streak bar
    fig.add_trace(go.Bar(
        x=['Longest Streak'],
        y=[longest_streak],
        name='Longest Streak',
        marker_color='#00CC96',
        text=[f'{longest_streak} days'],
        textposition='auto',
    ))

    # Update layout
    fig.update_layout(
        title='Learning Streak Progress',
        yaxis_title='Days',
        showlegend=True,
        height=400,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )

    return fig

def create_mastery_radar(particle_mastery, verb_mastery, pattern_mastery):
    """Create an animated radar chart for mastery levels"""
    categories = ['Particles', 'Verbs', 'Patterns']
    
    # Calculate average mastery for each category
    values = [
        _calculate_average_mastery(particle_mastery),
        _calculate_average_mastery(verb_mastery),
        _calculate_average_mastery(pattern_mastery)
    ]

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name='Mastery Level'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )),
        showlegend=False,
        title='Mastery Overview',
        height=400,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )

    return fig

def create_achievement_progress(achievements):
    """Create an animated achievement progress chart"""
    if not achievements:
        return None

    # Calculate completion percentages for each category
    categories = {
        'Streak': len(achievements.get('streak', [])),
        'Accuracy': len(achievements.get('accuracy', [])),
        'Practice': len(achievements.get('practice', [])),
        'Mastery': len(achievements.get('mastery', []))
    }

    # Maximum possible achievements in each category
    max_achievements = {
        'Streak': 6,  # 3, 7, 14, 30, 60, 90 days
        'Accuracy': 5, # 60%, 70%, 80%, 90%, 95%
        'Practice': 5, # 10, 50, 100, 500, 1000 checks
        'Mastery': 9   # 3 levels (50%, 70%, 90%) × 3 categories
    }

    # Calculate percentages
    percentages = {
        category: (count / max_achievements[category]) * 100
        for category, count in categories.items()
    }

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=list(percentages.keys()),
        y=list(percentages.values()),
        marker_color=['#FF9900', '#00CC96', '#AB63FA', '#FFA15A'],
        text=[f'{v:.0f}%' for v in percentages.values()],
        textposition='auto',
    ))

    fig.update_layout(
        title='Achievement Progress',
        yaxis_title='Completion %',
        yaxis_range=[0, 100],
        height=400,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )

    return fig

def _calculate_average_mastery(mastery_dict):
    """Calculate average mastery percentage from a mastery dictionary"""
    if not mastery_dict:
        return 0
    
    total_mastery = sum(
        stats['correct'] / stats['count'] * 100
        for stats in mastery_dict.values()
        if stats['count'] > 0
    )
    return total_mastery / len(mastery_dict) if mastery_dict else 0

def create_mood_trend_chart(mood_history):
    """Create a line chart showing mood trends over time"""
    if not mood_history or len(mood_history) < 2:
        return None
    
    # Convert emoji moods to numerical values for visualization
    mood_values = {
        "😊": 5,  # Happy
        "😀": 4,  # Satisfied
        "😐": 3,  # Neutral
        "😕": 2,  # Slightly Frustrated
        "😞": 1   # Frustrated
    }
    
    # Prepare data
    dates = []
    values = []
    
    for entry in mood_history:
        if 'date' in entry and 'mood' in entry and entry['mood'] in mood_values:
            dates.append(entry['date'])
            values.append(mood_values[entry['mood']])
    
    if not dates or not values:
        return None
    
    # Create DataFrame
    df = pd.DataFrame({
        'Date': dates,
        'Mood': values
    })
    
    # Create line chart
    fig = px.line(
        df, 
        x='Date', 
        y='Mood',
        markers=True,
        title='Your Mood Trends',
        labels={'Mood': 'Mood Level (1-5)'}
    )
    
    # Update layout
    fig.update_layout(
        xaxis_title='Date',
        yaxis_title='Mood Level',
        yaxis=dict(
            tickmode='array',
            tickvals=[1, 2, 3, 4, 5],
            ticktext=['😞', '😕', '😐', '😀', '😊']
        ),
        height=400,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )
    
    return fig

def create_difficulty_distribution_chart(difficulty_history):
    """Create a pie chart showing distribution of selected difficulty levels"""
    if not difficulty_history:
        return None
    
    # Count occurrences of each difficulty level
    difficulty_counts = {}
    difficulty_labels = {
        "🌱": "Beginner",
        "🌿": "Elementary", 
        "🌲": "Intermediate", 
        "🏔️": "Advanced", 
        "🏯": "Native-like"
    }
    
    for entry in difficulty_history:
        if 'difficulty' in entry and entry['difficulty'] in difficulty_labels:
            diff = difficulty_labels[entry['difficulty']]
            difficulty_counts[diff] = difficulty_counts.get(diff, 0) + 1
    
    if not difficulty_counts:
        return None
    
    # Create pie chart
    labels = list(difficulty_counts.keys())
    values = list(difficulty_counts.values())
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=.3,
        marker_colors=px.colors.qualitative.Pastel
    )])
    
    fig.update_layout(
        title='Your Selected Difficulty Levels',
        height=400,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )
    
    return fig

def create_lesson_progress_chart(completed_lessons, total_lessons_by_difficulty):
    """Create a horizontal bar chart showing lesson completion progress by difficulty"""
    if not completed_lessons or not total_lessons_by_difficulty:
        return None
    
    # Prepare data
    difficulties = list(total_lessons_by_difficulty.keys())
    total_counts = list(total_lessons_by_difficulty.values())
    completed_counts = [completed_lessons.get(diff, 0) for diff in difficulties]
    
    # Calculate completion percentages
    percentages = [
        (completed / total) * 100 if total > 0 else 0
        for completed, total in zip(completed_counts, total_counts)
    ]
    
    fig = go.Figure()
    
    # Add completed lessons bars
    fig.add_trace(go.Bar(
        y=difficulties,
        x=percentages,
        name='Completion Rate',
        orientation='h',
        marker_color='#00CC96',
        text=[f"{completed}/{total} ({perc:.1f}%)" for completed, total, perc in zip(completed_counts, total_counts, percentages)],
        textposition='auto',
    ))
    
    fig.update_layout(
        title='Lesson Completion by Difficulty',
        xaxis_title='Completion Percentage',
        xaxis=dict(
            range=[0, 100],
            tickvals=[0, 25, 50, 75, 100],
            ticktext=['0%', '25%', '50%', '75%', '100%']
        ),
        height=400,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )
    
    return fig

def create_japanese_cultural_badge_progress(achievements):
    """
    Create a visualization for Japanese cultural achievement badges
    
    Args:
        achievements: Dictionary of achievement lists by category
        
    Returns:
        Plotly figure with badge progress visualization
    """
    if not achievements:
        return None
    
    # Get badge information
    earned_badges = []
    for category, badge_ids in achievements.items():
        for badge_id in badge_ids:
            badge_info = get_badge_info(badge_id)
            if badge_info:
                earned_badges.append({
                    "id": badge_id,
                    "category": category,
                    **badge_info
                })
    
    if not earned_badges:
        return None
    
    # Create a grouped bar chart showing progress in each category
    categorized = categorize_badges()
    
    # Count earned badges in each detailed category
    earned_counts = {}
    for category, badges in categorized.items():
        category_display = category.replace('_', ' ').title()
        earned = sum(1 for badge in earned_badges if badge['id'] in [b['id'] for b in badges])
        total = len(badges)
        earned_counts[category_display] = {
            "earned": earned,
            "total": total,
            "percentage": (earned / total * 100) if total > 0 else 0
        }
    
    # Prepare data for visualization
    categories = list(earned_counts.keys())
    percentages = [earned_counts[cat]["percentage"] for cat in categories]
    text_labels = [f"{earned_counts[cat]['earned']}/{earned_counts[cat]['total']}" for cat in categories]
    
    # Create color mapping for Japanese-themed colors
    colors = [
        '#D73E02',  # Vermilion (朱色, shu-iro)
        '#E7A54D',  # Amber (琥珀色, kohaku-iro)
        '#8A6BBE',  # Wisteria (藤色, fuji-iro)
        '#24936E',  # Jade (翡翠色, hisui-iro)
        '#6A4028',  # Cinnamon (肉桂色, nikuzuku-iro)
        '#B28FCE'   # Lavender (藤紫, fujimurasaki)
    ]
    
    fig = go.Figure()
    
    # Add bars for each category
    fig.add_trace(go.Bar(
        x=categories,
        y=percentages,
        marker_color=colors[:len(categories)],
        text=text_labels,
        textposition='auto',
    ))
    
    # Update layout with Japanese-inspired design
    fig.update_layout(
        title={
            'text': '🏮 日本文化の徽章 Japanese Cultural Badges 🏮',
            'font': {
                'family': 'serif',
                'size': 24,
                'color': '#D73E02'
            },
            'x': 0.5,
            'y': 0.95
        },
        yaxis_title='収集完了率 (Completion %)',
        yaxis_range=[0, 100],
        height=450,
        paper_bgcolor='rgba(255,252,245,0.6)',  # Light cream background
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=80, b=40),
        font=dict(
            family='serif',
        ),
    )
    
    # Add a background pattern for Japanese-style design
    fig.add_layout_image(
        dict(
            source="https://img.freepik.com/free-vector/japanese-wave-pattern-vector-vintage-art-print-remix-original-artwork_53876-116088.jpg",
            xref="paper", yref="paper",
            x=0, y=1,
            sizex=1, sizey=1,
            sizing="stretch",
            opacity=0.05,
            layer="below")
    )
    
    return fig

def create_japanese_badge_card(badge_id):
    """
    Create a stylized HTML card for a Japanese cultural badge
    
    Args:
        badge_id: The ID of the badge to display
        
    Returns:
        HTML string with badge card
    """
    badge = get_badge_info(badge_id)
    
    if not badge:
        return ""
    
    html = f"""
    <div style="
        border: 2px solid #DAA520; 
        border-radius: 10px; 
        padding: 15px; 
        margin: 10px 0; 
        background: linear-gradient(135deg, rgba(255,252,245,0.9) 0%, rgba(248,243,230,0.9) 100%);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        font-family: serif;
    ">
        <div style="display: flex; align-items: center; margin-bottom: 10px;">
            <div style="
                font-size: 40px; 
                margin-right: 15px; 
                background-color: #FFF5E1; 
                border-radius: 50%; 
                width: 60px; 
                height: 60px; 
                display: flex; 
                align-items: center; 
                justify-content: center;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            ">{badge['icon']}</div>
            <div>
                <h3 style="
                    margin: 0; 
                    color: #DAA520; 
                    font-family: serif;
                    font-size: 1.4rem;
                    text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
                ">{badge['name']}</h3>
                <p style="
                    margin: 3px 0 0 0; 
                    font-style: italic; 
                    color: #666;
                    font-size: 0.9rem;
                ">{badge['translation']}</p>
            </div>
        </div>
        <p style="
            margin: 10px 0; 
            line-height: 1.5; 
            color: #383838;
            font-size: 1rem;
        ">{badge['description']}</p>
        <div style="
            background-color: #F8F3E6; 
            border-left: 3px solid #DAA520; 
            padding: 10px; 
            margin-top: 10px;
            font-size: 0.9rem;
            color: #666;
            font-style: italic;
        ">
            <span style="font-weight: bold; color: #383838;">Cultural Note:</span> {badge['cultural_note']}
        </div>
    </div>
    """
    
    return html

def create_srs_forecast_chart(forecast_data):
    """
    Create a chart showing spaced repetition review forecast
    
    Args:
        forecast_data: Dictionary with dates as keys and counts as values
        
    Returns:
        Plotly figure with review forecast
    """
    if not forecast_data:
        return None
    
    # Prepare data
    dates = list(forecast_data.keys())
    counts = list(forecast_data.values())
    
    # Format dates more nicely
    formatted_dates = [datetime.fromisoformat(date).strftime("%m-%d") for date in dates]
    
    # Create a bar chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=formatted_dates,
        y=counts,
        marker_color='#4B96E5',
        text=[f"{count} items" for count in counts],
        textposition='auto',
    ))
    
    fig.update_layout(
        title='Upcoming Review Schedule',
        xaxis_title='Date',
        yaxis_title='Items to Review',
        height=400,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )
    
    return fig

def create_srs_item_types_chart(items_by_type):
    """
    Create a pie chart showing distribution of items by type
    
    Args:
        items_by_type: Dictionary with item types as keys and counts as values
        
    Returns:
        Plotly figure with item type distribution
    """
    if not items_by_type:
        return None
    
    # Prepare data
    types = list(items_by_type.keys())
    counts = list(items_by_type.values())
    
    # Create color mapping for Japanese language learning
    colors = {
        'vocabulary': '#FF6B6B',  # Red for vocabulary
        'kanji': '#4ECDC4',       # Turquoise for kanji
        'grammar': '#FFD166',     # Yellow for grammar
        'sentence': '#06D6A0',    # Green for sentences
        'phrase': '#118AB2'       # Blue for phrases
    }
    
    # Assign colors to each type, default to gray if type not in mapping
    type_colors = [colors.get(t, '#CCCCCC') for t in types]
    
    # Create pie chart
    fig = go.Figure(data=[go.Pie(
        labels=types,
        values=counts,
        hole=.3,
        marker_colors=type_colors
    )])
    
    fig.update_layout(
        title='Items by Type',
        height=400,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )
    
    return fig

def create_srs_review_history_chart(daily_items):
    """
    Create a line chart showing review activity over time
    
    Args:
        daily_items: List of dictionaries with date and count
        
    Returns:
        Plotly figure with review history
    """
    if not daily_items:
        return None
    
    # Prepare data
    dates = [item['date'] for item in daily_items]
    counts = [item['count'] for item in daily_items]
    
    # Sort by date (ascending)
    sorted_indices = sorted(range(len(dates)), key=lambda i: dates[i])
    sorted_dates = [dates[i] for i in sorted_indices]
    sorted_counts = [counts[i] for i in sorted_indices]
    
    # Format dates more nicely
    formatted_dates = [datetime.fromisoformat(date).strftime("%m-%d") for date in sorted_dates]
    
    # Create a line chart
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=formatted_dates,
        y=sorted_counts,
        mode='lines+markers',
        name='Reviews',
        line=dict(color='#4B96E5', width=3),
        marker=dict(size=8, color='#4B96E5'),
    ))
    
    # Add a smoothed trend line
    if len(sorted_counts) > 3:
        # Create a smoothed trend using a simple moving average
        window_size = min(3, len(sorted_counts) - 1)
        trend = np.convolve(sorted_counts, np.ones(window_size)/window_size, mode='valid')
        trend_dates = formatted_dates[window_size-1:]
        
        fig.add_trace(go.Scatter(
            x=trend_dates,
            y=trend,
            mode='lines',
            name='Trend',
            line=dict(color='#FF6B6B', width=2, dash='dash'),
        ))
    
    fig.update_layout(
        title='Review Activity History',
        xaxis_title='Date',
        yaxis_title='Items Reviewed',
        height=400,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )
    
    return fig

def create_srs_mastery_distribution_chart(items):
    """
    Create a histogram showing distribution of ease factors
    
    Args:
        items: List of SRS items with ease_factor values
        
    Returns:
        Plotly figure with ease factor distribution
    """
    if not items:
        return None
    
    # Extract ease factors
    ease_factors = [item.ease_factor for item in items]
    
    # Create histogram
    fig = go.Figure()
    
    fig.add_trace(go.Histogram(
        x=ease_factors,
        nbinsx=10,
        marker_color='#4B96E5',
        opacity=0.7
    ))
    
    fig.update_layout(
        title='Memory Strength Distribution',
        xaxis_title='Ease Factor (Lower = More Difficult)',
        yaxis_title='Number of Items',
        height=400,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )
    
    # Add vertical lines for ease factor interpretation
    fig.add_shape(
        type="line",
        x0=1.3, x1=1.3, y0=0, y1=1,
        yref="paper",
        line=dict(color="#FF6B6B", width=2, dash="dash"),
    )
    
    fig.add_shape(
        type="line",
        x0=2.5, x1=2.5, y0=0, y1=1,
        yref="paper",
        line=dict(color="#FFD166", width=2, dash="dash"),
    )
    
    # Add annotations for ease factor zones
    fig.add_annotation(
        x=1.15,
        y=0.9,
        yref="paper",
        text="Very Difficult",
        showarrow=False,
        font=dict(color="#FF6B6B")
    )
    
    fig.add_annotation(
        x=1.9,
        y=0.9,
        yref="paper",
        text="Challenging",
        showarrow=False,
        font=dict(color="#FFD166")
    )
    
    fig.add_annotation(
        x=3.0,
        y=0.9,
        yref="paper",
        text="Well Known",
        showarrow=False,
        font=dict(color="#06D6A0")
    )
    
    return fig

def create_next_badge_card(category, current_achievements):
    """
    Create a stylized HTML card for the next badge a user can earn
    
    Args:
        category: The achievement category
        current_achievements: List of user's current achievements
        
    Returns:
        HTML string with next badge card or message if all badges earned
    """
    next_badge = get_next_badge(category, current_achievements)
    
    if not next_badge:
        return f"""
        <div style="
            border: 2px solid #DAA520; 
            border-radius: 10px; 
            padding: 15px; 
            margin: 10px 0; 
            background: linear-gradient(135deg, rgba(255,252,245,0.9) 0%, rgba(248,243,230,0.9) 100%);
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            font-family: serif;
            text-align: center;
        ">
            <p style="
                margin: 10px 0; 
                line-height: 1.5; 
                color: #383838;
                font-size: 1rem;
            ">🎉 Congratulations! You've earned all badges in this category! 🎉</p>
        </div>
        """
    
    milestone = next_badge.get('id', '').split('_')[-1]
    progress_message = ""
    
    if category == "streak":
        progress_message = f"Current streak: {milestone} days needed"
    elif category == "accuracy":
        progress_message = f"Target accuracy: {milestone}%"
    elif category == "practice":
        progress_message = f"Practice goal: {milestone} checks"
    elif "mastery" in category:
        type_name = category.split('_')[0].title()
        progress_message = f"{type_name} mastery goal: {milestone}%"
    
    html = f"""
    <div style="
        border: 2px dashed #DAA520; 
        border-radius: 10px; 
        padding: 15px; 
        margin: 10px 0; 
        background: linear-gradient(135deg, rgba(255,252,245,0.7) 0%, rgba(248,243,230,0.7) 100%);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        font-family: serif;
        position: relative;
    ">
        <div style="
            position: absolute;
            top: -10px;
            right: 10px;
            background: #DAA520;
            color: white;
            padding: 2px 10px;
            border-radius: 10px;
            font-size: 0.8rem;
        ">
            Next Badge
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 10px;">
            <div style="
                font-size: 40px; 
                margin-right: 15px; 
                background-color: #FFF5E1; 
                border-radius: 50%; 
                width: 60px; 
                height: 60px; 
                display: flex; 
                align-items: center; 
                justify-content: center;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                opacity: 0.6;
            ">{next_badge['icon']}</div>
            <div>
                <h3 style="
                    margin: 0; 
                    color: #DAA520; 
                    font-family: serif;
                    font-size: 1.4rem;
                    text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
                    opacity: 0.8;
                ">{next_badge['name']}</h3>
                <p style="
                    margin: 3px 0 0 0; 
                    font-style: italic; 
                    color: #666;
                    font-size: 0.9rem;
                ">{next_badge['translation']}</p>
            </div>
        </div>
        <p style="
            margin: 10px 0; 
            line-height: 1.5; 
            color: #383838;
            font-size: 1rem;
        ">{next_badge['description']}</p>
        <div style="
            background-color: #F8F3E6; 
            border-left: 3px solid #DAA520; 
            padding: 10px; 
            margin-top: 10px;
            font-size: 0.9rem;
            color: #666;
        ">
            <span style="font-weight: bold; color: #383838;">Progress Goal:</span> {progress_message}
        </div>
    </div>
    """
    
    return html
