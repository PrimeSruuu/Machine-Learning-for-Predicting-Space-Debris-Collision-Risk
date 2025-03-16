import os
import numpy as np
import pandas as pd
from skyfield.api import load
from scipy.spatial import cKDTree

# Path to the TLE file
TLE_FILE_PATH = "space_debris.tle"

# Step 1: Load TLE Data
if not os.path.exists(TLE_FILE_PATH):
    print("❌ Error: TLE file not found. Please check the filename and path.")
    exit()

print("📡 Loading TLE data...")
satellites = load.tle_file(TLE_FILE_PATH)

if not satellites:
    print("❌ No satellites loaded! Check the TLE file format.")
    exit()

print(f"✅ Loaded {len(satellites)} satellites from {TLE_FILE_PATH}")

ts = load.timescale()
t = ts.now()

# Store extracted features
data = []
positions = []

print("🔄 Extracting orbital parameters...")
valid_satellites = 0  # Count valid satellites

for sat in satellites:
    try:
        pos = sat.at(t)
        position = pos.position.km  # 3D position
        
        # Check for invalid data
        if np.isnan(position).any() or np.isinf(position).any():
            continue  # Skip this satellite
        
        velocity = np.linalg.norm(pos.velocity.km_per_s)  # Speed magnitude
        altitude = pos.subpoint().elevation.km
        inclination = sat.model.inclo
        eccentricity = sat.model.ecco
        raan = sat.model.nodeo
        perigee = sat.model.argpo
        anomaly = sat.model.mo
        sat_id = sat.model.satnum

        data.append([sat_id, altitude, velocity, inclination, eccentricity, raan, perigee, anomaly])
        positions.append(position)
        valid_satellites += 1

    except Exception as e:
        print(f"⚠️ Skipping satellite {sat.model.satnum}: {e}")  # Log error and continue

print(f"✅ Successfully extracted {valid_satellites} satellites!")

# Convert to DataFrame and Save
df = pd.DataFrame(data, columns=["sat_id", "altitude", "velocity", "inclination", "eccentricity", "raan", "perigee", "anomaly"])
df.to_csv("space_debris_features.csv", index=False)
print("✅ Orbital parameters saved to space_debris_features.csv")

# Step 2: Use KDTree for Fast Close Approach Detection
collision_threshold_km = 50

print("🔍 Checking for close approaches using KDTree...")

# Convert positions list to NumPy array
positions = np.array(positions)

# Build a KDTree for fast distance queries
tree = cKDTree(positions)

# Find all close pairs
pairs = tree.query_pairs(r=collision_threshold_km)  # Only finds close satellites

labels = [(df.iloc[i]["sat_id"], df.iloc[j]["sat_id"], 1) for i, j in pairs]  # Label as high risk

print(f"✅ Found {len(labels)} high-risk satellite pairs!")

# Convert labels to DataFrame and Save
labels_df = pd.DataFrame(labels, columns=["sat1", "sat2", "collision_risk"])
labels_df.to_csv("collision_risk_labels.csv", index=False)

print("\n📂 Data saved successfully:")
print("   ✅ space_debris_features.csv (Orbital parameters)")
print("   ✅ collision_risk_labels.csv (Collision risk labels)")
