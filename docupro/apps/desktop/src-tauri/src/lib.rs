//! DOCUPRO desktop/mobile shell.
//!
//! The user interface is the same TypeScript application that runs on the web.
//! The shell adds native windowing, native file dialogs and native file saving
//! through the Tauri plugins, plus Android share/back-button integration.

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_opener::init())
        .run(tauri::generate_context!())
        .expect("error while running DOCUPRO");
}
