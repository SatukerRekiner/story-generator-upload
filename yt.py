import os
os.environ["IMAGEMAGICK_BINARY"] = r"C:\\Program Files\\ImageMagick-7.1.1-Q16-HDRI\\magick.exe"

import time
import random
from dotenv import load_dotenv
import praw
from moviepy.editor import (
    TextClip, AudioFileClip, CompositeVideoClip, VideoFileClip, concatenate_videoclips
)
import assemblyai as aai
from moviepy.video.fx.resize import resize
from moviepy.video.fx.crop import crop
from TTS.api import TTS
import requests
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from pydub import AudioSegment




# === LOAD CONFIG ===
load_dotenv()
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")



# === SETUP REDDIT ===
reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT
)

backgrounds_folder = "backgrounds"
subreddits = ["AmItheAsshole", "TalesFromRetail", "confession", "ProRevenge"]

# === AssemblyAI API Helpers ===
assembly_headers = {
    "authorization": ASSEMBLYAI_API_KEY,
    "content-type": "application/json"
}
aai.settings.api_key = ASSEMBLYAI_API_KEY
transcriber = aai.Transcriber()

def upload_audio_to_assemblyai(filepath):
    print("[+] Uploading audio to AssemblyAI...")
    with open(filepath, "rb") as f:
        response = requests.post(
            "https://api.assemblyai.com/v2/upload",
            headers={"authorization": ASSEMBLYAI_API_KEY},
            data=f
        )
    response.raise_for_status()
    upload_url = response.json()["upload_url"]
    print("[+] Upload finished:", upload_url)
    return upload_url

def request_transcription(audio_path):
    print("[+] Requesting transcription with timestamps...")

    config = aai.TranscriptionConfig(
        word_boost=[],  # jeśli chcesz podbić konkretne słowa (tu puste)
        punctuate=True,
        format_text=True,
        language_code="en_us"
    )

    transcript = transcriber.transcribe(audio_path, config=config)

    # Wyciągnięcie timestampów słów
    words_timestamps = [
        {
            "text": word.text,
            "start": word.start,
            "end": word.end
        }
        for word in transcript.words
    ]

    return transcript.id, words_timestamps


def wait_for_transcription(transcript_id):
    print("[+] Waiting for transcription to complete...")
    polling_url = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"
    while True:
        response = requests.get(polling_url, headers=assembly_headers)
        response.raise_for_status()
        data = response.json()
        if data["status"] == "completed":
            print("[+] Transcription completed!")
            return data
        elif data["status"] == "error":
            raise Exception(f"Transcription failed: {data['error']}")
        else:
            time.sleep(3)

# === Other helpers ===
def clean_text(text):
    return text.replace("\n", " ").replace("&amp;", "&").strip()

def split_text(text, max_words=240):
    words = text.split()
    return [" ".join(words[i:i + max_words]) for i in range(0, len(words), max_words)]

def fetch_stories(limit_per_sub=5):
    stories = []
    for sub in subreddits:
        for post in reddit.subreddit(sub).hot(limit=limit_per_sub):
            if post.stickied:
                continue
            if post.selftext and len(post.selftext.split()) >= 30:
                stories.append({
                    "title": clean_text(post.title),
                    "text": clean_text(post.selftext)
                })
    return stories


# Inicjalizacja modelu - najlepiej raz
#tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC")
#tts = TTS(model_name="tts_models/en/vctk/vits")
#tts = TTS(model_name="tts_models/en/ek1/tacotron2")
# tts = TTS(model_name="tts_models/en/ljspeech/glow-tts")        to są różne przykładowe inne głosy
tts = TTS(model_name="tts_models/en/jenny/jenny")

def generate_audio(text, filename, speedup_factor=1.3):
    os.makedirs("audio", exist_ok=True)
    base_path = os.path.join("audio", filename + ".wav")
    fast_path = os.path.join("audio", filename + f"_x{int(speedup_factor)}.wav")

    # Jeśli przyspieszony audio już istnieje – zwróć
    if os.path.exists(fast_path):
        print(f"[✓] Przyspieszony audio już istnieje: {fast_path}")
        return fast_path

    # Jeśli bazowy audio istnieje, nie generuj ponownie
    if not os.path.exists(base_path):
        print(f"[+] Generowanie audio (Coqui TTS): {filename}")
        tts.tts_to_file(text=text, file_path=base_path)
    else:
        print(f"[✓] Audio już istnieje: {base_path}")

    print(f"[+] Przyspieszanie audio: {filename} x{speedup_factor}")
    sound = AudioSegment.from_file(base_path)
    faster_sound = sound._spawn(sound.raw_data, overrides={
        "frame_rate": int(sound.frame_rate * speedup_factor)
    }).set_frame_rate(sound.frame_rate)

    faster_sound.export(fast_path, format="wav")
    return fast_path



