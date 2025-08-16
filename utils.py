import math
import os
import time
import csv
import json
from datetime import datetime, timedelta

# ---------- Geometry ----------
def calculate_angle(a, b, c):
    """Angle at point b (degrees) between points a and c. Points are [x, y]."""
    angle = math.degrees(
        math.atan2(c[1]-b[1], c[0]-b[0]) - math.atan2(a[1]-b[1], a[0]-b[0])
    )
    angle = abs(angle)
    if angle > 180:
        angle = 360 - angle
    return angle

# ---------- Visuals ----------
def draw_progress_bar(frame, progress):
    import cv2
    progress = max(0.0, min(1.0, float(progress)))
    bar_x, bar_y = 20, 80
    bar_w, bar_h = 20, 300
    fill_h = int(bar_h * progress)
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (200, 200, 200), 2)
    cv2.rectangle(frame, (bar_x, bar_y + (bar_h - fill_h)), (bar_x + bar_w, bar_y + bar_h), (0, 255, 0), -1)
    cv2.putText(frame, f"{int(progress*100)}%", (bar_x - 5, bar_y + bar_h + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)

def draw_calorie_counter(frame, calories, target):
    """Draw calorie counter on frame"""
    import cv2
    progress = min(calories / target, 1.0) if target > 0 else 0
    
    # Draw background
    cv2.rectangle(frame, (20, 350), (220, 400), (50, 50, 50), -1)
    
    # Draw progress bar
    bar_width = int(180 * progress)
    cv2.rectangle(frame, (30, 370), (30 + bar_width, 380), (0, 255, 0), -1)
    
    # Draw text
    cv2.putText(frame, f"Calories: {calories:.0f}/{target}", (30, 395),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

# ---------- Calories ----------
MET_VALUES = {
    "squat": 5.0,
    "pushup": 8.0,
    "curl": 3.5,
    "lunge": 4.5,
    "plank": 3.3,
    "burpee": 10.0,
    "jumping_jack": 8.5
}

def estimate_calories(exercise: str, duration_sec: float, weight_kg: float) -> float:
    """Estimate calories burned based on exercise, duration, and weight"""
    met = MET_VALUES.get(exercise, 3.0)
    hours = duration_sec / 3600.0
    return round(met * weight_kg * hours, 2)

def calculate_bmr(weight_kg: float, height_cm: float, age: int, gender: str) -> float:
    """Calculate Basal Metabolic Rate using Mifflin-St Jeor Equation"""
    if gender.lower() == 'male':
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
    return round(bmr, 2)

# ---------- Form Scoring ----------
IDEAL_ANGLES = {
    "squat": {
        "bottom_knee": {"target": 90, "tolerance": 15},
        "top_knee": {"target": 170, "tolerance": 10},
        "back": {"target": 155, "tolerance": 10}
    },
    "pushup": {
        "down_elbow": {"target": 80, "tolerance": 10},
        "up_elbow": {"target": 165, "tolerance": 15},
        "back": {"target": 160, "tolerance": 10}
    },
    "curl": {
        "up_elbow": {"target": 45, "tolerance": 15},
        "down_elbow": {"target": 160, "tolerance": 20},
        "shoulder": {"target": 0, "tolerance": 10}
    },
    "lunge": {
        "bottom_knee": {"target": 90, "tolerance": 15},
        "top_knee": {"target": 160, "tolerance": 20},
        "back": {"target": 155, "tolerance": 10}
    },
    "plank": {
        "back": {"target": 155, "tolerance": 10},
        "hip": {"target": 155, "tolerance": 10}
    },
    "burpee": {
        "squat_knee": {"target": 90, "tolerance": 15},
        "pushup_elbow": {"target": 80, "tolerance": 10}
    }
}

def form_score(exercise: str, angle_name: str, current_angle: float) -> int:
    """Calculate form score based on how close current angle is to ideal"""
    if exercise not in IDEAL_ANGLES or angle_name not in IDEAL_ANGLES[exercise]:
        return 100
    
    target_data = IDEAL_ANGLES[exercise][angle_name]
    target = target_data["target"]
    tolerance = target_data["tolerance"]
    
    diff = abs(float(current_angle) - float(target))
    
    if diff <= tolerance:
        return 100
    elif diff <= tolerance * 2:
        return 80
    elif diff <= tolerance * 3:
        return 60
    else:
        return max(0, 100 - int(diff * 2))

def get_form_feedback(exercise: str, angle_name: str, current_angle: float) -> tuple:
    """Get form feedback and score for a specific angle"""
    score = form_score(exercise, angle_name, current_angle)
    
    if exercise not in IDEAL_ANGLES or angle_name not in IDEAL_ANGLES[exercise]:
        return score, "Form check unavailable"
    
    target_data = IDEAL_ANGLES[exercise][angle_name]
    target = target_data["target"]
    tolerance = target_data["tolerance"]
    
    diff = abs(float(current_angle) - float(target))
    
    if diff <= tolerance:
        feedback = "Perfect form!"
    elif diff <= tolerance * 2:
        feedback = "Good form, minor adjustment needed"
    elif diff <= tolerance * 3:
        feedback = "Form needs improvement"
    else:
        feedback = "Form needs significant improvement"
    
    return score, feedback

# ---------- Achievement System ----------
ACHIEVEMENTS = {
    "first_workout": {
        "name": "First Steps",
        "description": "Complete your first workout",
        "points": 50,
        "icon": "🎯"
    },
    "streak_3": {
        "name": "Getting Started",
        "description": "3-day workout streak",
        "points": 100,
        "icon": "🔥"
    },
    "streak_7": {
        "name": "Week Warrior",
        "description": "7-day workout streak",
        "points": 200,
        "icon": "⚡"
    },
    "streak_30": {
        "name": "Month Master",
        "description": "30-day workout streak",
        "points": 500,
        "icon": "👑"
    },
    "perfect_form": {
        "name": "Form Master",
        "description": "Achieve 95%+ form score",
        "points": 150,
        "icon": "🎯"
    },
    "calorie_burner": {
        "name": "Calorie Crusher",
        "description": "Burn 500+ calories in one session",
        "points": 300,
        "icon": "💪"
    },
    "speed_demon": {
        "name": "Speed Demon",
        "description": "Complete workout in under 10 minutes",
        "points": 200,
        "icon": "🏃"
    },
    "consistency_king": {
        "name": "Consistency King",
        "description": "Work out 5+ days in a week",
        "points": 250,
        "icon": "👑"
    }
}

def check_achievements(user_data: dict, workout_data: dict) -> list:
    """Check which achievements should be unlocked based on workout data"""
    new_achievements = []
    
    # First workout
    if user_data.get("total_workouts", 0) == 0:
        new_achievements.append("first_workout")
    
    # Perfect form
    if workout_data.get("avg_score", 0) >= 95:
        new_achievements.append("perfect_form")
    
    # Calorie burner
    if workout_data.get("calories", 0) >= 500:
        new_achievements.append("calorie_burner")
    
    # Speed demon
    if workout_data.get("duration_sec", 0) < 600:  # 10 minutes
        new_achievements.append("speed_demon")
    
    # Consistency check (would need weekly data)
    # This is a placeholder for future implementation
    
    return new_achievements

# ---------- Workout Planning ----------
def generate_workout_plan(fitness_goal: str, experience_level: str, available_time: int) -> dict:
    """Generate a personalized workout plan"""
    
    # Base exercises for different goals
    goal_exercises = {
        "build_muscle": ["squat", "pushup", "curl", "lunge", "plank"],
        "lose_weight": ["squat", "pushup", "lunge", "plank", "burpee", "jumping_jack"],
        "improve_fitness": ["squat", "pushup", "curl", "lunge", "plank", "burpee"],
        "strength": ["squat", "pushup", "plank", "lunge"],
        "endurance": ["burpee", "jumping_jack", "plank", "lunge"]
    }
    
    # Rep ranges based on experience
    rep_ranges = {
        "beginner": {"min": 8, "max": 12},
        "intermediate": {"min": 12, "max": 20},
        "advanced": {"min": 15, "max": 25}
    }
    
    # Set ranges
    set_ranges = {
        "beginner": {"min": 2, "max": 3},
        "intermediate": {"min": 3, "max": 4},
        "advanced": {"min": 4, "max": 5}
    }
    
    exercises = goal_exercises.get(fitness_goal, goal_exercises["improve_fitness"])
    rep_range = rep_ranges.get(experience_level, rep_ranges["intermediate"])
    set_range = set_ranges.get(experience_level, set_ranges["intermediate"])
    
    # Calculate estimated duration
    estimated_duration = len(exercises) * set_range["max"] * 2  # 2 minutes per set
    
    return {
        "exercises": exercises,
        "reps_per_set": rep_range,
        "sets": set_range,
        "estimated_duration": estimated_duration,
        "rest_periods": 60 if experience_level == "beginner" else 45 if experience_level == "intermediate" else 30
    }

# ---------- Data Management ----------
def ensure_dirs():
    """Ensure required directories exist"""
    os.makedirs("logs", exist_ok=True)
    os.makedirs("recordings", exist_ok=True)
    os.makedirs("user_data", exist_ok=True)

def session_filename(prefix: str, ext: str) -> str:
    """Generate filename for session data"""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    ensure_dirs()
    return os.path.join(prefix, f"session_{ts}.{ext}")

def append_log(row: dict, path: str = "logs/sessions.csv"):
    """Append workout session data to CSV log"""
    ensure_dirs()
    file_exists = os.path.exists(path)
    
    try:
        with open(path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "timestamp", "user", "exercise", "reps", "avg_score", "duration_sec", "calories"
            ])
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)
    except Exception as e:
        print(f"Error writing to log: {e}")
        # Create a backup log file if the main one fails
        backup_path = path.replace('.csv', f'_backup_{int(time.time())}.csv')
        try:
            with open(backup_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "timestamp", "user", "exercise", "reps", "avg_score", "duration_sec", "calories"
                ])
                writer.writeheader()
                writer.writerow(row)
            print(f"Backup log created at: {backup_path}")
        except Exception as backup_e:
            print(f"Failed to create backup log: {backup_e}")

