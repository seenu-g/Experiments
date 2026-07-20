#build docker image 
# docker build -t ai-agent .
#run docker image
# docker run -it ai-agent
from transformers import pipeline

# Load a small text generation model
generator = pipeline("text-generation", model="distilgpt2")

def run_agent():
    print("AI Agent is running. Type 'exit' to stop.\n")
    
    while True:
        user_input = input("You: ")
        
        if user_input.lower() == "exit":
            break
        
        response = generator(
            user_input,
            max_new_tokens=50,
            num_return_sequences=1,
            clean_up_tokenization_spaces=False,
        )
        print("Agent:", response[0]['generated_text'], "\n")

if __name__ == "__main__":
    run_agent()