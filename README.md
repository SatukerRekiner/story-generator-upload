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

1) **Pobranie historii z Reddita**  
   - Subreddity: `["AmItheAsshole","TalesFromRetail","confession","ProRevenge"]` (lista w kodzie, można bez problemu wybrać inne to tylko przykłady).  
   - Bierzemy **hot** z każdego suba (limit na sub konfigurowalny parametrem `limit_per_sub` w kodzie),  
   - pomijamy stickied, filtrujemy teksty **≥ 30 słów**.

2) **Dzielenie na części**  
   - Tytuł + treść łączone, potem dzielone na bloki po ok. **240 słów** (`split_text`). Każda część to osobny klip/part.

3) **TTS + przyspieszenie audio**  
   - Model **Coqui TTS**: `tts_models/en/jenny/jenny`.  
   - Generuje WAV do `audio/`, potem przyspiesza ~**1.3×** (zmiana `frame_rate` w `pydub`) i zapisuje jako osobny plik `*_x130.wav`. **Cache**: jeśli przyspieszona ścieżka istnieje, nie liczy ponownie.

4) **Transkrypcja + timestampy słów** (AssemblyAI)  
   - SDK: `Transcriber.transcribe(...)` z `language_code="en_us"`, `punctuate=True`.  
   - Ze zwrotki zbierane są **słowa z czasami** (`start`/`end` w ms) do „karaoke”.

5) **Wideo „karaoke”**  
   - Losowe tła z `backgrounds/` łączone do długości audio (**max 60 s**),  
   - każdy klip dopasowany do pionu: **resize do 1920 px wysokości** + **crop** do szerokości **1080 px** (środek kadru),  
   - na wierzchu **TextClip** na **każde słowo** (kolor żółty + czarny obrys; font `Impact`), zsynchronizowany z timestampem,  
   - opcjonalny overlay „**Part N**” dla fragmentów >1,  
   - render do `videos/story_X_part_Y.mp4` @ **24 fps**.

6) **Upload na YouTube**  
   - Tytuł (max 100 znaków), opis (do 5000), domyślne tagi (`reddit`,`shorts`,`storytime`), kategoria **22** (People & Blogs), **public**.  
   - Po wgraniu log: `Uploaded to YouTube: https://youtu.be/<id>`.

---

<h3>Demo (wideo)</h3>
<video src="demo.mp4"
       controls
       muted
       playsinline
       loop
       style="max-width:100%;height:auto;">
  Twój browser nie wspiera wideo HTML5.
  <a href="demo.mp4">Pobierz demo.mp4</a>
</video>

[Obejrzyj demo (MP4)](https://raw.githubusercontent.com/SatukerRekiner/story-generator-upload/main/demo.mp4)

