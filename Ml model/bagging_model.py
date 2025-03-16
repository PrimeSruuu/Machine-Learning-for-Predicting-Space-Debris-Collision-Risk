import numpy as np
import pandas as pd
from sklearn.ensemble import BaggingClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

# Load the preprocessed dataset
data = pd.read_csv('collision_risk_dataset_preprocessed.csv')
X = data.drop(columns=['collision_risk'])
y = data['collision_risk']

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
print(f'Training samples: {len(X_train)}')
print(f'Testing samples: {len(X_test)}')

# Initialize the Bagging Classifier
bagging_model = BaggingClassifier(
    estimator=DecisionTreeClassifier(),
    n_estimators=100,
    random_state=42
)

# Train the model
bagging_model.fit(X_train, y_train)


# Make predictions
y_pred = bagging_model.predict(X_test)

# Evaluate the model
accuracy = accuracy_score(y_test, y_pred)
conf_matrix = confusion_matrix(y_test, y_pred)
class_report = classification_report(y_test, y_pred)

print(f'✅ Bagging Model Accuracy: {accuracy:.4f}\n')
print('Confusion Matrix:\n', conf_matrix)
print('\nClassification Report:\n', class_report)
