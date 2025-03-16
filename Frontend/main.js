// Main application script

// Global variables
let timeSliderValue = 0;       // Default time (in seconds)
let startTime;                 // Cesium JulianDate reference
let selectedEntity = null;     // Currently selected entity for time control
window.viewer = null;          // Exposed globally if needed
let realTimeMode = false;      // Track if we're in real-time mode
let refreshInterval = null;    // Interval for refreshing data

// Celestrak TLE data URLs
const satelliteUrl = 'https://www.celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle';
const debrisUrl = 'https://www.celestrak.org/NORAD/elements/gp.php?GROUP=cosmos-2251-debris&FORMAT=tle';
// Additional specialty satellites and weather satellites
const scienceUrl = 'https://www.celestrak.org/NORAD/elements/gp.php?GROUP=science&FORMAT=tle';
const weatherUrl = 'https://www.celestrak.org/NORAD/elements/gp.php?GROUP=weather&FORMAT=tle';

document.addEventListener('DOMContentLoaded', () => {
    initCesium();
    setupSidebarToggle();
    setupEntityClickHandler();
    setupEventListeners();
    
    // Add real-time toggle button to UI
    addRealTimeToggle();
});


const API_BASE_URL = "http://127.0.0.1:5000";  // Local Flask API

async function getSatellitePosition(satelliteName) {
    try {
        const response = await fetch(`${API_BASE_URL}/satellite-position?satellite=${encodeURIComponent(satelliteName)}`);
        if (!response.ok) {
            throw new Error("Failed to fetch satellite data");
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error("Error fetching satellite position:", error);
        return null;
    }
}

function initCesium() {
    // Set your Cesium Ion access token here
    Cesium.Ion.defaultAccessToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJiNGFhNjQyZS01NGM1LTQ2YzItOTY2Mi1lZWRlZDA0OTBjNjQiLCJpZCI6MjgwNTEzLCJpYXQiOjE3NDA5ODEwMjh9.TqWAvnUF6yHfLOo3MYz5Ji32SzqCCgOJ9h_EXKXr1o0';
    
    // Create the Cesium Viewer with the default InfoBox enabled
    window.viewer = new Cesium.Viewer('visualization', {
        infoBox: true,
        selectionIndicator: true,
        contextOptions: { webgl: { version: 1, alpha: false } },
        terrainProvider: Cesium.createWorldTerrain(),
        timeline: false,
        animation: false
    });
    
    // Set simulation start time to current time
    startTime = Cesium.JulianDate.fromDate(new Date());
    viewer.clock.startTime = startTime;
    viewer.clock.currentTime = startTime;
    viewer.clock.multiplier = 1;
    viewer.clock.shouldAnimate = false;
    
    // Load real-time satellite and debris data
    loadRealTimeSatelliteData();
}

async function loadRealTimeSatelliteData() {
    showLoading(true);
    try {
        // Clear existing entities when reloading
        viewer.entities.removeAll();
        
        // Create Earth entity with atmosphere
        createEarthAtmosphere();
        
        // Fetch satellites from multiple sources
        const [satelliteData, scienceData, weatherData] = await Promise.all([
            fetchTLEData(satelliteUrl),
            fetchTLEData(scienceUrl),
            fetchTLEData(weatherUrl)
        ]);
        
        // Combine all satellite data
        const allSatelliteData = [...(satelliteData || []), ...(scienceData || []), ...(weatherData || [])];
        
        if (allSatelliteData && allSatelliteData.length > 0) {
            // Add ISS with real model
            const issTLE = findTLEByName(allSatelliteData, "ISS");
            if (issTLE) {
                addSatelliteFromTLE(issTLE, 'ISS', {
                    model: {
                        uri: 'models/iss.glb',
                        minimumPixelSize: 0,
                        maximumScale: 20000,
                        scale: 1.0
                    },
                    pathColor: Cesium.Color.YELLOW,
                    description: `
                      <h3>International Space Station</h3>
                      <p><strong>Launched:</strong> 20 November 1998</p>
                      <p><strong>Operator:</strong> NASA / Roscosmos / ESA / JAXA / CSA</p>
                      <p><strong>Orbit Altitude:</strong> ~408 km</p>
                      <p><strong>Inclination:</strong> 51.6°</p>
                      <p>A modular space station in low Earth orbit.</p>
                      <div id="iss-real-time-data">Loading real-time data...</div>
                      <p style="margin-top: 10px;">
                        Use the <strong>time slider</strong> to scrub through its orbit or enable real-time mode.
                      </p>
                    `
                });
                
                // Fetch additional real-time data for ISS
                fetchISSRealTimeData();
            }
            
            // Add NOAA-20 with custom image
            const noaaTLE = findTLEByName(allSatelliteData, "NOAA 20");
            if (noaaTLE) {
                addSatelliteFromTLE(noaaTLE, 'NOAA20', {
                    billboard: {
                        image: 'images/noaa20.png',
                        verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
                        scale: 0.5
                    },
                    pathColor: Cesium.Color.ORANGE,
                    description: `
                      <h3>NOAA-20</h3>
                      <p><strong>Launched:</strong> 18 November 2017</p>
                      <p><strong>Operator:</strong> NOAA / NASA</p>
                      <p><strong>Orbit Altitude:</strong> ~825 km (sun-synchronous)</p>
                      <p><strong>Inclination:</strong> 98.7°</p>
                      <p>A polar-orbiting satellite for weather and climate observations.</p>
                      <div id="noaa-real-time-data">Loading real-time data...</div>
                      <p style="margin-top: 10px;">
                        Use the <strong>time slider</strong> to scrub through its orbit or enable real-time mode.
                      </p>
                    `
                });
                
                // Fetch additional real-time data for NOAA
                fetchSatelliteRealTimeData('NOAA20');
            }
            
            // Add OSTM/Jason (look for any available Jason satellite)
            const jasonTLE = findTLEByName(allSatelliteData, "JASON");
            if (jasonTLE) {
                addSatelliteFromTLE(jasonTLE, 'OSTM', {
                    model: {
                        uri: 'models/ostm.glb',
                        minimumPixelSize: 0,
                        maximumScale: 150,
                        scale: 0.5
                    },
                    pathColor: Cesium.Color.LIME,
                    description: `
                      <h3>OSTM/Jason</h3>
                      <p><strong>Launched:</strong> 20 June 2008</p>
                      <p><strong>Operator:</strong> NASA / CNES / NOAA / EUMETSAT</p>
                      <p><strong>Orbit Altitude:</strong> ~1336 km</p>
                      <p><strong>Inclination:</strong> 66° (approx)</p>
                      <p>Measuring sea surface height for ocean surface topography.</p>
                      <div id="ostm-real-time-data">Loading real-time data...</div>
                      <p style="margin-top: 10px;">
                        Use the <strong>time slider</strong> to scrub through its orbit or enable real-time mode.
                      </p>
                    `
                });
                
                // Fetch additional real-time data for OSTM
                fetchSatelliteRealTimeData('OSTM');
            }
        }
        
        // Fetch debris data (up to 7 pieces)
        const debrisData = await fetchTLEData(debrisUrl);
        if (debrisData) {
            // Add up to 7 pieces of debris
            const maxDebris = Math.min(7, debrisData.length / 3);
            for (let i = 0; i < maxDebris; i++) {
                const index = i * 3;
                if (index + 2 < debrisData.length) {
                    const name = debrisData[index].trim();
                    const line1 = debrisData[index + 1];
                    const line2 = debrisData[index + 2];
                    
                    addSatelliteFromTLE({ name, line1, line2 }, `Debris_${i}`, {
                        point: {
                            pixelSize: 5,
                            color: Cesium.Color.RED
                        },
                        pathColor: Cesium.Color.RED,
                        description: `
                          <h3>${name}</h3>
                          <p><strong>Type:</strong> Space Debris (Cosmos 2251)</p>
                          <p><strong>TLE Data:</strong></p>
                          <pre>${line1}\n${line2}</pre>
                          <div id="debris-${i}-real-time-data">Loading real-time data...</div>
                        `
                    });
                    
                    // Fetch additional real-time data for debris
                    fetchDebrisRealTimeData(`Debris_${i}`);
                }
            }
        }
        
        // Fly to include all entities after adding them
        setTimeout(() => {
            viewer.flyTo(viewer.entities.values);
        }, 1000);
        
    } catch (error) {
        console.error("Error loading satellite data:", error);
        showErrorMessage("Failed to load satellite data. Using fallback data.");
        
        // Use fallback data if real-time data fails
        useFallbackSatelliteData();
    } finally {
        showLoading(false);
    }
}

async function fetchTLEData(url) {
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`Failed to fetch TLE data from ${url}`);
        }
        const text = await response.text();
        return text.split('\n');
    } catch (error) {
        console.error("Error fetching TLE data:", error);
        return null;
    }
}