def load_user_data(user_id: str = "default") -> dict:
    """Load user data from JSON file"""
    filepath = f"user_data/{user_id}.json"
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading user data: {e}")
            pass
    
    # Return default user data
    return {
        "username": "User",
        "age": 25,
        "weight_kg": 70,
        "height_cm": 175,
        "fitness_goal": "improve_fitness",
        "experience_level": "beginner",
        "points": 0,
        "streak": 0,
        "total_workouts": 0,
        "achievements": [],
        "created_at": datetime.now().isoformat()
    }

def save_user_data(user_data: dict, user_id: str = "default"):
    """Save user data to JSON file"""
    ensure_dirs()
    filepath = f"user_data/{user_id}.json"
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(user_data, f, indent=2, ensure_ascii=False)

# ---------- Analytics ----------
try:
    import pandas as pd
except ImportError:
    pd = None

def calculate_workout_stats(log_path: str = "logs/sessions.csv") -> dict:
    """Calculate comprehensive workout statistics"""
    if pd is None:
        return {}
    
    if not os.path.exists(log_path):
        return {}
    
    try:
        df = pd.read_csv(log_path, encoding='utf-8')
        if df.empty:
            return {}
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date
        
        stats = {
            "total_workouts": len(df),
            "total_reps": df['reps'].sum(),
            "total_calories": df['calories'].sum(),
            "avg_form_score": df['avg_score'].mean(),
            "total_duration": df['duration_sec'].sum(),
            "favorite_exercise": df['exercise'].mode().iloc[0] if not df['exercise'].mode().empty else "None",
            "workout_frequency": len(df.groupby('date')),
            "avg_workout_duration": df['duration_sec'].mean()
        }
        
        return stats
    except Exception as e:
        print(f"Error calculating stats: {e}")
        return {}

