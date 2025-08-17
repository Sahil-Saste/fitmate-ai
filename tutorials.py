import streamlit as st
import os

# Exercise tutorials with static images
EXERCISE_TUTORIALS = {
    'squat': {
        'animation': '''
        <div style="text-align:center; padding:10px; background-color:#f8f9fa; border-radius:5px;">
            <p style="font-weight:bold; color:#4a4a4a;">Squat Animation</p>
            <p style="font-style:italic; color:#666;">Stand with feet shoulder-width apart → Bend knees and lower hips → Return to standing</p>
        </div>
        ''',
        'key_points': [
            "Keep your back straight throughout the movement",
            "Knees should track over toes, not cave inward",
            "Lower until thighs are parallel to the ground",
            "Keep weight in your heels",
            "Keep your chest up and shoulders back"
        ]
    },
    'pushup': {
        'animation': '''
        <div style="text-align:center; padding:10px; background-color:#f8f9fa; border-radius:5px;">
            <p style="font-weight:bold; color:#4a4a4a;">Pushup Animation</p>
            <p style="font-style:italic; color:#666;">Start in plank position → Lower chest to ground → Push back up to starting position</p>
        </div>
        ''',
        'key_points': [
            "Keep your body in a straight line from head to heels",
            "Elbows should be at about 45 degrees from your body",
            "Lower your chest to just above the ground",
            "Keep your core engaged throughout the movement",
            "Don't let your hips sag or pike up"
        ]
    },
    'curl': {
        'animation': '''
        <div style="text-align:center; padding:10px; background-color:#f8f9fa; border-radius:5px;">
            <p style="font-weight:bold; color:#4a4a4a;">Curl Animation</p>
            <p style="font-style:italic; color:#666;">Hold weights at sides → Bend elbows to bring weights to shoulders → Lower back down</p>
        </div>
        ''',
        'key_points': [
            "Keep your upper arms stationary against your sides",
            "Only move your forearms during the curl",
            "Fully extend your arm at the bottom of the movement",
            "Curl the weight up to shoulder level",
            "Avoid swinging or using momentum"
        ]
    },
    'lunge': {
        'animation': '''
        <div style="text-align:center; padding:10px; background-color:#f8f9fa; border-radius:5px;">
            <p style="font-weight:bold; color:#4a4a4a;">Lunge Animation</p>
            <p style="font-style:italic; color:#666;">Stand tall → Step forward with one leg → Lower until both knees at 90° → Push back to start</p>
        </div>
        ''',
        'key_points': [
            "Keep your torso upright throughout the movement",
            "Front knee should be directly above your ankle",
            "Back knee should lower to just above the ground",
            "Push through the heel of your front foot to return to standing",
            "Keep your shoulders back and chest up"
        ]
    },
    'plank': {
        'animation': '''
        <div style="text-align:center; padding:10px; background-color:#f8f9fa; border-radius:5px;">
            <p style="font-weight:bold; color:#4a4a4a;">Plank Animation</p>
            <p style="font-style:italic; color:#666;">Position on forearms and toes → Keep body straight from head to heels → Hold position</p>
        </div>
        ''',
        'key_points': [
            "Keep your body in a straight line from head to heels",
            "Engage your core by pulling your belly button toward your spine",
            "Don't let your hips sag down or pike up",
            "Keep your shoulders directly above your elbows",
            "Look slightly forward to maintain neutral neck position"
        ]
    },
    'burpee': {
        'animation': '''
        <div style="text-align:center; padding:10px; background-color:#f8f9fa; border-radius:5px;">
            <p style="font-weight:bold; color:#4a4a4a;">Burpee Animation</p>
            <p style="font-style:italic; color:#666;">Stand → Squat down → Kick feet back to plank → Push-up → Return to squat → Jump up</p>
        </div>
        ''',
        'key_points': [
            "Start in a standing position with feet shoulder-width apart",
            "Drop into a squat position and place hands on the floor",
            "Kick feet back into a plank position",
            "Perform a push-up (optional for beginners)",
            "Return feet to squat position",
            "Jump up explosively with arms overhead"
        ]
    }
}

def show_tutorial(exercise):
    """Display the tutorial for the selected exercise."""
    if exercise not in EXERCISE_TUTORIALS:
        st.warning(f"No tutorial available for {exercise}")
        return
    
    tutorial = EXERCISE_TUTORIALS[exercise]
    
    # Display the animation
    st.markdown(f"### Proper {exercise.title()} Form")
    
    # Display the text-based animation description
    st.markdown(tutorial['animation'], unsafe_allow_html=True)
    
    # Display key points
    st.markdown("### Key Form Points")
    for i, point in enumerate(tutorial['key_points'], 1):
        st.markdown(f"**{i}.** {point}")
    
    # Add a note about the form
    st.info("Note: Pay attention to the key points for proper execution.")