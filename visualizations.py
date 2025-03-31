import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import pandas as pd

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
