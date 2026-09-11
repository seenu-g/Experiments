import sys
from tokenizers import Tokenizer
from tokenizers.models import BPE
from tokenizers.trainers import BpeTrainer
from tokenizers.pre_tokenizers import Whitespace
from tokenizers.normalizers import NFKC, Sequence

# Windows consoles default to cp1252, which can't print Devanagari/Tamil text
sys.stdout.reconfigure(encoding="utf-8")

# Per-language settings: corpus file to train on, where to save the
# resulting tokenizer, and a sample sentence to test it with afterwards.
LANGUAGES = {
    "hindi": {
        "corpus_file": "hindi_corpus.txt",
        "output_file": "hindi-custom-tokenizer.json",
        "test_sentence": "नमस्ते दुनिया, आप कैसे हैं?",
    },
    "tamil": {
        "corpus_file": "tamil_corpus.txt",
        "output_file": "tamil-custom-tokenizer.json",
        "test_sentence": "வணக்கம் உலகம், நீங்கள் எப்படி இருக்கிறீர்கள்?",
    },
}


def choose_language() -> str:
    """Prompts the user to pick a language from LANGUAGES, retrying on bad input."""
    options = "/".join(LANGUAGES)
    while True:
        choice = input(f"Select language ({options}): ").strip().lower()
        if choice in LANGUAGES:
            return choice
        print(f"Unknown language '{choice}'. Please choose one of: {options}")


def train_tokenizer(corpus_file: str) -> Tokenizer:
    # 1. Initialize a blank BPE Tokenizer
    tokenizer = Tokenizer(BPE(unk_token="[UNK]"))

    # 2. Setup Normalization (crucial for consistent Indic script handling)
    tokenizer.normalizer = Sequence([NFKC()])

    # 3. Setup Pre-tokenization (splitting roughly on spaces/punctuation)
    tokenizer.pre_tokenizer = Whitespace()

    # 4. Configure the Trainer
    # We set a smaller vocab size for this example, but production models use 32k-100k
    trainer = BpeTrainer(
        vocab_size=10000,
        special_tokens=["[UNK]", "[CLS]", "[SEP]", "[PAD]", "[MASK]"],
    )

    # 5. Train the tokenizer on the selected corpus file
    tokenizer.train([corpus_file], trainer)
    return tokenizer


if __name__ == "__main__":
    language = choose_language()
    settings = LANGUAGES[language]

    tokenizer = train_tokenizer(settings["corpus_file"])

    # 6. Save the trained tokenizer
    tokenizer.save(settings["output_file"])
    print(f"Saved trained tokenizer to '{settings['output_file']}'")

    # 7. Test it!
    output = tokenizer.encode(settings["test_sentence"])
    print("Tokens:", output.tokens)
    print("IDs:", output.ids)
