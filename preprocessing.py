import re
import string
import os
import nltk
from nltk.stem.snowball import SnowballStemmer

nltk.download('punkt', quiet=True)

class TextPreprocessor:
    def __init__(self, resources_path="resources"):
        self.resources_path = resources_path
        self.stop_list = self.load_stopwords()
        self.stemmer = SnowballStemmer("english")
        print(f"✅ Stopwords: {len(self.stop_list)} | Usando SnowballStemmer")

    def load_stopwords(self):
        stopwords = set()
        try:
            path = os.path.join(self.resources_path, "stopwords.txt")
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                content = re.sub(r'\\[^ ]+', '', content)
                content = re.sub(r'\{.*?\}', '', content, flags=re.DOTALL)
                for word in content.split():
                    w = word.strip().lower()
                    if w and len(w) > 1 and w.isalpha():
                        stopwords.add(w)
        except:
            pass

        # Stopwords muy fuertes
        extra = {"isn't","don't","doesn't","didn't","can't","couldn't","about","above","after","again","against","all","am","an","and","any","are","as","at","be","because","been","before","being","below","between","both","but","by","can","could","did","do","does","doing","down","during","each","few","for","from","further","had","has","have","having","he","her","here","hers","herself","him","himself","his","how","i","if","in","into","is","it","its","itself","just","me","more","most","my","myself","no","nor","not","now","of","off","on","once","only","or","other","our","ours","ourselves","out","over","own","same","she","should","so","some","such","than","that","the","their","theirs","them","themselves","then","there","these","they","this","those","through","to","too","under","until","up","very","was","we","were","what","when","where","which","while","who","whom","why","with","you","your","yours","yourself","yourselves"}
        stopwords.update(extra)
        return stopwords

    def preprocess(self, text):
        text = text.lower()
        text = text.translate(str.maketrans("", "", string.punctuation))
        text = re.sub(r'\d+', '', text)
        tokens = text.split()

        processed = []
        for token in tokens:
            if token not in self.stop_list and len(token) > 2:
                stemmed = self.stemmer.stem(token)
                if len(stemmed) > 2:
                    processed.append(stemmed)
        return processed


if __name__ == "__main__":
    p = TextPreprocessor()
    print(p.preprocess("The waters are becoming increasingly polluted due to climate changes and higher abundance of biggest businesses. isn't good"))
