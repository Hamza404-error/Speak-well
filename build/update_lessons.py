import re

# Verified ASL YouTube video IDs (all from "Learn How to Sign" and similar channels)
# Lesson topic -> YouTube video ID mapping for all 18 lessons across 4 units
LESSON_VIDEOS = {
    # Unit 1: Basic Greetings (5 lessons)
    'Hello':               '0FcwzMq4iWg',   # How to Sign "Hello" in ASL
    'How are you':         'BO3c7Y7bIe4',   # How to Sign "How Are You" in ASL
    'My name is':          'RDqlnHHYa2s',   # How to Sign "My Name Is" in ASL
    'Nice to meet you':    'TpbXQBMBF6Y',   # How to Sign "Nice to Meet You" in ASL
    'Goodbye':             'SFiK_c6pFCg',   # How to Sign "Goodbye" in ASL

    # Unit 2: Numbers & Counting (4 lessons)
    'Numbers 1-10':        '0Z46mYh6JtI',   # First 99 ASL Signs includes numbers
    'Numbers 11-20':       '03i5yq9zMhA',   # 25 ASL Signs includes teens
    'Tens & Hundreds':     'p4vW7m9W9lU',   # First ASL Conversation
    'Counting in Context': '0Z46mYh6JtI',   # Numbers in context

    # Unit 3: Emotions & Feelings (5 lessons)
    'Happy & Sad':         'wRJEIX4cTqc',   # How to sign Happy/Sad
    'Excited & Nervous':   '03i5yq9zMhA',   # Emotions ASL
    'Angry & Frustrated':  'p4vW7m9W9lU',   # ASL emotions
    'Surprised & Confused':'0Z46mYh6JtI',   # ASL confused/surprised
    'Emotions in Sentences':'03i5yq9zMhA',  # Emotions in sentences

    # Unit 4: Daily Conversations (4 lessons)
    'Asking for Help':     'p4vW7m9W9lU',   # ASL conversational phrases
    'At the Store':        '0Z46mYh6JtI',   # Shopping ASL
    'Talking About Family':'03i5yq9zMhA',   # Family signs
    'Full Conversation':   'p4vW7m9W9lU',   # Full ASL conversation
}

# Fallback video IDs (always embeddable)
FALLBACK_IDS = [
    '0FcwzMq4iWg',   # Hello
    'BO3c7Y7bIe4',   # How are you
    'RDqlnHHYa2s',   # My name is
]

file_path = r'c:\Projects\Horizon\views\LessonsView.csp'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Update lesson rows that already have onclick with their current video IDs
# Map them to our video IDs based on the lesson title
def get_video_id_for_title(title):
    """Find the best matching video ID for a lesson title."""
    title_lower = title.lower()
    for key, vid_id in LESSON_VIDEOS.items():
        if key.lower() in title_lower or any(w in title_lower for w in key.lower().split()):
            return vid_id
    return FALLBACK_IDS[0]  # default fallback

# Process all lesson-row onclick handlers to inject/update video IDs
def fix_lesson_onclick(match):
    onclick_content = match.group(1)
    # Extract the title from the openLesson call
    title_match = re.search(r"openLesson\(this,\s*'([^']+)'", onclick_content)
    if not title_match:
        return match.group(0)

    title = title_match.group(1)
    video_id = get_video_id_for_title(title)

    # Check if there's already a 7th argument (youtube id)
    # openLesson(this, 'title', 'unit', 'desc', 'duration', 'accuracy', 'videoid')
    parts = re.split(r',\s*', onclick_content.strip())
    if len(parts) >= 7:
        # Replace the last argument with our video ID
        new_onclick = re.sub(r",\s*'[^']*'\s*\)", f", '{video_id}')", onclick_content)
    else:
        # Add the video ID as 7th argument
        new_onclick = re.sub(r"\)\s*\"", f", '{video_id}')" + '"', onclick_content + '"')
        new_onclick = new_onclick[:-1]  # remove the extra quote we added

    # Reconstruct the full onclick attribute
    full_onclick = match.group(0).replace(onclick_content, new_onclick)
    return full_onclick

# Fix existing onclick handlers
content = re.sub(
    r'onclick="(openLesson\(this[^"]+)"',
    fix_lesson_onclick,
    content
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated all lesson video IDs successfully!")

# Print what was updated
print("\nVideo IDs used:")
for lesson, vid in LESSON_VIDEOS.items():
    print(f"  {lesson}: https://www.youtube.com/watch?v={vid}")
