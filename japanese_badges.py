"""
Japanese Cultural Achievement Badges

This module defines achievement badges with Japanese cultural themes.
Each badge has a Japanese name, cultural significance, description, and requirements.
"""

from typing import Dict, List, Any, Tuple

# Badge definitions with cultural significance
JAPANESE_BADGES = {
    # Streak Achievements
    "streak_3": {
        "name": "三日月 (Mikazuki)",
        "translation": "Crescent Moon",
        "icon": "🌙",
        "description": "You've practiced for 3 consecutive days, like the crescent moon that appears for 3 days each month.",
        "cultural_note": "In Japanese culture, viewing the crescent moon (三日月) is considered auspicious and symbolizes new beginnings."
    },
    "streak_7": {
        "name": "七福神 (Shichifukujin)",
        "translation": "Seven Lucky Gods",
        "icon": "🏮",
        "description": "You've practiced for 7 consecutive days, honoring the Seven Lucky Gods of Japanese mythology.",
        "cultural_note": "The Shichifukujin represent different aspects of fortune and are often depicted traveling together on their treasure ship."
    },
    "streak_14": {
        "name": "十四夜 (Jūyokka)",
        "translation": "Fourteenth Night Moon",
        "icon": "🌕",
        "description": "You've practiced for 14 consecutive days, like the full moon appearing on the 14th night of the lunar month.",
        "cultural_note": "The full moon has special significance in Japan and is celebrated during Otsukimi (moon-viewing) festivals."
    },
    "streak_30": {
        "name": "一ヶ月 (Ikkagetsu)",
        "translation": "One Month",
        "icon": "📅",
        "description": "You've practiced for a full month, showing dedication like a monthly tea ceremony practitioner.",
        "cultural_note": "Monthly dedication to arts and practices is highly valued in Japanese culture, symbolizing persistence and growth."
    },
    "streak_60": {
        "name": "扇 (Ōgi)",
        "translation": "Folding Fan",
        "icon": "🪭",
        "description": "You've practiced for 60 consecutive days, like the 60 ribs of a traditional Japanese folding fan.",
        "cultural_note": "The folding fan represents expansion of knowledge and has been used in traditional Japanese arts for centuries."
    },
    "streak_90": {
        "name": "変わり身 (Kawarimi)",
        "translation": "Transformation",
        "icon": "🌸",
        "description": "You've practiced for 90 consecutive days, transforming your knowledge like the changes of seasons in Japan.",
        "cultural_note": "The 90-day seasonal transitions are deeply important in Japanese culture, marking shifts in activities, foods, and celebrations."
    },
    
    # Accuracy Achievements
    "accuracy_60": {
        "name": "見習い (Minarai)",
        "translation": "Apprentice",
        "icon": "🧠",
        "description": "You've achieved 60% accuracy, beginning your apprenticeship in Japanese language.",
        "cultural_note": "Traditional Japanese crafts begin with an apprenticeship period where basic skills are developed before advancing."
    },
    "accuracy_70": {
        "name": "手習い (Tenarai)",
        "translation": "Practice Hand",
        "icon": "✍️",
        "description": "You've achieved 70% accuracy, developing your 'practice hand' in Japanese language.",
        "cultural_note": "Tenarai refers to handwriting practice, a fundamental skill in learning Japanese calligraphy (shodo)."
    },
    "accuracy_80": {
        "name": "内弟子 (Uchideshi)",
        "translation": "Inside Student",
        "icon": "🏯",
        "description": "You've achieved 80% accuracy, becoming an inside student of Japanese language.",
        "cultural_note": "Uchideshi are live-in students in traditional Japanese arts who receive more direct training from the master."
    },
    "accuracy_90": {
        "name": "名人 (Meijin)",
        "translation": "Master",
        "icon": "⛩️",
        "description": "You've achieved 90% accuracy, approaching mastery of Japanese language patterns.",
        "cultural_note": "Meijin is a title given to masters of traditional Japanese arts and games, signifying high achievement."
    },
    "accuracy_95": {
        "name": "達人 (Tatsujin)",
        "translation": "Expert",
        "icon": "🏆",
        "description": "You've achieved 95% accuracy, becoming a language expert with near-native understanding.",
        "cultural_note": "Tatsujin represents someone who has reached the highest level of skill, beyond mere technical mastery."
    },
    
    # Practice Count Achievements
    "practice_10": {
        "name": "十牛図 (Jūgyūzu)",
        "translation": "Ten Bulls",
        "icon": "🐂",
        "description": "You've completed 10 grammar checks, beginning your journey like the Ten Bulls Zen parable.",
        "cultural_note": "The Ten Bulls is a series of short poems and images used in Zen Buddhism to illustrate stages of enlightenment."
    },
    "practice_50": {
        "name": "五十音 (Gojūon)",
        "translation": "Fifty Sounds",
        "icon": "🔤",
        "description": "You've completed 50 grammar checks, mastering as many exercises as there are sounds in the Japanese syllabary.",
        "cultural_note": "The 50 sounds of the Japanese syllabary (gojūon) form the foundation of the written language."
    },
    "practice_100": {
        "name": "百人一首 (Hyakunin Isshu)",
        "translation": "One Hundred Poets",
        "icon": "📜",
        "description": "You've completed 100 grammar checks, like the famous collection of 100 Japanese poems.",
        "cultural_note": "Hyakunin Isshu is a classical Japanese anthology of 100 poems by 100 poets, often used in a traditional card game."
    },
    "practice_500": {
        "name": "五百羅漢 (Gohyaku Rakan)",
        "translation": "Five Hundred Arhats",
        "icon": "🧘",
        "description": "You've completed 500 grammar checks, showing dedication like the 500 disciples of Buddha.",
        "cultural_note": "The 500 Arhats are portrayed in many Japanese temples, each with unique expressions and characteristics."
    },
    "practice_1000": {
        "name": "千羽鶴 (Senbazuru)",
        "translation": "Thousand Cranes",
        "icon": "🦢",
        "description": "You've completed 1000 grammar checks, like folding 1000 origami cranes for good fortune.",
        "cultural_note": "In Japanese tradition, folding 1000 paper cranes is said to grant a wish and represents perseverance and hope."
    },
    
    # Particle Mastery Achievements
    "particle_mastery_50": {
        "name": "助詞初段 (Joshi Shodan)",
        "translation": "Particle First Rank",
        "icon": "🔖",
        "description": "You've achieved 50% mastery of Japanese particles, earning your first rank.",
        "cultural_note": "The ranking system (dan) is used in many Japanese arts and martial arts to denote progression of skill."
    },
    "particle_mastery_70": {
        "name": "助詞中段 (Joshi Chudan)",
        "translation": "Particle Middle Rank",
        "icon": "📎",
        "description": "You've achieved 70% mastery of Japanese particles, reaching intermediate level.",
        "cultural_note": "Middle rank practitioners in Japanese arts have solid fundamentals and are developing deeper understanding."
    },
    "particle_mastery_90": {
        "name": "助詞師範 (Joshi Shihan)",
        "translation": "Particle Master",
        "icon": "🏷️",
        "description": "You've achieved 90% mastery of Japanese particles, becoming a qualified teacher.",
        "cultural_note": "Shihan is a formal title given to senior instructors in Japanese martial arts and other traditional practices."
    },
    
    # Verb Mastery Achievements
    "verb_mastery_50": {
        "name": "動詞見習 (Dōshi Minarai)",
        "translation": "Verb Apprentice",
        "icon": "🔨",
        "description": "You've achieved 50% mastery of Japanese verbs, starting your verb apprenticeship.",
        "cultural_note": "The apprenticeship system in Japan has historically been the way crafts and skills are preserved and passed down."
    },
    "verb_mastery_70": {
        "name": "動詞職人 (Dōshi Shokunin)",
        "translation": "Verb Craftsman",
        "icon": "⚒️",
        "description": "You've achieved 70% mastery of Japanese verbs, becoming a skilled craftsman.",
        "cultural_note": "Shokunin refers to artisans who have dedicated their lives to perfecting a craft, with an emphasis on precision."
    },
    "verb_mastery_90": {
        "name": "動詞の達人 (Dōshi no Tatsujin)",
        "translation": "Verb Expert",
        "icon": "🛠️",
        "description": "You've achieved 90% mastery of Japanese verbs, becoming a true verb expert.",
        "cultural_note": "The concept of 'tatsujin' goes beyond technical skill to include intuitive understanding and creative application."
    },
    
    # Pattern Mastery Achievements
    "pattern_mastery_50": {
        "name": "型初心 (Kata Shoshin)",
        "translation": "Pattern Beginner's Mind",
        "icon": "🔰",
        "description": "You've achieved 50% mastery of Japanese grammar patterns, with a beginner's mindset.",
        "cultural_note": "Shoshin (beginner's mind) is a concept from Zen Buddhism, emphasizing an attitude of openness and lack of preconceptions."
    },
    "pattern_mastery_70": {
        "name": "型稽古 (Kata Keiko)",
        "translation": "Pattern Practice",
        "icon": "🔁",
        "description": "You've achieved 70% mastery of Japanese grammar patterns through diligent practice.",
        "cultural_note": "Keiko refers to the practice of traditional arts in Japan, with an emphasis on repetition to achieve mastery."
    },
    "pattern_mastery_90": {
        "name": "型破り (Kata Yaburi)",
        "translation": "Pattern Breaker",
        "icon": "✨",
        "description": "You've achieved 90% mastery of Japanese grammar patterns, allowing you to creatively break patterns.",
        "cultural_note": "Kata-yaburi refers to breaking from tradition after mastering it - a concept in Japanese arts that values innovation built on traditional foundations."
    }
}

