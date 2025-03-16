import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib

# Load preprocessed dataset
df = pd.read_csv("collision_risk_dataset_preprocessed.csv")

# Define feature columns & target variable
feature_cols = ["altitude", "velocity", "inclination", "eccentricity", "raan", "perigee", "anomaly"]
X = df[feature_cols]
y = df["collision_risk"]

# Split data into training (80%) & testing (20%) sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# Initialize and train XGBoost classifier
model = xgb.XGBClassifier(n_estimators=100, learning_rate=0.1, max_depth=5, random_state=42)
model.fit(X_train, y_train)

# Predictions
y_pred = model.predict(X_test)

# Evaluate performance
accuracy = accuracy_score(y_test, y_pred)
conf_matrix = confusion_matrix(y_test, y_pred)
class_report = classification_report(y_test, y_pred)

print(f"✅ Model Training Complete! Accuracy: {accuracy:.4f}")
print("\nConfusion Matrix:\n", conf_matrix)
print("\nClassification Report:\n", class_report)

# Save the trained model
joblib.dump(model, "xgboost_collision_model.pkl")
print("✅ Model saved as xgboost_collision_model.pkl")
