"""
chatbot.py - Natural Language Processing & Intent Classification Engine
========================================================================
This module handles:
1. Text Preprocessing (lowercasing, punctuation stripping, tokenization)
2. TF-IDF (Term Frequency - Inverse Document Frequency) Vectorization
3. Cosine Similarity Matching against college intent patterns
4. Fallback Handling with a configurable confidence threshold
5. Database FAQ integration so newly added administrative FAQs are answered
"""

import json
import os
import re
import math
from collections import Counter

# Try importing scikit-learn; if not yet installed, fallback gracefully to a built-in TF-IDF engine
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class PurePythonTFIDF:
    """
    Lightweight, dependency-free TF-IDF and Cosine Similarity engine.
    Ensures the chatbot always functions even before scikit-learn is installed.
    """
    def __init__(self):
        self.vocabulary = {}
        self.idf = {}
        self.doc_vectors = []

    def fit_transform(self, documents):
        # 1. Build vocabulary and document frequencies
        doc_count = len(documents)
        df = Counter()
        tokenized_docs = [self._tokenize(doc) for doc in documents]

        for tokens in tokenized_docs:
            unique_tokens = set(tokens)
            for t in unique_tokens:
                df[t] += 1

        # Calculate smooth IDF: log((1 + N) / (1 + df)) + 1
        self.idf = {t: math.log((1 + doc_count) / (1 + df[t])) + 1.0 for t in df}
        self.vocabulary = {t: idx for idx, t in enumerate(self.idf.keys())}

        # 2. Compute TF-IDF vectors for documents
        self.doc_vectors = [self._compute_vector(tokens) for tokens in tokenized_docs]
        return self.doc_vectors

    def transform(self, documents):
        tokenized_docs = [self._tokenize(doc) for doc in documents]
        return [self._compute_vector(tokens) for tokens in tokenized_docs]

    def _tokenize(self, text):
        clean = re.sub(r'[^a-zA-Z0-9\s]', ' ', text.lower())
        tokens = clean.split()
        # Include unigrams and bigrams
        bigrams = [f"{tokens[i]} {tokens[i+1]}" for i in range(len(tokens) - 1)]
        return tokens + bigrams

    def _compute_vector(self, tokens):
        tf = Counter(tokens)
        vector = {}
        total_tokens = len(tokens) if len(tokens) > 0 else 1
        for token, count in tf.items():
            if token in self.idf:
                vector[token] = (count / total_tokens) * self.idf[token]
        # Normalize vector (L2 norm)
        norm = math.sqrt(sum(v * v for v in vector.values()))
        if norm > 0:
            for k in vector:
                vector[k] /= norm
        return vector

    @staticmethod
    def cosine_similarity(vec1, vec2):
        dot_product = sum(vec1[k] * vec2.get(k, 0.0) for k in vec1)
        return dot_product


