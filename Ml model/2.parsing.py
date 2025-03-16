import os
import numpy as np
from skyfield.api import load

# Path to the TLE file
TLE_FILE_PATH = "space_debris.tle"

# Step 1: Load TLE File
if not os.path.exists(TLE_FILE_PATH):
    print("❌ Error: TLE file not found.")
    exit()

# Load TLE data
satellites = load.tle_file(TLE_FILE_PATH)

# Manually assign names using their NORAD IDs
satellite_data = {}
for satellite in satellites:
    norad_id = satellite.model.satnum  # Extract satellite ID
    satellite_data[norad_id] = satellite  # Store by ID

# Step 2: Print Orbital Data
ts = load.timescale()
t = ts.now()

for norad_id, satellite in satellite_data.items():
    position = satellite.at(t)
    altitude = position.subpoint().elevation.km  # Altitude (km)
    
    # Extract velocity components (km/s)
    velocity_vector = position.velocity.km_per_s  
    velocity_magnitude = np.linalg.norm(velocity_vector)  # Compute speed

    inclination = satellite.model.inclo  # Inclination (degrees)

    print(f"\n🔹 Satellite ID: {norad_id}")
    print(f"   🛰 Altitude: {altitude:.2f} km")
    print(f"   🚀 Velocity: {velocity_magnitude:.2f} km/s")
    print(f"   🔄 Inclination: {inclination:.2f}°")

    break  # Print data for only one satellite (remove this to print all)
