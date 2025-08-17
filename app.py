import os
import json
from datetime import datetime, timedelta
import streamlit as st
import pandas as pd
import subprocess
import sys
import plotly.express as px
# from streamlit_autorefresh import st_autorefresh

# Constants
LOG_PATH = "logs/sessions.csv"
REC_DIR = "recordings"
USER_DATA_PATH = "user_data.json"
ACHIEVEMENTS_PATH = "achievements.json"

# Page config
st.set_page_config(
    page_title="AI Fitness Trainer — Pro",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border-left: 4px solid #667eea;
    }
    .achievement-badge {
        display: inline-block;
        background: linear-gradient(45deg, #ff6b6b, #feca57);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        margin: 0.25rem;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .progress-bar {
        background: #f0f0f0;
        border-radius: 10px;
        height: 20px;
        overflow: hidden;
    }
    .progress-fill {
        background: linear-gradient(90deg, #667eea, #764ba2);
        height: 100%;
        transition: width 0.3s ease;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'current_exercise' not in st.session_state:
    st.session_state.current_exercise = None
if 'workout_started' not in st.session_state:
    st.session_state.workout_started = False
if 'voice_enabled' not in st.session_state:
    st.session_state.voice_enabled = True

# Utility functions
def load_user_data():
    if os.path.exists(USER_DATA_PATH):
        try:
            with open(USER_DATA_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading user data: {e}")
            # Return default user data if file can't be read
            pass
    return {
        "username": "Sahil",
        "age": 25,
        "weight_kg": 70,
        "height_cm": 175,
        "fitness_goal": "build_muscle",
        "experience_level": "intermediate",
        "points": 0,
        "streak": 0,
        "last_workout": None,
        "total_workouts": 0,
        "achievements": []
    }

def save_user_data(data):
    with open(USER_DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_achievements():
    if os.path.exists(ACHIEVEMENTS_PATH):
        try:
            with open(ACHIEVEMENTS_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading achievements: {e}")
            # Return default achievements if file can't be read
            pass
    return {
        "first_workout": {"name": "First Steps", "description": "Complete your first workout", "points": 50},
        "streak_3": {"name": "Getting Started", "description": "3-day workout streak", "points": 100},
        "streak_7": {"name": "Week Warrior", "description": "7-day workout streak", "points": 200},
        "streak_30": {"name": "Month Master", "description": "30-day workout streak", "points": 500},
        "perfect_form": {"name": "Form Master", "description": "Achieve 95%+ form score", "points": 150},
        "calorie_burner": {"name": "Calorie Crusher", "description": "Burn 500+ calories in one session", "points": 300}
    }

def calculate_bmi(weight_kg, height_cm):
    height_m = height_cm / 100
    return weight_kg / (height_m ** 2)

def generate_ai_workout_plan(user_data):
    """AI-based workout plan generator"""
    age = user_data.get('age', 25)
    weight = user_data.get('weight_kg', 70)
    goal = user_data.get('fitness_goal', 'build_muscle')
    level = user_data.get('experience_level', 'intermediate')
    
    # Base exercises
    base_exercises = {
        'build_muscle': ['squat', 'pushup', 'curl', 'lunge', 'plank'],
        'lose_weight': ['squat', 'pushup', 'lunge', 'plank', 'jumping_jack'],
        'improve_fitness': ['squat', 'pushup', 'curl', 'lunge', 'plank', 'burpee']
    }
    
    exercises = base_exercises.get(goal, base_exercises['improve_fitness'])
    
    # Adjust reps based on level and goal
    if goal == 'build_muscle':
        reps = {'beginner': 8, 'intermediate': 12, 'advanced': 15}
    elif goal == 'lose_weight':
        reps = {'beginner': 15, 'intermediate': 20, 'advanced': 25}
    else:
        reps = {'beginner': 10, 'intermediate': 15, 'advanced': 20}
    
    target_reps = reps.get(level, 12)
    
    # Calculate rest periods
    rest_sec = {'beginner': 90, 'intermediate': 60, 'advanced': 45}
    rest_time = rest_sec.get(level, 60)
    
    return {
        'exercises': exercises,
        'target_reps': target_reps,
        'sets': 3,
        'rest_seconds': rest_time,
        'estimated_duration': len(exercises) * 3 * 2 + (len(exercises) * 3 - 1) * rest_time / 60,
        'calories_target': int(weight * 0.1 * len(exercises) * 3)
    }

def get_workout_stats():
    """Get workout statistics for dashboard"""
    if not os.path.exists(LOG_PATH):
        return pd.DataFrame()
    
    try:
        df = pd.read_csv(LOG_PATH, encoding='utf-8')
        if df.empty:
            return df
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date
        return df
    except Exception as e:
        print(f"Error reading workout stats: {e}")
        return pd.DataFrame()

# Load data
user_data = load_user_data()
achievements = load_achievements()
workout_stats = get_workout_stats()

# Main header
st.markdown("""
<div class="main-header">
    <h1>🏋️ AI Fitness Trainer — Pro</h1>
    <p>Your Personal AI-Powered Fitness Companion</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("👤 Your Profile")
    
    # Profile editing
    with st.expander("Edit Profile", expanded=False):
        user_data['username'] = st.text_input("Username", user_data['username'])
        user_data['age'] = st.number_input("Age", min_value=16, max_value=100, value=user_data['age'])
        user_data['weight_kg'] = st.number_input("Weight (kg)", min_value=30.0, max_value=200.0, value=float(user_data['weight_kg']))
        user_data['height_cm'] = st.number_input("Height (cm)", min_value=100.0, max_value=250.0, value=float(user_data['height_cm']))
        user_data['fitness_goal'] = st.selectbox("Fitness Goal", 
            ['build_muscle', 'lose_weight', 'improve_fitness'], 
            index=['build_muscle', 'lose_weight', 'improve_fitness'].index(user_data['fitness_goal']))
        user_data['experience_level'] = st.selectbox("Experience Level", 
            ['beginner', 'intermediate', 'advanced'], 
            index=['beginner', 'intermediate', 'advanced'].index(user_data['experience_level']))
        
        if st.button("Save Profile"):
            save_user_data(user_data)
            st.success("Profile updated!")
    
    # Quick Navigation Buttons
    st.header("🚀 Quick Navigation")
    
    if st.button("🏋️ Start Workout", key="sidebar_workout"):
        st.session_state.current_section = "workout"
        st.rerun()
    
    if st.button("📊 Performance Dashboard", key="sidebar_dashboard"):
        st.session_state.current_section = "dashboard"
        st.rerun()
    
    if st.button("🎮 Gamification", key="sidebar_gamification"):
        st.session_state.current_section = "gamification"
        st.rerun()
    
    if st.button("🎧 Voice Settings", key="sidebar_voice"):
        st.session_state.current_section = "voice"
        st.rerun()
    
    if st.button("📋 Export & Reports", key="sidebar_export"):
        st.session_state.current_section = "export"
        st.rerun()
    
    if st.button("🏠 Home", key="sidebar_home"):
        st.session_state.current_section = "home"
        st.rerun()
    
    # Voice settings
    st.header("🎧 Settings")
    st.session_state.voice_enabled = st.checkbox("Enable Voice Feedback", value=st.session_state.voice_enabled)
    
    # AI Workout Plan
    st.header("🤖 AI Workout Plan")
    if st.button("Generate New Plan"):
        plan = generate_ai_workout_plan(user_data)
        st.session_state.ai_plan = plan
        st.success("New plan generated!")
    
    if 'ai_plan' in st.session_state:
        plan = st.session_state.ai_plan
        st.write("**Today's Plan:**")
        for i, exercise in enumerate(plan['exercises'], 1):
            st.write(f"{i}. {exercise.title()} - {plan['target_reps']} reps × {plan['sets']} sets")
        st.write(f"**Target:** {plan['calories_target']} calories")
        st.write(f"**Duration:** ~{plan['estimated_duration']:.0f} minutes")

# Main content area
# Initialize current section if not set
if 'current_section' not in st.session_state:
    st.session_state.current_section = "home"

# Section Navigation Logic
if st.session_state.current_section == "home":
    # Home Section (default) - Welcome and Overview
    st.header("🏠 Welcome to AI Fitness Trainer")
    
    # Quick overview
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 What You Can Do")
        st.write("""
        - **Start Workouts**: Choose from 6 different exercises
        - **Track Progress**: Monitor your fitness journey
        - **Earn Achievements**: Unlock badges and points
        - **Get AI Plans**: Personalized workout recommendations
        - **Voice Control**: Use voice commands during workouts
        """)
    
    with col2:
        st.subheader("🚀 Quick Start")
        st.write("""
        1. **Set up your profile** in the sidebar
        2. **Generate an AI workout plan**
        3. **Choose an exercise** and start working out
        4. **Track your progress** in the dashboard
        5. **Unlock achievements** and level up
        """)
    
    # Recent achievements or stats
    if user_data['achievements']:
        st.subheader("🏆 Recent Achievements")
        recent_achievements = user_data['achievements'][-3:]  # Show last 3
        for achievement_id in recent_achievements:
            if achievement_id in achievements:
                achievement = achievements[achievement_id]
                st.markdown(f"""
                <div class="achievement-badge">
                    {achievement['name']}
                </div>
                """, unsafe_allow_html=True)
                st.caption(achievement['description'])

elif st.session_state.current_section == "workout":
    # Workout Section
    st.header("🏋️ Start Your Workout")
    
    # Main content area for workout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🎯 Choose Your Exercise")
        
        # Exercise selection
        exercise_options = {
            'squat': '🏋️ Squats',
            'pushup': '💪 Push-ups', 
            'curl': '💪 Bicep Curls',
            'lunge': '🦵 Lunges',
            'plank': '🧘 Plank',
            'burpee': '🔥 Burpees'
        }
        
        selected_exercise = st.selectbox(
            "Choose Exercise:",
            options=list(exercise_options.keys()),
            format_func=lambda x: exercise_options[x],
            key="exercise_selector"
        )
        
        # Import the tutorial module
        from tutorials import show_tutorial
        
        # Show tutorial for the selected exercise
        with st.expander("View Exercise Tutorial", expanded=False):
            show_tutorial(selected_exercise)
        
        if st.button("🚀 Start Workout", type="primary", key="start_workout"):
            st.session_state.current_exercise = selected_exercise
            st.session_state.current_section = "workout"
            st.session_state.workout_started = True
            st.success(f"Starting {exercise_options[selected_exercise]} workout!")
            
            # Start the main exercise application
            try:
                subprocess.Popen([sys.executable, "main.py", selected_exercise])
                st.info("Exercise window opened! Switch to it to start your workout.")
            except Exception as e:
                st.error(f"Error starting workout: {e}")
        
        # Workout status
        if st.session_state.workout_started and st.session_state.current_exercise:
            st.info(f"🎯 Currently doing: {exercise_options[st.session_state.current_exercise]}")
            if st.button("⏹️ End Workout"):
                st.session_state.workout_started = False
                st.session_state.current_exercise = None
                st.success("Workout ended!")

    with col2:
        st.subheader("🏆 Quick Stats")
        
        # Stats summary
        bmi = calculate_bmi(user_data['weight_kg'], user_data['height_cm'])
        st.metric("BMI", f"{bmi:.1f}")
        st.metric("Points", f"{user_data['points']:,}")
        st.metric("Streak", f"{user_data['streak']} days")
        st.metric("Total Workouts", user_data['total_workouts'])

elif st.session_state.current_section == "dashboard":
    # Performance Dashboard
    st.header("📊 Performance Dashboard")
    
    if not workout_stats.empty:
        # Date range selector
        col1, col2, col3 = st.columns(3)
        with col1:
            date_range = st.selectbox("Time Period", ["7 days", "30 days", "90 days", "All time"])
        
        # Filter data based on selection
        if date_range != "All time":
            days = int(date_range.split()[0])
            cutoff_date = datetime.now().date() - timedelta(days=days)
            filtered_stats = workout_stats[workout_stats['date'] >= cutoff_date]
        else:
            filtered_stats = workout_stats
        
        # Metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_workouts = len(filtered_stats)
            st.metric("Total Workouts", total_workouts)
        
        with col2:
            total_reps = filtered_stats['reps'].sum() if 'reps' in filtered_stats.columns else 0
            st.metric("Total Reps", f"{total_reps:,}")
        
        with col3:
            total_calories = filtered_stats['calories'].sum() if 'calories' in filtered_stats.columns else 0
            st.metric("Calories Burned", f"{total_calories:,}")
        
        with col4:
            avg_score = filtered_stats['avg_score'].mean() if 'avg_score' in filtered_stats.columns else 0
            st.metric("Avg Form Score", f"{avg_score:.1f}%")
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Workout Frequency")
            if 'date' in filtered_stats.columns:
                daily_workouts = filtered_stats.groupby('date').size().reset_index(name='workouts')
                fig = px.line(daily_workouts, x='date', y='workouts', 
                             title="Workouts per Day")
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("🔥 Exercise Distribution")
            if 'exercise' in filtered_stats.columns:
                exercise_counts = filtered_stats['exercise'].value_counts()
                fig = px.pie(values=exercise_counts.values, names=exercise_counts.index,
                            title="Most Popular Exercises")
                st.plotly_chart(fig, use_container_width=True)
        
        # Progress tracking
        st.subheader("🎯 Progress Tracking")
        
        # Weekly goals
        col1, col2, col3 = st.columns(3)
        
        with col1:
            weekly_goal = 5  # workouts per week
            weekly_actual = len(filtered_stats[filtered_stats['date'] >= (datetime.now().date() - timedelta(days=7))])
            weekly_progress = min(weekly_actual / weekly_goal, 1.0)
            
            st.write("**Weekly Goal: 5 workouts**")
            st.markdown(f"""
            <div class="progress-bar">
                <div class="progress-fill" style="width: {weekly_progress * 100}%"></div>
            </div>
            """, unsafe_allow_html=True)
            st.write(f"{weekly_actual}/{weekly_goal} workouts completed")
        
        with col2:
            calorie_goal = 2000  # calories per week
            weekly_calories = filtered_stats[filtered_stats['date'] >= (datetime.now().date() - timedelta(days=7))]['calories'].sum()
            calorie_progress = min(weekly_calories / calorie_goal, 1.0)
            
            st.write("**Weekly Goal: 2000 calories**")
            st.markdown(f"""
            <div class="progress-bar">
                <div class="progress-fill" style="width: {calorie_progress * 100}%"></div>
            </div>
            """, unsafe_allow_html=True)
            st.write(f"{weekly_calories:.0f}/{calorie_goal} calories burned")
        
        with col3:
            form_goal = 90  # average form score
            weekly_avg_score = filtered_stats[filtered_stats['date'] >= (datetime.now().date() - timedelta(days=7))]['avg_score'].mean()
            form_progress = min(weekly_avg_score / form_goal, 1.0)
            
            st.write("**Weekly Goal: 90% form score**")
            st.markdown(f"""
            <div class="progress-bar">
                <div class="progress-fill" style="width: {form_progress * 100}%"></div>
            </div>
            """, unsafe_allow_html=True)
            st.write(f"{weekly_avg_score:.1f}% average form score")

    else:
        st.info("📝 No workout data yet. Start your first workout to see your progress!")

elif st.session_state.current_section == "gamification":
    # Gamification Section
    st.header("🎮 Gamification & Motivation")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏆 Level System")
        
        # Calculate level based on points
        level = (user_data['points'] // 100) + 1
        points_in_level = user_data['points'] % 100
        points_to_next = 100 - points_in_level
        
        st.metric("Current Level", f"Level {level}")
        st.metric("Points in Level", f"{points_in_level}/100")
        
        # Progress to next level
        st.write("**Progress to Next Level:**")
        progress = points_in_level / 100
        st.markdown(f"""
        <div class="progress-bar">
            <div class="progress-fill" style="width: {progress * 100}%"></div>
        </div>
        """, unsafe_allow_html=True)
        st.write(f"{points_to_next} points needed for Level {level + 1}")
    
    with col2:
        st.subheader("🔥 Streak & Motivation")
        
        # Streak display
        st.metric("🔥 Current Streak", f"{user_data['streak']} days")
        
        # Streak milestones
        streak_milestones = [3, 7, 14, 30, 60, 100]
        next_milestone = next((m for m in streak_milestones if m > user_data['streak']), None)
        
        if next_milestone:
            st.write(f"**Next milestone:** {next_milestone} days")
            streak_progress = user_data['streak'] / next_milestone
            st.markdown(f"""
            <div class="progress-bar">
                <div class="progress-fill" style="width: {streak_progress * 100}%"></div>
            </div>
            """, unsafe_allow_html=True)
            st.write(f"{next_milestone - user_data['streak']} days to go!")
        else:
            st.success("🎉 You've reached the maximum streak milestone!")
    
    # Achievements display
    st.subheader("🏆 Your Achievements")
    
    # Display user achievements
    for achievement_id, achievement in achievements.items():
        if achievement_id in user_data['achievements']:
            st.markdown(f"""
            <div class="achievement-badge">
                ✅ {achievement['name']}
            </div>
            """, unsafe_allow_html=True)
            st.caption(achievement['description'])
        else:
            st.markdown(f"""
            <div style="opacity: 0.5;">
                🔒 {achievement['name']}
            </div>
            """, unsafe_allow_html=True)

elif st.session_state.current_section == "voice":
    # Voice Interaction Section
    st.header("🎧 Voice Interaction & Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🗣️ Voice Commands")
        
        voice_commands = [
            "🎯 'Start workout' - Begin your exercise session",
            "⏸️ 'Pause workout' - Take a break",
            "🔄 'How many reps left?' - Get remaining rep count",
            "📊 'Show my progress' - Display current stats",
            "🎵 'Play music' - Start workout playlist",
            "⏰ 'Set timer' - Set rest timer between sets"
        ]
        
        for command in voice_commands:
            st.write(command)
    
    with col2:
        st.subheader("🎤 Voice Settings")
        
        voice_speed = st.slider("Voice Speed", min_value=0.5, max_value=2.0, value=1.0, step=0.1)
        voice_volume = st.slider("Voice Volume", min_value=0.0, max_value=1.0, value=0.8, step=0.1)
        
        if st.button("🔊 Test Voice"):
            st.info("Voice test initiated! Check your speakers.")
        
        st.write("**Available Voices:**")
        st.write("• English (US) - Male")
        st.write("• English (US) - Female")
        st.write("• English (UK) - Male")
    
    # Voice interaction tips
    st.subheader("💡 Voice Interaction Tips")
    st.write("""
    - **Speak clearly** and at a normal pace
    - **Use exact commands** for best results
    - **Ensure good microphone** quality
    - **Check audio settings** in your system
    - **Practice commands** to get familiar
    """)

elif st.session_state.current_section == "export":
    # Export and Reports Section
    st.header("📋 Export & Reports")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Export Data")
        
        if st.button("📥 Download Workout History (CSV)"):
            if not workout_stats.empty:
                try:
                    csv = workout_stats.to_csv(index=False, encoding='utf-8')
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"workout_history_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                except Exception as e:
                    st.error(f"Error exporting CSV: {e}")
            else:
                st.warning("No workout data to export")
        
        if st.button("📄 Generate PDF Report"):
            st.info("PDF report generation feature coming soon!")
        
        # Additional export options
        st.subheader("📈 Data Analytics")
        if st.button("📊 Generate Progress Report"):
            st.info("Progress report generation coming soon!")
        
        if st.button("🎯 Export Goals & Achievements"):
            st.info("Goals export feature coming soon!")

    with col2:
        st.subheader("📈 Share Progress")
        
        # Social sharing
        st.write("**Share your achievements:**")
        
        if st.button("📱 Share to Social Media"):
            st.success("Share feature coming soon!")
        
        if st.button("📧 Email Report"):
            st.info("Email feature coming soon!")
        
        # Additional sharing options
        st.subheader("🔗 Integration Options")
        if st.button("📱 Connect to Fitness Apps"):
            st.info("App integration coming soon!")
        
        if st.button("💾 Backup to Cloud"):
            st.info("Cloud backup feature coming soon!")
    
    # Export statistics
    st.subheader("📊 Export Summary")
    if not workout_stats.empty:
        st.write(f"**Total workouts available for export:** {len(workout_stats)}")
        st.write(f"**Date range:** {workout_stats['timestamp'].min()[:10]} to {workout_stats['timestamp'].max()[:10]}")
        st.write(f"**Data size:** {len(workout_stats.to_csv())} characters")
    else:
        st.info("No workout data available for export yet. Start working out to generate data!")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem;">
    <p>🏋️ AI Fitness Trainer — Pro | Built with ❤️ by Sahil</p>
    <p>Powered by OpenCV, MediaPipe, and Streamlit</p>
</div>
""", unsafe_allow_html=True)

# Auto-refresh for real-time updates
# if st.session_state.workout_started:
#     st_autorefresh(interval=5000, key="workout_refresh")