import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import google.generativeai as genai
from openai import OpenAI
import threading
import time
import re
import os
import requests

class UniversalSubtitleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Universal AI Subtitle Master v19 (The Final Masterpiece)")
        self.root.geometry("650x750")
        self.root.configure(bg="#1e272e")

        # Header
        tk.Label(root, text="UNIVERSAL AI TRANSLATOR", bg="#1e272e", fg="#00d8d6", font=("Arial", 16, "bold")).pack(pady=15)

        # API Key Input
        tk.Label(root, text="Paste your API Key here (Auto-Detects Provider):", bg="#1e272e", fg="#d2dae2").pack(pady=(5, 0))
        self.api_var = tk.StringVar()
        self.api_var.trace_add("write", self.on_key_change)
        self.api_entry = tk.Entry(root, textvariable=self.api_var, width=65, show="*", bg="#485460", fg="white", borderwidth=0, font=("Consolas", 10))
        self.api_entry.pack(pady=5, ipady=6)

        self.key_status_lbl = tk.Label(root, text="Waiting for API Key...", bg="#1e272e", fg="#808e9b", font=("Arial", 9, "bold"))
        self.key_status_lbl.pack(pady=2)

        # Advanced Settings Frame (Auto-filled by Auto-Detect)
        self.adv_frame = tk.Frame(root, bg="#2f3640", padx=10, pady=10)
        self.adv_frame.pack(pady=10, fill="x", padx=40)
        
        tk.Label(self.adv_frame, text="Base URL:", bg="#2f3640", fg="white").grid(row=0, column=0, sticky="w")
        self.base_url_var = tk.StringVar()
        tk.Entry(self.adv_frame, textvariable=self.base_url_var, width=50, bg="#1e272e", fg="white").grid(row=0, column=1, padx=10, pady=2)

        tk.Label(self.adv_frame, text="Model Name:", bg="#2f3640", fg="white").grid(row=1, column=0, sticky="w")
        self.model_var = tk.StringVar()
        tk.Entry(self.adv_frame, textvariable=self.model_var, width=50, bg="#1e272e", fg="white").grid(row=1, column=1, padx=10, pady=2)

        # File Selection
        self.file_path = ""
        tk.Button(root, text="📂 Select English SRT File", command=self.open_file, bg="#0fb9b1", fg="white", font=("Arial", 10, "bold"), width=30).pack(pady=10)
        self.lbl_status_file = tk.Label(root, text="No file selected", bg="#1e272e", fg="#808e9b")
        self.lbl_status_file.pack()

        # Settings
        settings_frame = tk.Frame(root, bg="#1e272e")
        settings_frame.pack(pady=10)
        
        tk.Label(settings_frame, text="Chunk Size:", bg="#1e272e", fg="white").grid(row=0, column=0, padx=5)
        self.chunk_var = tk.StringVar(value="40")
        ttk.Combobox(settings_frame, textvariable=self.chunk_var, values=["10", "20", "30", "40", "50"], width=5).grid(row=0, column=1, padx=5)
        
        tk.Label(settings_frame, text="Language:", bg="#1e272e", fg="white").grid(row=0, column=2, padx=15)
        self.lang_var = tk.StringVar(value="Sinhala")
        ttk.Combobox(settings_frame, textvariable=self.lang_var, values=["Sinhala", "Tamil", "Hindi"], width=10).grid(row=0, column=3, padx=5)

        # Resume Feature
        tk.Label(settings_frame, text="Start from Chunk:", bg="#1e272e", fg="#ff9f43").grid(row=1, column=0, columnspan=2, pady=10, sticky="e")
        self.resume_var = tk.StringVar(value="1")
        tk.Entry(settings_frame, textvariable=self.resume_var, width=6, bg="#ff9f43", fg="black", font=("Arial", 10, "bold")).grid(row=1, column=2, sticky="w", pady=10)
        tk.Label(settings_frame, text="(Use >1 to resume partial work)", bg="#1e272e", fg="#808e9b", font=("Arial", 8)).grid(row=1, column=3, sticky="w")

        # Logs
        self.log_box = tk.Text(root, height=12, width=75, bg="#000000", fg="#0be881", font=("Consolas", 9))
        self.log_box.pack(pady=5, padx=20)

        # Start Button
        self.btn_start = tk.Button(root, text="🚀 START TRANSLATION", command=self.run_thread, bg="#ff3f34", fg="white", font=("Arial", 12, "bold"), width=35, height=2)
        self.btn_start.pack(pady=10)

        self.provider_type = "Unknown"

    def log(self, text):
        self.log_box.insert(tk.END, "> " + text + "\n")
        self.log_box.see(tk.END)

    def on_key_change(self, *args):
        key = self.api_var.get().strip()
        if not key: return

        if key.startswith("AIza"):
            self.provider_type = "Gemini"
            self.key_status_lbl.config(text="✅ Detected: Google Gemini", fg="#0be881")
            self.base_url_var.set("N/A")
            self.model_var.set("Auto-Detecting...")
        elif key.startswith("sk-or-"):
            self.provider_type = "OpenRouter"
            self.key_status_lbl.config(text="⏳ OpenRouter: Fetching best FREE model...", fg="#ffdd59")
            self.base_url_var.set("https://openrouter.ai/api/v1")
            threading.Thread(target=self.fetch_openrouter_free_model, args=(key,), daemon=True).start()
        elif key.startswith("gsk_"):
            self.provider_type = "OpenAI_Compatible"
            self.key_status_lbl.config(text="✅ Detected: Groq API", fg="#0be881")
            self.base_url_var.set("https://api.groq.com/openai/v1")
            self.model_var.set("llama-3.3-70b-versatile")
        else:
            self.provider_type = "OpenAI_Compatible"
            self.key_status_lbl.config(text="⚠️ Unknown Key: Manual Setup Required", fg="#ffdd59")

    def fetch_openrouter_free_model(self, api_key):
        try:
            response = requests.get("https://openrouter.ai/api/v1/models")
            if response.status_code == 200:
                models = response.json().get('data', [])
                free_models = [m['id'] for m in models if float(m.get('pricing', {}).get('prompt', 1)) == 0]
                best_model = ""
                for m in free_models:
                    if "gemini" in m.lower():
                        best_model = m
                        break
                if not best_model and free_models: best_model = free_models[0]
                if best_model:
                    self.model_var.set(best_model)
                    self.key_status_lbl.config(text=f"✅ OpenRouter: Auto-selected {best_model}", fg="#0be881")
                else:
                    self.model_var.set("google/gemini-2.0-flash-lite-preview-02-05:free")
        except:
            self.model_var.set("google/gemini-2.0-flash-lite-preview-02-05:free")

    def open_file(self):
        self.file_path = filedialog.askopenfilename(filetypes=[("SRT files", "*.srt")])
        if self.file_path:
            self.lbl_status_file.config(text=os.path.basename(self.file_path), fg="white")

    def run_thread(self):
        if not self.file_path or not self.api_var.get().strip():
            messagebox.showwarning("Input Error", "Please provide the API Key and select a file.")
            return
        self.btn_start.config(state="disabled")
        threading.Thread(target=self.start_logic, daemon=True).start()

    def start_logic(self):
        api_key = self.api_var.get().strip()
        base_url = self.base_url_var.get().strip()
        model_name = self.model_var.get().strip()
        
        try:
            target = self.lang_var.get()
            start_chunk = int(self.resume_var.get())
            if start_chunk < 1: start_chunk = 1
            
            if start_chunk == 1:
                save_path = filedialog.asksaveasfilename(defaultextension=".srt", initialfile=f"AutoSync_{target}.srt")
                if not save_path:
                    self.btn_start.config(state="normal")
                    return
                open(save_path, 'w', encoding='utf-8').close()
            else:
                save_path = filedialog.askopenfilename(title="Select your partially translated SRT file to resume", filetypes=[("SRT files", "*.srt")])
                if not save_path:
                    self.btn_start.config(state="normal")
                    return

            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = f.read()

            blocks =[b.strip() for b in re.split(r'\n\s*\n', data.strip()) if b.strip()]
            c_size = int(self.chunk_var.get())
            total_chunks = (len(blocks) // c_size) + (1 if len(blocks) % c_size > 0 else 0)
            
            self.log(f"Total Blocks: {len(blocks)} | Total Chunks: {total_chunks}")
            
            gemini_model_to_use = None
            if self.provider_type == "Gemini":
                self.log("Scanning Google API key for best model...")
                genai.configure(api_key=api_key)
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods and 'flash' in m.name.lower(): 
                        gemini_model_to_use = m.name
                        break
                if not gemini_model_to_use: gemini_model_to_use = 'gemini-pro'
                self.log(f"Using Google Model: {gemini_model_to_use}")
            else:
                self.log(f"Using API -> Model: {model_name}")

            for i in range((start_chunk-1)*c_size, len(blocks), c_size):
                chunk_blocks = blocks[i:i + c_size]
                batch = "\n\n".join(chunk_blocks)
                expected_count = batch.count("-->")
                current_chunk_num = (i//c_size)+1
                
                prompt = f"""CRITICAL: You are a professional SRT translator.
1. DO NOT translate or change timestamps (00:00:10,000 --> 00:00:12,000).
2. DO NOT change sequence numbers.
3. Translate ONLY the English text into natural, meaningful {target}.
4. Keep the exact same SRT formatting.
5. You MUST output exactly {expected_count} subtitles. Do not merge them.

Subtitles to translate:
{batch}"""
                
                success = False
                while not success:
                    try:
                        result_text = ""
                        if self.provider_type == "Gemini":
                            model = genai.GenerativeModel(gemini_model_to_use)
                            response = model.generate_content(prompt, generation_config={"temperature": 0.2})
                            result_text = response.text
                        else:
                            client = OpenAI(
                                api_key=api_key, 
                                base_url=base_url,
                                default_headers={"HTTP-Referer": "https://github.com/Dhanushka995", "X-Title": "SubMaster"}
                            )
                            response = client.chat.completions.create(
                                model=model_name,
                                messages=[{"role": "user", "content": prompt}],
                                temperature=0.2
                            )
                            result_text = response.choices[0].message.content

                        if result_text:
                            clean = result_text.replace('```srt', '').replace('```', '').strip()
                            actual_count = clean.count("-->")
                            
                            if actual_count != expected_count:
                                raise Exception(f"Format Error: AI merged lines! (Expected {expected_count}, Got {actual_count})")
                            
                            with open(save_path, 'a', encoding='utf-8') as f:
                                f.write(clean + "\n\n")
                            self.log(f"✅ Chunk {current_chunk_num} of {total_chunks} success!")
                            success = True
                        
                    except Exception as api_err:
                        err_msg = str(api_err)
                        if "429" in err_msg or "quota" in err_msg.lower():
                            self.log(f"⏳ Limit Hit! Sleeping for 60s...")
                            time.sleep(60)
                        else:
                            self.log(f"⚠️ Error: {err_msg[:50]}... Retrying in 15s")
                            time.sleep(15)
                
                if i + c_size < len(blocks):
                    self.log("⏳ Waiting for 15 seconds to prevent Rate Limits...")
                    time.sleep(15)

            messagebox.showinfo("Done", "Translation completed successfully!")

        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            self.btn_start.config(state="normal")

if __name__ == "__main__":
    root = tk.Tk()
    app = UniversalSubtitleApp(root)
    root.mainloop()
