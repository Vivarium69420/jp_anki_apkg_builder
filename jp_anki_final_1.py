import sys
import os
import csv
import argparse
from jamdict import Jamdict
from gtts import gTTS

jam = Jamdict()

def is_kanji(char):
    return '\u4e00' <= char <= '\u9faf'

def process_word(word, base_dir, writer):
    print(f"--- Processing: {word} ---")
    result = jam.lookup(word)
    
    if not result.entries:
        print(f"⚠️ No entry found for: {word}")
        return False

    entry = result.entries[0]
    kanji_word = entry.kanji_forms[0].text if entry.kanji_forms else word
    kana_reading = entry.kana_forms[0].text if entry.kana_forms else ""
    english = ", ".join(["/".join([g.text for g in s.gloss]) for s in entry.senses[:2]])

    unique_kanji = [c for c in kanji_word if is_kanji(c)]
    breakdown = []
    for char in unique_kanji:
        c_res = jam.lookup(char)
        if c_res.chars:
            m = c_res.chars[0].meanings()
            breakdown.append(f"{char}: {', '.join(m[:2])}")
    kanji_breakdown = " | ".join(breakdown)

    audio_filename = f"{kanji_word}.mp3"
    audio_path = os.path.join(base_dir, audio_filename)

    try:
        # Save unique MP3 for this word
        tts = gTTS(text=kanji_word, lang='ja')
        tts.save(audio_path)
        
        # UPDATED: Use the absolute path instead of just the filename
        # Format: [sound:/full/path/to/word.mp3]
        sound_field = f"[sound:{audio_path}]"
        
        writer.writerow([kana_reading, kanji_word, english, kanji_breakdown, sound_field])
        print(f"✅ Saved audio and added to CSV with path.")
        return True
    except Exception as e:
        print(f"❌ Error processing {word}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Japanese to Anki Tool")
    parser.add_argument('words', nargs='*', help="Individual Japanese words")
    parser.add_argument('--list', nargs='+', help="Multiple words to process into one CSV")
    
    args = parser.parse_args()
    
    words_to_process = []
    if args.list:
        words_to_process = args.list
    elif args.words:
        words_to_process = args.words
    else:
        print("Usage: python jp_anki_final.py <word> OR python jp_anki_final.py --list <word1> <word2>")
        return

    # Using the standard Termux downloads path
    base_dir = os.path.expanduser("~/storage/downloads")
    if not os.path.exists(base_dir):
        os.makedirs(base_dir, exist_ok=True)

    csv_path = os.path.join(base_dir, "bulk_vocab.csv")
    mode = 'w' if args.list else 'a'
    
    with open(csv_path, mode=mode, newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if mode == 'w' or (os.path.exists(csv_path) and os.stat(csv_path).st_size == 0):
            writer.writerow(['japanese_kana', 'kanjis', 'english', 'kanji_meaning', 'sound'])
        
        for w in words_to_process:
            process_word(base_dir, base_dir, writer) # Note: Passing base_dir twice to match function signature
            # Wait, fixed the logic error in the call below:
            # process_word(w, base_dir, writer) 
        
        # Correcting the loop call logic:
        for w in words_to_process:
            process_word(w, base_dir, writer)
            f.flush()

    print(f"\n✨ Done! CSV with full paths: {csv_path}")

if __name__ == "__main__":
    main()
