import mlflow  # type: ignore
import mlflow.pytorch  # type: ignore
import torch  # type: ignore
import torch.nn as nn  # type: ignore
from torch.utils.data import DataLoader  # type: ignore
from transformers import DistilBertModel  # type: ignore
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score  # type: ignore
from collections import Counter
import os
import copy
import config
from data_processor import DataProcessor

# Define the Hybrid Model combining DistilBERT text embeddings and CRM tabular features
class HybridLeadClassifier(nn.Module):
    def __init__(self, num_classes=3, num_intents=4, num_urgencies=3, tabular_dim=18):
        super().__init__()
        # Load base DistilBERT model
        self.distilbert = DistilBertModel.from_pretrained(config.MODEL_NAME)
        
        # Tabular MLP projection layer
        self.tabular_encoder = nn.Sequential(
            nn.Linear(tabular_dim, config.TABULAR_DIM),
            nn.LayerNorm(config.TABULAR_DIM),
            nn.ReLU(),
            nn.Dropout(0.1)
        )
        
        # Combined feature size: 768 (BERT CLS representation) + config.TABULAR_DIM (Tabular representation)
        concat_dim = 768 + config.TABULAR_DIM
        
        # Task 1: Lead Class Head (Hot/Warm/Cold)
        self.class_head = nn.Sequential(
            nn.Linear(concat_dim, 128),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(128, num_classes)
        )
        
        # Task 2: Intent Classification Head
        self.intent_head = nn.Sequential(
            nn.Linear(concat_dim, 128),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(128, num_intents)
        )
        
        # Task 3: Urgency Classification Head
        self.urgency_head = nn.Sequential(
            nn.Linear(concat_dim, 128),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(128, num_urgencies)
        )

    def forward(self, input_ids, attention_mask, tabular_features):
        # 1. Text forward pass through DistilBERT
        bert_outputs = self.distilbert(input_ids=input_ids, attention_mask=attention_mask)
        # Extract CLS token output (index 0)
        cls_rep = bert_outputs.last_hidden_state[:, 0, :]
        
        # 2. Tabular forward pass
        tab_rep = self.tabular_encoder(tabular_features)
        
        # 3. Concatenate text and tabular embeddings
        combined = torch.cat((cls_rep, tab_rep), dim=1)
        
        # 4. Compute class logit predictions
        class_logits = self.class_head(combined)
        intent_logits = self.intent_head(combined)
        urgency_logits = self.urgency_head(combined)
        
        return class_logits, intent_logits, urgency_logits


def compute_class_weights(labels_list, num_classes):
    counts = Counter(labels_list)
    total = len(labels_list)
    weights = [total / (num_classes * counts.get(i, 1)) for i in range(num_classes)]
    return torch.tensor(weights, dtype=torch.float32)


def evaluate_predictions(all_labels, all_preds, average='weighted'):
    acc = accuracy_score(all_labels, all_preds)
    precision = precision_score(all_labels, all_preds, average=average, zero_division=0)
    recall = recall_score(all_labels, all_preds, average=average, zero_division=0)
    f1 = f1_score(all_labels, all_preds, average=average, zero_division=0)
    return acc, precision, recall, f1


