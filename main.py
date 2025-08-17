from utils import calculate_angle, calculate_angle_3d, smooth_angle, estimate_calories, form_score, append_log, ensure_dirs
import cv2
import mediapipe as mp
import pyttsx3
import json
import time
import os
from datetime import datetime
import sys

# Initialize voice engine
engine = pyttsx3.init()
engine.setProperty('rate', 150)

# Load user data
def load_user_data():
    if os.path.exists("user_data.json"):
        try:
            with open("user_data.json", 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading user data: {e}")
            pass
    return {"username": "Sahil", "weight_kg": 70, "points": 0, "streak": 0}

def save_user_data(data):
    with open("user_data.json", 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def update_achievements(user_data, exercise_type, reps, form_score, calories):
    """Update user achievements and points"""
    achievements = []
    points_earned = 0
    
    # First workout achievement
    if user_data.get("total_workouts", 0) == 0:
        achievements.append("first_workout")
        points_earned += 50
    
    # Perfect form achievement
    if form_score >= 95:
        achievements.append("perfect_form")
        points_earned += 150
    
    # Calorie burner achievement
    if calories >= 500:
        achievements.append("calorie_burner")
        points_earned += 300
    
    # Update user data
    user_data["points"] = user_data.get("points", 0) + points_earned
    user_data["total_workouts"] = user_data.get("total_workouts", 0) + 1
    user_data["last_workout"] = datetime.now().isoformat()
    
    # Update streak
    last_workout = user_data.get("last_workout")
    if last_workout:
        last_date = datetime.fromisoformat(last_workout).date()
        today = datetime.now().date()
        if (today - last_date).days == 1:
            user_data["streak"] = user_data.get("streak", 0) + 1
        elif (today - last_date).days > 1:
            user_data["streak"] = 0
    
    # Streak achievements
    current_streak = user_data.get("streak", 0)
    if current_streak >= 3 and "streak_3" not in user_data.get("achievements", []):
        achievements.append("streak_3")
        points_earned += 100
    if current_streak >= 7 and "streak_7" not in user_data.get("achievements", []):
        achievements.append("streak_7")
        points_earned += 200
    if current_streak >= 30 and "streak_30" not in user_data.get("achievements", []):
        achievements.append("streak_30")
        points_earned += 500
    
    # Add new achievements to user data
    if "achievements" not in user_data:
        user_data["achievements"] = []
    user_data["achievements"].extend(achievements)
    
    return points_earned, achievements

# Get exercise mode from command line argument
mode = sys.argv[1] if len(sys.argv) > 1 else "squat"

# Voice feedback variables
last_feedback = ""
feedback_cooldown = 0

# Exercise tracking variables
counter = 0
direction = 0
start_time = time.time()
form_scores = []
current_set = 1
target_sets = 3
rest_timer = 0
is_resting = False
burpee_state = "stand"  # Initialize burpee state machine

# Initialize angle history dictionary for temporal smoothing
angle_history = {}

# MediaPipe setup
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)
mp_draw = mp.solutions.drawing_utils


# Initialize webcam
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

# Create and configure the OpenCV window early for fast display and focus
window_name = "AI Fitness Trainer - Pro"
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 1)

# Load user data
user_data = load_user_data()


print(f"Starting {mode.upper()} workout for {user_data['username']}")
print(f"Target: {target_sets} sets with rest periods")

