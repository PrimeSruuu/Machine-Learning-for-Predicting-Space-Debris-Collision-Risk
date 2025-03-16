import streamlit as st
import numpy as np
import plotly.graph_objects as go
import joblib
from streamlit_react_bridge import space_debris_3d_visualizer
import requests
import certifi
import sgp4.api as sgp4
from sgp4.earth_gravity import wgs72
from sgp4.io import twoline2rv
import pandas as pd
from datetime import datetime, timedelta

# Load the trained ML model
model = joblib.load('updated_collision_risk_model.pkl')

# Function to fetch data from Celestrak (generalized for different datasets)
@st.cache_data(ttl=3600)  # Cache the data for 1 hour
def fetch_celestrak_data(url, dataset_name="space object"):
    try:
        # Fetch data from Celestrak
        st.info(f"Fetching {dataset_name} data from Celestrak...")
        response = requests.get(url, verify=certifi.where())
        response.raise_for_status()
        
        # Parse the TLE data
        tle_data = response.text.strip().split('\n')
        
        # Process TLEs into a list of objects
        object_data = []
        
        for i in range(0, len(tle_data), 3):
            if i+2 < len(tle_data):
                name = tle_data[i].strip()
                line1 = tle_data[i+1].strip()
                line2 = tle_data[i+2].strip()
                
                try:
                    # Parse TLE using SGP4
                    satellite = twoline2rv(line1, line2, wgs72)
                    
                    # Extract orbital parameters
                    inclination = satellite.inclo  # Inclination (radians)
                    eccentricity = satellite.ecco  # Eccentricity
                    raan = satellite.nodeo  # Right Ascension of Ascending Node (radians)
                    arg_perigee = satellite.argpo  # Argument of Perigee (radians)
                    mean_anomaly = satellite.mo  # Mean Anomaly (radians)
                    mean_motion = satellite.no_kozai  # Mean Motion (radians/min)
                    
                    # Calculate altitude (km) from semi-major axis
                    earth_radius = 6378.137  # Earth radius in km
                    semi_major_axis = ((60*24*7200) / (mean_motion * 2 * np.pi))**(2/3)
                    apogee = semi_major_axis * (1 + eccentricity) - earth_radius
                    perigee = semi_major_axis * (1 - eccentricity) - earth_radius
                    
                    # Make simple current position calculation
                    now = datetime.utcnow()
                    position, velocity = satellite.propagate(
                        now.year, now.month, now.day, 
                        now.hour, now.minute, now.second
                    )
                    
                    # Calculate risk based on some heuristics
                    if perigee < 500:
                        risk_factor = 0.8  # High risk
                    elif perigee < 800:
                        risk_factor = 0.6  # Medium-high risk
                    elif perigee < 1200:
                        risk_factor = 0.4  # Medium risk
                    else:
                        risk_factor = 0.2  # Low risk
                        
                    object_data.append({
                        'name': name,
                        'tle_line1': line1,
                        'tle_line2': line2,
                        'inclination': inclination,
                        'eccentricity': eccentricity,
                        'raan': raan,
                        'arg_perigee': arg_perigee,
                        'mean_anomaly': mean_anomaly,
                        'mean_motion': mean_motion,
                        'altitude': (apogee + perigee) / 2,  # Average altitude
                        'perigee': perigee,
                        'apogee': apogee,
                        'position_x': position[0],
                        'position_y': position[1],
                        'position_z': position[2],
                        'velocity_x': velocity[0],
                        'velocity_y': velocity[1],
                        'velocity_z': velocity[2],
                        'collision_risk': risk_factor,
                        'object_type': dataset_name  # Tag the type of object
                    })
                except Exception as e:
                    st.error(f"Error processing TLE for {name}: {str(e)}")
                    continue
        
        # Convert to DataFrame for easier processing
        df = pd.DataFrame(object_data)
        return df
    
    except Exception as e:
        st.error(f"Error fetching {dataset_name} data: {str(e)}")
        return pd.DataFrame()  # Return empty DataFrame in case of error

