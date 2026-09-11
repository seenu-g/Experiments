import re
from collections import Counter, defaultdict

my_raw_text = """
Cleaning Characters: Removing unwanted characters like hashtags, special symbols, or extra spaces.
 For example, "#unwanted_characters" might become "unwanted characters" after cleaning.

Converting to Lowercase: Transforming all text to lowercase helps ensure that words like "The" and
 "the" are treated as the same word, preventing the model from learning two separate representations 
 for what is essentially the same meaning.

Tokenization (Preliminary): While tokenization is a broad topic, the normalization step often involves
 an initial pass at tokenizing sentences or words. """

def create_tokenizer_dataset(text_input):
    # Clean text: make it lowercase and remove basic punctuation symbols
    cleaned = text_input.lower()
    cleaned = re.sub(r'[^\w\s]', '', cleaned)
    
    # Split text into separate words and compute raw statistical frequencies
    word_counts = Counter(cleaned.split())
    
    # Format words as tuples of individual base characters
    formatted_dataset = {}
    for word, count in word_counts.items():
        char_tuple = tuple(list(word))
        formatted_dataset[char_tuple] = count
        
    return formatted_dataset

# BPE statistical functions 
def get_stats(dataset):
    """Calculates pair frequencies across all tokens in the dataset"""
    pairs = defaultdict(int)
    for word_tuple, frequency in dataset.items():
        for i in range(len(word_tuple) - 1):
            pair = (word_tuple[i], word_tuple[i+1])
            pairs[pair] += frequency
    return pairs

def merge_vocab(pair, v_in):
    """Fuses the winning token pair together across the entire vocabulary"""
    v_out = {}
    for word_tuple in v_in:
        new_word = []
        i = 0
        while i < len(word_tuple):
            # If the current pair matches our winning merge target
            if i < len(word_tuple) - 1 and word_tuple[i] == pair[0] and word_tuple[i+1] == pair[1]:
                new_word.append(pair[0] + pair[1]) # Weld strings together
                i += 2
            else:
                new_word.append(word_tuple[i])
                i += 1
        v_out[tuple(new_word)] = v_in[word_tuple]
    return v_out

# Build the baseline dataset from your raw string input
dataset = create_tokenizer_dataset(my_raw_text)

print("=== STARTING RAW CHARACTER DICTIONARY ===")
for tokens, count in dataset.items():
    print(f"Count: {count} | Tokens: {tokens}")
print("\n=== STARTING STATISTICAL MERGING PROCESS ===\n")

# Run 5 rounds of statistical merging
num_rounds = 5
for round_num in range(1, num_rounds + 1):
    pairs = get_stats(dataset)
    if not pairs:
        print("No more character pairs left to merge!")
        break
        
    # Pick the pair that mathematically has the highest frequency count
    best_pair = max(pairs, key=pairs.get)
    highest_count = pairs[best_pair]
    
    # Execute the merge
    dataset = merge_vocab(best_pair, dataset)
    
    # Print progress updates so you can visually watch the chunks grow
    print(f"--- Round {round_num} ---")
    print(f"Winner: {best_pair} (Appeared {highest_count} times)")
    print("Current Dictionary State:")
    for tokens, count in dataset.items():
        # Represent chunks cleanly with brackets
        visual_tokens = " ".join([f"[{t}]" for t in tokens])
        print(f"    Count: {count} -> {visual_tokens}")
    print("-" * 50)