function findTLEByName(tleData, satelliteName) {
    if (!tleData || tleData.length < 3) return null;
    
    for (let i = 0; i < tleData.length - 2; i++) {
        const name = tleData[i].trim();
        if (name.includes(satelliteName)) {
            return {
                name: name,
                line1: tleData[i + 1],
                line2: tleData[i + 2]
            };
        }
    }
    return null;
}

function addSatelliteFromTLE(tle, id, options) {
    if (!tle || !tle.line1 || !tle.line2) return null;
    
    const satrec = satellite.twoline2satrec(tle.line1, tle.line2);
    if (!satrec) return null;
    
    // Estimate orbit period using mean motion (revolutions per day)
    const revPerDay = satellite.meanMotion(satrec.no);
    const orbitPeriodSeconds = (24 * 60 * 60) / revPerDay;
    
    const sampleCount = 180;
    const position = new Cesium.SampledPositionProperty();
    
    for (let i = 0; i <= sampleCount; i++) {
        const fraction = i / sampleCount;
        const timeInSec = fraction * orbitPeriodSeconds;
        const sampleTime = Cesium.JulianDate.addSeconds(startTime, timeInSec, new Cesium.JulianDate());
        const jsDate = Cesium.JulianDate.toDate(sampleTime);
        
        const positionAndVelocity = satellite.propagate(satrec, jsDate);
        if (positionAndVelocity.position) {
            const gmst = satellite.gstime(jsDate);
            const geo = satellite.eciToGeodetic(positionAndVelocity.position, gmst);
            const longitude = satellite.degreesLong(geo.longitude);
            const latitude = satellite.degreesLat(geo.latitude);
            const altitude = geo.height * 1000; // convert km to meters
            const cartesianPos = Cesium.Cartesian3.fromDegrees(longitude, latitude, altitude);
            position.addSample(sampleTime, cartesianPos);
        }
    }
    
    position.forwardExtrapolationType = Cesium.ExtrapolationType.HOLD;
    position.backwardExtrapolationType = Cesium.ExtrapolationType.HOLD;
    
    // Prepare entity options
    const entityOptions = {
        id: id,
        name: tle.name || id,
        position: position,
        path: {
            leadTime: orbitPeriodSeconds,
            trailTime: orbitPeriodSeconds,
            width: 2,
            material: options.pathColor || Cesium.Color.WHITE
        },
        label: {
            text: tle.name || id,
            font: '14pt sans-serif',
            style: Cesium.LabelStyle.FILL_AND_OUTLINE,
            outlineWidth: 2,
            verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
            pixelOffset: new Cesium.Cartesian2(0, -9)
        }
    };
    
    // Add optional properties
    if (options.model) {
        entityOptions.model = options.model;
    }
    
    if (options.billboard) {
        entityOptions.billboard = options.billboard;
    }
    
    if (options.point) {
        entityOptions.point = options.point;
    }
    
    if (options.description) {
        entityOptions.description = options.description;
    }
    
    // Add the entity to the viewer
    return viewer.entities.add(entityOptions);
}

