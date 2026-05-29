import os
import torch  # type: ignore
import pandas as pd  # type: ignore
import numpy as np  # type: ignore
from fastapi import FastAPI, HTTPException, status  # type: ignore
from pydantic import BaseModel, Field  # type: ignore
import logging
from transformers import DistilBertTokenizer  # type: ignore
import config
from data_processor import DataProcessor
from model_trainer import HybridLeadClassifier

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Lead Qualification Bot API",
    version="2.0.0",
    description="Advanced CRM Sales Intelligence API powered by DistilBERT and multi-task PyTorch embeddings."
)

# --------------------------------------------------
# PYDANTIC RESPONSE & REQUEST SCHEMAS
# --------------------------------------------------

class PredictionRequest(BaseModel):
    customer_response: str = Field(..., description="The raw customer text inquiry")

class AnalyzeRequest(BaseModel):
    customer_response: str = Field(..., description="The raw customer text inquiry")
    total_visits: float = Field(0.0, description="Total website visits")
    time_on_website: float = Field(0.0, description="Total time spent on website in seconds")
    page_views: float = Field(0.0, description="Page views per visit")
    source: str = Field("Unknown", description="Lead acquisition source channel")
    last_activity: str = Field("Unknown", description="Last activity recorded in CRM")
    occupation: str = Field("Unknown", description="Customer occupation status")

class PredictionResponse(BaseModel):
    prediction: str = Field(..., description="Qualified lead level (Hot Lead / Warm Lead / Cold Lead)")
    confidence: str = Field(..., description="Model classification confidence percentage")
    intent: str = Field(..., description="Detected customer intent (e.g. Enterprise Purchase)")
    urgency: str = Field(..., description="Urgency scale level (High / Medium / Low)")
    reason: list[str] = Field(..., description="Explainable AI reasoning points")

# --------------------------------------------------
# MODEL SERVICE & LOADER PIPELINE
# --------------------------------------------------

model = None
processor = None
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

@app.on_event("startup")
def load_model_service():
    global model, processor
    try:
        logger.info("Initializing Data Processor and Preprocessor resources...")
        processor = DataProcessor()
        
        # Load scaler and encoder if trained preprocessor exists
        if os.path.exists(config.PREPROCESSOR_PATH):
            processor.load_preprocessor()
        else:
            logger.warning(f"Tabular preprocessors not found at {config.PREPROCESSOR_PATH}. Inference might run with default scaling.")
            
        logger.info("Loading PyTorch Hybrid Multi-Task Model...")
        if os.path.exists(config.HYBRID_MODEL_PATH):
            checkpoint = torch.load(config.HYBRID_MODEL_PATH, map_location=device)
            tabular_dim = checkpoint['tabular_dim']
            
            # Reconstruct model skeleton and load state dictionary
            model = HybridLeadClassifier(
                num_classes=3, num_intents=4, num_urgencies=3, tabular_dim=tabular_dim
            )
            model.load_state_dict(checkpoint['model_state_dict'])
            model.to(device)
            model.eval()
            logger.info("Hybrid Multi-Task Model successfully initialized and loaded on device.")
        else:
            logger.error(f"Hybrid model checkpoint not found at {config.HYBRID_MODEL_PATH}. Run training first.")
            model = None
    except Exception as e:
        logger.critical(f"Critical error loading model service: {e}")
        model = None