def train_model():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")

    print("Initializing Data Processor...")
    processor = DataProcessor()
    
    print("Loading CRM Dataset...")
    df = processor.load_data()
    
    print("Fitting tabular encoders and splitting into Hybrid Datasets...")
    train_dataset, val_dataset = processor.get_train_test_split(df)
    
    # Save the tokenizer and preprocessors
    processor.save_tokenizer(config.DISTILBERT_MODEL_DIR)
    
    # Configure loaders
    train_loader = DataLoader(train_dataset, batch_size=config.BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=config.BATCH_SIZE)

    # Compute loss weighting for class imbalances
    class_weights = compute_class_weights(train_dataset.class_labels, num_classes=3).to(device)
    intent_weights = compute_class_weights(train_dataset.intent_labels, num_classes=4).to(device)
    urgency_weights = compute_class_weights(train_dataset.urgency_labels, num_classes=3).to(device)

    # Loss functions
    class_criterion = nn.CrossEntropyLoss(weight=class_weights)
    intent_criterion = nn.CrossEntropyLoss(weight=intent_weights)
    urgency_criterion = nn.CrossEntropyLoss(weight=urgency_weights)

    # Initialize Hybrid Multi-Task Model
    tabular_dim = train_dataset.tabular_features.shape[1]
    model = HybridLeadClassifier(
        num_classes=3, num_intents=4, num_urgencies=3, tabular_dim=tabular_dim
    )
    model.to(device)

    # MLflow Setup
    mlflow.set_tracking_uri(config.MLFLOW_TRACKING_URI)
    mlflow.set_experiment(config.EXPERIMENT_NAME)

    with mlflow.start_run():
        print("Logging hyperparameters to MLflow...")
        mlflow.log_params({
            "model_name": "HybridDistilBertTabularClassifier",
            "text_base_model": config.MODEL_NAME,
            "tabular_dim": tabular_dim,
            "epochs": config.EPOCHS,
            "batch_size": config.BATCH_SIZE,
            "learning_rate": config.LEARNING_RATE,
            "weight_decay": config.WEIGHT_DECAY,
            "max_length": config.MAX_LEN,
            "patience": config.PATIENCE
        })

        optimizer = torch.optim.AdamW(model.parameters(), lr=config.LEARNING_RATE, weight_decay=config.WEIGHT_DECAY)
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=config.EPOCHS)

        best_val_loss = float('inf')
        best_model_weights = None
        patience_counter = 0

        print("Starting training loop...")
        for epoch in range(config.EPOCHS):
            # Training Phase
            model.train()
            total_train_loss = 0
            for step, batch in enumerate(train_loader):
                optimizer.zero_grad()
                
                input_ids = batch['input_ids'].to(device)
                attention_mask = batch['attention_mask'].to(device)
                tab_feats = batch['tabular_features'].to(device)
                
                labels = batch['labels'].to(device)
                intents = batch['intent'].to(device)
                urgencies = batch['urgency'].to(device)
                
                # Multi-head forward pass
                out_class, out_intent, out_urgency = model(input_ids, attention_mask, tab_feats)
                
                # Compute multi-task losses
                loss_c = class_criterion(out_class, labels)
                loss_i = intent_criterion(out_intent, intents)
                loss_u = urgency_criterion(out_urgency, urgencies)
                
                # Combined Loss
                loss = loss_c + loss_i + loss_u
                
                loss.backward()
                optimizer.step()
                
                total_train_loss += loss.item()
                if (step + 1) % 10 == 0 or (step + 1) == len(train_loader):
                    print(f"Epoch {epoch + 1}/{config.EPOCHS} | Step {step + 1}/{len(train_loader)} | Loss: {loss.item():.4f} (Class: {loss_c.item():.4f}, Intent: {loss_i.item():.4f}, Urgency: {loss_u.item():.4f})")
            
            avg_train_loss = total_train_loss / len(train_loader)
            scheduler.step()
            
            # Validation Phase
            model.eval()
            total_val_loss = 0
            
            # Lists to store true labels and predictions
            class_trues, class_preds = [], []
            intent_trues, intent_preds = [] ,[]
            urgency_trues, urgency_preds = [], []
            
            with torch.no_grad():
                for batch in val_loader:
                    input_ids = batch['input_ids'].to(device)
                    attention_mask = batch['attention_mask'].to(device)
                    tab_feats = batch['tabular_features'].to(device)
                    
                    labels = batch['labels'].to(device)
                    intents = batch['intent'].to(device)
                    urgencies = batch['urgency'].to(device)
                    
                    out_class, out_intent, out_urgency = model(input_ids, attention_mask, tab_feats)
                    
                    loss_c = class_criterion(out_class, labels)
                    loss_i = intent_criterion(out_intent, intents)
                    loss_u = urgency_criterion(out_urgency, urgencies)
                    
                    val_loss = loss_c + loss_i + loss_u
                    total_val_loss += val_loss.item()
                    
                    # Store class predictions
                    class_preds.extend(torch.argmax(out_class, dim=1).cpu().numpy())
                    class_trues.extend(labels.cpu().numpy())
                    
                    # Store intent predictions
                    intent_preds.extend(torch.argmax(out_intent, dim=1).cpu().numpy())
                    intent_trues.extend(intents.cpu().numpy())
                    
                    # Store urgency predictions
                    urgency_preds.extend(torch.argmax(out_urgency, dim=1).cpu().numpy())
                    urgency_trues.extend(urgencies.cpu().numpy())
            
            avg_val_loss = total_val_loss / len(val_loader)
            
            # Compute epoch metrics
            c_acc, c_pr, c_rc, c_f1 = evaluate_predictions(class_trues, class_preds)
            i_acc, i_pr, i_rc, i_f1 = evaluate_predictions(intent_trues, intent_preds)
            u_acc, u_pr, u_rc, u_f1 = evaluate_predictions(urgency_trues, urgency_preds)
            
            print(f"\n--- Epoch {epoch + 1} Summary ---")
            print(f"Train Loss: {avg_train_loss:.4f} | Val Loss: {avg_val_loss:.4f}")
            print(f"Lead Class  -> Acc: {c_acc:.4f} | F1: {c_f1:.4f}")
            print(f"Lead Intent -> Acc: {i_acc:.4f} | F1: {i_f1:.4f}")
            print(f"Lead Urgency-> Acc: {u_acc:.4f} | F1: {u_f1:.4f}\n")

            # Log metrics to MLflow
            mlflow.log_metrics({
                "train_loss": avg_train_loss,
                "val_loss": avg_val_loss,
                "class_accuracy": c_acc,
                "class_f1": c_f1,
                "intent_accuracy": i_acc,
                "intent_f1": i_f1,
                "urgency_accuracy": u_acc,
                "urgency_f1": u_f1
            }, step=epoch)

            # Early Stopping check
            if avg_val_loss < best_val_loss:
                best_val_loss = avg_val_loss
                best_model_weights = copy.deepcopy(model.state_dict())
                patience_counter = 0
            else:
                patience_counter += 1
                if patience_counter >= config.PATIENCE:
                    print(f"Early stopping triggered at epoch {epoch + 1}. Restoring best weights.")
                    break

        # Load best weights
        if best_model_weights is not None:
            model.load_state_dict(best_model_weights)

        # Log PyTorch Model to MLflow Registry
        print("Registering Hybrid model to MLflow...")
        mlflow.pytorch.log_model(model, artifact_path="hybrid_model")

        # Save model locally for API serving
        print(f"Saving final trained model state to {config.HYBRID_MODEL_PATH}...")
        os.makedirs(os.path.dirname(config.HYBRID_MODEL_PATH), exist_ok=True)
        torch.save({
            'model_state_dict': model.state_dict(),
            'tabular_dim': tabular_dim,
            'num_classes': 3,
            'num_intents': 4,
            'num_urgencies': 3
        }, config.HYBRID_MODEL_PATH)
        print("Hybrid Model successfully trained and saved!")


if __name__ == "__main__":
    train_model()
