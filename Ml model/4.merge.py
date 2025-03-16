import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler

# Load datasets
features_df = pd.read_csv("space_debris_features.csv")
labels_df = pd.read_csv("collision_risk_labels.csv")

# Merge features for each satellite pair
def merge_features(row, features):
    sat1_features = features[features["sat_id"] == row["sat1"]].iloc[:, 1:].values.flatten()
    sat2_features = features[features["sat_id"] == row["sat2"]].iloc[:, 1:].values.flatten()
    
    if len(sat1_features) == 0 or len(sat2_features) == 0:
        return None  # Skip if data is missing for either satellite
    
    relative_features = np.abs(sat1_features - sat2_features)  # Compute differences
    return relative_features

# Apply merging
feature_cols = ["altitude", "velocity", "inclination", "eccentricity", "raan", "perigee", "anomaly"]
merged_data = labels_df.copy()
merged_data[feature_cols] = labels_df.apply(lambda row: merge_features(row, features_df), axis=1, result_type="expand")

# Drop rows where merge failed
merged_data = merged_data.dropna().reset_index(drop=True)

# Generate negative samples (randomly pairing satellites with label 0)
num_neg_samples = len(merged_data)
neg_samples = []
sat_ids = features_df["sat_id"].values

for _ in range(num_neg_samples):
    sat1, sat2 = np.random.choice(sat_ids, size=2, replace=False)
    if (sat1, sat2) not in zip(merged_data["sat1"], merged_data["sat2"]):
        neg_samples.append([sat1, sat2, 0])

neg_df = pd.DataFrame(neg_samples, columns=["sat1", "sat2", "collision_risk"])
neg_df[feature_cols] = neg_df.apply(lambda row: merge_features(row, features_df), axis=1, result_type="expand")
neg_df = neg_df.dropna().reset_index(drop=True)

# Combine positive and negative samples
final_dataset = pd.concat([merged_data, neg_df]).reset_index(drop=True)

# Normalize features
scaler = StandardScaler()
final_dataset[feature_cols] = scaler.fit_transform(final_dataset[feature_cols])

# Save dataset
final_dataset.to_csv("collision_risk_dataset.csv", index=False)
print("✅ Collision risk dataset generated successfully!")
