"use client";

import { useEffect, useState } from "react";
import { Folder, FileText } from "lucide-react";

const buildTree = (items) => {
  if (!Array.isArray(items)) {
    console.warn("Expected items to be an array, but got:", items);
    return [];
  }

  const lookup = {};
  const root = [];

  items.forEach((item) => {
    lookup[item.id] = { ...item, children: [] };
  });

  items.forEach((item) => {
    if (
      item.parent_id === null ||
      item.parent_id === "None" ||
      item.parent_id === 0
    ) {
      root.push(lookup[item.id]);
    } else if (lookup[item.parent_id]) {
      lookup[item.parent_id].children.push(lookup[item.id]);
    }
  });

  return root;
};

const FileTreeItem = ({
  item,
  depth = 0,
  onClick,
  selectedItem,
  isLastChild = false,
}) => {
  const isSelected = selectedItem !== null && selectedItem.id === item.id;
  const isFolder = item.type === "folder";
  const hasChildren = item.children && item.children.length > 0;

  const handleItemClick = (e) => {
    e.stopPropagation();
    onClick(item);
  };

  return (
    <li className="relative">
      {/* Item row with indentation and connectors */}
      <div
        className={`flex items-center py-1.5 rounded-md cursor-pointer transition-colors duration-150 ${
          isSelected ? "bg-gray-700" : "hover:bg-gray-700"
        }`}
        onClick={handleItemClick}
      >
        {/* Indentation and tree connectors */}
        <div
          className="flex items-center"
          style={{ marginLeft: `${depth * 16}px` }}
        >
          {depth > 0 && (
            <div className="relative mr-2">
              {/* Horizontal connector line */}
              <div className="absolute top-1/2 right-full w-4 h-px bg-gray-600"></div>

              {/* Vertical connector line (if not the last child) */}
              {!isLastChild && (
                <div className="absolute bottom-1/2 right-full w-px h-full bg-gray-600"></div>
              )}
            </div>
          )}
        </div>

        {/* Icon */}
        <div className={`mr-2 ${isFolder ? "text-blue-400" : "text-gray-400"}`}>
          {isFolder ? (
            <Folder className="h-4 w-4" />
          ) : (
            <FileText className="h-4 w-4" />
          )}
        </div>

        {/* Item name */}
        <span className={`text-sm ${isFolder ? "font-medium" : ""}`}>
          {item.name}
        </span>
      </div>

      {/* Children */}
      {hasChildren && (
        <ul className="list-none relative">
          {/* Vertical line connecting to children */}
          <div
            className="absolute left-0 top-0 bottom-0 w-px bg-gray-600"
            style={{ left: `${depth * 16 + 8}px` }}
          ></div>

          {item.children.map((child, index) => (
            <FileTreeItem
              key={child.id}
              item={child}
              depth={depth + 1}
              onClick={onClick}
              selectedItem={selectedItem}
              isLastChild={index === item.children.length - 1}
            />
          ))}
        </ul>
      )}
    </li>
  );
};

const FileSystemDisplay = ({ onClick, selectedItem }) => {
  const [fileSystem, setFileSystem] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchFileSystem = async () => {
      try {
        setLoading(true);
        setError(null);
        const res = await fetch("http://localhost:8000/api/filesystem");

        if (!res.ok) {
          throw new Error(`Failed to fetch file system: ${res.status}`);
        }

        const data = await res.json();
        const tree = buildTree(data);
        setFileSystem(tree);
      } catch (err) {
        console.error("Error fetching file system:", err);
        setError(
          err instanceof Error ? err.message : "Failed to load file system"
        );
      } finally {
        setLoading(false);
      }
    };

    fetchFileSystem();
  }, []);

  if (loading) {
    return (
      <div className="p-4 text-center">
        <div className="animate-pulse">Loading file system...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 text-center text-red-500">
        <p>Error: {error}</p>
        <button
          className="mt-2 text-blue-400 hover:underline"
          onClick={() => window.location.reload()}
        >
          Retry
        </button>
      </div>
    );
  }

  if (!fileSystem.length) {
    return (
      <div className="p-4 text-center text-gray-400">
        <p>No files or folders</p>
        <p className="text-sm">
          Create your first file or folder to get started
        </p>
      </div>
    );
  }

  return (
    <div className="p-2">
      <ul className="list-none space-y-1">
        {fileSystem.map((item, index) => (
          <FileTreeItem
            key={item.id}
            item={item}
            onClick={onClick}
            selectedItem={selectedItem}
            isLastChild={index === fileSystem.length - 1}
          />
        ))}
      </ul>
    </div>
  );
};

export default FileSystemDisplay;
