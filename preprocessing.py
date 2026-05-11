import re
import string
import os


class TextPreprocessor:
    def __init__(self, resources_path="resources"):
        self.resources_path = resources_path
        self.stop_list = self.load_stopwords()
        self.suffix_list = self.load_suffixes()

    def clean_rtf_content(self, content):
        content = re.sub(r'\\[^ \n\t]+', ' ', content)
        content = re.sub(r'\{[^}]+\}', ' ', content)
        content = re.sub(r'[\{\}\\\*\t]', ' ', content)
        content = re.sub(r'\s+', ' ', content)
        return content.strip()

    def load_stopwords(self):
        stopwords = set()
        try:
            path = os.path.join(self.resources_path, "stopwords.txt")
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = self.clean_rtf_content(f.read())
            for word in content.split():
                word = word.strip().lower()
                if word and len(word) > 1 and word.isalpha():
                    stopwords.add(word)
        except:
            pass

        if len(stopwords) < 50:
            stopwords = {"a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
                         "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but",
                         "by", "could", "did", "do", "does", "doing", "down", "during", "each", "few", "for", "from",
                         "further", "had", "has", "have", "having", "he", "her", "here", "hers", "herself", "him",
                         "himself", "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself", "just", "me",
                         "more", "most", "my", "myself", "no", "nor", "not", "now", "of", "off", "on", "once", "only",
                         "or", "other", "our", "ours", "ourselves", "out", "over", "own", "same", "she", "should", "so",
                         "some", "such", "than", "that", "the", "their", "theirs", "them", "themselves", "then",
                         "there", "these", "they", "this", "those", "through", "to", "too", "under", "until", "up",
                         "very", "was", "we", "were", "what", "when", "where", "which", "while", "who", "whom", "why",
                         "with", "you", "your", "yours", "yourself", "yourselves"}
        return stopwords

    def load_suffixes(self):
        suffixes = [("ing", ""), ("ed", ""), ("s", ""), ("ly", ""), ("es", ""), ("ment", "")]
        return suffixes

    def clean_text(self, text):
        text = text.lower()
        text = text.translate(str.maketrans("", "", string.punctuation))
        text = re.sub(r'\d+', '', text)
        return text

    def tokenize(self, text):
        return text.split()

    def stem(self, word):
        for suffix, replacement in self.suffix_list:
            if word.endswith(suffix) and len(word) > len(suffix) + 2:
                return word[:-len(suffix)] + replacement
        return word

    def preprocess(self, text):
        cleaned = self.clean_text(text)
        tokens = self.tokenize(cleaned)
        processed = []
        for token in tokens:
            if token not in self.stop_list and len(token) > 2:
                stemmed = self.stem(token)
                if stemmed:
                    processed.append(stemmed)
        return processed


# ====================== PRUEBA ======================
if __name__ == "__main__":
    preprocessor = TextPreprocessor()
    test = "The waters are becoming increasingly polluted due to climate changes."
    print(preprocessor.preprocess(test))
