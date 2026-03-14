import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import google.generativeai as genai
from openai import OpenAI
import threading
import time
import re
import os
import requests
import json

CONFIG_FILE = "sub_master_config.json"

class UniversalSubtitleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Universal AI Subtitle Master v25 (Flawless Edition)")
        self.root.geometry("650x850")
        self.root.configure(bg="#1e272e")

        self.is_running = False
        self.provider_type = "Unknown"
        self.file_path = ""
        self.current_thread = None

        tk.Label(root, text="UNIVERSAL AI TRANSLATOR", bg="#1e272e", fg="#00d8d6", font=("Arial", 16, "bold")).pack(pady=15)

        tk.Label(root, text="Paste your API Key here (Auto-Detects Provider & Best Model):", bg="#1e272e", fg="#d2dae2").pack(pady=(5, 0))
        self.api_var = tk.StringVar()
        self.api_var.trace_add("write", self.on_key_change)
        self.api_entry = tk.Entry(root, textvariable=self.api_var, width=65, show="*", bg="#485460", fg="white", borderwidth=0, font=("Consolas", 10))
        self.api_entry.pack(pady=5, ipady=6)

        self.key_status_lbl = tk.Label(root, text="Waiting for API Key...", bg="#1e272e", fg="#808e9b", font=("Arial", 9, "bold"))
        self.key_status_lbl.pack(pady=2)

        self.adv_frame = tk.Frame(root, bg="#2f3640", padx=10, pady=10)
        self.adv_frame.pack(pady=10, fill="x", padx=40)
        
        tk.Label(self.adv_frame, text="Base URL:", bg="#2f3640", fg="white").grid(row=0, column=0, sticky="w")
        self.base_url_var = tk.StringVar()
        tk.Entry(self.adv_frame, textvariable=self.base_url_var, width=50, bg="#1e272e", fg="white").grid(row=0, column=1, padx=10, pady=2)

        tk.Label(self.adv_frame, text="Model Name:", bg="#2f3640", fg="white").grid(row=1, column=0, sticky="w")
        self.model_var = tk.StringVar()
        tk.Entry(self.adv_frame, textvariable=self.model_var, width=50, bg="#1e272e", fg="white").grid(row=1, column=1, padx=10, pady=2)

        self.btn_file = tk.Button(root, text="📂 Select English SRT File", command=self.open_file, bg="#0fb9b1", fg="white", font=("Arial", 10, "bold"), width=30)
        self.btn_file.pack(pady=10)
        self.lbl_status_file = tk.Label(root, text="No file selected", bg="#1e272e", fg="#808e9b")
        self.lbl_status_file.pack()

        settings_frame = tk.Frame(root, bg="#1e272e")
        settings_frame.pack(pady=10)
        
        tk.Label(settings_frame, text="Chunk Size:", bg="#1e272e", fg="white").grid(row=0, column=0, padx=5)
        self.chunk_var = tk.StringVar(value="40")
        ttk.Combobox(settings_frame, textvariable=self.chunk_var, values=["10", "20", "30", "40", "50"], width=5).grid(row=0, column=1, padx=5)
        
        tk.Label(settings_frame, text="Language:", bg="#1e272e", fg="white").grid(row=0, column=2, padx=15)
        self.lang_var = tk.StringVar(value="Sinhala")
        ttk.Combobox(settings_frame, textvariable=self.lang_var, values=["Sinhala", "Tamil", "Hindi"], width=10).grid(row=0, column=3, padx=5)

        self.delay_enabled = tk.BooleanVar(value=True)
        tk.Checkbutton(settings_frame, text="Enable 15s Rate Limit Delay (Safe Mode)", variable=self.delay_enabled, bg="#1e272e", fg="#0be881", selectcolor="#1e272e", activebackground="#1e272e", activeforeground="white").grid(row=1, column=0, columnspan=4, pady=10)

        tk.Label(settings_frame, text="Start from Chunk:", bg="#1e272e", fg="#ff9f43").grid(row=2, column=0, columnspan=2, pady=5, sticky="e")
        self.resume_var = tk.StringVar(value="1")
        tk.Entry(settings_frame, textvariable=self.resume_var, width=6, bg="#ff9f43", fg="black", font=("Arial", 10, "bold")).grid(row=2, column=2, sticky="w", pady=5)
        tk.Label(settings_frame, text="(Leave 1 for new file)", bg="#1e272e", fg="#808e9b", font=("Arial", 8)).grid(row=2, column=3, sticky="w")

        self.log_box = tk.Text(root, height=10, width=75, bg="#000000", fg="#0be881", font=("Consolas", 9))
        self.log_box.pack(pady=5, padx=20)

        btn_frame = tk.Frame(root, bg="#1e272e")
        btn_frame.pack(pady=15)

        self.btn_start = tk.Button(btn_frame, text="START", command=self.start_process, bg="#0984e3", fg="white", font=("Arial", 12, "bold"), width=15, height=2)
        self.btn_start.grid(row=0, column=0, padx=10)

        self.btn_stop = tk.Button(btn_frame, text="STOP", command=self.stop_process, bg="#2d3436", fg="white", font=("Arial", 12, "bold"), width=15, height=2, state="disabled")
        self.btn_stop.grid(row=0, column=1, padx=10)

        self.btn_reset = tk.Button(btn_frame, text="Reset", command=self.reset_all, bg="#d63031", fg="white", font=("Arial", 12, "bold"), width=15, height=2)
        self.btn_reset.grid(row=0, column=2, padx=10)

        self.load_settings()

    def save_settings(self):
        data = {"api_key": self.api_var.get(), "base_url": self.base_url_var.get(), "model_name": self.model_var.get()}
        try:
            with open(CONFIG_FILE, "w") as f: json.dump(data, f)
        except: pass

    def load_settings(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    if data.get("api_key"): self.api_var.set(data["api_key"])
                    if data.get("base_url"): self.base_url_var.set(data["base_url"])
                    if data.get("model_name"): self.model_var.set(data["model_name"])
            except: pass

    def log(self, text):
        self.log_box.insert(tk.END, "> " + text + "\n")
        self.log_box.see(tk.END)

    def on_key_change(self, *args):
        key = self.api_var.get().strip()
        if not key: 
            self.key_status_lbl.config(text="Waiting for API Key...", fg="#808e9b")
            return

        if key.startswith("AIza"):
            self.provider_type = "Gemini"
            self.key_status_lbl.config(text="✅ Detected: Google Gemini", fg="#0be881")
            self.base_url_var.set("N/A")
            self.model_var.set("Auto-Detecting...")
        elif key.startswith("sk-or-"):
            self.provider_type = "OpenRouter"
            self.key_status_lbl.config(text="⏳ OpenRouter: Fetching best FREE model...", fg="#ffdd59")
            self.base_url_var.set("https://openrouter.ai/api/v1")
            threading.Thread(target=self.fetch_best_model, args=(key, "https://openrouter.ai/api/v1", True), daemon=True).start()
        elif key.startswith("nvapi-"):
            self.provider_type = "NVIDIA"
            self.key_status_lbl.config(text="⏳ NVIDIA: Fetching best model...", fg="#ffdd59")
            self.base_url_var.set("https://integrate.api.nvidia.com/v1")
            threading.Thread(target=self.fetch_best_model, args=(key, "https://integrate.api.nvidia.com/v1", False), daemon=True).start()
        elif key.startswith("gsk_"):
            self.provider_type = "Groq"
            self.key_status_lbl.config(text="✅ Detected: Groq API", fg="#0be881")
            self.base_url_var.set("https://api.groq.com/openai/v1")
            self.model_var.set("llama-3.3-70b-versatile")
        else:
            self.provider_type = "OpenAI_Compatible"
            self.key_status_lbl.config(text="⚠️ Unknown Key: Please enter Base URL & Model manually", fg="#ffdd59")

    def fetch_best_model(self, api_key, base_url, is_openrouter=False):
        try:
            headers = {"Authorization": f"Bearer {api_key}"}
            response = requests.get(f"{base_url}/models", headers=headers, timeout=10)
            
            if response.status_code == 200:
                models_data = response.json().get('data', [])
                
                if is_openrouter:
                    available_models = [m['id'] for m in models_data if float(m.get('pricing', {}).get('prompt', 1)) == 0]
                else:
                    available_models = [m['id'] for m in models_data]

                priorities = ["gemini", "deepseek-v3", "deepseek-r1", "qwen-72b", "qwen-2.5", "gpt-4o", "llama-3.3"]
                best_model = ""

                for priority in priorities:
                    for m in available_models:
                        if "coder" in m.lower() or "math" in m.lower():
                            continue
                        if priority in m.lower():
                            best_model = m
                            break
                    if best_model: break

                if best_model:
                    self.model_var.set(best_model)
                    self.key_status_lbl.config(text=f"✅ Auto-selected: {best_model}", fg="#0be881")
                else:
                    fallback = "meta-llama/llama-3.1-70b-instruct" if "nvidia" in base_url else available_models[0]
                    self.model_var.set(fallback)
                    self.key_status_lbl.config(text=f"⚠️ Selected fallback: {fallback}", fg="#ffdd59")
            else:
                self.key_status_lbl.config(text="❌ Failed to fetch models. Enter manually.", fg="#ff7675")
        except Exception as e:
            self.key_status_lbl.config(text="❌ Network error. Enter manually.", fg="#ff7675")

    def open_file(self):
        self.file_path = filedialog.askopenfilename(filetypes=[("SRT files", "*.srt")])
        if self.file_path:
            self.lbl_status_file.config(text=os.path.basename(self.file_path), fg="white")

    def reset_all(self):
        if self.is_running:
            messagebox.showwarning("Warning", "Please STOP the translation before resetting.")
            return
        self.api_var.set("")
        self.base_url_var.set("")
        self.model_var.set("")
        self.file_path = ""
        self.lbl_status_file.config(text="No file selected", fg="#808e9b")
        self.resume_var.set("1")
        self.log_box.delete('1.0', tk.END)
        self.key_status_lbl.config(text="Waiting for API Key...", fg="#808e9b")
        if os.path.exists(CONFIG_FILE): os.remove(CONFIG_FILE)

    def stop_process(self):
        if self.is_running:
            self.is_running = False
            self.log("🛑 STOPPING... (Please wait a few seconds for the current task to abort)")
            self.btn_stop.config(state="disabled", text="Stopping...")
            self.root.after(3000, self.force_ui_reset)

    def force_ui_reset(self):
        self.btn_start.config(state="normal")
        self.btn_reset.config(state="normal")
        self.btn_file.config(state="normal")
        self.btn_stop.config(state="disabled", text="STOP")
        self.log("🛑 Process completely stopped.")

    def start_process(self):
        if not self.file_path or not self.api_var.get().strip():
            messagebox.showwarning("Input Error", "Please provide the API Key and select a file.")
            return
        
        self.save_settings()
        self.is_running = True
        self.btn_start.config(state="disabled")
        self.btn_reset.config(state="disabled")
        self.btn_file.config(state="disabled")
        self.btn_stop.config(state="normal", text="STOP")
        
        self.current_thread = threading.Thread(target=self.translation_thread, daemon=True)
        self.current_thread.start()

    def translation_thread(self):
        api_key = self.api_var.get().strip()
        base_url = self.base_url_var.get().strip()
        model_name = self.model_var.get().strip()
        
        try:
            target = self.lang_var.get()
            start_chunk = int(self.resume_var.get())
            if start_chunk < 1: start_chunk = 1
            
            if start_chunk == 1:
                save_path = filedialog.asksaveasfilename(defaultextension=".srt", initialfile=f"Sub_{target}.srt")
                if not save_path: raise Exception("Save cancelled")
                open(save_path, 'w', encoding='utf-8').close()
            else:
                save_path = filedialog.askopenfilename(title="Select partially translated SRT file", filetypes=[("SRT files", "*.srt")])
                if not save_path: raise Exception("Resume cancelled")

            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = f.read()

            blocks =[b.strip() for b in re.split(r'\n\s*\n', data.strip()) if b.strip()]
            c_size = int(self.chunk_var.get())
            total_chunks = (len(blocks) // c_size) + (1 if len(blocks) % c_size > 0 else 0)
            
            gemini_model_to_use = None
            if self.provider_type == "Gemini":
                genai.configure(api_key=api_key)
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods and 'flash' in m.name.lower(): 
                        gemini_model_to_use = m.name
                        break
                if not gemini_model_to_use: gemini_model_to_use = 'gemini-pro'
                self.log(f"Model: {gemini_model_to_use}")
            else:
                self.log(f"Model: {model_name}")

            self.log(f"Total Blocks: {len(blocks)} | Chunks: {total_chunks}")
            if start_chunk > 1: self.log(f"Resuming from Chunk {start_chunk}...")

            for i in range((start_chunk-1)*c_size, len(blocks), c_size):
                if not self.is_running: break

                chunk_blocks = blocks[i:i + c_size]
                batch = "\n\n".join(chunk_blocks)
                expected_count = batch.count("-->")
                current_chunk_num = (i//c_size)+1
                
                prompt = f"""CRITICAL: Professional SRT Translator.
1. DO NOT change sequence numbers or timestamps.
2. Translate ONLY the English text into natural {target}.
3. Preserve SRT formatting exactly.
4. Output EXACTLY {expected_count} subtitles. Do not merge them.

{batch}"""
                
                success = False
                while not success and self.is_running:
                    try:
                        res_text = ""
                        if self.provider_type == "Gemini":
                            model = genai.GenerativeModel(gemini_model_to_use)
                            response = model.generate_content(prompt, generation_config={"temperature": 0.2})
                            res_text = response.text
                        else:
                            client = OpenAI(
                                api_key=api_key, 
                                base_url=base_url if base_url != "N/A" else None,
                                default_headers={"HTTP-Referer": "https://github.com/Dhanushka995", "X-Title": "SubMaster"}
                            )
                            response = client.chat.completions.create(
                                model=model_name,
                                messages=[{"role": "user", "content": prompt}],
                                temperature=0.2
                            )
                            res_text = response.choices[0].message.content

                        if res_text:
                            clean = res_text.replace('```srt', '').replace('```', '').strip()
                            if clean.count("-->") != expected_count:
                                raise Exception("Line mismatch detected! Retrying...")
                            
                            with open(save_path, 'a', encoding='utf-8') as f:
                                f.write(clean + "\n\n")
                            self.log(f"✅ Chunk {current_chunk_num} of {total_chunks} success!")
                            success = True
                        
                    except Exception as api_err:
                        err_msg = str(api_err)
                        if "429" in err_msg or "quota" in err_msg.lower():
                            self.log(f"⏳ Limit Hit! Sleeping for 60s...")
                            for _ in range(60):
                                if not self.is_running: break
                                time.sleep(1)
                        else:
                            self.log(f"⚠️ {err_msg[:40]}... Retrying in 15s")
                            for _ in range(15):
                                if not self.is_running: break
                                time.sleep(1)
                
                if self.is_running and self.delay_enabled.get() and i + c_size < len(blocks):
                    self.log("⏳ Waiting for 15s to prevent Rate Limits...")
                    for _ in range(15):
                        if not self.is_running: break
                        time.sleep(1)

            if self.is_running:
                self.log("🎉 ALL DONE! Translation completed successfully.")
                messagebox.showinfo("Done", "Success!")

        except Exception as e:
            if "cancelled" not in str(e).lower():
                self.log(f"CRITICAL Error: {str(e)}")
                messagebox.showerror("Error", str(e))
        finally:
            self.is_running = False
            self.root.after(0, self.force_ui_reset)

if __name__ == "__main__":
    root = tk.Tk()
    app = UniversalSubtitleApp(root)
    root.mainloop()