# Helper method to run model prediction
def predict_hybrid(text, total_visits, time_on_website, page_views, source, last_activity, occupation):
    if model is None or processor is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail="Model weights or tokenizers are not loaded. Please train the model first."
        )

    # 1. Preprocess raw text input
    cleaned_text = processor.clean_text(text)
    inputs = processor.tokenizer(
        cleaned_text,
        truncation=True,
        padding=True,
        max_length=config.MAX_LEN,
        return_tensors="pt"
    )
    
    # 2. Build pandas DataFrame row for tabular scaling & one-hot encoding
    tab_data = {
        'TotalVisits': [total_visits],
        'Total_Time_Spent_on_Website': [time_on_website],
        'Page_Views_Per_Visit': [page_views],
        'Lead_Source': [source],
        'Last_Activity': [last_activity],
        'Occupation': [occupation]
    }
    df_tab = pd.DataFrame(tab_data)
    tab_feats = processor.transform_tabular(df_tab)
    
    # Convert inputs to PyTorch tensors and move to device
    input_ids = inputs['input_ids'].to(device)
    attention_mask = inputs['attention_mask'].to(device)
    tab_tensor = torch.tensor(tab_feats, dtype=torch.float32).to(device)
    
    # 3. Model Forward Pass
    with torch.no_grad():
        class_logits, intent_logits, urgency_logits = model(input_ids, attention_mask, tab_tensor)
        
        # Softmax probabilities
        class_probs = torch.softmax(class_logits, dim=1)[0]
        intent_probs = torch.softmax(intent_logits, dim=1)[0]
        urgency_probs = torch.softmax(urgency_logits, dim=1)[0]
        
        pred_class_idx = torch.argmax(class_probs).item()
        pred_intent_idx = torch.argmax(intent_probs).item()
        pred_urgency_idx = torch.argmax(urgency_probs).item()

    prediction_label = processor.inverse_class_map[pred_class_idx]
    confidence_val = class_probs[pred_class_idx].item()
    intent_label = processor.inverse_intent_map[pred_intent_idx]
    urgency_label = processor.inverse_urgency_map[pred_urgency_idx]

    # 4. Generate Explainable AI (XAI) Reasons
    reasons = []
    
    # Text intent indicators
    if intent_label == "Enterprise Purchase":
        reasons.append("pricing or high-scale enterprise deployment request detected")
    elif intent_label == "Product Inquiry":
        reasons.append("specific product inquiry or information request identified")
    elif intent_label == "Technical Support":
        reasons.append("technical specifications or setup support requested")
    elif intent_label == "Just Browsing":
        reasons.append("browsing intent or low buying indicators observed")
        
    # Urgency indicators
    if urgency_label == "High":
        reasons.append("urgent timeline or immediate contact request identified")
    elif urgency_label == "Medium":
        reasons.append("medium-term deployment target (e.g. next quarter)")
        
    # Tabular metric-based reasons
    if time_on_website > 1000:
        reasons.append(f"significant site interaction history logged ({time_on_website:.0f} seconds spent on website)")
    if total_visits > 5:
        reasons.append(f"frequent research activity recorded ({total_visits:.0f} website visits)")
    if occupation == "Working Professional":
        reasons.append("working professional occupation correlates with high conversion potential")
        
    # Overall summary reason
    if prediction_label == "Hot Lead":
        reasons.append("strong combined buying signals match high-intent classification criteria")
    elif prediction_label == "Cold Lead" and len(reasons) == 0:
        reasons.append("inactive engagement score matches cold browsing indicators")
        
    if len(reasons) == 0:
        reasons.append("default system classification criteria applied")

    return PredictionResponse(
        prediction=prediction_label,
        confidence=f"{confidence_val * 100:.1f}%",
        intent=intent_label,
        urgency=urgency_label,
        reason=reasons
    )

# --------------------------------------------------
# FASTAPI ENDPOINTS
# --------------------------------------------------

@app.get("/health")
async def health_check():
    """Health check endpoint for system monitoring."""
    if model is None or processor is None:
        return {
            "status": "unhealthy",
            "model_loaded": model is not None,
            "processor_loaded": processor is not None
        }
    return {
        "status": "healthy",
        "device": str(device),
        "model_loaded": True
    }

@app.post("/predict", response_model=PredictionResponse)
async def predict_basic(request: PredictionRequest):
    """Legacy/simple endpoint running text-only prediction with default tabular parameters."""
    return predict_hybrid(
        text=request.customer_response,
        total_visits=0.0,
        time_on_website=0.0,
        page_views=0.0,
        source="Unknown",
        last_activity="Unknown",
        occupation="Unknown"
    )

@app.post("/analyze", response_model=PredictionResponse)
async def predict_advanced(request: AnalyzeRequest):
    """Enterprise endpoint running hybrid predictions incorporating CRM tabular attributes."""
    if not request.customer_response.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Customer inquiry text cannot be blank."
        )
    return predict_hybrid(
        text=request.customer_response,
        total_visits=request.total_visits,
        time_on_website=request.time_on_website,
        page_views=request.page_views,
        source=request.source,
        last_activity=request.last_activity,
        occupation=request.occupation
    )
