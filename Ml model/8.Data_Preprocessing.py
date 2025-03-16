import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from imblearn.over_sampling import RandomOverSampler

# Load dataset
df = pd.read_csv("collision_risk_dataset.csv")

# Handle missing values (drop rows with NaNs)
df = df.dropna().reset_index(drop=True)

# Feature columns (excluding sat IDs and target label)
feature_cols = ["altitude", "velocity", "inclination", "eccentricity", "raan", "perigee", "anomaly"]

# Scale features
scaler = StandardScaler()
df[feature_cols] = scaler.fit_transform(df[feature_cols])

# Check class balance
risk_counts = df["collision_risk"].value_counts()
print("Class distribution before balancing:")
print(risk_counts)

# Balance dataset (oversample high-risk pairs if imbalanced)
if risk_counts.min() / risk_counts.max() < 0.5:
    ros = RandomOverSampler(sampling_strategy='auto', random_state=42)
    X_resampled, y_resampled = ros.fit_resample(df[feature_cols], df["collision_risk"])
    df = pd.DataFrame(X_resampled, columns=feature_cols)
    df["collision_risk"] = y_resampled
    print("✅ Oversampling applied to balance classes.")

# Save preprocessed dataset
df.to_csv("collision_risk_dataset_preprocessed.csv", index=False)
print("✅ Data preprocessing complete! Saved as collision_risk_dataset_preprocessed.csv")
