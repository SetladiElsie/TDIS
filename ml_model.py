"""Machine Learning models for improved extraction"""

import os
import pickle
import json
from datetime import datetime
from logger import get_logger
from validators import sanitize_text

logger = get_logger(__name__)

try:
    from sklearn.pipeline import Pipeline
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.svm import SVC
    from sklearn.ensemble import RandomForestClassifier
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False


class ExtractionMLModel:
    """Machine Learning model for tender extraction"""
    
    def __init__(self, model_dir='models'):
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)
        self.available = ML_AVAILABLE
        self.models = {}
        self._load_models()
    
    def _load_models(self):
        """Load trained models from disk"""
        if not self.available:
            logger.warning("Scikit-learn not available - ML extraction disabled")
            return
        
        # Try to load pre-trained models
        for filename in os.listdir(self.model_dir):
            if filename.endswith('.pkl'):
                try:
                    model_name = filename.replace('.pkl', '')
                    with open(os.path.join(self.model_dir, filename), 'rb') as f:
                        self.models[model_name] = pickle.load(f)
                    logger.info(f"Loaded model: {model_name}")
                except Exception as e:
                    logger.warning(f"Failed to load model {filename}: {str(e)}")
    
    def extract_field_ml(self, text, field_name):
        """Extract field using ML model"""
        if not self.available or field_name not in self.models:
            logger.debug(f"ML extraction not available for {field_name}")
            return None
        
        try:
            model = self.models[field_name]
            
            # Preprocess text
            cleaned_text = sanitize_text(text)
            
            # Predict
            result = model.predict([cleaned_text])
            confidence = max(model.predict_proba([cleaned_text])[0])
            
            return {
                'value': result[0],
                'confidence': float(confidence)
            }
        except Exception as e:
            logger.warning(f"ML extraction failed for {field_name}: {str(e)}")
            return None
    
    def batch_extract_ml(self, text, fields):
        """Extract multiple fields using ML models"""
        results = {}
        
        for field in fields:
            result = self.extract_field_ml(text, field)
            if result:
                results[field] = result
        
        return results
    
    def train_model(self, field_name, training_data):
        """Train a new model on labeled data"""
        if not self.available:
            logger.warning("Cannot train - Scikit-learn not available")
            return False
        
        try:
            texts, labels = zip(*training_data)
            
            # Create pipeline
            pipeline = Pipeline([
                ('tfidf', TfidfVectorizer(max_features=1000)),
                ('clf', RandomForestClassifier(n_estimators=100, random_state=42))
            ])
            
            # Train model
            pipeline.fit(texts, labels)
            
            # Save model
            model_path = os.path.join(self.model_dir, f'{field_name}.pkl')
            with open(model_path, 'wb') as f:
                pickle.dump(pipeline, f)
            
            self.models[field_name] = pipeline
            logger.info(f"Model trained and saved for {field_name}")
            
            return True
        except Exception as e:
            logger.error(f"Model training failed: {str(e)}")
            return False
    
    def evaluate_model(self, field_name, test_data):
        """Evaluate model performance"""
        if not self.available or field_name not in self.models:
            return None
        
        try:
            from sklearn.metrics import accuracy_score, precision_score, recall_score
            
            model = self.models[field_name]
            texts, labels = zip(*test_data)
            
            predictions = model.predict(texts)
            
            return {
                'accuracy': float(accuracy_score(labels, predictions)),
                'precision': float(precision_score(labels, predictions, average='weighted')),
                'recall': float(recall_score(labels, predictions, average='weighted'))
            }
        except Exception as e:
            logger.warning(f"Model evaluation failed: {str(e)}")
            return None
    
    def get_feature_importance(self, field_name):
        """Get feature importance for a model"""
        if not self.available or field_name not in self.models:
            return None
        
        try:
            model = self.models[field_name]
            
            # Get feature names
            if hasattr(model, 'named_steps'):
                vectorizer = model.named_steps.get('tfidf')
                if vectorizer:
                    feature_names = vectorizer.get_feature_names_out()
                    importance = model.named_steps['clf'].feature_importances_
                    
                    # Get top features
                    top_indices = sorted(range(len(importance)), key=lambda i: importance[i], reverse=True)[:20]
                    
                    return {
                        feature_names[i]: float(importance[i]) for i in top_indices
                    }
            
            return None
        except Exception as e:
            logger.warning(f"Failed to get feature importance: {str(e)}")
            return None


class ConfidenceScorer:
    """Score confidence of extracted fields"""
    
    @staticmethod
    def score_date(date_value, original_text):
        """Score date extraction confidence"""
        if not date_value:
            return 0.0
        
        # Check if date appears in text
        if str(date_value) in original_text:
            return 0.95
        
        # Check if components appear
        score = 0.5
        if str(date_value.year) in original_text:
            score += 0.15
        if str(date_value.month) in original_text:
            score += 0.15
        if str(date_value.day) in original_text:
            score += 0.15
        
        return min(score, 1.0)
    
    @staticmethod
    def score_number(value, original_text):
        """Score number extraction confidence"""
        if value is None:
            return 0.0
        
        # Check if number appears in text
        if str(value) in original_text:
            return 0.95
        
        return 0.6
    
    @staticmethod
    def score_text(value, original_text):
        """Score text extraction confidence"""
        if not value:
            return 0.0
        
        # Check if text is long enough
        if len(value) < 10:
            return 0.4
        
        # Check if text appears in original (approximately)
        if value[:20] in original_text:
            return 0.9
        
        return 0.7
    
    @staticmethod
    def score_list(items, original_text):
        """Score list extraction confidence"""
        if not items:
            return 0.0
        
        # Check how many items appear in original text
        found = sum(1 for item in items if str(item)[:20] in original_text)
        return found / len(items)
    
    @staticmethod
    def calculate_overall_confidence(scores):
        """Calculate overall confidence from field scores"""
        if not scores:
            return 0.0
        
        values = list(scores.values())
        if not values:
            return 0.0
        
        return sum(values) / len(values)


# Global ML model instance
ml_model = ExtractionMLModel()
confidence_scorer = ConfidenceScorer()
