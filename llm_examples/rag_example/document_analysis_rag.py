import os

from dotenv import load_dotenv
load_dotenv()

import pdfplumber
import torch
import nltk
from nltk.tokenize import sent_tokenize
from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
    AutoModelForQuestionAnswering,
)

PDF_PATH = "documents/srini.pdf"
OUTPUT_TEXT_FILE = "extracted_text.txt"
MODEL_CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")


def extract_pdf_text(pdf_path, output_text_file):
    """Extract text from every page of the PDF and save it to a text file."""
    with pdfplumber.open(pdf_path) as pdf:
        extracted_text = ""
        for page in pdf.pages:
            extracted_text += page.extract_text() or ""

    with open(output_text_file, "w", encoding="utf-8") as text_file:
        text_file.write(extracted_text)

    print(f"Text extracted and saved to {output_text_file}")
    return extracted_text


def summarize_text(text, max_length=150, min_length=30):
    """Summarize text with a small local seq2seq model (t5-small)."""
    tokenizer = AutoTokenizer.from_pretrained("t5-small", cache_dir=MODEL_CACHE_DIR)
    model = AutoModelForSeq2SeqLM.from_pretrained("t5-small", cache_dir=MODEL_CACHE_DIR)

    input_ids = tokenizer("summarize: " + text, return_tensors="pt", truncation=True).input_ids
    output_ids = model.generate(input_ids, max_length=max_length, min_length=min_length, do_sample=False)
    return tokenizer.decode(output_ids[0], skip_special_tokens=True)


def split_into_passages(document_text, word_limit=200):
    """Split text into sentences, then combine sentences into ~word_limit-word passages."""
    nltk.download('punkt', quiet=True)
    nltk.download('punkt_tab', quiet=True)
    sentences = sent_tokenize(document_text)

    passages = []
    current_passage = ""
    for sentence in sentences:
        if len(current_passage.split()) + len(sentence.split()) < word_limit:
            current_passage += " " + sentence
        else:
            passages.append(current_passage.strip())
            current_passage = sentence
    if current_passage:
        passages.append(current_passage.strip())

    return passages


class QuestionGenerator:
    """Generates questions from a passage with a local seq2seq model (t5-base-qg-hl)."""

    def __init__(self, model_name="valhalla/t5-base-qg-hl"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=MODEL_CACHE_DIR)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name, cache_dir=MODEL_CACHE_DIR)

    def _generate(self, prompt, max_length=128):
        input_ids = self.tokenizer(prompt, return_tensors="pt", truncation=True).input_ids
        output_ids = self.model.generate(input_ids, max_length=max_length)
        return self.tokenizer.decode(output_ids[0], skip_special_tokens=True)

    def generate_questions(self, passage, min_questions=3):
        generated_text = self._generate(f"generate questions: {passage}")
        questions = [q.strip() for q in generated_text.split('<sep>') if q.strip()]

        # if fewer than min_questions, try to regenerate from smaller parts of the passage
        if len(questions) < min_questions:
            passage_sentences = passage.split('. ')
            for i in range(len(passage_sentences)):
                if len(questions) >= min_questions:
                    break
                additional_input = ' '.join(passage_sentences[i:i + 2])
                additional_text = self._generate(f"generate questions: {additional_input}")
                questions.extend(q.strip() for q in additional_text.split('<sep>') if q.strip())

        return questions[:min_questions]


class QuestionAnswerer:
    """Answers a question given a context with a local extractive QA model."""

    def __init__(self, model_name="deepset/roberta-base-squad2"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=MODEL_CACHE_DIR)
        self.model = AutoModelForQuestionAnswering.from_pretrained(model_name, cache_dir=MODEL_CACHE_DIR)

    def answer(self, question, context):
        inputs = self.tokenizer(question, context, return_tensors="pt", truncation=True)
        with torch.no_grad():
            outputs = self.model(**inputs)

        start = torch.argmax(outputs.start_logits)
        end = torch.argmax(outputs.end_logits) + 1
        return self.tokenizer.decode(inputs["input_ids"][0][start:end], skip_special_tokens=True)


def generate_questions_for_passages(passages, question_generator):
    """Generate questions for every passage once, so callers don't regenerate them."""
    return {passage: question_generator.generate_questions(passage) for passage in passages}


def print_passage_questions(passage_questions):
    for idx, (passage, questions) in enumerate(passage_questions.items()):
        print(f"Passage {idx+1}:\n{passage}\n")
        print("Generated Questions:")
        for q in questions:
            print(f"- {q}")
        print(f"\n{'-'*50}\n")


def answer_unique_questions(passage_questions, question_answerer):
    """Answer every unique question, paired with the passage it was generated from."""
    answered_questions = set()

    for passage, questions in passage_questions.items():
        for question in questions:
            if question not in answered_questions:
                answer = question_answerer.answer(question, passage)
                print(f"Q: {question}")
                print(f"A: {answer}\n")
                answered_questions.add(question)
        print(f"{'='*50}\n")


def main():
    extracted_text = extract_pdf_text(PDF_PATH, OUTPUT_TEXT_FILE)

    with open(OUTPUT_TEXT_FILE, "r", encoding="utf-8") as file:
        document_text = file.read()

    print(document_text[:500])  # preview the first 500 characters

    summary = summarize_text(document_text[:1000])
    print("Summary:", summary)

    passages = split_into_passages(document_text)

    question_generator = QuestionGenerator()
    passage_questions = generate_questions_for_passages(passages, question_generator)
    print_passage_questions(passage_questions)

    question_answerer = QuestionAnswerer()
    answer_unique_questions(passage_questions, question_answerer)


if __name__ == "__main__":
    main()
