from dataclasses import dataclass
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

@dataclass
class SupportResponse:
    answer: str

KNOWLEDGE_BASE = { "How do I reset my password?": "...", "What are the shipping times?": "...", "Can I get a refund?": "..." }
kb_questions, kb_answers = list(KNOWLEDGE_BASE.keys()), list(KNOWLEDGE_BASE.values())
vectorizer = TfidfVectorizer().fit(kb_questions)
kb_vectors = vectorizer.transform(kb_questions)

def get_support_answer(customer_query: str) -> SupportResponse:
    query_vector = vectorizer.transform([customer_query])
    scores = cosine_similarity(query_vector, kb_vectors)
    if scores.max() < 0.3:
        return SupportResponse(answer="I'm sorry, I couldn't find a specific answer...")
    return SupportResponse(answer=kb_answers[scores.argmax()])