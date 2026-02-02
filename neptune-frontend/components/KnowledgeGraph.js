"use client";

import React, { useRef, useState, useEffect, useMemo } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { OrbitControls, Text, Billboard } from '@react-three/drei';
import { EffectComposer, Bloom, Vignette } from '@react-three/postprocessing';
import { BlendFunction } from 'postprocessing';
import * as THREE from 'three';
import { Loader2, RefreshCw, Zap, Network } from "lucide-react";
import { api } from "@/lib/api";

const HoverPopup = ({ topic, relatedNotes, position, onNoteClick, onMouseEnter, onMouseLeave }) => {
  if (!topic || !relatedNotes || relatedNotes.length === 0) return null;

  const maxHeight = window.innerHeight * 0.6;
  
  const leftPos = Math.min(position.x + 15, window.innerWidth - 400);
  const topPos = Math.max(10, Math.min(position.y - 10, window.innerHeight - Math.min(400, maxHeight)));
  
  const popupStyle = {
    position: 'fixed',
    left: `${leftPos}px`,
    top: `${topPos}px`,
    backgroundColor: 'rgba(0, 0, 0, 0.95)',
    border: '1px solid #444',
    borderRadius: '8px',
    padding: '12px',
    minWidth: '280px',
    maxWidth: '400px',
    maxHeight: `${maxHeight}px`,
    zIndex: 1000,
    color: 'white',
    fontSize: '12px',
    backdropFilter: 'blur(10px)',
    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)',
    pointerEvents: 'auto',
    overflow: 'hidden',
    display: 'flex',
    flexDirection: 'column'
  };

  const headerStyle = {
    fontWeight: 'bold',
    marginBottom: '8px',
    color: '#60a5fa',
    borderBottom: '1px solid #444',
    paddingBottom: '4px',
    fontSize: '13px',
    flexShrink: 0
  };

  const scrollableContentStyle = {
    maxHeight: `${maxHeight - 80}px`,
    overflowY: 'auto',
    overflowX: 'hidden',
    paddingRight: '4px',
    scrollbarWidth: 'thin',
    scrollbarColor: '#444 transparent'
  };

  const noteItemStyle = {
    padding: '8px',
    margin: '2px 0',
    cursor: 'pointer',
    borderRadius: '4px',
    transition: 'background-color 0.2s',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: '8px'
  };

  const strengthBadgeStyle = (strength) => ({
    backgroundColor: `rgba(96, 165, 250, ${strength})`,
    color: strength > 0.5 ? 'white' : 'black',
    padding: '2px 6px',
    borderRadius: '12px',
    fontSize: '10px',
    fontWeight: 'bold',
    minWidth: '35px',
    textAlign: 'center',
    flexShrink: 0
  });

  return (
    <div 
      style={popupStyle}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
      onMouseDown={(e) => e.stopPropagation()}
      onMouseUp={(e) => e.stopPropagation()}
      onMouseMove={(e) => e.stopPropagation()}
    >
      <div style={headerStyle}>
        Related Notes for {topic}
      </div>
      
      <div style={{ fontSize: '11px', color: '#888', marginBottom: '6px', flexShrink: 0 }}>
        {relatedNotes.length} note{relatedNotes.length !== 1 ? 's' : ''} found
        {relatedNotes.length > 5 && <span style={{ color: '#60a5fa' }}> • Scroll to see all</span>}
      </div>
      
      <div style={scrollableContentStyle}>
        {relatedNotes.map((note, index) => (
          <div
            key={`${note.id}-${index}`}
            style={{
              ...noteItemStyle,
              backgroundColor: index % 2 === 0 ? 'rgba(255, 255, 255, 0.05)' : 'transparent'
            }}
            onMouseEnter={(e) => {
              e.stopPropagation();
              e.currentTarget.style.backgroundColor = 'rgba(96, 165, 250, 0.2)';
            }}
            onMouseLeave={(e) => {
              e.stopPropagation();
              e.currentTarget.style.backgroundColor = index % 2 === 0 ? 'rgba(255, 255, 255, 0.05)' : 'transparent';
            }}
            onClick={(e) => {
              e.stopPropagation();
              onNoteClick(note.id);
            }}
          >
            <span style={{ fontWeight: '500', flex: 1 }}>{note.name}</span>
            <span style={strengthBadgeStyle(note.strength)}>
              {(note.strength * 100).toFixed(0)}%
            </span>
          </div>
        ))}
      </div>
      
      {relatedNotes.length > 5 && (
        <div style={{ 
          fontSize: '9px', 
          color: '#666', 
          textAlign: 'center', 
          marginTop: '4px',
          flexShrink: 0 
        }}>
          ↕ Scroll for more
        </div>
      )}
    </div>
  );
};

