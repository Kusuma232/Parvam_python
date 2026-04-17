import re
from collections import Counter


def analyze_text(text):
    words = re.findall(r"\b\w+\b", text.lower())
    sentences = [sentence.strip() for sentence in re.findall(r"[^.!?]+[.!?]?", text) if sentence.strip()]

    word_count = len(words)
    sentence_count = len(sentences)
    character_count = len(text)
    unique_words = len(set(words))
    most_common_words = Counter(words).most_common(5)

    return {
        "characters": character_count,
        "words": word_count,
        "sentences": sentence_count,
        "unique_words": unique_words,
        "most_common_words": most_common_words,
    }


def print_analysis(result):
    print("Text Analysis")
    print("Characters:", result["characters"])
    print("Words:", result["words"])
    print("Sentences:", result["sentences"])
    print("Unique Words:", result["unique_words"])
    print("Most Common Words:")

    for word, count in result["most_common_words"]:
        print(f"- {word}: {count}")


sample_text = input("Enter text to analyze: ").strip()

if not sample_text:
    sample_text = "Python is simple and powerful. Python is also easy to learn."

analysis = analyze_text(sample_text)
print_analysis(analysis)