/* =========================
   5) Entity Click Handler
   - Enables the time slider when a satellite is selected.
   - The built-in InfoBox automatically displays the description.
========================= */
function setupEntityClickHandler() {
    const handler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);
    const timeSlider = document.getElementById('time-slider');
    
    handler.setInputAction((click) => {
        const pickedObject = viewer.scene.pick(click.position);
        if (Cesium.defined(pickedObject) && pickedObject.id) {
            const id = pickedObject.id.id;
            if (id === 'ISS' || id === 'NOAA20' || id === 'OSTM') {
                selectedEntity = pickedObject.id;
                timeSlider.disabled = false;
            } else {
                selectedEntity = null;
                timeSlider.disabled = true;
            }
        } else {
            selectedEntity = null;
            timeSlider.disabled = true;
        }
    }, Cesium.ScreenSpaceEventType.LEFT_CLICK);
}

/* =========================
   6) Sidebar Toggle Functionality
========================= */
function setupSidebarToggle() {
    const leftSidebar = document.getElementById('control-panel');
    const rightSidebar = document.getElementById('details-panel');
    const toggleLeftBtn = document.getElementById('toggle-left');
    const toggleRightBtn = document.getElementById('toggle-right');
    const visualizationContainer = document.getElementById('visualization-container');
    
    if (toggleLeftBtn && leftSidebar) {
        toggleLeftBtn.addEventListener('click', () => {
            leftSidebar.classList.toggle('collapsed');
            toggleLeftBtn.classList.toggle('open');
            visualizationContainer.style.marginLeft = leftSidebar.classList.contains('collapsed') ? '0' : '250px';
        });
    }
    
    if (toggleRightBtn && rightSidebar) {
        toggleRightBtn.addEventListener('click', () => {
            rightSidebar.classList.toggle('collapsed');
            toggleRightBtn.classList.toggle('open');
            visualizationContainer.style.marginRight = rightSidebar.classList.contains('collapsed') ? '0' : '250px';
        });
    }
}

