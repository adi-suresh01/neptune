"use client";

import React, { useRef, useState, useEffect, useMemo } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { OrbitControls, Text, Billboard, Bounds, useBounds } from '@react-three/drei';
import { EffectComposer, Bloom, Vignette } from '@react-three/postprocessing';
import { BlendFunction } from 'postprocessing';
import * as THREE from 'three';
import { Loader2 } from "lucide-react";

// Node component representing a topic in 3D space
const Node = ({ position, label, nodeSize = 2, color = '#4b92ff', selected = false, onClick, id }) => {
  const materialRef = useRef();
  const glowRef = useRef();
  const dragRef = useRef(false);
  const startPosRef = useRef([0, 0]);
  
  const handlePointerDown = (e) => {
    dragRef.current = false;
    startPosRef.current = [e.clientX, e.clientY];
    e.stopPropagation();
  };
  
  const handlePointerUp = (e) => {
    const dx = Math.abs(e.clientX - startPosRef.current[0]);
    const dy = Math.abs(e.clientY - startPosRef.current[1]);
    const isDrag = dx > 3 || dy > 3;
    
    if (!isDrag && !dragRef.current) {
      onClick(id);
    }
    
    e.stopPropagation();
  };
  
  const handlePointerMove = (e) => {
    if (Math.abs(e.clientX - startPosRef.current[0]) > 3 || 
        Math.abs(e.clientY - startPosRef.current[1]) > 3) {
      dragRef.current = true;
    }
  };

  useFrame(({ clock }) => {
    if (materialRef.current) {
      const pulse = Math.sin(clock.getElapsedTime() * 0.8) * 0.05 + 1;
      materialRef.current.emissiveIntensity = selected ? 2.5 : (pulse * 1.5);
    }
    if (glowRef.current) {
      const pulse = Math.sin(clock.getElapsedTime() * 0.8 + Math.PI) * 0.1 + 1;
      glowRef.current.scale.set(pulse * 1.1, pulse * 1.1, pulse * 1.1);
    }
  });

  return (
    <group position={position} 
      onPointerDown={handlePointerDown}
      onPointerUp={handlePointerUp}
      onPointerMove={handlePointerMove}
    >
      <mesh ref={glowRef}>
        <sphereGeometry args={[nodeSize * 1.3, 16, 16]} />
        <meshBasicMaterial 
          color={color} 
          transparent={true} 
          opacity={0.2} 
          blending={THREE.AdditiveBlending} 
        />
      </mesh>
      
      <mesh>
        <sphereGeometry args={[nodeSize, 32, 32]} />
        <meshStandardMaterial 
          ref={materialRef}
          color={color}
          emissive={color}
          emissiveIntensity={selected ? 2.5 : 1.5}
          roughness={0.2}
          metalness={0.8}
        />
      </mesh>
      
      <Billboard follow={true} lockX={false} lockY={false} lockZ={false}>
        <Text
          position={[0, -nodeSize * 1.8, 0]}
          fontSize={nodeSize * 1.2}
          color="white"
          anchorX="center"
          anchorY="middle"
          outlineWidth={0.1}
          outlineColor="#000000"
          outlineOpacity={0.8}
        >
          {label}
        </Text>
      </Billboard>
    </group>
  );
};