def get_weekly_progress(log_path: str = "logs/sessions.csv", weeks: int = 4) -> dict:
    """Get weekly progress data for the last N weeks"""
    if pd is None:
        return {}
    
    if not os.path.exists(log_path):
        return {}
    
    try:
        df = pd.read_csv(log_path, encoding='utf-8')
        if df.empty:
            return {}
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date
        
        # Get date range
        end_date = datetime.now().date()
        start_date = end_date - timedelta(weeks=weeks)
        
        # Filter data
        weekly_data = df[df['date'] >= start_date].copy()
        weekly_data['week'] = weekly_data['date'].apply(lambda x: x.isocalendar()[1])
        
        # Group by week
        weekly_stats = weekly_data.groupby('week').agg({
            'reps': 'sum',
            'calories': 'sum',
            'avg_score': 'mean',
            'duration_sec': 'sum'
        }).reset_index()
        
        return weekly_stats.to_dict('records')
    except Exception as e:
        print(f"Error getting weekly progress: {e}")
        return {}

# ---------- Voice and Audio ----------
def text_to_speech(text: str, rate: float = 150, volume: float = 0.8):
    """Convert text to speech using pyttsx3"""
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty('rate', rate)
        engine.setProperty('volume', volume)
        engine.say(text)
        engine.runAndWait()
    except ImportError:
        print(f"Voice feedback: {text}")
    except Exception as e:
        print(f"Voice error: {e}")

def get_voice_commands() -> dict:
    """Get available voice commands"""
    return {
        "start_workout": "Begin your exercise session",
        "pause_workout": "Take a break",
        "resume_workout": "Continue your workout",
        "end_workout": "Finish your session",
        "show_progress": "Display current stats",
        "set_timer": "Set rest timer",
        "play_music": "Start workout playlist",
        "form_check": "Check current form"
    }
