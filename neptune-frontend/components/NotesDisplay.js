"use client";

import React from "react";
import { useState, useEffect } from "react";
import { Loader2, Folder, Save, Check, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { SelectedItem } from "@/app/page";
import ReactMarkdown from "react-markdown";

const NotesDisplay = ({ selectedItem }) => {
  const [note, setNote] = useState(null);
  const [content, setContent] = useState("");
  const [originalContent, setOriginalContent] = useState("");
  const [status, setStatus] = useState("idle");
  const [loading, setLoading] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [isEditing, setIsEditing] = useState(false);

  useEffect(() => {
    if (!selectedItem) {
      setNote(null);
      setContent("");
      setOriginalContent("");
      setStatus("idle");
      setHasChanges(false);
      return;
    }

    if (selectedItem.type === "folder") {
      setNote(null);
      setContent("");
      setOriginalContent("");
      setStatus("idle");
      setHasChanges(false);
      return;
    }

    const fetchNote = async () => {
      try {
        setLoading(true);
        setStatus("loading");

        const res = await fetch(
          `http://localhost:8000/api/filesystem/${selectedItem.id}`
        );

        if (!res.ok) {
          throw new Error(`Failed to fetch note: ${res.status}`);
        }

        const data = await res.json();
        setNote(data);
        setContent(data.content || "");
        setOriginalContent(data.content || "");
        setStatus("idle");
        setHasChanges(false);
      } catch (err) {
        console.error("Error loading note:", err);
        setStatus("error");
      } finally {
        setLoading(false);
      }
    };

    fetchNote();
  }, [selectedItem]);

  const handleNoteChange = (e) => {
    const newContent = e.target.value;
    setContent(newContent);
    setHasChanges(newContent !== originalContent);
  };

  const handleSave = async () => {
    if (!selectedItem || !hasChanges) return;

    try {
      setStatus("saving");
      console.log("CONTENT:", content, selectedItem.id);
      const res = await fetch(
        `http://localhost:8000/api/filesystem/${selectedItem.id}/content`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ content }),
        }
      );

      if (!res.ok) {
        throw new Error("Failed to save note");
      }

      setOriginalContent(content);
      setStatus("saved");
      setHasChanges(false);

      setTimeout(() => {
        if (status === "saved") {
          setStatus("idle");
        }
      }, 2000);
    } catch (err) {
      console.error("Error saving note:", err);
      setStatus("error");
    }
  };

  const renderStatusIndicator = () => {
    if (loading) {
      return (
        <div className="flex items-center text-gray-400">
          <Loader2 className="w-3 h-3 mr-2 animate-spin" />
          <span>Loading...</span>
        </div>
      );
    }

    switch (status) {
      case "saving":
        return (
          <div className="flex items-center text-gray-400">
            <Loader2 className="w-3 h-3 mr-2 animate-spin" />
            <span>Saving...</span>
          </div>
        );
      case "saved":
        return (
          <div className="flex items-center text-green-500">
            <Check className="w-3 h-3 mr-2" />
            <span>Saved</span>
          </div>
        );
      case "error":
        return (
          <div className="flex items-center text-red-500">
            <AlertCircle className="w-3 h-3 mr-2" />
            <span>Error</span>
          </div>
        );
      default:
        if (selectedItem?.type === "file") {
          return (
            <Button
              size="sm"
              onClick={handleSave}
              disabled={!hasChanges || status === "saving"}
              className="flex items-center"
            >
              <Save className="w-3 h-3 mr-2" />
              Save
            </Button>
          );
        }
        return null;
    }
  };

  return (
    <div className="h-full flex flex-col p-4">
      <div className="flex justify-between items-center mb-4">
        <h2 className="font-semibold text-lg">
          {selectedItem ? selectedItem.name : "No file selected"}
        </h2>
        <div className="text-sm">{renderStatusIndicator()}</div>
      </div>

      {!selectedItem ? (
        <div className="flex-1 flex items-center justify-center text-gray-400">
          <p>Select a file to view or edit notes</p>
        </div>
      ) : selectedItem.type === "folder" ? (
        <div className="flex-1 flex flex-col items-center justify-center text-gray-400">
          <Folder className="w-16 h-16 mb-4 text-blue-400 opacity-50" />
          <p>This is a folder</p>
          <p className="mt-2">Select a file to view or edit notes</p>
        </div>
      ) : loading ? (
        <div className="flex-1 flex items-center justify-center">
          <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
        </div>
      ) : (
        <div className="flex-1 flex flex-col">
          {isEditing ? (
            <textarea
              value={content}
              onChange={handleNoteChange}
              placeholder="Start typing your notes here..."
              className="flex-1 w-full p-4 rounded-lg bg-gray-800 text-gray-100 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          ) : (
            <div
              className="flex-1 w-full p-4 rounded-lg bg-gray-800 text-gray-100 overflow-auto"
              onClick={() => setIsEditing(true)}
            >
              <ReactMarkdown>
                {content || "_Nothing here yet..._"}
              </ReactMarkdown>
            </div>
          )}

          <button
            onClick={() => setIsEditing(!isEditing)}
            className="mt-2 self-end px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700 transition"
          >
            {isEditing ? "Preview" : "Edit"}
          </button>
          {hasChanges && (
            <div className="mt-2 text-xs text-gray-400">
              You have unsaved changes
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default NotesDisplay;
