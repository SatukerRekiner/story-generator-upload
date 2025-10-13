# Reddit → TTS → „karaoke” wideo → YouTube (Shorts)

Skrypt **`yt.py`** automatycznie:
1) pobiera dłuższe wpisy z wybranych subredditów,  
2) generuje lektora (TTS) + **przyspiesza** audio,  
3) uzyskuje **timestampy słów** (word-level) z AssemblyAI,  
4) składa pionowe wideo 1080×1920 z word-by-word „karaoke” na tle losowych klipów,  
5) **uploaduje** wynik na YouTube (Shorts).

---

## Wymagania

### System / binaria
- **Python 3.10+**  
- **FFmpeg** w systemie (wymagane przez MoviePy)  
- **ImageMagick** – na Windows ścieżka ustawiona w skrypcie, np.:
  ```py
  os.environ["IMAGEMAGICK_BINARY"] = r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"
  ``` 
  Jeśli masz inną wersję/ścieżkę, zaktualizuj ją w `yt.py`.

### Pakiety Pythona
```bash
pip install python-dotenv praw moviepy imageio-ffmpeg assemblyai TTS requests             google-api-python-client google-auth-oauthlib pydub
```
*(MoviePy pociągnie `imageio-ffmpeg`; `pydub` używa lokalnego ffmpeg.)*

---

## Klucze/API & pliki tajne

Utwórz plik **`.env`** (nie commituj) z danymi do Reddit i AssemblyAI:
```env
REDDIT_CLIENT_ID=xxx
REDDIT_CLIENT_SECRET=xxx
REDDIT_USER_AGENT=your-app-name/1.0
ASSEMBLYAI_API_KEY=xxx
```
Skrypt ładuje je przez `dotenv`.

**YouTube Data API (upload):**
- Plik **`secret_yt.json`** (OAuth Client „Desktop”) w katalogu projektu.  
- Przy pierwszym uruchomieniu powstanie **`token.pickle`** (autoryzacja w przeglądarce).  
- Zakres uprawnień: `https://www.googleapis.com/auth/youtube.upload`.

> Uwaga: `secret_yt.json` i `token.pickle` trzymaj **lokalnie** (dodaj do `.gitignore`).

---

## Dane wejściowe (foldery)

- **`backgrounds/`** – pionowe/poziome **.mp4** z tłem do wideo. Skrypt wybiera losowe klipy i składa je do docelowego czasu.  
- Skrypt sam utworzy: **`audio/`** i **`videos/`**.

---

## Jak to działa – pipeline

1) **Pobranie historii z Reddita**  
   - Subreddity: `["AmItheAsshole","TalesFromRetail","confession","ProRevenge"]` (lista w kodzie).  
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

## Uruchomienie

```bash
# 1) Zainstaluj zależności (patrz wyżej) + miej FFmpeg & ImageMagick
# 2) Dodaj .env z kluczami (Reddit + AssemblyAI)
# 3) Umieść sekrety YouTube: secret_yt.json (Desktop OAuth) – token.pickle utworzy się sam
# 4) Dodaj tła .mp4 do ./backgrounds

python yt.py
```

**Parametry/zmiany w kodzie (szybko):**
- Lista subredditów → `subreddits = [...]`  
- Limit postów na sub → `fetch_stories(limit_per_sub=5)`  
- Graniczna długość fragmentu → `split_text(..., max_words=240)`  
- Maksymalny czas klipu → `target_duration = min(audio, 60.0)` w `create_karaoke_video`.

---

## Struktura (po pierwszym przebiegu)
```
.
├─ backgrounds/          # Twoje tła .mp4
├─ audio/                # wav + wersje przyspieszone (cache)
├─ videos/               # gotowe mp4 (Shorts)
├─ secret_yt.json        # OAuth (lokalnie)
├─ token.pickle          # token YouTube (lokalnie)
├─ .env                  # klucze API (lokalnie)
└─ yt.py
```
*(Pliki tajne trzymaj lokalnie; nie commituj.)*

---

## Notatki techniczne

- **Lazy cache audio** – jeśli istnieje wersja przyspieszona, TTS jest pomijany (oszczędność czasu).  
- **Czcionka** – `TextClip` używa zdefiniowanej nazwy (np. `Impact`). Upewnij się, że font jest w systemie; w razie błędu zmień na dostępny (`Arial-Bold`, `DejaVu Sans`).  
- **Nieużywana pomocnicza funkcja** `upload_audio_to_assemblyai` – w kodzie jest alternatywa uploadu przez REST; aktualna ścieżka korzysta ze **SDK**.

---

## Bezpieczeństwo & zgodność

- **Sekrety lokalnie**: `.env`, `secret_yt.json`, `token.pickle` — **nie commituj** do repo.  
- **Prawa do treści**: publikowanie cudzych historii/głosów/tła może podlegać prawom autorskim/regulaminom (Reddit API / zasady subreddita / YouTube). To nie jest porada prawna; twórz **własne treści** lub trzymaj się zasad licencji/zgód.  
- **Limity/koszty**: API AssemblyAI i YouTube mają limity/rozliczenia — obserwuj użycie.  
- **Tryb testowy**: rozważ tryb **DRY_RUN** (ENV/flaga), by pominąć upload podczas testów.

---

## Pomysły na rozbudowę
- Flaga `--dry-run` (bez uploadu), `--limit` postów, `--max-duration` (np. 30–45 s).  
- Auto-skróty (TL;DR) lub stress-timingi (przyspieszenie w ciszy).  
- Szablony wyglądu (kolor/pozycja/animacja słów), watermark, miniatury.  
- Kolejka uploadów z kontrolą quota.