# Main exercise loop
while True:
    success, frame = cap.read()
    if not success:
        break

    # Flip frame horizontally for mirror effect
    frame = cv2.flip(frame, 1)
    
    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(img_rgb)

    if results.pose_landmarks:
        # Draw pose landmarks
        mp_draw.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

        h, w, _ = frame.shape
        lm = results.pose_landmarks.landmark

        def get_point(i):
            return [lm[i].x * w, lm[i].y * h]

        # Joint points with 3D coordinates and confidence scores
        def get_point_3d(i):
            return [lm[i].x * w, lm[i].y * h, lm[i].z * w]  # Scale z by width for proportional depth
        
        def get_confidence(i):
            return lm[i].visibility  # MediaPipe provides visibility as confidence
        
        # Get 3D points
        l_sh, r_sh = get_point_3d(11), get_point_3d(12)
        l_el, r_el = get_point_3d(13), get_point_3d(14)
        l_wr, r_wr = get_point_3d(15), get_point_3d(16)
        l_hp, r_hp = get_point_3d(23), get_point_3d(24)
        l_kn, r_kn = get_point_3d(25), get_point_3d(26)
        l_an, r_an = get_point_3d(27), get_point_3d(28)
        
        # Get confidence scores
        l_sh_conf, r_sh_conf = get_confidence(11), get_confidence(12)
        l_el_conf, r_el_conf = get_confidence(13), get_confidence(14)
        l_wr_conf, r_wr_conf = get_confidence(15), get_confidence(16)
        l_hp_conf, r_hp_conf = get_confidence(23), get_confidence(24)
        l_kn_conf, r_kn_conf = get_confidence(25), get_confidence(26)
        l_an_conf, r_an_conf = get_confidence(27), get_confidence(28)
        
        # Calculate angles with confidence weighting
        l_el_ang_result = calculate_angle_3d(l_sh, l_el, l_wr, [l_sh_conf, l_el_conf, l_wr_conf])
        r_el_ang_result = calculate_angle_3d(r_sh, r_el, r_wr, [r_sh_conf, r_el_conf, r_wr_conf])
        l_kn_ang_result = calculate_angle_3d(l_hp, l_kn, l_an, [l_hp_conf, l_kn_conf, l_an_conf])
        r_kn_ang_result = calculate_angle_3d(r_hp, r_kn, r_an, [r_hp_conf, r_kn_conf, r_an_conf])
        back_ang_result = calculate_angle_3d(l_sh, l_hp, l_kn, [l_sh_conf, l_hp_conf, l_kn_conf])
        
        # Process angle results (handle tuple returns with confidence)
        def process_angle_result(result, angle_key):
            if result is None:
                return None
            elif isinstance(result, tuple):
                angle, conf = result
                return smooth_angle(angle_key, angle, confidence=conf)
            else:
                return smooth_angle(angle_key, result)
        
        # Apply temporal smoothing
        l_el_ang = process_angle_result(l_el_ang_result, 'l_elbow')
        r_el_ang = process_angle_result(r_el_ang_result, 'r_elbow')
        l_kn_ang = process_angle_result(l_kn_ang_result, 'l_knee')
        r_kn_ang = process_angle_result(r_kn_ang_result, 'r_knee')
        back_ang = process_angle_result(back_ang_result, 'back')

        # Initialize feedback
        feedback = ""
        color = (0, 255, 0)
        current_form_score = 100

        # Exercise-specific logic
        if mode == "squat":
            angle = l_kn_ang
            if angle is None:
                feedback = "Adjusting pose detection..."
                color = (255, 165, 0)  # Orange
                current_form_score = 50
            else:
                # Improved rep counting with hysteresis for squats
                if direction == 0 and angle < 90:
                    direction = 1  # Down position reached
                elif direction == 1 and angle > 160:
                    counter += 1
                    direction = 0  # Up position reached, rep counted
                    if not is_resting:
                        engine.say(f"Great! Rep {counter}")
                        engine.runAndWait()

                # Form checking
                if angle < 50 or angle > 180:
                    feedback = "Knee angle incorrect!"
                    color = (0, 0, 255)
                    current_form_score = form_score("squat", "bottom_knee", angle)
                elif back_ang is None:
                    feedback = "Cannot see your back clearly"
                    color = (255, 165, 0)  # Orange
                    current_form_score = 70
                elif back_ang < 145:
                    feedback = "Straighten your back!"
                    color = (0, 0, 255)
                    current_form_score = form_score("squat", "back", back_ang)
                else:
                    feedback = "Perfect squat form!"
                    current_form_score = 100


        elif mode == "pushup":
            angle = l_el_ang
            if angle is None:
                feedback = "Adjusting pose detection..."
                color = (255, 165, 0)  # Orange
                current_form_score = 50
            else:
                # Improved rep counting with hysteresis
                # Only count a rep when angle goes below 80 (down) and then above 160 (up)
                if direction == 0 and angle < 80:
                    direction = 1  # Down position reached
                elif direction == 1 and angle > 160:
                    counter += 1
                    direction = 0  # Up position reached, rep counted
                    if not is_resting:
                        engine.say(f"Excellent! Rep {counter}")
                        engine.runAndWait()

                if angle < 60:
                    feedback = "Too low on push-up!"
                    color = (0, 0, 255)
                    current_form_score = form_score("pushup", "down_elbow", angle)
                elif angle > 180:
                    feedback = "Don't lock elbows!"
                    color = (0, 0, 255)
                    current_form_score = form_score("pushup", "up_elbow", angle)
                elif back_ang is None:
                    feedback = "Cannot see your back clearly"
                    color = (255, 165, 0)  # Orange
                    current_form_score = 70
                else:
                    feedback = "Perfect push-up form!"
                    current_form_score = 100

        elif mode == "curl":
            angle = l_el_ang
            if angle is None:
                feedback = "Adjusting pose detection..."
                color = (255, 165, 0)  # Orange
                current_form_score = 50
            else:
                # Improved rep counting with hysteresis for curls
                if direction == 0 and angle < 60:
                    direction = 1  # Curl up position reached
                elif direction == 1 and angle > 150:
                    counter += 1
                    direction = 0  # Curl down position reached, rep counted
                    if not is_resting:
                        engine.say(f"Strong! Rep {counter}")
                        engine.runAndWait()

                if angle > 160:
                    feedback = "Fully extended arm!"
                    color = (0, 0, 255)
                    current_form_score = form_score("curl", "down_elbow", angle)
                elif angle < 40:
                    feedback = "Excellent curl!"
                    current_form_score = 100
                else:
                    feedback = "Keep curling!"
                    current_form_score = form_score("curl", "up_elbow", angle)

        elif mode == "lunge":
            angle = l_kn_ang
            if angle is None:
                feedback = "Adjusting pose detection..."
                color = (255, 165, 0)  # Orange
                current_form_score = 50
            else:
                # Improved rep counting with hysteresis for lunges
                if direction == 0 and angle < 90:
                    direction = 1  # Down position reached
                elif direction == 1 and angle > 150:
                    counter += 1
                    direction = 0  # Up position reached, rep counted
                    if not is_resting:
                        engine.say(f"Powerful! Rep {counter}")
                        engine.runAndWait()

                if angle < 60 or angle > 170:
                    feedback = "Incorrect lunge form!"
                    color = (0, 0, 255)
                    current_form_score = form_score("lunge", "bottom_knee", angle)
                elif back_ang is None:
                    feedback = "Cannot see your back clearly"
                    color = (255, 165, 0)  # Orange
                    current_form_score = 70
                else:
                    feedback = "Nice lunge form!"
                    current_form_score = 100

        elif mode == "plank":
            feedback = "Hold steady!"
            if back_ang is None:
                feedback = "Cannot see your back clearly"
                color = (255, 165, 0)  # Orange
                current_form_score = 70
            elif back_ang < 145 or back_ang > 165:
                feedback = "Keep your back straight!"
                color = (0, 0, 255)
                current_form_score = form_score("plank", "back", back_ang)
            else:
                current_form_score = 100
                
        elif mode == "burpee":
            # Burpee has multiple stages: stand > squat > plank > squat > jump
            if l_kn_ang is None or r_kn_ang is None:
                knee_angle = None
                feedback = "Adjusting pose detection..."
                color = (255, 165, 0)  # Orange
                current_form_score = 50
            else:
                knee_angle = min(l_kn_ang, r_kn_ang)
                
                # State machine for burpee
                if knee_angle is not None and back_ang is not None:
                    if burpee_state == "stand" and knee_angle < 100:
                        burpee_state = "squat"
                    elif burpee_state == "squat" and back_ang < 140:  # Transitioned to plank
                        burpee_state = "plank"
                    elif burpee_state == "plank" and back_ang > 160 and knee_angle < 100:  # Back to squat
                        burpee_state = "squat_up"
                    elif burpee_state == "squat_up" and knee_angle > 170:  # Standing/jumping
                        burpee_state = "stand"
                        counter += 1
                        if not is_resting:
                            engine.say(f"Burpee {counter} complete!")
                            engine.runAndWait()
                
                feedback = f"Burpee state: {burpee_state}"
                current_form_score = 100  # Simplified scoring for burpees

        # Add form score to tracking
        form_scores.append(current_form_score)

        # Voice feedback with cooldown
        if feedback != last_feedback and "Perfect" not in feedback and feedback != "" and feedback_cooldown <= 0:
            if len(feedback) > 0:
                engine.say(feedback)
                engine.runAndWait()
                last_feedback = feedback
                feedback_cooldown = 30  # frames cooldown
        elif "Perfect" in feedback:
            last_feedback = feedback

        # Decrease cooldown
        if feedback_cooldown > 0:
            feedback_cooldown -= 1

        # Set completion logic
        if counter >= 12:  # Assuming 12 reps per set
            if current_set < target_sets:
                current_set += 1
                counter = 0
                is_resting = True
                rest_timer = 60  # 60 seconds rest
                engine.say(f"Set {current_set - 1} complete! Take a {rest_timer} second rest.")
                engine.runAndWait()
            else:
                # Workout complete
                engine.say("Congratulations! Workout complete!")
                engine.runAndWait()
                break

        # Rest timer logic
        if is_resting:
            rest_timer -= 1/30  # Assuming 30 FPS
            if rest_timer <= 0:
                is_resting = False
                engine.say(f"Rest complete! Start set {current_set}")
                engine.runAndWait()

    # Display information on frame
    # Header info
    cv2.putText(frame, f'{mode.upper()} WORKOUT', (30, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)
    
    # Set and rep info
    cv2.putText(frame, f'Set: {current_set}/{target_sets}', (30, 100),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.putText(frame, f'Reps: {counter}/12', (30, 140),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    # Form score
    if form_scores:
        avg_score = sum(form_scores) / len(form_scores)
        cv2.putText(frame, f'Form Score: {avg_score:.1f}%', (30, 180),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    # Feedback
    if feedback:
        cv2.putText(frame, feedback, (30, 220),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
    
    # Rest timer
    if is_resting:
        cv2.putText(frame, f'REST: {int(rest_timer)}s', (30, 260),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
    
    # Progress bar
    progress = counter / 12.0
    bar_width = 400
    bar_height = 20
    bar_x, bar_y = 30, 300
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (100, 100, 100), -1)
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + int(bar_width * progress), bar_y + bar_height), (0, 255, 0), -1)
    cv2.putText(frame, f'Progress: {progress*100:.0f}%', (bar_x, bar_y + bar_height + 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    # Display frame
    cv2.imshow(window_name, frame)
    
    # Check for quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()

# Calculate workout statistics
workout_duration = time.time() - start_time
total_reps = (current_set - 1) * 12 + counter
avg_form_score = sum(form_scores) / len(form_scores) if form_scores else 0
calories_burned = estimate_calories(mode, workout_duration, user_data.get('weight_kg', 70))

# Update user data and achievements
points_earned, new_achievements = update_achievements(user_data, mode, total_reps, avg_form_score, calories_burned)
save_user_data(user_data)

# Log workout session
session_data = {
    "timestamp": datetime.now().isoformat(),
    "user": user_data["username"],
    "exercise": mode,
    "reps": total_reps,
    "avg_score": round(avg_form_score, 1),
    "duration_sec": round(workout_duration, 1),
    "calories": round(calories_burned, 1)
}
append_log(session_data)

# Final summary
print(f"\n{'='*50}")
print(f"WORKOUT COMPLETE!")
print(f"{'='*50}")
print(f"Exercise: {mode.upper()}")
print(f"Sets completed: {current_set - 1}")
print(f"Total reps: {total_reps}")
print(f"Duration: {workout_duration:.1f} seconds")
print(f"Average form score: {avg_form_score:.1f}%")
print(f"Calories burned: {calories_burned:.1f}")
print(f"Points earned: {points_earned}")
print(f"Total points: {user_data['points']}")
print(f"Current streak: {user_data['streak']} days")

if new_achievements:
    print(f"\n🏆 NEW ACHIEVEMENTS UNLOCKED:")
    for achievement in new_achievements:
        print(f"   ✅ {achievement}")

print(f"\nGreat job, {user_data['username']}! Keep up the amazing work! 💪")
