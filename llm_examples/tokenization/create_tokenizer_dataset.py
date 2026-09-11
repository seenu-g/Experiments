from collections import Counter
import re

my_raw_text = """
•	Week 1 Notice - When does the pattern appear? What triggers it?
•	Week 2 Trace - Which sequential does this belong to? What was its original adaptive function?
•	Week 3 Name: Bring it in to language with someone who can hold the complexity. Not to fix it but to see it
•	Week 4 Observe the system - What changes when you do not automatically enact the pattern? What becomes possible in the team?
"""

def create_tokenizer_dataset(text_input):
    # 1. Clean the text (lowercase and remove punctuation to keep it simple)
    cleaned_text = text_input.lower()
    cleaned_text = re.sub(r'[^\w\s]', '', cleaned_text)
    
    # 2. Split the text into individual words
    words = cleaned_text.split()
    
    # 3. Count how many times each word appears (statistical frequency)
    word_counts = Counter(words)
    
    # 4. Format into a dictionary where characters are separated by spaces
    formatted_dataset = {}
    for word, count in word_counts.items():
        # Turn "cat" into ('c', 'a', 't')
        char_tuple = tuple(list(word))
        formatted_dataset[char_tuple] = count
        
    return formatted_dataset


custom_dataset = create_tokenizer_dataset(my_raw_text)
print("Your Custom Dataset for the Simulation:")
import pprint
pprint.pprint(custom_dataset)
