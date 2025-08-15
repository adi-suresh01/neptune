"use client";

import type React from "react";
import { useState } from "react";
import FileSystemDisplay from "@/components/FileSystemDisplay";
import NotesDisplay from "@/components/NotesDisplay";
import KnowledgeGraph from "@/components/KnowledgeGraph";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { File, EarthIcon as PlanetIcon, FileText, Network, Trash2, Plus } from "lucide-react";

export interface FileSystemItem {
  id: number;
  name: string;
  type: string;
  parent_id: string | null;
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
  
  const [parent, setParent] = useState(0);
  const [refreshKey, setRefreshKey] = useState(0);
  const [selectedItem, setSelectedItem] = useState<SelectedItem | null>(null);

  const generateRandomId = () => Math.floor(Math.random() * 1000000);

  const refreshFileSystem = () => {
    setRefreshKey((prev) => prev + 1);
  };

  const handleAddFile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file.trim()) return;

    const id = generateRandomId();
    try {
      const res = await fetch("http://localhost:8000/api/filesystem", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          id: id,
          name: file,
          type: "file",
          parent: null, // All files are root level now
        }),
      });

      if (!res.ok) throw new Error("Failed to create file");

      refreshFileSystem();
    } catch (err) {
      console.error("Error creating file:", err);
    }
    setFile("");
    setShowFileForm(false);
  };

  // NEW: Delete function
  const handleDeleteFile = async (fileId: number) => {
    if (!fileId) return;
    
    const confirmDelete = window.confirm("Are you sure you want to delete this file? This action cannot be undone.");
    if (!confirmDelete) return;

    try {
      const res = await fetch(`http://localhost:8000/api/filesystem/${fileId}`, {
        method: "DELETE",
      });

      if (!res.ok) throw new Error("Failed to delete file");

      // If we're deleting the currently selected file, clear selection
      if (selectedItem && selectedItem.id === fileId) {
        setSelectedItem(null);
        setShowGraph(true); // Switch back to graph view
        setShowNotes(false);
      }

      refreshFileSystem();
      console.log("File deleted successfully");
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

    // REMOVED: folder handling since we don't have folders anymore
    if (item.type === "file") {
      // When selecting a file, switch to notes view automatically
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

  return (
    <div className="flex h-screen bg-gray-900 text-gray-100">
      {/* Sidebar */}
      <div className="w-70 border-r border-gray-700 flex flex-col">
        {/* Header with view toggle */}
        <div className="p-4 border-b border-gray-700">
          {/* View Toggle Buttons */}
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

          {/* UPDATED: File creation and delete buttons */}
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
            {/* NEW: Delete button - only show when a file is selected */}
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
              showKnowledgeGraph(); // Switch to graph when clicking header
            }}
          >
            Notes
          </h2>
          
          {/* NEW: Show selected file name */}
          {selectedItem && selectedItem.type === "file" && (
            <div className="text-sm text-gray-400 mt-2">
              Selected: {selectedItem.name}
            </div>
          )}
        </div>

        {/* File system display */}
        <div className="flex-1 overflow-auto">
          <FileSystemDisplay
            key={refreshKey}
            onClick={handleItemClick}
            selectedItem={selectedItem}
          />
        </div>

        {/* Bottom toggle */}
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
            <KnowledgeGraph />
          </div>
        )}
      </div>
    </div>
  );
};

export default Home;