def get_badge_info(achievement_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a Japanese cultural badge.
    
    Args:
        achievement_id: The ID of the achievement (e.g., 'streak_7')
        
    Returns:
        Dictionary with badge information or a default if not found
    """
    return JAPANESE_BADGES.get(achievement_id, {
        "name": achievement_id,
        "translation": "",
        "icon": "🔶",
        "description": "Achievement earned!",
        "cultural_note": ""
    })

def get_all_badges() -> Dict[str, Dict[str, Any]]:
    """
    Get all available Japanese cultural badges.
    
    Returns:
        Dictionary of all badge information
    """
    return JAPANESE_BADGES

def categorize_badges() -> Dict[str, List[Dict[str, Any]]]:
    """
    Categorize badges by type (streak, accuracy, practice, mastery).
    
    Returns:
        Dictionary of categorized badges
    """
    categories = {
        "streak": [],
        "accuracy": [],
        "practice": [],
        "particle_mastery": [],
        "verb_mastery": [],
        "pattern_mastery": []
    }
    
    for badge_id, badge_info in JAPANESE_BADGES.items():
        category = badge_id.split('_')[0]
        if category == "particle" or category == "verb" or category == "pattern":
            category = f"{category}_mastery"
        
        if category in categories:
            categories[category].append({
                "id": badge_id,
                **badge_info
            })
    
    return categories

def get_next_badge(achievement_type: str, current_achievements: List[str]) -> Dict[str, Any]:
    """
    Get information about the next badge a user can earn in a category.
    
    Args:
        achievement_type: Type of achievement (streak, accuracy, practice, mastery)
        current_achievements: List of achievement IDs the user has already earned
        
    Returns:
        Dictionary with next badge information or empty dict if all badges earned
    """
    # Filter badges by the specified type
    category_badges = []
    prefix = achievement_type
    if achievement_type in ["particle_mastery", "verb_mastery", "pattern_mastery"]:
        prefix = achievement_type.split('_')[0]
    
    for badge_id, badge_info in JAPANESE_BADGES.items():
        if badge_id.startswith(prefix):
            category_badges.append({"id": badge_id, **badge_info})
    
    # Sort badges by their milestone (extracted from the ID)
    category_badges.sort(key=lambda x: int(x["id"].split('_')[-1]))
    
    # Find the first badge that hasn't been earned yet
    for badge in category_badges:
        if badge["id"] not in current_achievements:
            return badge
    
    # If all badges are earned, return empty dict
    return {}

def get_milestone_for_badge(badge_id: str) -> int:
    """
    Extract the milestone number from a badge ID.
    
    Args:
        badge_id: The ID of the badge (e.g., 'streak_7')
        
    Returns:
        The milestone number as an integer
    """
    try:
        return int(badge_id.split('_')[-1])
    except (ValueError, IndexError):
        return 0