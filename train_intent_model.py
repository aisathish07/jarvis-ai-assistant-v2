import json
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.pipeline import Pipeline

# Load training data
with open('skill_training_data.json', 'r') as f:
    data = json.load(f)

# Separate text and labels
texts = [item['text'] for item in data]
intents = [item['intent'] for item in data]

# Create a pipeline with a vectorizer and a classifier
text_clf = Pipeline([
    ('tfidf', TfidfVectorizer()),
    ('clf', SGDClassifier(loss='hinge', penalty='l2',
                          alpha=1e-3, random_state=42,
                          max_iter=100, tol=None)),
])

# Train the model
text_clf.fit(texts, intents)

# Save the trained model and vectorizer
with open('intent_model.pkl', 'wb') as f:
    pickle.dump(text_clf, f)

print("Intent recognition model trained and saved as intent_model.pkl")