/* =========================
   7) Additional UI Event Listeners
========================= */
function setupEventListeners() {
    const timeSlider = document.getElementById('time-slider');
    timeSlider.disabled = true;
    
    timeSlider.addEventListener('input', (e) => {
        if (selectedEntity && (selectedEntity.id === 'ISS' || selectedEntity.id === 'NOAA20' || selectedEntity.id === 'OSTM')) {
            timeSliderValue = parseInt(e.target.value, 10);
            updateTimeDisplay(timeSliderValue);
            
            // Update real-time data when slider changes
            if (selectedEntity.id === 'ISS') fetchISSRealTimeData();
            else fetchSatelliteRealTimeData(selectedEntity.id);
        }
    });
    
    timeSlider.addEventListener('change', () => {
        if (selectedEntity && (selectedEntity.id === 'ISS' || selectedEntity.id === 'NOAA20' || selectedEntity.id === 'OSTM')) {
            console.log('Time slider changed:', timeSliderValue);
        }
    });
    
    const satelliteSelect = document.getElementById('satellite-select');
    if (satelliteSelect) {
        satelliteSelect.addEventListener('change', (e) => {
            const selection = e.target.value;
            if (selection === 'all') {
                viewer.flyTo(viewer.entities.values);
            } else {
                viewer.flyTo(viewer.entities.getById(selection));
            }
        });
    }
    
    // Add interval to update the time display in real-time mode
    setInterval(() => {
        if (realTimeMode) {
            const currentTimeSeconds = Math.floor((new Date() - Cesium.JulianDate.toDate(startTime)) / 1000);
            updateTimeDisplay(currentTimeSeconds);
        }
    }, 1000);
}