class CollegeChatbot:
    """
    Core AI Chatbot engine for handling student college queries.
    Combines NLP feature extraction, intent matching, and SQLite FAQ lookup.
    """

    CONFIDENCE_THRESHOLD = 0.32  # Minimum similarity score required to accept an intent

    def __init__(self, intents_path=None):
        if intents_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            intents_path = os.path.join(base_dir, 'data', 'intents.json')

        self.intents_path = intents_path
        self.intents_data = []
        self.fallback_responses = []
        self.patterns = []
        self.pattern_tags = []
        self.tag_to_intent = {}

        # Vectorizer and matrix
        self.sklearn_vectorizer = None
        self.sklearn_matrix = None
        self.python_vectorizer = None

        self.load_intents()
        self.train_model()

    def clean_text(self, text):
        """Lowercase, remove punctuation, and normalize whitespace."""
        text = text.lower().strip()
        text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def load_intents(self):
        """Load intent patterns and responses from JSON."""
        if not os.path.exists(self.intents_path):
            raise FileNotFoundError(f"Intents file not found at: {self.intents_path}")

        with open(self.intents_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.intents_data = data.get('intents', [])
        self.fallback_responses = data.get('fallback_responses', [
            "I'm sorry, I could not understand your question. Please try rephrasing or ask about admissions, courses, fees, or contact details."
        ])

        self.patterns = []
        self.pattern_tags = []
        self.tag_to_intent = {}

        for intent in self.intents_data:
            tag = intent['tag']
            self.tag_to_intent[tag] = intent
            for pattern in intent.get('patterns', []):
                cleaned = self.clean_text(pattern)
                if cleaned:
                    self.patterns.append(cleaned)
                    self.pattern_tags.append(tag)

    def train_model(self):
        """
        Train the TF-IDF feature extraction model on the training patterns.
        Uses Scikit-Learn if available, otherwise uses the built-in pure Python engine.
        """
        if not self.patterns:
            return

        if SKLEARN_AVAILABLE:
            self.sklearn_vectorizer = TfidfVectorizer(
                ngram_range=(1, 2),
                stop_words='english',
                sublinear_tf=True
            )
            self.sklearn_matrix = self.sklearn_vectorizer.fit_transform(self.patterns)
        else:
            self.python_vectorizer = PurePythonTFIDF()
            self.python_vectorizer.fit_transform(self.patterns)

    def predict_intent(self, user_text):
        """
        Predict the most likely intent for a student query using Cosine Similarity.
        Returns: (intent_tag, confidence_score)
        """
        cleaned = self.clean_text(user_text)
        if not cleaned:
            return None, 0.0

        # Exact match fast-path for common single-word greetings and shortcuts
        for intent in self.intents_data:
            for pat in intent.get('patterns', []):
                if cleaned == self.clean_text(pat):
                    return intent['tag'], 1.0

        if SKLEARN_AVAILABLE and self.sklearn_vectorizer is not None:
            query_vec = self.sklearn_vectorizer.transform([cleaned])
            similarities = cosine_similarity(query_vec, self.sklearn_matrix).flatten()
            best_idx = similarities.argmax()
            best_score = float(similarities[best_idx])
            best_tag = self.pattern_tags[best_idx]
            return best_tag, best_score

        elif self.python_vectorizer is not None:
            query_vecs = self.python_vectorizer.transform([cleaned])
            if not query_vecs:
                return None, 0.0
            query_vec = query_vecs[0]

            best_score = 0.0
            best_tag = None
            for idx, doc_vec in enumerate(self.python_vectorizer.doc_vectors):
                score = PurePythonTFIDF.cosine_similarity(query_vec, doc_vec)
                if score > best_score:
                    best_score = score
                    best_tag = self.pattern_tags[idx]
            return best_tag, best_score

        return None, 0.0

    def search_database_faqs(self, user_text):
        """
        Search the SQLite database for a match if the administrator added new FAQs.
        """
        try:
            from database import search_faqs
            cleaned = self.clean_text(user_text)
            words = cleaned.split()
            # Try searching by multi-word keywords
            for word in words:
                if len(word) > 3:  # skip trivial stopwords
                    matches = search_faqs(word)
                    if matches:
                        first_match = matches[0]
                        return {
                            "response": first_match['answer'],
                            "category": first_match['category'],
                            "question": first_match['question']
                        }
        except Exception:
            pass
        return None

    def get_response(self, user_text):
        """
        Main query handling pipeline:
        1. Validates input
        2. Predicts intent and computes confidence score
        3. Falls back or retrieves response & suggested questions
        """
        if not user_text or not user_text.strip():
            return {
                "response": "Please type a question or select one of the suggested topics below.",
                "intent": "empty_input",
                "confidence": 0.0,
                "is_fallback": True,
                "suggestions": ["Admission Process", "Courses Offered", "Fee Structure", "Contact Details"]
            }

        intent_tag, confidence = self.predict_intent(user_text)

        # High/moderate confidence match from NLP intent engine
        if intent_tag and confidence >= self.CONFIDENCE_THRESHOLD:
            intent_info = self.tag_to_intent.get(intent_tag, {})
            responses = intent_info.get('responses', [])
            response_text = responses[0] if responses else "Information not available."
            suggestions = intent_info.get('suggestions', [
                "Admission Process", "Courses Offered", "Fee Structure"
            ])

            return {
                "response": response_text,
                "intent": intent_tag,
                "confidence": round(confidence, 3),
                "is_fallback": False,
                "suggestions": suggestions
            }

        # Check SQLite FAQs as second layer
        db_match = self.search_database_faqs(user_text)
        if db_match:
            return {
                "response": db_match['response'],
                "intent": "database_faq",
                "confidence": 0.65,
                "is_fallback": False,
                "suggestions": ["Admission Process", "Fee Structure", "Contact Details"]
            }

        # Fallback response when confidence is below threshold
        fallback_msg = self.fallback_responses[0]
        return {
            "response": fallback_msg,
            "intent": "fallback",
            "confidence": round(confidence, 3) if confidence else 0.0,
            "is_fallback": True,
            "suggestions": [
                "Admission Process",
                "Courses Offered",
                "Fee Structure",
                "Hostel Facilities",
                "Scholarships",
                "Contact Details"
            ]
        }


# Global singleton instance for the application
chatbot_engine = CollegeChatbot()