// Edge component - same as your existing implementation
const Edge = ({ start, end, strength = 0.5 }) => {
  const lineRef = useRef();
  const particlesRef = useRef();
  const lineGeometryRef = useRef();
  
  const particleCount = Math.floor(100 * Math.max(0.3, strength));
  
  const points = useMemo(() => {
    const startVec = new THREE.Vector3(start[0], start[1], start[2]);
    const endVec = new THREE.Vector3(end[0], end[1], end[2]);
    
    const midPoint = new THREE.Vector3().lerpVectors(startVec, endVec, 0.5);
    const distance = startVec.distanceTo(endVec);
    midPoint.y += 2 * (1 - strength) * Math.min(10, distance/10); 
    
    const curve = new THREE.QuadraticBezierCurve3(startVec, midPoint, endVec);
    return curve.getPoints(20);
  }, [start, end, strength]);
  
  const particlePositions = useMemo(() => {
    const positions = new Float32Array(particleCount * 3);
    const curve = new THREE.QuadraticBezierCurve3(
      new THREE.Vector3(start[0], start[1], start[2]),
      new THREE.Vector3(
        (start[0] + end[0]) / 2,
        ((start[1] + end[1]) / 2) + 2 * (1 - strength) * Math.min(10, 
        Math.sqrt(Math.pow(end[0]-start[0], 2) + Math.pow(end[1]-start[1], 2) + Math.pow(end[2]-start[2], 2))/10),
        (start[2] + end[2]) / 2
      ),
      new THREE.Vector3(end[0], end[1], end[2])
    );
    
    for (let i = 0; i < particleCount; i++) {
      const t = i / particleCount;
      const point = curve.getPoint(t);
      positions[i * 3] = point.x;
      positions[i * 3 + 1] = point.y;
      positions[i * 3 + 2] = point.z;
    }
    
    return positions;
  }, [start, end, particleCount, strength]);
  
  const particleSizes = useMemo(() => {
    const sizes = new Float32Array(particleCount);
    for (let i = 0; i < particleCount; i++) {
      sizes[i] = Math.random() * 2.5 * strength + 0.8;
    }
    return sizes;
  }, [particleCount, strength]);
  
  const particleColors = useMemo(() => {
    const colors = new Float32Array(particleCount * 3);
    for (let i = 0; i < particleCount; i++) {
      const t = Math.random();
      colors[i * 3] = 0.7 + 0.3 * t;
      colors[i * 3 + 1] = 0.7 + 0.3 * t;
      colors[i * 3 + 2] = 1.0;
    }
    return colors;
  }, [particleCount]);
  
  useFrame(({ clock }) => {
    if (particlesRef.current && lineGeometryRef.current) {
      const time = clock.getElapsedTime() * Math.max(0.4, strength);
      const positions = particlesRef.current.attributes.position.array;
      const sizes = particlesRef.current.attributes.size.array;
      
      if (lineRef.current) {
        const pulse = Math.sin(time * 2) * 0.2 + 0.8;
        lineRef.current.material.opacity = Math.max(0.2, pulse * strength);
      }
      
      const waveSpeed = time * 1.5;
      const waveWidth = 0.1;
      
      for (let i = 0; i < particleCount; i++) {
        const baseT = ((i / particleCount) + (time * 0.2)) % 1;
        const t = baseT;
        
        const point = new THREE.Vector3();
        const curve = new THREE.QuadraticBezierCurve3(
          new THREE.Vector3(start[0], start[1], start[2]),
          new THREE.Vector3(
            (start[0] + end[0]) / 2,
            ((start[1] + end[1]) / 2) + 2 * (1 - strength) * 
              Math.min(10, Math.sqrt(Math.pow(end[0]-start[0], 2) + 
              Math.pow(end[1]-start[1], 2) + Math.pow(end[2]-start[2], 2))/10),
            (start[2] + end[2]) / 2
          ),
          new THREE.Vector3(end[0], end[1], end[2])
        );
        
        point.copy(curve.getPoint(t));
        
        const jitter = 0.2;
        point.x += (Math.random() - 0.5) * jitter * strength;
        point.y += (Math.random() - 0.5) * jitter * strength;
        point.z += (Math.random() - 0.5) * jitter * strength;
        
        positions[i * 3] = point.x;
        positions[i * 3 + 1] = point.y;
        positions[i * 3 + 2] = point.z;
        
        const wave = Math.sin((baseT * 10 + waveSpeed) * Math.PI * 2);
        const waveInfluence = Math.max(0, 1 - Math.abs(wave) / waveWidth);
        
        sizes[i] = Math.random() * 1.5 * strength + 0.5 + waveInfluence * 2.5;
      }
      
      particlesRef.current.attributes.position.needsUpdate = true;
      particlesRef.current.attributes.size.needsUpdate = true;
    }
  });
  
  return (
    <group>
      <line ref={lineRef}>
        <bufferGeometry ref={lineGeometryRef}>
          <bufferAttribute
            attach="attributes-position"
            count={points.length}
            array={new Float32Array(points.flatMap(p => [p.x, p.y, p.z]))}
            itemSize={3}
          />
        </bufferGeometry>
        <lineBasicMaterial 
          color={strength > 0.7 ? "#ffffff" : "#73a7ff"}
          transparent
          opacity={Math.max(0.3, strength * 0.9)}
          linewidth={1}
          blending={THREE.AdditiveBlending}
        />
      </line>
      
      <line>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            count={points.length}
            array={new Float32Array(points.flatMap(p => [p.x, p.y, p.z]))}
            itemSize={3}
          />
        </bufferGeometry>
        <lineBasicMaterial 
          color="#ffffff"
          transparent
          opacity={0.6}
          linewidth={1}
          blending={THREE.AdditiveBlending}
        />
      </line>
      
      <points>
        <bufferGeometry ref={particlesRef}>
          <bufferAttribute
            attach="attributes-position"
            count={particleCount}
            array={particlePositions}
            itemSize={3}
          />
          <bufferAttribute
            attach="attributes-size"
            count={particleCount}
            array={particleSizes}
            itemSize={1}
          />
          <bufferAttribute
            attach="attributes-color"
            count={particleCount}
            array={particleColors}
            itemSize={3}
          />
        </bufferGeometry>
        <pointsMaterial
          size={2}
          vertexColors
          transparent
          opacity={Math.min(1.0, strength * 2)}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
          sizeAttenuation
        />
      </points>
    </group>
  );
};

