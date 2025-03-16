import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier, StackingClassifier
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

# Load preprocessed dataset
data = pd.read_csv("collision_risk_dataset_preprocessed.csv")
X = data.drop(columns=["collision_risk", "sat1", "sat2"])
y = data["collision_risk"]

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Base Learners
base_learners = [
    ('xgb', XGBClassifier(**{
        'n_estimators': 280,
        'learning_rate': 0.036541994291996734,
        'max_depth': 3,
        'min_child_weight': 4,
        'gamma': 0.003183240446003429,
        'subsample': 0.9816476083262271,
        'colsample_bytree': 0.5121185969866127,
        'scale_pos_weight': 0.9247235590896973
    })),
    ('rf', RandomForestClassifier(n_estimators=100, random_state=42)),
    ('lr', LogisticRegression(max_iter=1000))
]

# Meta-Learner
meta_learner = XGBClassifier()

# Stacking Classifier
stacking_model = StackingClassifier(estimators=base_learners, final_estimator=meta_learner, cv=5)
stacking_model.fit(X_train, y_train)

# Evaluation
y_pred = stacking_model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"✅ Stacking Model Accuracy: {accuracy:.4f}")

print("\nConfusion Matrix:\n", confusion_matrix(y_test, y_pred))
print("\nClassification Report:\n", classification_report(y_test, y_pred))