const Node = ({ position, label, nodeSize = 2, color = '#4b92ff', selected = false, onClick, id, onHover, onHoverEnd }) => {
  const meshRef = useRef();
  const [hovered, setHovered] = useState(false);

  useFrame((state, delta) => {
    if (meshRef.current) {
      meshRef.current.rotation.x += delta * 0.2;
      meshRef.current.rotation.y += delta * 0.3;
    }
  });

  const handlePointerOver = (event) => {
    event.stopPropagation();
    setHovered(true);
    document.body.style.cursor = 'pointer';
    if (onHover) {
      onHover(label, {
        x: event.clientX,
        y: event.clientY
      });
    }
  };

  const handlePointerOut = (event) => {
    event.stopPropagation();
    setHovered(false);
    document.body.style.cursor = 'auto';
    if (onHoverEnd) {
      setTimeout(() => {
        onHoverEnd();
      }, 300);
    }
  };

  const handleClick = (event) => {
    event.stopPropagation();
    if (onClick) {
      onClick(id);
    }
  };

  return (
    <group position={position}>
      <mesh
        ref={meshRef}
        onClick={handleClick}
        onPointerOver={handlePointerOver}
        onPointerOut={handlePointerOut}
      >
        <sphereGeometry args={[nodeSize, 32, 32]} />
        <meshStandardMaterial 
          color={hovered ? '#ffffff' : color}
          emissive={hovered ? '#444444' : '#222222'}
          emissiveIntensity={selected ? 0.6 : (hovered ? 0.4 : 0.1)}
          transparent
          opacity={0.9}
        />
      </mesh>
      <Billboard follow={true} lockX={false} lockY={false} lockZ={false}>
        <Text
          position={[0, nodeSize + 1, 0]}
          fontSize={Math.max(1.5, nodeSize * 0.8)}
          color={hovered ? '#ffffff' : '#e2e8f0'}
          anchorX="center"
          anchorY="middle"
          outlineWidth={0.1}
          outlineColor="#000000"
        >
          {label}
        </Text>
      </Billboard>
    </group>
  );
};

const Edge = ({ start, end, strength = 0.5 }) => {
  const coreRef = useRef();
  const glowRef = useRef();
  
  const startVec = useMemo(() => new THREE.Vector3(start[0], start[1], start[2]), [start]);
  const endVec = useMemo(() => new THREE.Vector3(end[0], end[1], end[2]), [end]);
  
  const { position, rotation, length } = useMemo(() => {
    const direction = new THREE.Vector3().subVectors(endVec, startVec);
    const length = direction.length();
    const position = new THREE.Vector3().addVectors(startVec, endVec).multiplyScalar(0.5);
    
    const axis = new THREE.Vector3(0, 1, 0);
    const quaternion = new THREE.Quaternion().setFromUnitVectors(axis, direction.normalize());
    const rotation = new THREE.Euler().setFromQuaternion(quaternion);
    
    return { position, rotation, length };
  }, [startVec, endVec]);

  useFrame(({ clock }) => {
    const time = clock.getElapsedTime();
    const pulse = Math.sin(time * 3) * 0.1 + 0.9;
    
    if (coreRef.current) {
      const baseOpacity = Math.max(0.3, strength);
      coreRef.current.material.opacity = baseOpacity * pulse;
      
      const baseEmissive = Math.max(0.2, strength * 0.8);
      coreRef.current.material.emissiveIntensity = baseEmissive * pulse;
    }
    
    if (glowRef.current) {
      const glowOpacity = Math.max(0.1, strength * 0.5);
      glowRef.current.material.opacity = glowOpacity * pulse;
      
      const glowEmissive = Math.max(0.05, strength * 0.3);
      glowRef.current.material.emissiveIntensity = glowEmissive * pulse;
    }
  });

  const laserColor = '#8b5cf6';
  const coreRadius = Math.max(0.03, strength * 0.12);
  const glowRadius = coreRadius * 2.5;

  return (
    <group position={[position.x, position.y, position.z]} rotation={[rotation.x, rotation.y, rotation.z]}>
      <mesh ref={coreRef}>
        <cylinderGeometry args={[coreRadius, coreRadius, length, 6]} />
        <meshStandardMaterial
          color={laserColor}
          emissive={laserColor}
          emissiveIntensity={Math.max(0.2, strength * 0.8)}
          transparent
          opacity={Math.max(0.3, strength)}
          toneMapped={false}
        />
      </mesh>
      
      <mesh ref={glowRef}>
        <cylinderGeometry args={[glowRadius, glowRadius, length, 8]} />
        <meshStandardMaterial
          color={laserColor}
          emissive={laserColor}
          emissiveIntensity={Math.max(0.05, strength * 0.3)}
          transparent
          opacity={Math.max(0.1, strength * 0.5)}
          toneMapped={false}
          blending={THREE.AdditiveBlending}
        />
      </mesh>
    </group>
  );
};

