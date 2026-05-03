import re
import string

class TextPreprocessor:
    def __init__(self, stopwords=None, suffixes=None):
        # Default stop list
        self.stop_list = stopwords or {
            "a", "an", "the", "and", "or", "but", "is", "are", "was", "were", 
            "to", "of", "in", "on", "at", "by", "for", "with", "about", "against", 
            "between", "into", "through", "during", "before", "after", "above", 
            "below", "from", "up", "down", "out", "off", "over", "under", "again", 
            "further", "then", "once", "here", "there", "when", "where", "why", 
            "how", "all", "any", "both", "each", "few", "more", "most", "other", 
            "some", "such", "no", "nor", "not", "only", "own", "same", "so", 
            "than", "too", "very", "s", "t", "can", "will", "just", "don", 
            "should", "now", "i", "me", "my", "myself", "we", "our", "ours", 
            "ourselves", "you", "your", "yours", "yourself", "yourselves", "he", 
            "him", "his", "himself", "she", "her", "hers", "herself", "it", "its", 
            "itself", "they", "them", "their", "theirs", "themselves", "what", 
            "which", "who", "whom", "this", "that", "these", "those", "am"
        }
        
        # Default suffix list for a simple stemmer
        # (Simplified Porter Stemmer-like rules)
        self.suffix_list = suffixes or [
            ("ies", "y"),
            ("ing", ""),
            ("ed", ""),
            ("s", ""),
            ("ly", ""),
            ("ment", ""),
            ("ness", ""),
            ("able", ""),
            ("ible", ""),
            ("tion", "t"),
            ("sion", "s"),
            ("al", ""),
            ("ive", ""),
            ("ize", ""),
        ]

    def clean_text(self, text):
        """Lowercase, remove punctuation and numbers."""
        text = text.lower()
        # Remove punctuation
        text = text.translate(str.maketrans("", "", string.punctuation))
        # Remove numbers
        text = re.sub(r'\d+', '', text)
        return text

    def tokenize(self, text):
        """Split text into words."""
        return text.split()

    def stem(self, word):
        """Apply suffix removal to get the word stem."""
        for suffix, replacement in self.suffix_list:
            if word.endswith(suffix) and len(word) > len(suffix) + 2:
                return word[:-len(suffix)] + replacement
        return word

    def preprocess(self, text):
        """Full pipeline: clean, tokenize, remove stopwords, stem."""
        cleaned = self.clean_text(text)
        tokens = self.tokenize(cleaned)
        
        # Remove stopwords and stem
        processed_tokens = []
        for token in tokens:
            if token not in self.stop_list:
                stemmed = self.stem(token)
                if stemmed:
                    processed_tokens.append(stemmed)
        
        return processed_tokens

# Test the preprocessor
if __name__ == "__main__":
    preprocessor = TextPreprocessor()
    test_text = "Renewable energy sources like solar and wind are increasingly efficient and sustainable."
    print(f"Original: {test_text}")
    print(f"Processed: {preprocessor.preprocess(test_text)}")
