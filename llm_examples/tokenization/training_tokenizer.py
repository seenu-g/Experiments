import re
from collections import defaultdict


def train_bpe(corpus: list[str], vocab_size: int) -> dict[tuple[str, str], str]:
    """Trains a BPE tokenizer on a text corpus until the target vocab_size is reached.

    Returns a dictionary of learned merges mapping (char1, char2) -> merged_token.
    """
    # 1. Initialize the vocabulary with words split into characters + a special end-of-word token (</w>)
    #    Example: "hug" -> ["h", "u", "g", "</w>"]
    splits = [list(word) + ["</w>"] for word in corpus]

    # Calculate how many merges we need to perform
    # Initial unique tokens count
    unique_tokens = set(token for word in splits for token in word)
    num_merges = vocab_size - len(unique_tokens)

    if num_merges <= 0:
        print("Target vocabulary size is already smaller than the base characters.")
        return {}

    merges = {}

    # 2. Iteratively find and merge the most frequent adjacent pairs
    for i in range(num_merges):
        # Count frequencies of all adjacent pairs
        pair_counts = defaultdict(int)
        for word in splits:
            for i in range(len(word) - 1):
                pair_counts[(word[i], word[i + 1])] += 1

        if not pair_counts:
            break  # No more pairs left to merge

        # Find the most frequent pair
        best_pair = max(pair_counts, key=pair_counts.get)
        new_token = "".join(best_pair)
        merges[best_pair] = new_token

        # Perform the merge across the entire corpus split tracking
        new_splits = []
        for word in splits:
            new_word = []
            i = 0
            while i < len(word):
                # Check if current and next token match the best pair
                if i < len(word) - 1 and (word[i], word[i + 1]) == best_pair:
                    new_word.append(new_token)
                    i += 2
                else:
                    new_word.append(word[i])
                    i += 1
            new_splits.append(new_word)

        splits = new_splits

    return merges


def tokenize_bpe(text: str, merges: dict[tuple[str, str], str]) -> list[str]:
    """Tokenizes a new string using the pre-trained merges dictionary."""
    # Pre-process text by splitting into words
    words = text.split()
    final_tokens = []

    for word in words:
        # Initialize word as a list of characters + end of word symbol
        word_split = list(word) + ["</w>"]

        # Repeatedly apply the learned merges in the order they were trained
        for pair, merged_token in merges.items():
            i = 0
            new_split = []
            while i < len(word_split):
                if (
                    i < len(word_split) - 1
                    and (word_split[i], word_split[i + 1]) == pair
                ):
                    new_split.append(merged_token)
                    i += 2
                else:
                    new_split.append(word_split[i])
                    i += 1
            word_split = new_split

        final_tokens.extend(word_split)

    return final_tokens


if __name__ == "__main__":
    # Toy corpus simulating repetitive text patterns
    training_corpus = [
        "hug",
        "hug",
        "hug",
        "pug",
        "pug",
        "pun",
        "bun",
        "slangs",
    ]

    print("--- 1. Training BPE ---")
    # Target vocabulary size of 15 (Base characters + unique merges)
    learned_merges = train_bpe(training_corpus, vocab_size=15)

    print("\nLearned Merges (in order of priority):")
    for pair, result in learned_merges.items():
        print(f"  {pair} -> '{result}'")

    print("\n--- 2. Tokenizing New Text ---")
    test_sentence = "hug a pug dog"
    tokens = tokenize_bpe(test_sentence, learned_merges)

    print(f"Input sentence: '{test_sentence}'")
    print(f"BPE Subword Tokens: {tokens}")
