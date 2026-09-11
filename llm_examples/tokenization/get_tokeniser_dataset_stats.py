from collections import defaultdict

# 1. Our sample dataset with word counts
dataset = {
    ('T', 'h', 'e'): 2,
    ('c', 'a', 't'): 3,
    ('s', 'a', 't'): 1,
    ('a', 't', 'e'): 1,
    ('f', 'a', 't'): 1
}

def get_stats(dataset):
    """Counts how often adjacent pairs appear together"""
    pairs = defaultdict(int)
    for word, frequency in dataset.items():
        for i in range(len(word) - 1):
            pair = (word[i], word[i+1])
            pairs[pair] += frequency
    return pairs

def merge_vocab(pair, v_in):
    """Welds the winning pair together into a single token"""
    v_out = {}
    bigram = pair
    for word in v_in:
        new_word = []
        i = 0
        while i < len(word):
            if i < len(word) - 1 and word[i] == bigram[0] and word[i+1] == bigram[1]:
                new_word.append(bigram[0] + bigram[1])
                i += 2
            else:
                new_word.append(word[i])
                i += 1
        v_out[tuple(new_word)] = v_in[word]
    return v_out

# Run 2 rounds of statistical merging
for round_num in range(1, 3):
    pairs = get_stats(dataset)
    if not pairs:
        break
    # Find the pair with the highest statistical frequency
    best_pair = max(pairs, key=pairs.get)
    dataset = merge_vocab(best_pair, dataset)
    
    print(f"--- Round {round_num} ---")
    print(f"Highest frequency pair: {best_pair} (Appeared {pairs[best_pair]} times)")
    print(f"Updated Dataset state: {list(dataset.keys())}\n")
