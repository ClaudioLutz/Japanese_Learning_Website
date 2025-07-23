"""
JLPT Level Conversion Utilities

This module provides utilities for converting between different JLPT level formats.
"""

def convert_jlpt_level_to_int(jlpt_level):
    """
    Convert JLPT level from string format (N4, N3, etc.) to integer format (4, 3, etc.)
    
    Args:
        jlpt_level: String like "N4", "N3" or integer like 4, 3
    
    Returns:
        Integer representation of JLPT level
    """
    if isinstance(jlpt_level, int):
        return jlpt_level
    
    if isinstance(jlpt_level, str):
        # Handle formats like "N4", "n4", "4"
        jlpt_level = jlpt_level.upper().strip()
        if jlpt_level.startswith('N'):
            try:
                return int(jlpt_level[1:])
            except ValueError:
                pass
        else:
            try:
                return int(jlpt_level)
            except ValueError:
                pass
    
    # Default to N5 (beginner level) if conversion fails
    return 5

def convert_int_to_jlpt_level(level_int):
    """
    Convert integer JLPT level to string format
    
    Args:
        level_int: Integer like 4, 3, 2, 1
    
    Returns:
        String representation like "N4", "N3", etc.
    """
    if isinstance(level_int, int) and 1 <= level_int <= 5:
        return f"N{level_int}"
    return "N5"  # Default to N5

def validate_jlpt_level(jlpt_level):
    """
    Validate that a JLPT level is valid (N1-N5 or 1-5)
    
    Args:
        jlpt_level: JLPT level in any format
    
    Returns:
        Boolean indicating if the level is valid
    """
    try:
        level_int = convert_jlpt_level_to_int(jlpt_level)
        return 1 <= level_int <= 5
    except:
        return False


def convert_difficulty_to_int(difficulty):
    """
    Convert difficulty level from string format to integer format
    
    Args:
        difficulty: String like "Beginner", "Intermediate", "Advanced" or integer
    
    Returns:
        Integer representation of difficulty level (1-5)
    """
    if isinstance(difficulty, int):
        return max(1, min(5, difficulty))  # Ensure it's between 1-5
    
    if isinstance(difficulty, str):
        difficulty = difficulty.lower().strip()
        difficulty_map = {
            'beginner': 1,
            'elementary': 1,
            'easy': 1,
            'basic': 1,
            'intermediate': 3,
            'medium': 3,
            'advanced': 4,
            'hard': 4,
            'expert': 5,
            'master': 5
        }
        return difficulty_map.get(difficulty, 3)  # Default to intermediate
    
    return 3  # Default to intermediate

def convert_int_to_difficulty_level(level_int):
    """
    Convert integer difficulty level to string format
    
    Args:
        level_int: Integer like 1, 2, 3, 4, 5
    
    Returns:
        String representation like "Beginner", "Intermediate", etc.
    """
    difficulty_map = {
        1: "Beginner",
        2: "Elementary", 
        3: "Intermediate",
        4: "Advanced",
        5: "Expert"
    }
    return difficulty_map.get(level_int, "Intermediate")

def validate_difficulty_level(difficulty):
    """
    Validate that a difficulty level is valid
    
    Args:
        difficulty: Difficulty level in any format
    
    Returns:
        Boolean indicating if the level is valid
    """
    try:
        level_int = convert_difficulty_to_int(difficulty)
        return 1 <= level_int <= 5
    except:
        return False

def truncate_field(text, max_length):
    """
    Truncate text to fit database field constraints
    
    Args:
        text: Text to truncate
        max_length: Maximum allowed length
    
    Returns:
        Truncated text that fits the constraint
    """
    if not text:
        return text
    
    if len(text) <= max_length:
        return text
    
    # Truncate and add ellipsis
    return text[:max_length-3] + "..."
