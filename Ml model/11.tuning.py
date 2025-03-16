import optuna
import xgboost as xgb
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
import pandas as pd

# Load preprocessed dataset
data = pd.read_csv("collision_risk_dataset_preprocessed.csv")
X = data.drop(columns=["collision_risk"])
y = data["collision_risk"]

# Split data
X_train, X_valid, y_train, y_valid = train_test_split(X, y, test_size=0.2, random_state=42)

# Objective function for Optuna
def objective(trial):
    # Hyperparameters to tune
    params = {
        'objective': 'binary:logistic',
        'eval_metric': 'logloss',
        'use_label_encoder': False,
        'n_estimators': trial.suggest_int('n_estimators', 100, 1000),
        'learning_rate': trial.suggest_loguniform('learning_rate', 0.01, 0.3),
        'max_depth': trial.suggest_int('max_depth', 3, 10),
        'min_child_weight': trial.suggest_int('min_child_weight', 1, 10),
        'gamma': trial.suggest_loguniform('gamma', 1e-8, 1.0),
        'subsample': trial.suggest_uniform('subsample', 0.5, 1.0),
        'colsample_bytree': trial.suggest_uniform('colsample_bytree', 0.5, 1.0),
        'scale_pos_weight': trial.suggest_uniform('scale_pos_weight', 0.5, 1.0)
    }
    
    # Train XGBoost model
    model = xgb.XGBClassifier(**params)
    model.fit(X_train, y_train)
    
    # Validate model
    preds = model.predict(X_valid)
    accuracy = accuracy_score(y_valid, preds)
    
    return accuracy

# Run Optuna
study = optuna.create_study(direction="maximize")
study.optimize(objective, n_trials=50)

# Best hyperparameters
print("✅ Best Hyperparameters:", study.best_params)
print("✅ Best Accuracy:", study.best_value)
