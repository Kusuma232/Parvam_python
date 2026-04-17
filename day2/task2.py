import re


def tokenize_words(sentence):
    return re.findall(r"\b\w+\b", sentence.lower())


sample_sentence = "Hello, world! Python is fun."
tokens = tokenize_words(sample_sentence)
print(tokens)
