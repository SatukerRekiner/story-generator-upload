*[🇵🇱 Przejdź do polskiej wersji (Go to Polish version)](#wersja-polska)*

---

# Reddit → TTS → "karaoke" video → YouTube (Shorts)
The script generates and uploads short videos in Shorts format to YouTube based on viral Reddit stories. It can, of course, be adapted to post on other platforms as well.

The **`yt.py`** script automatically:
1) fetches longer posts from selected subreddits,  
2) generates a voiceover (TTS) + **speeds up** the audio,  
3) obtains **word-level timestamps** from AssemblyAI,  
4) assembles a vertical 1080×1920 video with word-by-word "karaoke" against a background of random clips,  
5) **uploads** the result to YouTube (Shorts).
---
## List of packages used in the project:

1) Reddit → TTS → "karaoke" video → YouTube
2) python-dotenv — configuration via .env.
3) praw — Reddit API (fetching posts).
4) TTS (Coqui TTS) — text-to-speech generation.
5) pydub — audio processing/tempo editing.
6) assemblyai — transcription and word timestamps.
7) moviepy + imageio-ffmpeg — video editing, MP4 (Shorts) rendering.
8) requests — auxiliary HTTP requests.
9) google-api-python-client, google-auth-oauthlib — YouTube Data API (upload).

External tools (binaries)
1) FFmpeg — required for video/audio rendering (MoviePy/pydub).
2) ImageMagick — subtitle/layer generation (used by MoviePy; path to magick.exe recommended on Windows).

---

## How it works

1) **Fetching stories from Reddit** - Subreddits: `["AmItheAsshole","TalesFromRetail","confession","ProRevenge"]` (list in the code, you can easily choose others, these are just examples).  
   - We take the **hot** posts from each sub (limit per sub is configurable by the `limit_per_sub` parameter in the code),  
   - we skip stickied posts, filter texts **≥ 30 words**.

2) **Splitting into parts** - Title + body are combined, then split into blocks of approx. **240 words** (`split_text`). Each part is a separate clip/part.

3) **TTS + audio speedup** - **Coqui TTS** model: `tts_models/en/jenny/jenny`.  
   - Generates a WAV file to `audio/`, then speeds it up ~**1.3×** (changing `frame_rate` in `pydub`) and saves it as a separate `*_x130.wav` file. **Cache**: if the sped-up track exists, it does not calculate it again.

4) **Transcription + word timestamps** (AssemblyAI)  
   - SDK: `Transcriber.transcribe(...)` with `language_code="en_us"`, `punctuate=True`.  
   - From the response, **words with times** (`start`/`end` in ms) are collected for the "karaoke".

5) **"Karaoke" video** - Random backgrounds from `backgrounds/` are combined to match the audio length (**max 60 s**),  
   - each clip is adjusted to a vertical format: **resize to 1920 px height** + **crop** to a width of **1080 px** (center of the frame),  
   - on top, a **TextClip** for **each word** (yellow color + black outline; `Impact` font), synchronized with the timestamp,  
   - optional "**Part N**" overlay for fragments >1,  
   - render to `videos/story_X_part_Y.mp4` @ **24 fps**.

6) **Upload to YouTube** - Title (max 100 characters), description (up to 5000), default tags (`reddit`,`shorts`,`storytime`), category **22** (People & Blogs), **public**.  
   - After uploading, log: `Uploaded to YouTube: https://youtu.be/<id>`.

---
## Demo (video)

