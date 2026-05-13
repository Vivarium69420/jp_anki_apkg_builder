import sys
import os
import genanki
from jamdict import Jamdict
from gtts import gTTS

# Initialize Dictionary
jam = Jamdict()

MODEL_J_TO_E_ID = 1607392319
MODEL_E_TO_J_ID = 1607392320
DECK_ID = 2059400110

CSS = """
.card {
  font-family: "Noto Sans Japanese";
  font-size: 20px;
  text-align: center;
}
@font-face {
  font-family: "Noto Sans Japanese";
  src: url("_NotoSansCJKjp-Regular.woff2") format("woff2");
}
.japanese {
 font-family: "Noto Sans Japanese";
}
"""

# Japanese -> English Model
MODEL_J_TO_E = genanki.Model(
  MODEL_J_TO_E_ID,
  'Japanese to English (Custom)',
  fields=[
    {'name': 'japanese_kana'},
    {'name': 'kanjis'},
    {'name': 'english'},
    {'name': 'breakdown'},
    {'name': 'sound'},
  ],
  templates=[{
    'name': 'Jp -> En',
    'qfmt': '<font lang="jp" size="6px" color="#C0C0C0"><span class="japanese">{{kanjis}}</span></font><br><font lang="jp" size="15px"><span class="japanese">{{japanese_kana}}</span></font><br>{{sound}}<br>',
    'afmt': '{{FrontSide}}<font lang="jp" size="4px" color="#C0C0C0">Meaning: </font><br><font lang="jp" size="15px"><span class="text">{{english}}</span></font><br><br>{{#breakdown}}<font lang="jp" size="4px" color="#C0C0C0">Kanji Meaning: </font><br><font lang="jp" size="6px"><span class="japanese">{{kanjis}}</span></font><br><font lang="jp" size="6px"><span class="text">{{breakdown}}</span></font><br>{{/breakdown}}',
  }],
  css=CSS)

# English -> Japanese Model (Type Answer)
MODEL_E_TO_J = genanki.Model(
  MODEL_E_TO_J_ID,
  'English to Japanese (Custom)',
  fields=[
    {'name': 'japanese_kana'},
    {'name': 'kanjis'},
    {'name': 'english'},
    {'name': 'breakdown'},
    {'name': 'sound'},
  ],
  templates=[{
    'name': 'En -> Jp',
    'qfmt': '<font lang="jp" size="15px"><span class="text">{{english}}</span></font><br>{{type:japanese_kana}}<br>',
    'afmt': '{{FrontSide}}<font lang="jp" size="4px" color="#C0C0C0">Meaning: </font><br><font lang="jp" size="6px" color="#C0C0C0"><span class="japanese">{{kanjis}}</span></font><br><font lang="jp" size="15px"><span class="japanese">{{japanese_kana}}</span></font><br><br>{{#breakdown}}<font lang="jp" size="4px" color="#C0C0C0">Kanji Meaning: </font><br><font lang="jp" size="6px"><span class="japanese">{{kanjis}}</span></font><br><font lang="jp" size="6px"><span class="text">{{breakdown}}</span></font><br>{{/breakdown}}{{sound}}<br>',
  }],
  css=CSS)

def is_kanji(char):
    return '\u4e00' <= char <= '\u9faf'

def get_word_data(word):
    result = jam.lookup(word)
    if not result.entries:
        return None
    entry = result.entries[0]
    kanji_word = entry.kanji_forms[0].text if entry.kanji_forms else word
    kana_reading = entry.kana_forms[0].text if entry.kana_forms else ""
    english = ", ".join(["/".join([g.text for g in s.gloss]) for s in entry.senses[:2]])
    unique_kanji = [c for c in kanji_word if is_kanji(c)]
    breakdown_parts = []
    for char in unique_kanji:
        c_res = jam.lookup(char)
        if c_res.chars:
            m = c_res.chars[0].meanings()
            breakdown_parts.append(f"{char}: {', '.join(m[:2])}")
    return {'kanji': kanji_word, 'kana': kana_reading, 'english': english, 'breakdown': " | ".join(breakdown_parts)}

def main():
    words = sys.argv[1:]
    if not words:
        print("Usage: python jp_to_apkg.py <word1> <word2> ...")
        return

    base_dir = os.path.expanduser("~/storage/downloads")
    os.makedirs(base_dir, exist_ok=True)
    
    deck = genanki.Deck(DECK_ID, 'Japanese::Vocabulary_Auto')
    media_files = []

    for word in words:
        data = get_word_data(word)
        if not data:
            print(f"⚠️ Not found: {word}")
            continue
        
        print(f"📦 Processing: {data['kanji']}")
        audio_file = f"{data['kanji']}.mp3"
        audio_path = os.path.join(base_dir, audio_filename := audio_file)
        gTTS(text=data['kanji'], lang='ja').save(audio_path)
        media_files.append(audio_path)

        fields = [data['kana'], data['kanji'], data['english'], data['breakdown'], f"[sound:{audio_file}]"]
        deck.add_note(genanki.Note(model=MODEL_J_TO_E, fields=fields))
        deck.add_note(genanki.Note(model=MODEL_E_TO_J, fields=fields))

    # Name file after the first word if only one word, otherwise use generic name
    out_name = f"{words[0]}.apkg" if len(words) == 1 else "00_Japanese_Batch.apkg"
    output_path = os.path.join(base_dir, out_name)
    
    genanki.Package(deck, media_files=media_files).write_to_file(output_path)
    print(f"\n✨ DONE! Deck saved: {output_path}")

if __name__ == "__main__":
    main()
