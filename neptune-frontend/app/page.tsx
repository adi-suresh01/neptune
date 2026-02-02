"use client";

import type React from "react";
import { useState, useEffect } from "react";
import FileSystemDisplay from "@/components/FileSystemDisplay";
import NotesDisplay from "@/components/NotesDisplay";
import KnowledgeGraph from "@/components/KnowledgeGraph";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { EarthIcon as PlanetIcon, FileText, Network, Trash2, Plus, Loader2, AlertTriangle } from "lucide-react";
import { api, checkBackendHealth } from "@/lib/api";

export interface FileSystemItem {
  id: number;
  name: string;
  type: string;
  parent_id: number | null;
  content?: string;
  children?: FileSystemItem[];
}

export interface SelectedItem {
  id: number;
  type: string;
  name?: string;
}

const Home = () => {
  const [showFileForm, setShowFileForm] = useState(false);
  const [file, setFile] = useState("");
  
  // Default to showing graph first
  const [showGraph, setShowGraph] = useState(true);
  const [showNotes, setShowNotes] = useState(false);
  
  // Backend connection state
  const [backendReady, setBackendReady] = useState(false);
  const [backendError, setBackendError] = useState<string | null>(null);
  const [isCheckingBackend, setIsCheckingBackend] = useState(true);

  const [, setParent] = useState(0);
  const [refreshKey, setRefreshKey] = useState(0);
  const [selectedItem, setSelectedItem] = useState<SelectedItem | null>(null);

  // Check backend health on startup
  useEffect(() => {
    let attempts = 0;
    const maxAttempts = 15;
    
    const checkBackend = async () => {
      attempts++;
      setIsCheckingBackend(true);
      
      try {
        const isHealthy = await checkBackendHealth();
        
        if (isHealthy) {
          setBackendReady(true);
          setBackendError(null);
          setIsCheckingBackend(false);
          return;
        }
        
        if (attempts >= maxAttempts) {
          setBackendError(`Backend not available after ${maxAttempts} attempts`);
          setIsCheckingBackend(false);
          return;
        }
        
        setTimeout(checkBackend, 3000);
        
      } catch (error) {
        if (attempts >= maxAttempts) {
          setBackendError('Failed to connect to Neptune backend');
          setIsCheckingBackend(false);
        } else {
          setTimeout(checkBackend, 3000);
        }
      }
    };
    
    checkBackend();
  }, []);

  const refreshFileSystem = () => {
    setRefreshKey((prev) => prev + 1);
  };

  const handleAddFile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file.trim()) return;

    const id = generateRandomId();
    try {
      const res = await api.filesystem.create({
        name: file,
        type: "file",
        parent_id: null,
      });

      if (!res.ok) throw new Error("Failed to create file");

      refreshFileSystem();
    } catch (err) {
      console.error("Error creating file:", err);
    }
    setFile("");
    setShowFileForm(false);
  };

  const handleDeleteFile = async (fileId: number) => {
    if (!fileId) return;
    
    const confirmDelete = window.confirm("Are you sure you want to delete this file? This action cannot be undone.");
    if (!confirmDelete) return;

    try {
      const res = await api.filesystem.delete(fileId);

      if (!res.ok) throw new Error("Failed to delete file");

      if (selectedItem && selectedItem.id === fileId) {
        setSelectedItem(null);
        setShowGraph(true);
        setShowNotes(false);
      }

      refreshFileSystem();
    } catch (err) {
      console.error("Error deleting file:", err);
      alert("Failed to delete file. Please try again.");
    }
  };

  const handleItemClick = (item: FileSystemItem) => {
    setSelectedItem({
      id: item.id,
      type: item.type,
      name: item.name,
    });

    if (item.type === "file") {
      setShowGraph(false);
      setShowNotes(true);
    }
  };

  const handleDisplayGraph = () => {
    setShowGraph(!showGraph);
    setShowNotes(!showNotes);
  };

  const showKnowledgeGraph = () => {
    setShowGraph(true);
    setShowNotes(false);
  };

  const showNotesView = () => {
    setShowGraph(false);
    setShowNotes(true);
  };

  const handleNoteSelectionFromGraph = (noteId: number) => {
    setSelectedItem({
      id: noteId,
      type: "file"
    });
    
    setShowGraph(false);
    setShowNotes(true);
    
  };

  // Show backend loading state
  if (isCheckingBackend) {
    return (
      <div className="flex h-screen bg-gray-900 text-gray-100 pt-7">
        <div className="flex-1 flex items-center justify-center">
          <div className="flex flex-col items-center space-y-4">
            <Loader2 className="w-8 h-8 animate-spin text-blue-400" />
            <h2 className="text-xl font-semibold text-white">Starting Neptune...</h2>
            <p className="text-gray-400">Please wait while the backend initializes</p>
          </div>
        </div>
      </div>
    );
  }

  // Show backend error state
  if (backendError) {
    return (
      <div className="flex h-screen bg-gray-900 text-gray-100 pt-7">
        <div className="flex-1 flex items-center justify-center">
          <div className="flex flex-col items-center space-y-4 max-w-md text-center">
            <AlertTriangle className="w-12 h-12 text-red-400" />
            <h2 className="text-xl font-semibold text-red-400">Backend Connection Failed</h2>
            <p className="text-gray-400">{backendError}</p>
            <div className="flex space-x-2">
              <Button 
                onClick={() => window.location.reload()} 
                variant="outline"
                className="text-blue-400 border-blue-400 hover:bg-blue-400 hover:text-white"
              >
                Retry
              </Button>
              <Button 
                onClick={() => setBackendError(null)} 
                variant="outline"
                className="text-green-400 border-green-400 hover:bg-green-400 hover:text-white"
              >
                Force Continue
              </Button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Main app UI (only shows when backend is ready)
  return (
    <div className="flex h-screen bg-gray-900 text-gray-100 pt-7">
      {/* Sidebar */}
      <div className="w-70 border-r border-gray-700 flex flex-col">
        <div className="p-4 border-b border-gray-700">
          <div className="flex space-x-2 mb-4">
            <Button
              onClick={showKnowledgeGraph}
              variant={showGraph ? "default" : "outline"}
              size="sm"
              className="flex-1"
            >
              <Network className="w-4 h-4 mr-2" />
              Graph
            </Button>
            <Button
              onClick={showNotesView}
              variant={showNotes ? "default" : "outline"}
              size="sm"
              className="flex-1"
            >
              <FileText className="w-4 h-4 mr-2" />
              Notes
            </Button>
          </div>

          <div className="flex space-x-2 mb-4">
            <Button
              onClick={() => setShowFileForm(true)}
              variant="outline"
              size="sm"
              className="flex-1 text-black"
            >
              <Plus className="w-4 h-4 mr-2" />
              New Note
            </Button>
            {selectedItem && selectedItem.type === "file" && (
              <Button
                onClick={() => handleDeleteFile(selectedItem.id)}
                variant="outline"
                size="sm"
                className="bg-red-900 hover:bg-red-800 border-red-700 text-red-100"
              >
                <Trash2 className="w-4 h-4" />
              </Button>
            )}
          </div>

          {showFileForm && (
            <form onSubmit={handleAddFile} className="mb-2">
              <Input
                placeholder="Note name"
                value={file}
                onChange={(e) => setFile(e.target.value)}
                className="mb-1"
                autoFocus
              />
              <div className="flex justify-end space-x-2">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowFileForm(false)}
                >
                  Cancel
                </Button>
                <Button type="submit" size="sm">
                  Create
                </Button>
              </div>
            </form>
          )}

          <h2
            className="font-semibold text-lg cursor-pointer hover:text-gray-300"
            onClick={() => {
              setParent(0);
              setSelectedItem(null);
              showKnowledgeGraph();
            }}
          >
            Notes
          </h2>
          
          {selectedItem && selectedItem.type === "file" && (
            <div className="text-sm text-gray-400 mt-2">
              Selected: {selectedItem.name}
            </div>
          )}
        </div>

        <div className="flex-1 overflow-auto">
          <FileSystemDisplay
            key={refreshKey}
            onClick={handleItemClick}
            selectedItem={selectedItem}
          />
        </div>

        <div className="p-4 border-t border-gray-700">
          <div className="text-xs text-gray-400 mb-2">
            Current View: {showGraph ? "Knowledge Graph" : "Notes Editor"}
          </div>
          <Button
            onClick={handleDisplayGraph}
            variant="ghost"
            className="w-full flex items-center justify-center"
          >
            <PlanetIcon className="w-5 h-5 mr-2" />
            {showGraph ? "Switch to Notes" : "Switch to Graph"}
          </Button>
        </div>
      </div>

      {/* Main content area */}
      <div className="flex-1 flex">
        {showNotes && (
          <div className="flex-1">
            <NotesDisplay selectedItem={selectedItem} />
          </div>
        )}

        {showGraph && (
          <div className="flex-1">
            <KnowledgeGraph onSelectNote={handleNoteSelectionFromGraph} />
          </div>
        )}
      </div>
    </div>
  );
};

export default Home;
