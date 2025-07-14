# mcp_servers/inbox_server.py
from pydantic import BaseModel
import pickle
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

class EmailCategory(BaseModel):
    category: str
    priority: str

def get_email_classifier():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(current_dir, "email_classifier.pkl")
    # --- END OF FIX ---

    if os.path.exists(model_path):
        with open(model_path, 'rb') as f:
            return pickle.load(f)
    
    # This block runs only on the very first startup to train and save the model
    print("--- Training and saving new email classifier model... ---")
    training_data = [
        ("Your invoice #1234 is due", "Important"),
        ("Let's schedule a meeting", "Important"),
        ("URGENT: Action Required", "Important"),
        ("Big summer sale!", "Promotions"),
        ("50% off everything", "Promotions"),
        ("Here's your weekly newsletter", "Promotions"),
        ("Re: Project discussion", "General"),
        ("Quick question about the report", "General"),
    ]
    texts, labels = zip(*training_data)
    pipeline = Pipeline([
        ('vectorizer', TfidfVectorizer()),
        ('classifier', MultinomialNB())
    ])
    pipeline.fit(list(texts), list(labels))
    
    with open(model_path, 'wb') as f:
        pickle.dump(pipeline, f)
    
    print("--- Email classifier model saved. ---")
    return pipeline

classifier = get_email_classifier()
priority_map = {"Important": "High", "General": "Medium", "Promotions": "Low"}

def categorize_email(subject: str, sender: str) -> EmailCategory:
    """Categorizes an email based on its subject and sender to determine its importance."""
    full_text = f"{subject} from {sender}"
    # The classifier expects an iterable, so we pass the text in a list
    predicted_category = classifier.predict([full_text])[0]
    return EmailCategory(category=predicted_category, priority=priority_map.get(predicted_category, "Medium"))