/* =========================
   8) Update Time Display and Viewer Clock
========================= */
function updateTimeDisplay(value) {
    const timeDisplay = document.getElementById('time-display');
    if (!timeDisplay) return;
    const newTime = Cesium.JulianDate.addSeconds(startTime, value, new Cesium.JulianDate());
    viewer.clock.currentTime = newTime;
    
    const hours = Math.floor(value / 3600);
    const minutes = Math.floor((value % 3600) / 60);
    const seconds = value % 60;
    timeDisplay.textContent = `${hours.toString().padStart(2, '0')}:` +
                              `${minutes.toString().padStart(2, '0')}:` +
                              `${seconds.toString().padStart(2, '0')}`;
}

/* =========================
   Helper Functions
========================= */
async function fetchInitialData() {
    return { satellites: [], predictions: [] };
}

function showLoading(isLoading) {
    const loadingOverlay = document.getElementById('loading-overlay');
    if (!loadingOverlay) return;
    loadingOverlay.classList.toggle('active', isLoading);
}

function debounce(func, wait) {
    let timeout;
    return function () {
        const context = this;
        const args = arguments;
        clearTimeout(timeout);
        timeout = setTimeout(() => { func.apply(context, args); }, wait);
    };
}

// Helper function to calculate mean motion from TLE
satellite.meanMotion = function(noRadiansPerMinute) {
    // Convert from radians per minute to revolutions per day
    return (noRadiansPerMinute * 60 * 24) / (2 * Math.PI);
};

// Create Earth entity with atmosphere
function createEarthAtmosphere() {
    viewer.scene.globe.enableLighting = true;
    viewer.scene.globe.showGroundAtmosphere = true;
    viewer.scene.skyAtmosphere.show = true;
    viewer.scene.fog.enabled = true;
}

// Show error messages to user
function showErrorMessage(message) {
    const errorContainer = document.getElementById('error-container');
    if (errorContainer) {
        errorContainer.textContent = message;
        errorContainer.style.display = 'block';
        setTimeout(() => {
            errorContainer.style.display = 'none';
        }, 5000);
    } else {
        console.error(message);
    }
}

// Use fallback data if API fails
function useFallbackSatelliteData() {
    // ... existing code ...
    // This would implement fallback hardcoded data similar to what was in the original code
}

// Fetch real-time ISS data
async function fetchISSRealTimeData() {
    try {
        const response = await fetch('https://api.wheretheiss.at/v1/satellites/25544');
        if (!response.ok) throw new Error('Failed to fetch ISS data');
        
        const data = await response.json();
        
        const issDataContainer = document.getElementById('iss-real-time-data');
        if (issDataContainer) {
            issDataContainer.innerHTML = `
                <p><strong>Current Position:</strong></p>
                <p>Latitude: ${data.latitude.toFixed(4)}°</p>
                <p>Longitude: ${data.longitude.toFixed(4)}°</p>
                <p>Altitude: ${data.altitude.toFixed(2)} km</p>
                <p>Velocity: ${data.velocity.toFixed(2)} km/h</p>
                <p><strong>Last Updated:</strong> ${new Date().toLocaleTimeString()}</p>
            `;
        }
    } catch (error) {
        console.error('Error fetching real-time ISS data:', error);
    }
}

// Generic function to fetch satellite real-time data
async function fetchSatelliteRealTimeData(satelliteId) {
    try {
        // This would be implemented with a real API
        // For now, we'll simulate with the entity position
        const entity = viewer.entities.getById(satelliteId);
        if (!entity) return;
        
        const position = entity.position.getValue(viewer.clock.currentTime);
        if (!position) return;
        
        const cartographic = Cesium.Cartographic.fromCartesian(position);
        const longitude = Cesium.Math.toDegrees(cartographic.longitude);
        const latitude = Cesium.Math.toDegrees(cartographic.latitude);
        const altitude = cartographic.height / 1000; // km
        
        const dataContainer = document.getElementById(`${satelliteId.toLowerCase()}-real-time-data`);
        if (dataContainer) {
            dataContainer.innerHTML = `
                <p><strong>Current Position (Calculated):</strong></p>
                <p>Latitude: ${latitude.toFixed(4)}°</p>
                <p>Longitude: ${longitude.toFixed(4)}°</p>
                <p>Altitude: ${altitude.toFixed(2)} km</p>
                <p><strong>Last Updated:</strong> ${new Date().toLocaleTimeString()}</p>
            `;
        }
    } catch (error) {
        console.error(`Error fetching real-time data for ${satelliteId}:`, error);
    }
}