// GraphScene component
const GraphScene = ({ data, onSelectNode }) => {
  const [selectedNode, setSelectedNode] = useState(null);
  const { scene, camera } = useThree();
  
  useEffect(() => {
    scene.background = new THREE.Color('#050A1C');
  }, [scene]);
  
  const focusOnNode = (position) => {
    if (!position) return;
    
    const target = new THREE.Vector3(position[0], position[1], position[2]);
    const start = new THREE.Vector3().copy(camera.position);
    
    const duration = 1000;
    const startTime = Date.now();
    
    function animate() {
      const now = Date.now();
      const progress = Math.min((now - startTime) / duration, 1);
      const easeProgress = progress < 0.5 ? 2 * progress * progress : -1 + (4 - 2 * progress) * progress;
      
      const distance = 30;
      const direction = new THREE.Vector3().copy(target).sub(camera.position).normalize();
      const targetPosition = new THREE.Vector3().copy(target).sub(direction.multiplyScalar(distance));
      
      camera.position.lerpVectors(start, targetPosition, easeProgress);
      camera.lookAt(target);
      
      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    }
    
    animate();
  };
  
  const handleNodeClick = (nodeId) => {
    setSelectedNode(nodeId === selectedNode ? null : nodeId);
    
    if (nodeId !== selectedNode) {
      const node = data.nodes.find(n => n.id === nodeId);
      
      if (node && node.position) {
        focusOnNode(node.position);
      }
      
      if (onSelectNode) {
        onSelectNode(nodeId);
      }
    }
  };

  return (
    <group>
      <ambientLight intensity={0.2} />
      <directionalLight position={[10, 10, 5]} intensity={0.7} />
      
      <Stars />
      
      {data.nodes.map((node) => (
        <Node
          key={node.id}
          id={node.id}
          position={node.position}
          label={node.label}
          nodeSize={(node.size / 50) + 1}
          selected={selectedNode === node.id}
          onClick={handleNodeClick}
        />
      ))}
      
      {data.links.map((link, index) => {
        const sourceNode = data.nodes.find(n => n.id === link.source);
        const targetNode = data.nodes.find(n => n.id === link.target);
        
        if (!sourceNode || !targetNode) return null;
        
        return (
          <Edge
            key={`edge-${index}`}
            start={sourceNode.position}
            end={targetNode.position}
            strength={link.strength}
          />
        );
      })}
      
      <EffectComposer>
        <Bloom 
          luminanceThreshold={0.1}
          luminanceSmoothing={0.9} 
          intensity={1.8}
          mipmapBlur
        />
        <Vignette
          offset={0.3}
          darkness={0.8}
          eskil={false}
          blendFunction={BlendFunction.NORMAL}
        />
      </EffectComposer>
    </group>
  );
};

// Background stars component
const Stars = () => {
  const particlesRef = useRef();
  const count = 5000;
  
  const positions = useMemo(() => {
    const positions = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      const distance = Math.random() * 400 + 100;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.random() * Math.PI * 2;
      
      positions[i * 3] = distance * Math.sin(phi) * Math.cos(theta);
      positions[i * 3 + 1] = distance * Math.sin(phi) * Math.sin(theta);
      positions[i * 3 + 2] = distance * Math.cos(phi);
    }
    return positions;
  }, [count]);
  
  useFrame(({ clock }) => {
    if (particlesRef.current) {
      particlesRef.current.rotation.y = clock.getElapsedTime() * 0.02;
      particlesRef.current.rotation.z = clock.getElapsedTime() * 0.01;
    }
  });
  
  return (
    <points ref={particlesRef}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={count}
          array={positions}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial
        size={1.5}
        color="#ffffff"
        transparent
        opacity={0.7}
        blending={THREE.AdditiveBlending}
        sizeAttenuation={false}
      />
    </points>
  );
};