const GraphScene = ({ data, onSelectNode, onNodeHover, onNodeHoverEnd }) => {
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
      
      {data.nodes.map((node) => (
        <Node
          key={node.id}
          id={node.id}
          position={node.position}
          label={node.label}
          nodeSize={(node.size / 50) + 1}
          selected={selectedNode === node.id}
          onClick={handleNodeClick}
          onHover={onNodeHover}
          onHoverEnd={onNodeHoverEnd}
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

// Main Knowledge Graph component
function KnowledgeGraph({ onSelectNote }) {
  const [data, setData] = useState({ nodes: [], links: [] });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [, setCacheStatus] = useState({ cached: false, fresh: false });
  const [generationStatus, setGenerationStatus] = useState({ is_generating: false, progress: "idle" });

  const [hoveredNode, setHoveredNode] = useState(null);
  const [hoverPosition, setHoverPosition] = useState({ x: 0, y: 0 });
  const [relatedNotes, setRelatedNotes] = useState([]);
  const [hoverTimeout, setHoverTimeout] = useState(null);
  const [isPopupHovered, setIsPopupHovered] = useState(false);

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
        size: node.size || (node.note_ids && node.note_ids.length * 20) || 30,
        label: node.topic || node.label || 'Unknown Topic'
      };
    });
    
    return { nodes, links: data.links || [] };
  };

  const fetchKnowledgeGraph = async (force = false) => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await api.knowledgeGraph.get();
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const rawData = await response.json();
      
      if (rawData.nodes && rawData.nodes.length > 0) {
        const processedData = processGraphData(rawData);
        setData(processedData);
        setCacheStatus({ cached: true, fresh: !force });
      } else if (force) {
        await handleRefreshGraph();
      } else {
        setData({ nodes: [], links: [] });
        setCacheStatus({ cached: false, fresh: false });
      }
      
    } catch (err) {
      console.error("Error fetching knowledge graph:", err);
      setError(err instanceof Error ? err.message : "Failed to load knowledge graph");
    } finally {
      setIsLoading(false);
    }
  };

  const handleRefreshGraph = async () => {
    try {
      setRefreshing(true);
      const response = await api.knowledgeGraph.refresh();
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const result = await response.json();
      
      if (result.generating) {
        setGenerationStatus({ is_generating: true, progress: "starting" });
      }
      
    } catch (err) {
      console.error("Error starting background generation:", err);
      setError(err instanceof Error ? err.message : "Failed to start generation");
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    const loadGraph = async () => {
      await fetchKnowledgeGraph(false);
    };
    loadGraph();
  }, []);

  useEffect(() => {
    let statusInterval;
    
    if (generationStatus.is_generating) {
      statusInterval = setInterval(async () => {
        try {
          const response = await api.knowledgeGraph.status();
          const status = await response.json();
          
          setGenerationStatus(status.generation_status || { is_generating: false, progress: "idle" });
          
          if (!status.generation_status.is_generating && status.has_cached_graph) {
            fetchKnowledgeGraph(false);
          }
        } catch (err) {
          console.error("Error checking status:", err);
        }
      }, 2000);
    }
    
    return () => {
      if (statusInterval) clearInterval(statusInterval);
    };
  }, [generationStatus.is_generating]);

  const handleSelectNode = () => {};

  const handleNodeHover = async (topicName, position) => {
    if (hoverTimeout) {
      clearTimeout(hoverTimeout);
      setHoverTimeout(null);
    }

    setHoveredNode(topicName);
    setHoverPosition(position);

    const topicNode = data.nodes.find(node => node.topic === topicName || node.label === topicName);
    if (!topicNode) {
      setRelatedNotes([]);
      return;
    }

    let directNotes = (topicNode.noteDetails || []).map((note) => ({
      id: note.id,
      name: note.name,
      strength: 1.0,
    }));
    if (directNotes.length === 0 && topicNode.noteIds && topicNode.noteIds.length > 0) {
      directNotes = topicNode.noteIds.map((noteId) => ({
        id: noteId,
        name: `Note ${noteId}`,
        strength: 1.0,
      }));
    }

    const noteIds = (topicNode.noteDetails || []).map((note) => note.id).length
      ? (topicNode.noteDetails || []).map((note) => note.id)
      : (topicNode.noteIds || []);

    const primaryNoteId = noteIds && noteIds.length > 0 ? Number(noteIds[0]) : null;
    if (!primaryNoteId || Number.isNaN(primaryNoteId)) {
      setRelatedNotes(directNotes);
      return;
    }

    try {
      const response = await api.embeddings.related(primaryNoteId, 12);
      if (response.ok) {
        const payload = await response.json();
        const related = (payload.results || []).map((note) => ({
          id: note.id,
          name: note.name,
          strength: note.score,
        }));
        const merged = new Map();
        for (const item of directNotes) merged.set(item.id, item);
        for (const item of related) merged.set(item.id, item);
        setRelatedNotes(Array.from(merged.values()));
        return;
      }
    } catch {
      // Ignore and fall back to direct notes.
    }

    setRelatedNotes(directNotes);
  };

  const handleNodeHoverEnd = () => {
    if (!isPopupHovered) {
      const timeout = setTimeout(() => {
        if (!isPopupHovered) {
          setHoveredNode(null);
          setRelatedNotes([]);
        }
      }, 500);
      
      setHoverTimeout(timeout);
    }
  };

  const handlePopupMouseEnter = () => {
    setIsPopupHovered(true);
    if (hoverTimeout) {
      clearTimeout(hoverTimeout);
      setHoverTimeout(null);
    }
  };

  const handlePopupMouseLeave = () => {
    setIsPopupHovered(false);
    const timeout = setTimeout(() => {
      setHoveredNode(null);
      setRelatedNotes([]);
    }, 200);
    
    setHoverTimeout(timeout);
  };

  const handleNoteClick = (noteId) => {
    setHoveredNode(null);
    setRelatedNotes([]);
    
    if (onSelectNote) {
      onSelectNote(noteId);
    }
  };

  // Show loading state
  if (isLoading) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-[#050a1c]">
        <div className="flex flex-col items-center space-y-4">
          <Loader2 className="w-8 h-8 animate-spin text-blue-400" />
          <span className="text-blue-400">Loading your knowledge graph...</span>
        </div>
      </div>
    );
  }

  // Show error state
  if (error) {
    return (
      <div className="w-full h-full flex flex-col items-center justify-center bg-[#050a1c] text-red-400">
        <p className="mb-4">Error loading knowledge graph: {error}</p>
        <div className="space-x-4">
          <button 
            className="px-4 py-2 bg-blue-900 text-white rounded hover:bg-blue-800 transition"
            onClick={() => fetchKnowledgeGraph(false)}
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
        <Network className="w-16 h-16 mb-4 text-gray-500" />
        <p className="text-lg mb-2">No knowledge graph available</p>
        <p className="text-sm mb-4">Add some notes to generate your knowledge map</p>
        <button 
          className="px-6 py-3 bg-blue-900 text-white rounded-lg hover:bg-blue-800 transition flex items-center space-x-2"
          onClick={handleRefreshGraph}
          disabled={refreshing}
        >
          {refreshing ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Generating...</span>
            </>
          ) : (
            <>
              <Zap className="w-4 h-4" />
              <span>Generate Knowledge Graph</span>
            </>
          )}
        </button>
      </div>
    );
  }

  return (
    <div className="w-full h-full bg-[#050a1c] relative">
      <div className="absolute top-4 right-4 z-10 space-x-2">
        <button
          onClick={handleRefreshGraph}
          disabled={refreshing}
          className="px-3 py-1 bg-blue-700 rounded text-sm text-white hover:bg-blue-600 transition disabled:opacity-50 flex items-center space-x-1"
        >
          <RefreshCw className={`w-3 h-3 ${refreshing ? 'animate-spin' : ''}`} />
          <span>{refreshing ? 'Refreshing...' : 'Refresh'}</span>
        </button>
      </div>
      
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
          onNodeHover={handleNodeHover}
          onNodeHoverEnd={handleNodeHoverEnd}
        />
      </Canvas>

      {hoveredNode && relatedNotes.length > 0 && (
        <HoverPopup
          topic={hoveredNode}
          relatedNotes={relatedNotes}
          position={hoverPosition}
          onNoteClick={handleNoteClick}
          onMouseEnter={handlePopupMouseEnter}
          onMouseLeave={handlePopupMouseLeave}
        />
      )}
    </div>
  );
}

export default KnowledgeGraph;
