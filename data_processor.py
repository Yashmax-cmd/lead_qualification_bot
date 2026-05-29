import pandas as pd  # type: ignore
import numpy as np  # type: ignore
import re
import string
import os
import torch  # type: ignore
import joblib  # type: ignore
from sklearn.model_selection import train_test_split  # type: ignore
from sklearn.preprocessing import StandardScaler, OneHotEncoder  # type: ignore
from transformers import DistilBertTokenizer  # type: ignore
import config

class LeadInquiryDataset(torch.utils.data.Dataset):
    def __init__(self, encodings, tabular_features, class_labels=None, intent_labels=None, urgency_labels=None):
        self.encodings = encodings
        self.tabular_features = tabular_features
        self.class_labels = class_labels
        self.intent_labels = intent_labels
        self.urgency_labels = urgency_labels

    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        item['tabular_features'] = torch.tensor(self.tabular_features[idx], dtype=torch.float32)
        
        if self.class_labels is not None:
            item['labels'] = torch.tensor(self.class_labels[idx], dtype=torch.long)
        if self.intent_labels is not None:
            item['intent'] = torch.tensor(self.intent_labels[idx], dtype=torch.long)
        if self.urgency_labels is not None:
            item['urgency'] = torch.tensor(self.urgency_labels[idx], dtype=torch.long)
            
        return item

    def __len__(self):
        return len(self.encodings['input_ids'])

