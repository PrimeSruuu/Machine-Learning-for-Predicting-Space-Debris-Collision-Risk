import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from imblearn.over_sampling import SMOTE
from sklearn.metrics import classification_report

# Load your dataset
data = pd.read_csv('collision_risk_dataset_preprocessed.csv')  # Replace with your dataset file

# Separate features (X) and target variable (y)
X = data.drop(columns=['target_column'])  # Replace 'target_column' with the name of your target column
y = data['target_column']  # Replace 'target_column' with the name of your target column

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Load the pre-trained model
model = joblib.load('collision_risk_model.pkl')  # Replace with your model file

# Apply SMOTE to balance the training data
smote = SMOTE()
X_resampled, y_resampled = smote.fit_resample(X_train, y_train)

# Train the model on the resampled data
model.fit(X_resampled, y_resampled)

# Evaluate the model on the test set
y_pred = model.predict(X_test)
print(classification_report(y_test, y_pred))