[▶️ Watch demo (MP4)](https://github.com/SatukerRekiner/story-generator-upload/releases/download/1/demo.mp4)
this is one of the videos

---

<br>

*[🇬🇧 Go to English version](#reddit--tts--karaoke-video--youtube-shorts)*

---

## Wersja polska

# Reddit → TTS → „karaoke” wideo → YouTube (Shorts)
Skrypt generuje i uploaduje na youtube krótkie filmiki w formie shorts na podstawie viralowych historii z reddita, można go oczywiście dostosować żeby postował też na innych platformach

Skrypt **`yt.py`** automatycznie:
1) pobiera dłuższe wpisy z wybranych subredditów,  
2) generuje lektora (TTS) + **przyspiesza** audio,  
3) uzyskuje **timestampy słów** (word-level) z AssemblyAI,  
4) składa pionowe wideo 1080×1920 z word-by-word „karaoke” na tle losowych klipów,  
5) **uploaduje** wynik na YouTube (Shorts).
---
## Lista pakietów użytch w projekcie:

1) Reddit → TTS → „karaoke” wideo → YouTube
2) python-dotenv — konfiguracja z .env.
3) praw — Reddit API (pobieranie postów).
4) TTS (Coqui TTS) — generowanie mowy z tekstu.
5) pydub — obróbka/tempo audio.
6) assemblyai — transkrypcja i znaczniki słów (word timestamps).
7) moviepy + imageio-ffmpeg — montaż wideo, render MP4 (Shorts).
8) requests — pomocnicze zapytania HTTP.
9) google-api-python-client, google-auth-oauthlib — YouTube Data API (upload).

Zewnętrzne narzędzia (binaria)
1) FFmpeg — wymagane do renderu wideo/audio (MoviePy/pydub).
2) ImageMagick — generowanie napisów/warstw (używane przez MoviePy; na Windows wskazana ścieżka do magick.exe).

---

## Jak to działa

1) **Pobranie historii z Reddita** - Subreddity: `["AmItheAsshole","TalesFromRetail","confession","ProRevenge"]` (lista w kodzie, można bez problemu wybrać inne to tylko przykłady).  
   - Bierzemy **hot** z każdego suba (limit na sub konfigurowalny parametrem `limit_per_sub` w kodzie),  
   - pomijamy stickied, filtrujemy teksty **≥ 30 słów**.

2) **Dzielenie na części** - Tytuł + treść łączone, potem dzielone na bloki po ok. **240 słów** (`split_text`). Każda część to osobny klip/part.

3) **TTS + przyspieszenie audio** - Model **Coqui TTS**: `tts_models/en/jenny/jenny`.  
   - Generuje WAV do `audio/`, potem przyspiesza ~**1.3×** (zmiana `frame_rate` w `pydub`) i zapisuje jako osobny plik `*_x130.wav`. **Cache**: jeśli przyspieszona ścieżka istnieje, nie liczy ponownie.

4) **Transkrypcja + timestampy słów** (AssemblyAI)  
   - SDK: `Transcriber.transcribe(...)` z `language_code="en_us"`, `punctuate=True`.  
   - Ze zwrotki zbierane są **słowa z czasami** (`start`/`end` w ms) do „karaoke”.

5) **Wideo „karaoke”** - Losowe tła z `backgrounds/` łączone do długości audio (**max 60 s**),  
   - każdy klip dopasowany do pionu: **resize do 1920 px wysokości** + **crop** do szerokości **1080 px** (środek kadru),  
   - na wierzchu **TextClip** na **każde słowo** (kolor żółty + czarny obrys; font `Impact`), zsynchronizowany z timestampem,  
   - opcjonalny overlay „**Part N**” dla fragmentów >1,  
   - render do `videos/story_X_part_Y.mp4` @ **24 fps**.

6) **Upload na YouTube** - Tytuł (max 100 znaków), opis (do 5000), domyślne tagi (`reddit`,`shorts`,`storytime`), kategoria **22** (People & Blogs), **public**.  
   - Po wgraniu log: `Uploaded to YouTube: https://youtu.be/<id>`.

---
## Demo (wideo)

[▶️ Obejrzyj demo (MP4)](https://github.com/SatukerRekiner/story-generator-upload/releases/download/1/demo.mp4)
jest to jeden z filmików wygenerowany przy jednej z wersji tego projektu
