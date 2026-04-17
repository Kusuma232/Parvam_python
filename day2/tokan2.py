import re
from nltk.tokenize import wordpunct_tokenize

text = "Python is very powerful. It is used in NLP."

# Word tokenization without external NLTK data
words = wordpunct_tokenize(text)
print("Words:", words)

# Simple sentence tokenization without external NLTK data
sentences = [sentence.strip() for sentence in re.findall(r"[^.!?]+[.!?]", text)]
print("Sentences:", sentences)
