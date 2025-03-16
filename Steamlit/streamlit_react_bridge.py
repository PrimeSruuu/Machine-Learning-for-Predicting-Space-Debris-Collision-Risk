import streamlit as st
import streamlit.components.v1 as components
import os
import json

def space_debris_3d_visualizer(celestrak_data=None):
    """
    Renders the 3D Space Debris Visualizer React component in Streamlit
    
    Parameters:
    -----------
    celestrak_data : str, optional
        JSON string containing Celestrak data, if available
    """
    # Get the directory of the current file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create HTML that embeds the React component
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Space Debris Visualizer</title>
        <script src="https://unpkg.com/react@17/umd/react.production.min.js"></script>
        <script src="https://unpkg.com/react-dom@17/umd/react-dom.production.min.js"></script>
        <script src="https://unpkg.com/three@0.137.0/build/three.min.js"></script>
        <script src="https://unpkg.com/@react-three/fiber@7.0.26/dist/react-three-fiber.min.js"></script>
        <script src="https://unpkg.com/@react-three/drei@8.19.5/dist/drei.min.js"></script>
        <script src="https://unpkg.com/csvtojson@2.0.10/browser/csvtojson.min.js"></script>
        <style>
            body, html {{
                margin: 0;
                padding: 0;
                width: 100%;
                height: 100%;
                overflow: hidden;
            }}
            #root {{
                width: 100%;
                height: 100vh;
            }}
        </style>
    </head>
    <body>
        <div id="root"></div>
        <script>
            // Import required libraries
            const {{ useState, useEffect, Suspense }} = React;
            const {{ Canvas }} = ReactThreeFiber;
            const {{ OrbitControls, Stars }} = drei;
            
            // Preload Celestrak data if available
            const celestrakData = {json.dumps(celestrak_data) if celestrak_data else 'null'};
            
            // SpaceDebrisVisualizer component
            function SpaceDebrisVisualizer() {{
                const [debris, setDebris] = useState([]);
                const [loading, setLoading] = useState(true);
                const [error, setError] = useState(null);
                const [dataSource, setDataSource] = useState(celestrakData ? 'Celestrak' : 'CSV');

                useEffect(() => {{
                    setLoading(true);
                    
                    if (celestrakData) {{
                        try {{
                            // Parse the Celestrak data directly
                            const json = JSON.parse(celestrakData);
                            const processedDebris = json.map(item => ({{
                                position: [
                                    parseFloat(item.position_x),
                                    parseFloat(item.position_y),
                                    parseFloat(item.position_z)
                                ],
                                risk: parseFloat(item.collision_risk),
                                name: item.name,
                                altitude: parseFloat(item.altitude),
                                id: `debris-${{Math.random().toString(36).substr(2, 9)}}`
                            }}));
                            setDebris(processedDebris);
                            setLoading(false);
                        }} catch (err) {{
                            console.error('Error processing Celestrak data:', err);
                            setError('Failed to process Celestrak data. Falling back to CSV.');
                            fetchCSVData();
                        }}
                    }} else {{
                        // Fall back to CSV data
                        fetchCSVData();
                    }}
                }}, []);
                
                const fetchCSVData = () => {{
                    fetch('collision_risk_dataset_preprocessed.csv')
                        .then(response => {{
                            if (!response.ok) {{
                                throw new Error('Failed to fetch data');
                            }}
                            return response.text();
                        }})
                        .then(data => csvtojson().fromString(data))
                        .then(json => {{
                            const processedDebris = json.map(item => ({{
                                position: [
                                    parseFloat(item.altitude) * Math.cos(parseFloat(item.raan)),
                                    parseFloat(item.altitude) * Math.sin(parseFloat(item.raan)),
                                    parseFloat(item.perigee)
                                ],
                                risk: parseFloat(item.collision_risk),
                                id: `debris-${{Math.random().toString(36).substr(2, 9)}}`
                            }}));
                            setDebris(processedDebris);
                            setDataSource('CSV');
                            setLoading(false);
                        }})
                        .catch(err => {{
                            console.error('Error loading debris data:', err);
                            setError(err.message);
                            setLoading(false);
                        }});
                }};

                const getColorFromRisk = (risk) => {{
                    if (risk > 0.75) return 'red';
                    if (risk > 0.5) return 'orange';
                    if (risk > 0.25) return 'yellow';
                    return 'green';
                }};

                if (loading) {{
                    return React.createElement('div', {{ 
                        style: {{ 
                            width: '100%', 
                            height: '100vh', 
                            backgroundColor: 'black',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            color: 'white'
                        }}
                    }}, 'Loading debris data...');
                }}

                if (error) {{
                    return React.createElement('div', {{ 
                        style: {{ 
                            width: '100%', 
                            height: '100vh', 
                            backgroundColor: 'black',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            color: 'white'
                        }}
                    }}, `Error: ${{error}}`);
                }}

                return React.createElement('div', {{ 
                    style: {{ width: '100%', height: '100vh', backgroundColor: 'black' }}
                }}, [
                    React.createElement(Canvas, {{ 
                        camera: {{ position: [0, 0, 1000] }}
                    }}, 
                        React.createElement(Suspense, {{ fallback: null }}, [
                            React.createElement(Stars, {{ 
                                radius: 1000, 
                                depth: 50, 
                                count: 5000, 
                                factor: 4, 
                                fade: true 
                            }}),
                            React.createElement(OrbitControls, {{ 
                                enableZoom: true, 
                                enablePan: true, 
                                enableRotate: true 
                            }}),
                            React.createElement('ambientLight', {{ intensity: 0.5 }}),
                            React.createElement('pointLight', {{ position: [10, 10, 10] }}),
                            
                            // Earth
                            React.createElement('mesh', {{ position: [0, 0, 0] }}, [
                                React.createElement('sphereGeometry', {{ args: [6378.137, 32, 32] }}),
                                React.createElement('meshStandardMaterial', {{ 
                                    color: 'blue',
                                    opacity: 0.8,
                                    transparent: true
                                }})
                            ]),
                            
                            // Debris objects
                            ...debris.map(d => 
                                React.createElement('mesh', {{ 
                                    key: d.id, 
                                    position: d.position 
                                }}, [
                                    React.createElement('sphereGeometry', {{ args: [5, 16, 16] }}),
                                    React.createElement('meshStandardMaterial', {{ color: getColorFromRisk(d.risk) }})
                                ])
                            )
                        ])
                    ),
                    
                    // Legend
                    React.createElement('div', {{ 
                        style: {{
                            position: 'absolute',
                            bottom: '20px',
                            right: '20px',
                            backgroundColor: 'rgba(0, 0, 0, 0.7)',
                            padding: '16px',
                            borderRadius: '4px',
                            color: 'white'
                        }}
                    }}, [
                        React.createElement('h3', {{ 
                            style: {{ fontWeight: 'bold', marginBottom: '8px' }} 
                        }}, 'Collision Risk'),
                        
                        React.createElement('div', {{ style: {{ display: 'flex', alignItems: 'center', marginBottom: '4px' }} }}, [
                            React.createElement('div', {{ 
                                style: {{ width: '16px', height: '16px', backgroundColor: 'red', marginRight: '8px' }} 
                            }}),
                            React.createElement('span', {{}}, 'High (>75%)')
                        ]),
                        
                        React.createElement('div', {{ style: {{ display: 'flex', alignItems: 'center', marginBottom: '4px' }} }}, [
                            React.createElement('div', {{ 
                                style: {{ width: '16px', height: '16px', backgroundColor: 'orange', marginRight: '8px' }} 
                            }}),
                            React.createElement('span', {{}}, 'Medium-High (50-75%)')
                        ]),
                        
                        React.createElement('div', {{ style: {{ display: 'flex', alignItems: 'center', marginBottom: '4px' }} }}, [
                            React.createElement('div', {{ 
                                style: {{ width: '16px', height: '16px', backgroundColor: 'yellow', marginRight: '8px' }} 
                            }}),
                            React.createElement('span', {{}}, 'Medium (25-50%)')
                        ]),
                        
                        React.createElement('div', {{ style: {{ display: 'flex', alignItems: 'center', marginBottom: '8px' }} }}, [
                            React.createElement('div', {{ 
                                style: {{ width: '16px', height: '16px', backgroundColor: 'green', marginRight: '8px' }} 
                            }}),
                            React.createElement('span', {{}}, 'Low (<25%)')
                        ]),
                        
                        React.createElement('div', {{ 
                            style: {{ 
                                fontSize: '11px', 
                                opacity: 0.8,
                                marginTop: '4px'
                            }} 
                        }}, `Data source: ${{dataSource}}`)
                    ]),
                    
                    // Data source indicator
                    React.createElement('div', {{ 
                        style: {{
                            position: 'absolute',
                            top: '20px',
                            left: '20px',
                            backgroundColor: 'rgba(0, 0, 0, 0.7)',
                            padding: '8px 12px',
                            borderRadius: '4px',
                            color: 'white',
                            fontSize: '14px'
                        }}
                    }}, `Live Data: ${{celestrakData ? 'Yes' : 'No'}}`)
                ]);
            }}

            // Render the component
            ReactDOM.render(
                React.createElement(SpaceDebrisVisualizer, null),
                document.getElementById('root')
            );
        </script>
    </body>
    </html>
    """
    
    # Render the component in an iframe
    components.html(html, height=600)

if __name__ == "__main__":
    st.title("Space Debris 3D Visualization")
    st.write("This 3D visualization shows space debris based on collision risk data.")
    
    space_debris_3d_visualizer() 