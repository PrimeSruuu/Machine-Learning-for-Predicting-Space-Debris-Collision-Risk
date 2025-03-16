# Space Debris Collision Predictor

An interactive application for visualizing and analyzing space debris collision risks using Streamlit.

## Features

- **Machine Learning Prediction**: Uses a trained Bagging Classifier model to predict collision risks
- **Dual Visualization Modes**:
  - **Plotly 3D Scatter**: Traditional data visualization with customizable parameters
  - **React Three.js Integration**: Immersive 3D visualization with interactive controls
- **Risk Classification**: Color-coded risk levels for easy identification

## Files Overview

- `app.py`: Main Streamlit application
- `streamlit_react_bridge.py`: Bridge between Streamlit and React for 3D visualization
- `SpaceDebrisVisualizer.jsx`: React component for 3D visualization (source reference)
- `bagging_model.pkl`: Pre-trained machine learning model
- `collision_risk_dataset_preprocessed.csv`: Dataset containing space debris information

## How to Run

1. Install the required dependencies:
   ```
   pip install streamlit plotly joblib numpy
   ```

2. Run the Streamlit application:
   ```
   streamlit run app.py
   ```

## Visualization Controls

### Plotly Visualization
- Adjust distance and threshold sliders to filter debris objects
- View risk summary statistics

### 3D React Visualization
- **Zoom**: Mouse wheel
- **Rotate**: Click and drag
- **Pan**: Right-click and drag
- Color-coded risk levels:
  - 🔴 High risk (>75%)
  - 🟠 Medium-high risk (50-75%)
  - 🟡 Medium risk (25-50%)
  - 🟢 Low risk (<25%) 