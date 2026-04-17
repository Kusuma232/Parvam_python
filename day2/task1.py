import re


def tokenize_sentence(sentence):
    return re.findall(r"\b\w+\b", sentence.lower())


sample_sentence = "Hello, world! Python is easy to learn."
tokens = tokenize_sentence(sample_sentence)
print(tokens)
