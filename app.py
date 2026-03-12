import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import google.generativeai as genai
from openai import OpenAI
import threading
import time
import re
import os

class UniversalSubtitleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Universal AI Subtitle Master v13 (OpenRouter Fixed)")
        self.root.geometry("650x750")
        self.root.configure(bg="#1e272e")

        tk.Label(root, text="UNIVERSAL AI TRANSLATOR", bg="#1e272e", fg="#00d8d6", font=("Arial", 16, "bold")).pack(pady=15)

        tk.Label(root, text="Paste your API Key here (Auto-Detects Provider):", bg="#1e272e", fg="#d2dae2", font=("Arial", 10)).pack(pady=(5, 0))
        self.api_var = tk.StringVar()
        self.api_var.trace_add("write", self.on_key_change)
        self.api_entry = tk.Entry(root, textvariable=self.api_var, width=65, show="*", bg="#485460", fg="white", borderwidth=0, font=("Consolas", 10))
        self.api_entry.pack(pady=5, ipady=6)

        self.key_status_lbl = tk.Label(root, text="Waiting for API Key...", bg="#1e272e", fg="#808e9b", font=("Arial", 9, "bold"))
        self.key_status_lbl.pack(pady=2)

        self.adv_frame = tk.Frame(root, bg="#2f3640", padx=10, pady=10)
        self.adv_frame.pack(pady=10, fill="x", padx=40)
        
        tk.Label(self.adv_frame, text="Base URL:", bg="#2f3640", fg="white").grid(row=0, column=0, sticky="w", pady=2)
        self.base_url_var = tk.StringVar()
        self.base_url_entry = tk.Entry(self.adv_frame, textvariable=self.base_url_var, width=50, bg="#1e272e", fg="white")
        self.base_url_entry.grid(row=0, column=1, padx=10, pady=2)

        tk.Label(self.adv_frame, text="Model Name:", bg="#2f3640", fg="white").grid(row=1, column=0, sticky="w", pady=2)
        self.model_var = tk.StringVar()
        self.model_entry = tk.Entry(self.adv_frame, textvariable=self.model_var, width=50, bg="#1e272e", fg="white")
        self.model_entry.grid(row=1, column=1, padx=10, pady=2)

        self.file_path = ""
        tk.Button(root, text="📂 Select English SRT File", command=self.open_file, bg="#0fb9b1", fg="white", font=("Arial", 10, "bold"), width=30).pack(pady=10)
        self.lbl_status_file = tk.Label(root, text="No file selected", bg="#1e272e", fg="#808e9b")
        self.lbl_status_file.pack()

        settings_frame = tk.Frame(root, bg="#1e272e")
        settings_frame.pack(pady=10)
        
        tk.Label(settings_frame, text="Chunk Size:", bg="#1e272e", fg="white").grid(row=0, column=0, padx=5)
        self.chunk_var = tk.StringVar(value="30")
        ttk.Combobox(settings_frame, textvariable=self.chunk_var, values=["10", "20", "30", "40", "50"], width=5).grid(row=0, column=1, padx=5)
        
        tk.Label(settings_frame, text="Language:", bg="#1e272e", fg="white").grid(row=0, column=2, padx=15)
        self.lang_var = tk.StringVar(value="Sinhala")
        ttk.Combobox(settings_frame, textvariable=self.lang_var, values=["Sinhala", "Tamil", "Hindi"], width=10).grid(row=0, column=3, padx=5)

        tk.Label(settings_frame, text="Start from Chunk:", bg="#1e272e", fg="#ff9f43").grid(row=1, column=0, columnspan=2, pady=10, sticky="e")
        self.resume_var = tk.StringVar(value="1")
        tk.Entry(settings_frame, textvariable=self.resume_var, width=6, bg="#ff9f43", fg="black", font=("Arial", 10, "bold")).grid(row=1, column=2, sticky="w", pady=10)

        self.log_box = tk.Text(root, height=10, width=75, bg="#000000", fg="#0be881", font=("Consolas", 9))
        self.log_box.pack(pady=5, padx=20)

        self.btn_start = tk.Button(root, text="🚀 START TRANSLATION", command=self.run_thread, bg="#ff3f34", fg="white", font=("Arial", 12, "bold"), width=35, height=2)
        self.btn_start.pack(pady=10)

        self.provider_type = "Unknown"

    def on_key_change(self, *args):
        key = self.api_var.get().strip()
        if not key:
            self.key_status_lbl.config(text="Waiting for API Key...", fg="#808e9b")
            return

        if key.startswith("AIza"):
            self.provider_type = "Gemini"
            self.key_status_lbl.config(text="✅ Detected: Google Gemini", fg="#0be881")
            self.base_url_var.set("N/A")
            self.model_var.set("Auto-Detect")
            
        elif key.startswith("gsk_"):
            self.provider_type = "OpenAI_Compatible"
            self.key_status_lbl.config(text="✅ Detected: Groq API", fg="#0be881")
            self.base_url_var.set("https://api.groq.com/openai/v1")
            self.model_var.set("llama-3.3-70b-versatile")
            
        elif key.startswith("sk-or-"):
            self.provider_type = "OpenRouter"
            self.key_status_lbl.config(text="✅ Detected: OpenRouter API", fg="#0be881")
            self.base_url_var.set("https://openrouter.ai/api/v1")
            # FIXED: Using a more stable free model name
            self.model_var.set("google/gemini-2.0-flash-lite-preview-02-05:free")
            
        else:
            self.provider_type = "OpenAI_Compatible"
            self.key_status_lbl.config(text="⚠️ Unknown Key: Manual Setup Required", fg="#ffdd59")

    def log(self, text):
        self.log_box.insert(tk.END, "> " + text + "\n")
        self.log_box.see(tk.END)

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
            
            if start_chunk == 1:
                save_path = filedialog.asksaveasfilename(defaultextension=".srt", initialfile=f"AutoSync_{target}.srt")
                if not save_path:
                    self.btn_start.config(state="normal")
                    return
                open(save_path, 'w', encoding='utf-8').close()
            else:
                save_path = filedialog.askopenfilename(filetypes=[("SRT files", "*.srt")])
                if not save_path:
                    self.btn_start.config(state="normal")
                    return

            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = f.read()

            blocks =[b.strip() for b in re.split(r'\n\s*\n', data.strip()) if b.strip()]
            c_size = int(self.chunk_var.get())
            
            if self.provider_type == "Gemini":
                genai.configure(api_key=api_key)
                gemini_model_name = 'gemini-1.5-flash'
                self.log(f"Using Google Model: {gemini_model_name}")
            else:
                self.log(f"Using API -> Model: {model_name}")

            for i in range((start_chunk-1)*c_size, len(blocks), c_size):
                chunk_blocks = blocks[i:i + c_size]
                batch = "\n\n".join(chunk_blocks)
                expected_count = batch.count("-->")
                
                prompt = f"Translate the following SRT subtitles into natural {target}. Return ONLY the translated SRT text:\n\n{batch}"
                
                success = False
                while not success:
                    try:
                        result_text = ""
                        if self.provider_type == "Gemini":
                            model = genai.GenerativeModel(gemini_model_name)
                            response = model.generate_content(prompt)
                            result_text = response.text
                        else:
                            # FIXED: Added required headers for OpenRouter Free Tier
                            client = OpenAI(
                                api_key=api_key, 
                                base_url=base_url,
                                default_headers={
                                    "HTTP-Referer": "https://github.com/Dhanushka995/subtitle-ai-master",
                                    "X-Title": "Subtitle AI Master"
                                }
                            )
                            response = client.chat.completions.create(
                                model=model_name,
                                messages=[{"role": "user", "content": prompt}]
                            )
                            result_text = response.choices[0].message.content

                        if result_text:
                            clean = result_text.replace('```srt', '').replace('```', '').strip()
                            with open(save_path, 'a', encoding='utf-8') as f:
                                f.write(clean + "\n\n")
                            self.log(f"✅ Chunk {(i//c_size)+1} success!")
                            success = True
                        
                    except Exception as api_err:
                        self.log(f"⚠️ Error: {str(api_err)[:50]}... Retrying in 15s")
                        time.sleep(15)
                
                time.sleep(10)

            messagebox.showinfo("Done", "Translation completed!")

        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            self.btn_start.config(state="normal")

if __name__ == "__main__":
    root = tk.Tk()
    app = UniversalSubtitleApp(root)
    root.mainloop()
