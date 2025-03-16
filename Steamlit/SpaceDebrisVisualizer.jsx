import { Canvas } from '@react-three/fiber';
import { OrbitControls, Stars } from '@react-three/drei';
import { Suspense, useEffect, useState } from 'react';
import * as THREE from 'three';
import csv from 'csvtojson';

export default function SpaceDebrisVisualizer() {
    const [debris, setDebris] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        setLoading(true);
        fetch('/collision_risk_dataset_preprocessed.csv')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to fetch data');
                }
                return response.text();
            })
            .then(data => csv().fromString(data))
            .then(json => {
                const processedDebris = json.map(item => ({
                    position: [
                        parseFloat(item.altitude) * Math.cos(parseFloat(item.raan)),
                        parseFloat(item.altitude) * Math.sin(parseFloat(item.raan)),
                        parseFloat(item.perigee)
                    ],
                    risk: parseFloat(item.collision_risk),
                    id: `debris-${Math.random().toString(36).substr(2, 9)}`
                }));
                setDebris(processedDebris);
                setLoading(false);
            })
            .catch(err => {
                console.error('Error loading debris data:', err);
                setError(err.message);
                setLoading(false);
            });
    }, []);

    const getColorFromRisk = (risk) => {
        if (risk > 0.75) return 'red';
        if (risk > 0.5) return 'orange';
        if (risk > 0.25) return 'yellow';
        return 'green';
    };

    if (loading) {
        return <div className="w-screen h-screen bg-black flex items-center justify-center text-white">Loading debris data...</div>;
    }

    if (error) {
        return <div className="w-screen h-screen bg-black flex items-center justify-center text-white">Error: {error}</div>;
    }

    return (
        <div className="w-screen h-screen bg-black">
            <Canvas camera={{ position: [0, 0, 1000] }}>
                <Suspense fallback={null}>
                    <Stars radius={1000} depth={50} count={5000} factor={4} fade />
                    <OrbitControls enableZoom={true} enablePan={true} enableRotate={true} />
                    <ambientLight intensity={0.5} />
                    <pointLight position={[10, 10, 10]} />
                    
                    {/* Earth */}
                    <mesh position={[0, 0, 0]}>
                        <sphereGeometry args={[50, 32, 32]} />
                        <meshStandardMaterial color="blue" />
                    </mesh>
                    
                    {/* Debris objects */}
                    {debris.map((d) => (
                        <mesh key={d.id} position={d.position}>
                            <sphereGeometry args={[5, 16, 16]} />
                            <meshStandardMaterial color={getColorFromRisk(d.risk)} />
                        </mesh>
                    ))}
                </Suspense>
            </Canvas>
            
            {/* Legend */}
            <div className="absolute bottom-5 right-5 bg-black bg-opacity-70 p-4 rounded text-white">
                <h3 className="font-bold mb-2">Collision Risk</h3>
                <div className="flex items-center mb-1">
                    <div className="w-4 h-4 bg-red-500 mr-2"></div>
                    <span>High (&gt;75%)</span>
                </div>
                <div className="flex items-center mb-1">
                    <div className="w-4 h-4 bg-orange-500 mr-2"></div>
                    <span>Medium-High (50-75%)</span>
                </div>
                <div className="flex items-center mb-1">
                    <div className="w-4 h-4 bg-yellow-500 mr-2"></div>
                    <span>Medium (25-50%)</span>
                </div>
                <div className="flex items-center">
                    <div className="w-4 h-4 bg-green-500 mr-2"></div>
                    <span>Low (&lt;25%)</span>
                </div>
            </div>
        </div>
    );
} 