// Main Knowledge Graph component
function KnowledgeGraph() {
  const [data, setData] = useState({ nodes: [], links: [] });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  // Process fetched data to add positions to nodes
  const processGraphData = (data) => {
    if (!data.nodes || data.nodes.length === 0) {
      return { nodes: [], links: [] };
    }

    const nodes = data.nodes.map((node, index) => {
      const phi = Math.acos(-1 + (2 * index) / data.nodes.length);
      const theta = Math.sqrt(data.nodes.length * Math.PI) * phi;
      
      const radius = 50;
      const x = radius * Math.cos(theta) * Math.sin(phi);
      const y = radius * Math.sin(theta) * Math.sin(phi);
      const z = radius * Math.cos(phi);
      
      return {
        ...node,
        position: [x, y, z],
        // Use proper fallback for size
        size: node.size || (node.note_ids && node.note_ids.length * 20) || 30,
        // Ensure we have a proper label
        label: node.topic || node.label || 'Unknown Topic'
      };
    });
    
    return { nodes, links: data.links || [] };
  };

  // Fetch knowledge graph data from backend
  const fetchKnowledgeGraph = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      console.log('Fetching knowledge graph...');
      const response = await fetch('http://localhost:8000/api/knowledge-graph');
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const rawData = await response.json();
      console.log('Raw graph data:', rawData);
      
      // Process data to add 3D positions
      const processedData = processGraphData(rawData);
      console.log('Processed graph data:', processedData);
      
      setData(processedData);
    } catch (err) {
      console.error("Error fetching knowledge graph:", err);
      setError(err instanceof Error ? err.message : "Failed to load knowledge graph");
    } finally {
      setIsLoading(false);
    }
  };

  // Refresh the graph data
  const handleRefreshGraph = async () => {
    try {
      setRefreshing(true);
      console.log('Refreshing knowledge graph...');
      
      const response = await fetch('http://localhost:8000/api/knowledge-graph/refresh', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const rawData = await response.json();
      console.log('Refreshed graph data:', rawData);
      
      const processedData = processGraphData(rawData);
      setData(processedData);
    } catch (err) {
      console.error("Error refreshing knowledge graph:", err);
      setError(err instanceof Error ? err.message : "Failed to refresh graph");
    } finally {
      setRefreshing(false);
    }
  };

  // Load data on component mount
  useEffect(() => {
    fetchKnowledgeGraph();
  }, []);

  // Handle node selection
  const handleSelectNode = (nodeId) => {
    console.log(`Selected node: ${nodeId}`);
    // Future: Show related notes or additional info
  };

  // Show loading state
  if (isLoading) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-[#050a1c]">
        <Loader2 className="w-8 h-8 animate-spin text-blue-400" />
        <span className="ml-2 text-blue-400">Loading knowledge graph...</span>
      </div>
    );
  }

  // Show error state
  if (error) {
    return (
      <div className="w-full h-full flex flex-col items-center justify-center bg-[#050a1c] text-red-400">
        <p>Error loading knowledge graph: {error}</p>
        <div className="mt-4 space-x-4">
          <button 
            className="px-4 py-2 bg-blue-900 text-white rounded hover:bg-blue-800 transition"
            onClick={fetchKnowledgeGraph}
          >
            Retry
          </button>
          <button 
            className="px-4 py-2 bg-green-900 text-white rounded hover:bg-green-800 transition"
            onClick={handleRefreshGraph}
          >
            Force Refresh
          </button>
        </div>
      </div>
    );
  }

  // Show empty state
  if (!data.nodes || data.nodes.length === 0) {
    return (
      <div className="w-full h-full flex flex-col items-center justify-center bg-[#050a1c] text-gray-400">
        <p>No knowledge graph available</p>
        <p className="text-sm mt-2">Add some notes to generate your knowledge map</p>
        <button 
          className="mt-4 px-4 py-2 bg-blue-900 text-white rounded hover:bg-blue-800 transition"
          onClick={handleRefreshGraph}
          disabled={refreshing}
        >
          {refreshing ? 'Generating...' : 'Generate Graph'}
        </button>
      </div>
    );
  }

  return (
    <div className="w-full h-screen bg-[#050a1c] relative">
      {/* Control buttons */}
      <div className="absolute top-4 right-4 z-10 space-x-2">
        <button
          onClick={handleRefreshGraph}
          disabled={refreshing}
          className="px-3 py-1 bg-blue-700 rounded text-sm text-white hover:bg-blue-600 transition disabled:opacity-50"
        >
          {refreshing ? 'Refreshing...' : 'Refresh Graph'}
        </button>
        <div className="text-xs text-gray-400 mt-1">
          {data.nodes.length} topics, {data.links.length} connections
        </div>
      </div>
      
      {/* Three.js canvas */}
      <Canvas 
        camera={{ 
          position: [0, 0, 100], 
          fov: 60, 
          near: 1,
          far: 1000
        }}
        style={{ background: '#050a1c' }}
      >
        <OrbitControls 
          enablePan={true}
          enableZoom={true}
          enableRotate={true}
          minDistance={20}
          maxDistance={200}
        />
        <GraphScene 
          data={data} 
          onSelectNode={handleSelectNode} 
        />
      </Canvas>
    </div>
  );
}

export default KnowledgeGraph;