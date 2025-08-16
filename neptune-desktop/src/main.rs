// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::Command;
use tauri::Manager;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .setup(|app| {
            // Start the backend process
            let resource_path = app.path().resource_dir().expect("failed to resolve resource");
            let backend_path = resource_path.join("neptune-backend");
            
            println!("Starting Neptune backend from: {:?}", backend_path);
            
            match Command::new(&backend_path).spawn() {
                Ok(_child) => {
                    println!("Neptune backend started successfully");
                }
                Err(e) => {
                    println!("Failed to start Neptune backend: {}", e);
                }
            }
            
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

fn main() {
    run();
}