# Function to preprocess input data
def preprocess(data):
    return np.array(data).reshape(1, -1)

# Function to predict collision probability
def predict_collision(data):
    processed_data = preprocess(data)
    prediction = model.predict_proba(processed_data)[0][1]  # Probability of collision
    return prediction

# UI
st.title("🌌 Space Debris and Satellite Collision Predictor 🚀")

# Fetch both debris and active satellite data
with st.spinner("Fetching space data from Celestrak..."):
    # Fetch space debris
    debris_url = "https://celestrak.org/NORAD/elements/gp.php?GROUP=cosmos-2251-debris&FORMAT=tle"
    debris_df = fetch_celestrak_data(debris_url, "debris")
    
    # Fetch active satellites
    satellites_url = "https://www.celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle"
    satellites_df = fetch_celestrak_data(satellites_url, "satellite")
    
    # Combine the datasets
    combined_df = pd.concat([debris_df, satellites_df], ignore_index=True)

if combined_df.empty:
    st.error("Failed to fetch space data. Using simulated data instead.")
    # Use simulated data as fallback
    np.random.seed(42)
    debris_positions = np.random.rand(100, 3) * 100  # Random positions
    collision_probabilities = np.random.rand(100) * 100  # Random probabilities (0-100%)
    object_types = ["debris"] * 100  # All simulated objects are debris
else:
    st.success(f"Successfully fetched {len(combined_df)} space objects ({len(debris_df)} debris + {len(satellites_df)} satellites) from Celestrak!")
    # Extract position data and collision risks from the fetched data
    debris_positions = combined_df[['position_x', 'position_y', 'position_z']].values
    collision_probabilities = combined_df['collision_risk'].values * 100  # Convert to percentage
    object_types = combined_df['object_type'].values

# Create tabs for different visualizations
tab1, tab2 = st.tabs(["Plotly Visualization", "3D React Visualization"])

