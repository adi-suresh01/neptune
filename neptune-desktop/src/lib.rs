use std::process::{Command, Stdio};

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_log::Builder::default().build())
        .setup(|_app| {
            // Just backend startup code - no menus for now
            std::thread::spawn(move || {
                let current_dir = std::env::current_dir().unwrap();
                log::info!("Current working directory: {:?}", current_dir);
                
                let backend_dir_1 = current_dir.parent().unwrap().join("neptune-backend");
                let backend_dir_2 = current_dir.join("../neptune-backend");
                let backend_dir_3 = std::path::PathBuf::from("/Users/adi/Desktop/neptune/neptune-backend");
                
                let backend_dir = if backend_dir_1.exists() {
                    backend_dir_1
                } else if backend_dir_2.exists() {
                    backend_dir_2  
                } else if backend_dir_3.exists() {
                    backend_dir_3
                } else {
                    log::error!("No backend directory found!");
                    return;
                };

                let venv_python = backend_dir.join("neptune-env/bin/python");
                let python_cmd = if venv_python.exists() {
                    venv_python.to_str().unwrap()
                } else {
                    "python3"
                };
                
                let cmd = Command::new(python_cmd)
                    .args(&["-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"])
                    .current_dir(&backend_dir)
                    .stdout(Stdio::piped())
                    .stderr(Stdio::piped())
                    .spawn();

                match cmd {
                    Ok(mut child) => {
                        log::info!("✅ Python backend started successfully on port 8000");
                        let _ = child.wait();
                    }
                    Err(_) => {
                        let cmd2 = Command::new("python")
                            .args(&["-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"])
                            .current_dir(&backend_dir)
                            .spawn();
                        if let Ok(mut child) = cmd2 {
                            let _ = child.wait();
                        }
                    }
                }
            });

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
