# AI Lead Qualification Bot

An end-to-end Machine Learning application that analyzes customer inquiries and classifies them into:
1. Hot Lead
2. Warm Lead
3. Cold Lead

## Architecture

The project implements MLOps best practices with the following stack:
- **Data & ML**: pandas, scikit-learn (Random Forest, TF-IDF)
- **MLOps**: MLflow for experiment tracking and model registry
- **Backend API**: FastAPI
- **Frontend UI**: Streamlit
- **Deployment**: Docker & Docker Compose

## Project Structure

```text
lead_qualification_bot/
├── data/                    # Data storage (raw)
├── models/                  # Saved ML models (DistilBERT weights & tokenizer)
├── config.py                # Configuration and hyperparameters
├── data_processor.py        # Tokenization & PyTorch Dataset wrapping
├── model_trainer.py         # PyTorch model training & MLflow tracking
├── main.py                  # FastAPI Backend API
├── app.py                   # Streamlit Frontend UI
├── generate_mock_data.py    # Script to create synthetic data
├── requirements.txt         # Project dependencies
├── Dockerfile               # Container setup
└── docker-compose.yml       # Docker compose setup

```

## Setup and Installation

### 1. Local Setup

1. Create a virtual environment and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Generate the mock data (simulating the Kaggle dataset):
   ```bash
   python generate_mock_data.py
   ```
3. Train the model (This will create `mlruns/` and save models to `models/`):
   ```bash
   python model_trainer.py
   ```
4. Start the FastAPI server:
   ```bash
   uvicorn main:app --reload
   ```
5. In a new terminal, start the Streamlit UI:
   ```bash
   streamlit run app.py
   ```

### 2. Docker Setup

You can run the entire application (training + API + UI) using Docker Compose:

```bash
docker-compose up --build
```
- The API will be available at `http://localhost:8000`
- The Streamlit UI will be available at `http://localhost:8501`

## API Usage Example

**Request:**
```bash
curl -X POST "http://localhost:8000/predict" -H "Content-Type: application/json" -d '{"customer_response": "Need a demo urgently"}'
```

**Response:**
```json
{"prediction": "Hot Lead"}
```

## Kaggle Dataset Details

The system is designed to work with the [Kaggle Lead Scoring Dataset](https://www.kaggle.com/datasets/amritachatterjee09/lead-scoring-dataset). 
To use the real dataset:
1. Download it from Kaggle.
2. Place the CSV file in `data/raw/lead_scoring_dataset.csv`.
3. Re-run `python src/model_trainer.py`.