with tab1:
    distance = st.slider("Distance from Earth's Surface (km) 🚀", min_value=1, max_value=5000, value=2000)
    threshold = st.slider("Risk Threshold (%) ⚡", min_value=0, max_value=100, value=70)

    # Filter positions, collision probabilities, and object types together
    if not combined_df.empty:
        # For real data, filter based on distance from Earth's SURFACE
        earth_radius = 6378.137  # Earth radius in km
        filter_distance = distance + earth_radius
        mask = np.sqrt(np.sum(debris_positions**2, axis=1)) <= filter_distance
    else:
        # For simulated data, use the original filtering method
        mask = np.linalg.norm(debris_positions, axis=1) <= distance
    
    filtered_positions = debris_positions[mask]
    filtered_probabilities = collision_probabilities[mask]
    filtered_object_types = object_types[mask]

    # Assign risk levels
    risk_levels = []
    for prob in filtered_probabilities:
        if prob >= threshold:
            risk_levels.append("High")
        elif prob >= 50:
            risk_levels.append("Medium-High")
        elif prob >= 25:
            risk_levels.append("Medium")
        else:
            risk_levels.append("Low")

    # Count risk levels
    high_count = risk_levels.count("High")
    medium_high_count = risk_levels.count("Medium-High")
    medium_count = risk_levels.count("Medium")
    low_count = risk_levels.count("Low")

    # Display risk summary with counts and percentages
    total_count = len(risk_levels)
    
    # Calculate percentages safely
    high_percent = (high_count/total_count*100) if total_count > 0 else 0.0
    medium_high_percent = (medium_high_count/total_count*100) if total_count > 0 else 0.0
    medium_percent = (medium_count/total_count*100) if total_count > 0 else 0.0
    low_percent = (low_count/total_count*100) if total_count > 0 else 0.0
    
    st.markdown(f"""
    ### 🚨 Risk Summary ({total_count} objects within {distance} km):
    - **High Risk:** {high_count} objects ({high_percent:.1f}% of visible debris)
    - **Medium-High Risk:** {medium_high_count} objects ({medium_high_percent:.1f}% of visible debris)
    - **Medium Risk:** {medium_count} objects ({medium_percent:.1f}% of visible debris)
    - **Low Risk:** {low_count} objects ({low_percent:.1f}% of visible debris)
    """)

    # 3D Scatter Plot
    colors = {'High': 'red', 'Medium-High': 'orange', 'Medium': 'yellow', 'Low': 'green'}
    fig = go.Figure()

    # Add debris and satellite points with different markers
    for i, (position, risk_level, obj_type) in enumerate(zip(filtered_positions, risk_levels, filtered_object_types)):
        marker_size = 5 if obj_type == 'debris' else 8
        marker_symbol = 'circle' if obj_type == 'debris' else 'diamond'
        
        fig.add_trace(go.Scatter3d(
            x=[position[0]],
            y=[position[1]],
            z=[position[2]],
            mode='markers',
            marker=dict(
                size=marker_size, 
                color=colors[risk_level],
                symbol=marker_symbol
            ),
            name=f"{obj_type.capitalize()} - {risk_level} risk",
            showlegend=i < 8  # Only show first few in legend to avoid clutter
        ))

    # Add Earth
    earth_radius = 6378.137  # Earth radius in km
    u, v = np.mgrid[0:2*np.pi:20j, 0:np.pi:10j]
    x = earth_radius * np.cos(u) * np.sin(v)
    y = earth_radius * np.sin(u) * np.sin(v)
    z = earth_radius * np.cos(v)
    
    fig.add_trace(go.Surface(
        x=x, y=y, z=z,
        colorscale=[[0, 'blue'], [1, 'lightblue']],
        opacity=0.8,
        showscale=False,
        name="Earth"
    ))

    fig.update_layout(
        title="Real-Time Space Debris Collision Risk Visualization 🚀",
        scene=dict(
            xaxis_title="X Position (km)",
            yaxis_title="Y Position (km)",
            zaxis_title="Z Position (km)",
            aspectmode="data"
        )
    )

    # Show plot
    st.plotly_chart(fig)

    # Add data table with details
    if not combined_df.empty and st.checkbox("Show detailed debris data"):
        st.subheader("Space Debris Details")
        # Select columns to display
        display_columns = ['name', 'altitude', 'perigee', 'apogee', 'inclination', 'collision_risk']
        # Format the numerical columns
        display_df = combined_df[display_columns].copy()
        display_df['collision_risk'] = (display_df['collision_risk'] * 100).round(2).astype(str) + '%'
        display_df['altitude'] = display_df['altitude'].round(2).astype(str) + ' km'
        display_df['perigee'] = display_df['perigee'].round(2).astype(str) + ' km'
        display_df['apogee'] = display_df['apogee'].round(2).astype(str) + ' km'
        display_df['inclination'] = (display_df['inclination'] * 180/np.pi).round(2).astype(str) + '°'
        
        # Rename columns for better readability
        display_df.columns = ['Name', 'Altitude', 'Perigee', 'Apogee', 'Inclination', 'Collision Risk']
        
        st.dataframe(display_df)

with tab2:
    st.write("This interactive 3D visualization renders space debris based on real-time Celestrak data.")
    st.write("You can zoom, rotate, and pan using your mouse to explore the debris field.")
    
    # Add the 3D React visualization
    # We'll use our celestrak data by passing it to the React component
    if not combined_df.empty:
        # Prepare data for JavaScript
        js_data = combined_df.to_json(orient='records')
        space_debris_3d_visualizer(celestrak_data=js_data)
    else:
        # Fall back to original mode if no data
        space_debris_3d_visualizer()
    
    st.write("Visualization legend:")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("🔵 **Active satellites**")
        st.markdown("⚪ **Space debris**") 
    with col2:
        st.markdown("**Risk levels:**")
        st.markdown("🔴 High risk (>75%), 🟠 Medium-high (50-75%), 🟡 Medium (25-50%), 🟢 Low (<25%)")

    # Add a timestamp to show when the data was last updated
    st.caption(f"Data last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
