import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
RAW_DATA_PATH = os.path.join(DATA_DIR, 'raw', 'lead_scoring_dataset.csv')
MODELS_DIR = os.path.join(BASE_DIR, 'models')

MODEL_PATH = os.path.join(MODELS_DIR, 'lead_classifier.pkl')
VECTORIZER_PATH = os.path.join(MODELS_DIR, 'tfidf_vectorizer.pkl')

# Hybrid Model Configurations & Paths
HYBRID_MODEL_PATH = os.path.join(MODELS_DIR, 'hybrid_lead_model.pt')
PREPROCESSOR_PATH = os.path.join(MODELS_DIR, 'tabular_preprocessor.joblib')
DISTILBERT_MODEL_DIR = os.path.join(MODELS_DIR, 'distilbert_lead_classifier')

MODEL_NAME = 'distilbert-base-uncased'
BATCH_SIZE = 16
EPOCHS = 4
LEARNING_RATE = 2e-5
MAX_LEN = 128
PATIENCE = 2
VAL_SIZE = 0.2
WEIGHT_DECAY = 0.01
TABULAR_DIM = 64

# MLFlow settings
MLFLOW_TRACKING_URI = "sqlite:///mlruns.db"
EXPERIMENT_NAME = "Lead_Qualification_Experiment"
