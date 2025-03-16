import joblib
import bagging_model  # Import the script with the trained model

# Save the trained model
joblib.dump(bagging_model.bagging_model, 'bagging_model.pkl')

print("✅ Model saved as bagging_model.pkl")