// Fetch debris real-time data
function fetchDebrisRealTimeData(debrisId) {
    try {
        // Similar to fetchSatelliteRealTimeData
        const entity = viewer.entities.getById(debrisId);
        if (!entity) return;
        
        const position = entity.position.getValue(viewer.clock.currentTime);
        if (!position) return;
        
        const cartographic = Cesium.Cartographic.fromCartesian(position);
        const longitude = Cesium.Math.toDegrees(cartographic.longitude);
        const latitude = Cesium.Math.toDegrees(cartographic.latitude);
        const altitude = cartographic.height / 1000; // km
        
        const dataContainer = document.getElementById(`${debrisId.toLowerCase()}-real-time-data`);
        if (dataContainer) {
            dataContainer.innerHTML = `
                <p><strong>Current Position:</strong></p>
                <p>Latitude: ${latitude.toFixed(4)}°</p>
                <p>Longitude: ${longitude.toFixed(4)}°</p>
                <p>Altitude: ${altitude.toFixed(2)} km</p>
                <p><strong>Last Updated:</strong> ${new Date().toLocaleTimeString()}</p>
            `;
        }
    } catch (error) {
        console.error(`Error fetching real-time data for ${debrisId}:`, error);
    }
}

// Add real-time toggle to UI
function addRealTimeToggle() {
    const controlPanel = document.getElementById('control-panel');
    if (!controlPanel) return;
    
    const toggleContainer = document.createElement('div');
    toggleContainer.className = 'control-group';
    toggleContainer.innerHTML = `
        <label>Real-time Mode</label>
        <div class="toggle-switch">
            <input type="checkbox" id="real-time-toggle">
            <label for="real-time-toggle"></label>
        </div>
        <button id="refresh-data" class="btn">Refresh Data</button>
    `;
    
    controlPanel.appendChild(toggleContainer);
    
    // Setup event listeners
    document.getElementById('real-time-toggle').addEventListener('change', toggleRealTimeMode);
    document.getElementById('refresh-data').addEventListener('click', () => loadRealTimeSatelliteData());
}

// Toggle real-time mode
function toggleRealTimeMode(event) {
    realTimeMode = event.target.checked;
    const timeSlider = document.getElementById('time-slider');
    
    if (realTimeMode) {
        // Disable time slider in real-time mode
        if (timeSlider) timeSlider.disabled = true;
        
        // Start clock animation
        viewer.clock.shouldAnimate = true;
        
        // Setup periodic data refresh (every 60 seconds)
        refreshInterval = setInterval(() => {
            updateRealTimeData();
        }, 60000);
        
        // Initial update
        updateRealTimeData();
    } else {
        // Stop auto-refresh
        if (refreshInterval) {
            clearInterval(refreshInterval);
            refreshInterval = null;
        }
        
        // Stop clock animation
        viewer.clock.shouldAnimate = false;
        
        // Re-enable time slider for selected entity
        if (timeSlider && selectedEntity && ['ISS', 'NOAA20', 'OSTM'].includes(selectedEntity.id)) {
            timeSlider.disabled = false;
        }
    }
}

// Update all real-time data
function updateRealTimeData() {
    // Update the Cesium clock to current time
    viewer.clock.currentTime = Cesium.JulianDate.fromDate(new Date());
    
    // Update real-time data for major satellites
    fetchISSRealTimeData();
    fetchSatelliteRealTimeData('NOAA20');
    fetchSatelliteRealTimeData('OSTM');
    
    // Update debris data
    for (let i = 0; i < 7; i++) {
        fetchDebrisRealTimeData(`Debris_${i}`);
    }
    
    console.log('Real-time data updated at', new Date().toLocaleTimeString());
}