class DataProcessor:
    def __init__(self):
        # Load from pretrained model name or local directory
        model_src = config.DISTILBERT_MODEL_DIR if os.path.exists(config.DISTILBERT_MODEL_DIR) else config.MODEL_NAME
        try:
            self.tokenizer = DistilBertTokenizer.from_pretrained(model_src)
        except Exception:
            self.tokenizer = DistilBertTokenizer.from_pretrained(config.MODEL_NAME)
        
        # Mappings
        self.class_map = {'Cold Lead': 0, 'Warm Lead': 1, 'Hot Lead': 2}
        self.inverse_class_map = {0: 'Cold Lead', 1: 'Warm Lead', 2: 'Hot Lead'}
        
        self.intent_map = {'Just Browsing': 0, 'Product Inquiry': 1, 'Technical Support': 2, 'Enterprise Purchase': 3}
        self.inverse_intent_map = {0: 'Just Browsing', 1: 'Product Inquiry', 2: 'Technical Support', 3: 'Enterprise Purchase'}
        
        self.urgency_map = {'Low': 0, 'Medium': 1, 'High': 2}
        self.inverse_urgency_map = {0: 'Low', 1: 'Medium', 2: 'High'}

        # Preprocessing tools
        self.scaler = StandardScaler()
        self.encoder = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
        
        self.num_cols = ['TotalVisits', 'Total_Time_Spent_on_Website', 'Page_Views_Per_Visit']
        self.cat_cols = ['Lead_Source', 'Last_Activity', 'Occupation']
        
        # Load preprocessor if exists
        self.load_preprocessor()

    def load_data(self, path=config.RAW_DATA_PATH):
        try:
            return pd.read_csv(path)
        except FileNotFoundError:
            raise FileNotFoundError(f"Data not found at {path}. Please run generate_mock_data.py first.")

    def clean_text(self, text):
        if not isinstance(text, str):
            return ""
        
        # 1. Convert to lowercase
        text = text.lower()
        
        # 2. Remove URLs
        text = re.sub(r'https?://\S+|www\.\S+', '', text)
        
        # 3. Remove Emojis & Non-ASCII characters
        text = text.encode('ascii', 'ignore').decode('ascii')
        
        # 4. Remove punctuation
        text = text.translate(str.maketrans('', '', string.punctuation))
        
        # 5. Clean extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    def impute_nulls(self, df):
        df = df.copy()
        # Impute numerical columns with median
        for col in self.num_cols:
            median_val = df[col].median() if col in df and not pd.isna(df[col].median()) else 0
            df[col] = df[col].fillna(median_val)
            
        # Impute categorical columns with 'Unknown'
        for col in self.cat_cols:
            df[col] = df[col].fillna('Unknown')
            
        return df

    def fit_tabular(self, df):
        df = self.impute_nulls(df)
        
        # Fit scaler on numerical columns
        self.scaler.fit(df[self.num_cols])
        
        # Fit encoder on categorical columns
        self.encoder.fit(df[self.cat_cols])
        
        # Save fitted preprocessing objects
        self.save_preprocessor()

    def transform_tabular(self, df):
        df = self.impute_nulls(df)
        
        # Scale numerical features
        num_feats = self.scaler.transform(df[self.num_cols])
        
        # One-hot encode categorical features
        cat_feats = self.encoder.transform(df[self.cat_cols])
        
        # Concatenate features
        tabular_feats = np.hstack((num_feats, cat_feats))
        return tabular_feats

    def get_train_test_split(self, df):
        # 1. Basic Cleaning and Imputation
        df = self.impute_nulls(df)
        df['Cleaned_Inquiry'] = df['Customer_Inquiry'].apply(self.clean_text)
        
        # Determine targets dynamically if they are missing
        if 'Target' not in df.columns:
            def determine_lead_type(row):
                inquiry = str(row['Customer_Inquiry']).lower()
                hot_indicators = ["demo", "pricing", "ready to buy", "sales", "contract", "urgent", "call today"]
                cold_indicators = ["exploring", "not interested", "expensive", "competitor", "browsing", "remove me"]
                if any(ind in inquiry for ind in hot_indicators):
                    return 'Hot Lead'
                elif any(ind in inquiry for ind in cold_indicators):
                    return 'Cold Lead'
                else:
                    return 'Warm Lead'
            df['Target'] = df.apply(determine_lead_type, axis=1)

        # 2. Train-Validation Split (Stratified on target classes)
        train_df, val_df = train_test_split(
            df, 
            test_size=config.VAL_SIZE, 
            random_state=42, 
            stratify=df['Target']
        )
        
        # 3. Fit and Transform Tabular Pipeline
        self.fit_tabular(train_df)
        X_train_tab = self.transform_tabular(train_df)
        X_val_tab = self.transform_tabular(val_df)
        
        # 4. Tokenization for NLP
        train_texts = train_df['Cleaned_Inquiry'].tolist()
        val_texts = val_df['Cleaned_Inquiry'].tolist()
        
        train_encodings = self.tokenizer(train_texts, truncation=True, padding=True, max_length=config.MAX_LEN)
        val_encodings = self.tokenizer(val_texts, truncation=True, padding=True, max_length=config.MAX_LEN)
        
        # 5. Extract and Map Multi-Task Target Labels
        train_class = train_df['Target'].map(self.class_map).fillna(0).astype(int).values
        val_class = val_df['Target'].map(self.class_map).fillna(0).astype(int).values
        
        train_intent = train_df['intent'].map(self.intent_map).fillna(0).astype(int).values
        val_intent = val_df['intent'].map(self.intent_map).fillna(0).astype(int).values
        
        train_urgency = train_df['urgency'].map(self.urgency_map).fillna(0).astype(int).values
        val_urgency = val_df['urgency'].map(self.urgency_map).fillna(0).astype(int).values
        
        # 6. Construct Datasets
        train_dataset = LeadInquiryDataset(
            train_encodings, X_train_tab, train_class, train_intent, train_urgency
        )
        val_dataset = LeadInquiryDataset(
            val_encodings, X_val_tab, val_class, val_intent, val_urgency
        )
        
        return train_dataset, val_dataset

    def save_preprocessor(self, path=config.PREPROCESSOR_PATH):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump({
            'scaler': self.scaler,
            'encoder': self.encoder,
            'num_cols': self.num_cols,
            'cat_cols': self.cat_cols
        }, path)
        print(f"Tabular preprocessors saved successfully at {path}")

    def load_preprocessor(self, path=config.PREPROCESSOR_PATH):
        if os.path.exists(path):
            preprocessors = joblib.load(path)
            self.scaler = preprocessors['scaler']
            self.encoder = preprocessors['encoder']
            self.num_cols = preprocessors['num_cols']
            self.cat_cols = preprocessors['cat_cols']
            print(f"Tabular preprocessors loaded from {path}")

    def save_tokenizer(self, path=config.DISTILBERT_MODEL_DIR):
        os.makedirs(path, exist_ok=True)
        self.tokenizer.save_pretrained(path)
        print(f"Tokenizer saved to {path}")

    def load_tokenizer(self, path=config.DISTILBERT_MODEL_DIR):
        self.tokenizer = DistilBertTokenizer.from_pretrained(path)

if __name__ == "__main__":
    print("Testing DataProcessor with CRM Tabular features...")
    try:
        processor = DataProcessor()
        df = processor.load_data()
        print(f"Loaded raw CRM data of shape: {df.shape}")
        
        train_dataset, val_dataset = processor.get_train_test_split(df)
        print("Preprocessed & split data successfully!")
        print(f"Train dataset size: {len(train_dataset)}")
        print(f"Val dataset size: {len(val_dataset)}")
        
        sample = train_dataset[0]
        print("\nKeys in sample item:", list(sample.keys()))
        print("Inquiry token tensor input_ids shape:", sample['input_ids'].shape)
        print("Tabular CRM feature vector shape:", sample['tabular_features'].shape)
        print("Lead Quality Class Label:", sample['labels'].item())
        print("Lead Intent Label:", sample['intent'].item())
        print("Lead Urgency Label:", sample['urgency'].item())
        
    except Exception as e:
        print(f"Error during DataProcessor validation: {e}")
