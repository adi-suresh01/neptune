// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::{Command, Child, Stdio};
use std::sync::Mutex;
use std::thread;
use std::time::Duration;
use tauri::Manager;

// Global backend process handle
static BACKEND_PROCESS: Mutex<Option<Child>> = Mutex::new(None);

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .setup(|app| {
            println!("🚀 Neptune app starting...");
            
            // Kill any existing backend processes first
            let _ = Command::new("pkill")
                .arg("-f")
                .arg("neptune-backend")
                .output();
            
            thread::sleep(Duration::from_millis(500)); // Wait for cleanup
            
            // Get the resource path
            let resource_path = app.path().resource_dir().expect("failed to resolve resource");
            let backend_path = resource_path.join("binaries").join("neptune-backend");
            
            println!("=== Neptune Backend Debug ===");
            println!("Resource path: {:?}", resource_path);
            println!("Backend path: {:?}", backend_path);
            println!("Backend exists: {}", backend_path.exists());
            
            if !backend_path.exists() {
                eprintln!("❌ Backend file not found!");
                return Ok(());
            }
            
            // Make executable
            #[cfg(unix)]
            {
                use std::os::unix::fs::PermissionsExt;
                if let Ok(metadata) = std::fs::metadata(&backend_path) {
                    let mut perms = metadata.permissions();
                    perms.set_mode(0o755);
                    let _ = std::fs::set_permissions(&backend_path, perms);
                }
            }
            
            println!("🚀 Starting Neptune backend...");
            
            match Command::new(&backend_path)
                .stdout(Stdio::piped())
                .stderr(Stdio::piped())
                .spawn()
            {
                Ok(child) => {
                    println!("✅ Backend started with PID: {}", child.id());
                    
                    // Store the process handle
                    if let Ok(mut backend) = BACKEND_PROCESS.lock() {
                        *backend = Some(child);
                    }
                    
                    // Monitor backend startup
                    thread::spawn(move || {
                        thread::sleep(Duration::from_secs(5)); // Wait for backend to start
                        
                        // Test if backend is responding
                        for port in 8000..8010 {
                            if let Ok(_) = std::net::TcpStream::connect(format!("127.0.0.1:{}", port)) {
                                println!("🌐 Backend is responding on port {}", port);
                                return;
                            }
                        }
                        println!("⚠️  Backend may not be responding on any port");
                    });
                }
                Err(e) => {
                    eprintln!("❌ Failed to start backend: {}", e);
                }
            }
            
            Ok(())
        })
        .on_window_event(|_window, event| {
            // Clean up backend when app closes
            if let tauri::WindowEvent::CloseRequested { .. } = event {
                println!("🛑 App closing, stopping backend...");
                if let Ok(mut backend) = BACKEND_PROCESS.lock() {
                    if let Some(mut child) = backend.take() {
                        let _ = child.kill();
                        println!("✅ Backend stopped");
                    }
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

fn main() {
    run();
}
