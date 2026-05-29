import pandas as pd
import numpy as np
import os

def generate_data():
    os.makedirs('data/raw', exist_ok=True)
    np.random.seed(42) # Set seed for reproducibility
    
    # Generate 1000 records
    n_samples = 1000
    
    # Core columns simulating Kaggle Lead Scoring Dataset
    data = {
        'Lead_ID': [f'L_{i}' for i in range(n_samples)],
        'Lead_Source': np.random.choice(['Organic Search', 'Direct Traffic', 'Google Campaigns', 'Referral Sites', 'Unknown'], n_samples, p=[0.3, 0.3, 0.2, 0.1, 0.1]),
        'Total_Time_Spent_on_Website': np.random.randint(0, 2500, n_samples),
        'TotalVisits': np.random.randint(0, 50, n_samples),
        'Page_Views_Per_Visit': np.round(np.random.uniform(0.0, 10.0, n_samples), 2),
        'Last_Activity': np.random.choice(['Email Opened', 'SMS Sent', 'Page Visited on Website', 'Email Bounced', 'Unknown'], n_samples, p=[0.4, 0.3, 0.15, 0.05, 0.1]),
        'Occupation': np.random.choice(['Working Professional', 'Student', 'Unemployed', 'Businessman', 'Unknown'], n_samples, p=[0.4, 0.2, 0.15, 0.15, 0.1]),
        'City': np.random.choice(['Mumbai', 'Delhi', 'Bangalore', 'Other'], n_samples),
        'Converted': np.random.choice([0, 1], n_samples, p=[0.65, 0.35]),
    }
    
    # Templates of inquiries mapped to classes
    hot_texts = [
        "We need a demo urgently this month for our enterprise CRM.",
        "We are looking for enterprise pricing and deployment details.",
        "Ready to buy, need to talk to sales today.",
        "Please send the contract for enterprise license.",
        "Urgent deployment requirement for our sales team.",
        "Can we schedule a call today to discuss procurement?"
    ]
    warm_texts = [
        "Interested in learning more about your product features.",
        "What are the features of your CRM tool?",
        "Can you send some product case studies?",
        "Looking for a solution to implement next quarter.",
        "Comparing CRM software options right now.",
        "Need some technical specifications and setup guides."
    ]
    cold_texts = [
        "Just exploring options on the web.",
        "Not interested in purchasing right now.",
        "Too expensive for our small budget.",
        "We already use a competitor's software.",
        "Just browsing around.",
        "Remove me from your newsletter list."
    ]
    
    inquiries = []
    intents = []
    urgencies = []
    
    for i in range(n_samples):
        converted = data['Converted'][i]
        time_spent = data['Total_Time_Spent_on_Website'][i]
        
        # Correlate inquiry text, intent, and urgency with CRM values
        if converted == 1:
            inquiries.append(np.random.choice(hot_texts))
            intents.append("Enterprise Purchase")
            urgencies.append("High")
        elif time_spent > 1200:
            inquiries.append(np.random.choice(warm_texts))
            intents.append("Product Inquiry")
            urgencies.append("Medium")
        else:
            inquiries.append(np.random.choice(cold_texts))
            intents.append("Just Browsing")
            urgencies.append("Low")
            
    data['Customer_Inquiry'] = inquiries
    data['intent'] = intents
    data['urgency'] = urgencies
    
    df = pd.DataFrame(data)
    
    # Introduce some missing values to simulate real CRM datasets
    df.loc[np.random.choice(df.index, 50), 'TotalVisits'] = np.nan
    df.loc[np.random.choice(df.index, 50), 'Page_Views_Per_Visit'] = np.nan
    df.loc[np.random.choice(df.index, 100), 'Lead_Source'] = np.nan
    
    df.to_csv('data/raw/lead_scoring_dataset.csv', index=False)
    print("Upgraded mock dataset successfully saved at data/raw/lead_scoring_dataset.csv")

if __name__ == "__main__":
    generate_data()
