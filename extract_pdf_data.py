import os
import json
import string
from math import log2
import fitz
import spacy
import numpy as np
from wordfreq import word_frequency
from collections import Counter
from utils import delete_if_exists

nlp = spacy.load("en_core_web_sm") #python -m spacy download en_core_web_sm

def extract_geometric_features(pdf_path, output_json="output.json"):
    delete_if_exists(output_json)
    doc = fitz.open(pdf_path)
    all_pages_data = []

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        blocks = page.get_text("blocks")
        all_relative_font_sizes = calculate_all_relative_font_sizes(page)

        page_data = []
        for idx, block in enumerate(blocks):
            if len(block) < 6:
                print(f"Warning: Block at index {idx} on page {page_num + 1} is incomplete")
                continue

            x0, y0, x1, y1, text, block_id = block[:6]
            if text.strip():
                page_data.append({
                    "x0": x0, "y0": y0, "x1": x1, "y1": y1,
                    "height": calculate_height(y0, y1),
                    "width": calculate_width(x0, x1),
                    "position": calculate_position(y0, page.rect.height),
                    "letter_count": calculate_letter_count(text),
                    "font_size": calculate_average_font_size(page, idx),
                    "relative_font_size": all_relative_font_sizes[idx],
                    "num_lines": calculate_num_lines(page, idx),
                    "punctuation_proportion": calculate_punctuation_proportion(text),
                    "average_words_per_sentence": calculate_average_words_per_sentence(text),
                    "starts_with_number": calculate_starts_with_number(text),
                    "capitalization_proportion": calculate_capitalization_proportion(text),
                    "average_word_commonality": get_word_commonality(text),
                    "squared_entropy": calculate_entropy(text) ** 2,
                    "page": page_num,
                    "text": text.strip(),
                    "type": '0'
                })

        processed_page_data = process_drop_cap(page_data)
        all_pages_data.append({"page": page_num, "blocks": processed_page_data})

    save_to_json(all_pages_data, output_json)

def save_to_json(data, output_file):
    """ Save extracted text block data to a JSON file. """
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# Utility functions
def calculate_height(y0, y1): return y1 - y0
def calculate_width(x0, x1): return x1 - x0
def calculate_position(y0, page_height): return y0 / page_height
def calculate_letter_count(text): return sum(c.isalpha() for c in text)

def calculate_punctuation_proportion(text):
    total_characters = len(text)
    punctuation_count = sum(1 for c in text if c in string.punctuation)
    return punctuation_count / total_characters if total_characters > 0 else 0

def calculate_average_font_size(page, block_index):
    blocks_dict = page.get_text("dict").get("blocks", [])
    if block_index < 0 or block_index >= len(blocks_dict):
        return 0
    block = blocks_dict[block_index]
    font_sizes = [span["size"] for line in block.get("lines", []) for span in line.get("spans", []) if "size" in span]
    return sum(font_sizes) / len(font_sizes) if font_sizes else None

def calculate_all_relative_font_sizes(page):
    blocks_dict = page.get_text("dict").get("blocks", [])
    all_font_sizes = [calculate_average_font_size(page, idx) for idx in range(len(blocks_dict))]
    all_font_sizes = [size for size in all_font_sizes if size is not None]
    max_font_size = max(all_font_sizes) if all_font_sizes else 1
    return [font_size / max_font_size for font_size in all_font_sizes]

def calculate_num_lines(page, block_index):
    blocks_dict = page.get_text("dict").get("blocks", [])
    if block_index < 0 or block_index >= len(blocks_dict):
        return 0
    return len(blocks_dict[block_index].get("lines", []))

def calculate_average_words_per_sentence(text):
    sentences = text.split('.')
    sentence_lengths = [len(sentence.split()) for sentence in sentences if sentence]
    return sum(sentence_lengths) / len(sentence_lengths) if sentence_lengths else 0

def calculate_starts_with_number(text):
    return 1 if text.strip() and text.strip()[0].isdigit() else 0

def calculate_capitalization_proportion(text):
    letter_count = sum(1 for c in text if c.isalpha())
    capitalized_count = sum(1 for c in text if c.isupper())
    return capitalized_count / letter_count if letter_count > 0 else 0

def get_word_commonality(text, scale_factor=100):
    words = [word.strip(string.punctuation).lower() for word in text.split() if word.isalpha()]
    if not words:
        return 0.01
    word_frequencies = [word_frequency(word, 'en') for word in words if word_frequency(word, 'en') > 0]
    return (sum(word_frequencies) / len(word_frequencies) * scale_factor) if word_frequencies else 0.01

def calculate_entropy(text):
    if not text:
        return 0
    probabilities = [text.count(c) / len(text) for c in set(text)]
    return -sum(p * log2(p) for p in probabilities if p > 0)

def process_drop_cap(page_data):
    font_sizes = [block['font_size'] for block in page_data if 'font_size' in block]
    if not font_sizes:
        return page_data
    font_size_counts = Counter(font_sizes)
    common_font_size, _ = font_size_counts.most_common(1)[0]
    avg_font_size = np.mean(font_sizes)
    font_size_std = np.std(font_sizes)
    threshold = avg_font_size + 2 * font_size_std
    drop_cap_indices = [i for i, block in enumerate(page_data) if block.get('font_size', 0) > threshold and block.get('letter_count', 0) < 10]
    for i in drop_cap_indices:
        if i + 1 < len(page_data):
            page_data[i]['font_size'] = page_data[i + 1].get('font_size', common_font_size)
    max_font_size = max(font_sizes) if font_sizes else 1
    for block in page_data:
        if 'font_size' in block:
            block['relative_font_size'] = block['font_size'] / max_font_size
    return page_data

if __name__ == "__main__":
    extract_geometric_features("input.pdf", "output.json")

