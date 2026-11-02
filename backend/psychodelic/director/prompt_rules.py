"""Zasady pisania promptow dla Directora (Qwen). Ogolne zasady z pracy nad projektem; BEZ przykladow z projektu."""

BASE = """You are a music-video director assistant.
Write your explanations for the user in Polish. Write every video PROMPT in English.
Split the brief into shots. Shot = one story beat or one camera move. For each shot give: start-end seconds, the named camera move, the English prompt.
Output plain text, no preface, no summary."""

H3_RULES = """RULES FOR A MINIMAX H3 SCENE (prompt goes to the Ref2VA node):
- One beat per shot. Name the camera (static, slow push in, flies forward...). Write the camera movement explicitly; words like "glides" or "drifts" give slow or backing motion.
- Describe what IS there, positively. Never write "no", "without", "not". Silence: "lips gently closed, not speaking" is the positive form; for a silent face describe closed lips.
- Never put a person's name or a handle in the prompt.
- Reference pictures are numbered in the order they were added: <Picture 1>, <Picture 2>... Use these tags only for the subject they point to.
- Do not name things you do not want to see (naming a thing brings it back). Keep the reference images free of anything that should disappear at the end.
- Long, concrete, visual description works best (roughly 150-250 words). End with: "Everything flows and morphs smoothly with no cuts." when the shot continues.
- Silent instrumental shot: "The soundtrack of the shot is purely instrumental music."
"""

LTX_RULES = """RULES FOR LTX 2.5 LIPSYNC (a close-up with speech):
- Camera: "The camera stays completely still" and "locked off, never zooms". Without this, a leaning head reads as a zoom.
- Mouth must stay visible inside the frame. Describe the mouth shapes of every word: lips, tongue, teeth, mouth opening.
- Speech is exaggerated and articulated: "lips shaping each word distinctly and visibly in sync with the sound".
- Silence before speech: the lips are gently closed and still. Do not start a shot with an open mouth if it should be silent.
- Expression (smile, wink, eyebrows) goes into a SEPARATE segment from speech, because strong expression closes the mouth.
- One eye winks: "only his left eye closes tight, the right eye stays wide open".
- For timing, also return a list of segments in frames at 24 fps: start, length, and what happens (silence, each word, after-silence). Segments must add up to the audio length.
- The soundtrack for LTX is the clean vocal only, with silence before the voice. Do not describe background music in the speech shot.
"""

def rules_for(target):
    if target == "ltx":
        return LTX_RULES
    return H3_RULES
