"use client";

import type React from "react";
import { useState } from "react";
import FileSystemDisplay from "@/components/FileSystemDisplay";
import NotesDisplay from "@/components/NotesDisplay";
import KnowledgeGraph from "@/components/KnowledgeGraph";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Folder, File, EarthIcon as PlanetIcon } from "lucide-react";

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
  const [showFolderForm, setShowFolderForm] = useState(false);
  const [showFileForm, setShowFileForm] = useState(false);
  const [folder, setFolder] = useState("");
  const [file, setFile] = useState("");
  const [showGraph, setShowGraph] = useState(false);
  const [showNotes, setShowNotes] = useState(true);
  const [parent, setParent] = useState(0);
  const [refreshKey, setRefreshKey] = useState(0);

  // Update selectedItem to include name
  const [selectedItem, setSelectedItem] = useState<SelectedItem | null>(null);

  const generateRandomId = () => Math.floor(Math.random() * 1000000);

  const refreshFileSystem = () => {
    setRefreshKey((prev) => prev + 1);
  };

  const handleAddFolder = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!folder.trim()) return;

    const id = generateRandomId();
    try {
      const res = await fetch("http://localhost:8000/api/filesystem", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          id: id,
          name: folder,
          type: "folder",
          parent: parent,
        }),
      });

      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(`Failed to create folder: ${res.status} ${errorText}`);
      }

      refreshFileSystem();
    } catch (err) {
      console.error("Request error:", err);
    }
    setFolder("");
    setShowFolderForm(false);
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
          parent: parent,
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

  // Update handleItemClick to include the item name
  const handleItemClick = (item: FileSystemItem) => {
    setSelectedItem({
      id: item.id,
      type: item.type,
      name: item.name,
    });

    if (item.type === "folder") {
      setParent(item.id);
    }
  };

  const handleDisplayGraph = () => {
    setShowGraph(!showGraph);
    setShowNotes(!showNotes);
  };

  return (
    <div className="flex h-screen bg-gray-900 text-gray-100">
      <div className="w-70 border-r border-gray-700 flex flex-col">
        <div className="p-4 border-b border-gray-700">
          <div className="flex space-x-2 mb-4">
            <Button
              onClick={() => setShowFolderForm(true)}
              variant="outline"
              size="sm"
              className="flex-1 text-black"
            >
              <Folder className="w-4 h-4 mr-2" />
              New Folder
            </Button>
            <Button
              onClick={() => setShowFileForm(true)}
              variant="outline"
              size="sm"
              className="flex-1 text-black"
            >
              <File className="w-4 h-4 mr-2" />
              New File
            </Button>
          </div>

          {showFolderForm && (
            <form onSubmit={handleAddFolder} className="mb-2">
              <Input
                placeholder="Folder name"
                value={folder}
                onChange={(e) => setFolder(e.target.value)}
                className="mb-1"
                autoFocus
              />
              <div className="flex justify-end space-x-2">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowFolderForm(false)}
                >
                  Cancel
                </Button>
                <Button type="submit" size="sm">
                  Create
                </Button>
              </div>
            </form>
          )}

          {showFileForm && (
            <form onSubmit={handleAddFile} className="mb-2">
              <Input
                placeholder="File name"
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
            }}
          >
            File System
          </h2>
        </div>

        <div className="flex-1 overflow-auto">
          <FileSystemDisplay
            key={refreshKey}
            onClick={handleItemClick}
            selectedItem={selectedItem}
          />
        </div>

        <Button
          onClick={handleDisplayGraph}
          variant="ghost"
          className="m-4 flex items-center justify-center"
        >
          <PlanetIcon className="w-5 h-5 mr-2" />
          {showGraph ? "Show Notes" : "Show Graph"}
        </Button>
      </div>

      <div className="flex-1 flex">
        {showNotes && (
          <div className="flex-1">
            <NotesDisplay selectedItem={selectedItem} />
          </div>
        )}

        {showGraph && (
          <div className="flex-1 bg-white">
            <KnowledgeGraph />
          </div>
        )}
      </div>
    </div>
  );
};

export default Home;
