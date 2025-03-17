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