def create_karaoke_video(text, audio_path, backgrounds_folder, filename, words_timestamps, story_title=None, part_number=1):
    audio_clip = AudioFileClip(audio_path)
    target_duration = min(audio_clip.duration, 60.0)  # max 60 sekund
    audio_clip = audio_clip.subclip(0, target_duration)

    # Load backgrounds
    backgrounds = [os.path.join(backgrounds_folder, f) for f in os.listdir(backgrounds_folder) if f.endswith(".mp4")]
    if not backgrounds:
        raise Exception("No background videos found!")

    clips = []
    total_duration = 0
    while total_duration < target_duration:
        bg_path = random.choice(backgrounds)

        #clip = VideoFileClip(bg_path).resize((1080, 1920))
        clip = VideoFileClip(bg_path)
        clip = clip.fx(resize, height=1920)
        clip = clip.fx(crop, width=1080, x_center=clip.w / 2)
        clips.append(clip)
        total_duration += clip.duration
    bg_clip = concatenate_videoclips(clips).subclip(0, target_duration)

    # === [1] Tytuł posta ===
    # title_clip = (
    #     TextClip(story_title, fontsize=75, color='white', font='Arial-Bold', size=(900, None), method='caption', align='center')
    #     .set_duration(target_duration)
    #     .set_position(("center", 55))
    # )   w tej wersji akurat wyłączyłem tutuł posta bo lepiej wygląda bez, ale no jak ktoś chce to można

    # === [2] Numer części (jeśli > 1) ===
    if part_number > 1:
        part_clip = (
            TextClip(
                f"Part {part_number}",
                fontsize=75,
                color='red',
                font='Arial-Bold',
                size=(600, None),
                stroke_color='black',
                stroke_width=2,
                method='caption'
            )
            .set_duration(target_duration)
            .set_position(("center", 500))
            .fadeout(5)
        )
    else:
        part_clip = None

    # Przytnij słowa do czasu trwania video
    words_timestamps = [w for w in words_timestamps if (w["start"] / 1000.0) < target_duration]

    # Twórz napisy słowo po słowie
    txt_clips = []
    for w in words_timestamps:
        word_text = w["text"]
        start = w["start"] / 1000.0
        end = w["end"] / 1000.0
        duration = end - start

        txt_clip = (
            TextClip(
                word_text,
                fontsize=72,
                font="Impact",               # Możesz zmienić na Arial-Bold, DejaVu-Sans itp.
                color='yellow',
                stroke_color='black',
                stroke_width=2,
                method='caption',
            )
            .set_start(start)
            .set_duration(duration)
            .set_position('center')
            # .fadein(0.1).fadeout(0.1)    # Opcjonalnie: dodaj delikatne pojawianie/zanikanie
        )
        txt_clips.append(txt_clip)

    #video = CompositeVideoClip([bg_clip, *txt_clips])
    #video = video.set_audio(audio_clip).set_duration(target_duration)

    video_layers = [bg_clip, *txt_clips]
    if part_clip:
        video_layers.insert(2, part_clip)

    video = CompositeVideoClip(video_layers)
    video = video.set_audio(audio_clip).set_duration(target_duration)

    os.makedirs("videos", exist_ok=True)
    output_path = os.path.join("videos", filename + ".mp4")
    video.write_videofile(output_path, fps=24, threads=4)

    for clip in clips:
        clip.close()
    audio_clip.close()

    return output_path

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CLIENT_SECRETS_FILE = "secret_yt.json"  # ← tu wrzuć swój plik
TOKEN_FILE = "token.pickle"  # zapisany po autoryzacji

def get_authenticated_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    return build("youtube", "v3", credentials=creds)

def upload_video_to_youtube(video_path, title, description, tags=None):
    youtube = get_authenticated_service()

    request_body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags or ["reddit", "shorts", "storytime"],
            "categoryId": "22"  # 22 = People & Blogs
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False
        }
    }

    media_file = MediaFileUpload(video_path, resumable=True, mimetype="video/*")

    response_upload = youtube.videos().insert(
        part="snippet,status",
        body=request_body,
        media_body=media_file
    ).execute()

    print(f"[✓] Uploaded to YouTube: https://youtu.be/{response_upload['id']}")



if __name__ == "__main__":
    os.makedirs("audio", exist_ok=True)
    os.makedirs("videos", exist_ok=True)

    stories = fetch_stories(limit_per_sub=5)

    for i, story in enumerate(stories):
        print(f"Processing story {i + 1}: {story['title'][:50]}...")
        full_text = story['title'] + ". " + story['text']
        text_parts = split_text(full_text)

        for j, part in enumerate(text_parts):
            filename = f"story_{i + 1}_part_{j + 1}"

            # 1) Generuj audio (lub wykorzystaj jeśli już istnieje)
            audio_path = generate_audio(part, filename)

            # 2) Użyj AssemblyAI SDK do transkrypcji z timestampami
            transcript_id, words_timestamps = request_transcription(audio_path)

            # 3) Generuj video z audiodeskrypcją na podstawie timestampów
            output_path = create_karaoke_video(
                text=part,
                audio_path=audio_path,
                backgrounds_folder=backgrounds_folder,
                filename=filename,
                words_timestamps=words_timestamps,
                story_title=story["title"],
                part_number=j + 1
            )
            time.sleep(1)
            # === Upload to YouTube ===
            upload_video_to_youtube(
                video_path=output_path,
                title=f"{story['title'][:80]} #shorts",
                description=f"A Reddit story from r/{random.choice(subreddits)}.\n#reddit #shorts #storytime",
                tags=["reddit", "shorts", "AI", "story", "voiceover"]
            )
            time.sleep(100)


