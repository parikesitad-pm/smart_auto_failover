use std::fs;
use std::path::Path;
use std::process::Command;

fn main() {
    let frontend_dist = Path::new("../frontend/dist");
    let index_html = frontend_dist.join("index.html");

    if !index_html.exists() {
        println!("cargo:warning=frontend/dist not found, attempting to build frontend...");

        let npm_cmd = if cfg!(target_os = "windows") {
            "npm.cmd"
        } else {
            "npm"
        };
        let _ = Command::new(npm_cmd)
            .args(["--prefix", "../frontend", "run", "build"])
            .status();

        if !frontend_dist.exists() {
            let _ = fs::create_dir_all(frontend_dist);
        }
        if !index_html.exists() {
            let _ = fs::write(
                &index_html,
                r#"<!DOCTYPE html><html><head><title>AutoFailover 3.0</title><meta charset="utf-8"/></head><body style="background:#080b10;color:#e2e8f0;font-family:sans-serif;padding:2rem;text-align:center;"><h2>AutoFailover 3.0 by Modula</h2><p>Frontend assets were not pre-built before compiling.</p><p>Please run: <code>cd frontend && npm install && npm run build</code> and recompile.</p></body></html>"#,
            );
        }
    }

    tauri_build::build();
}

