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
        self.root.title("Universal AI Subtitle Master v12 (Smart Auto-Detect)")
        self.root.geometry("650x750")
        self.root.configure(bg="#1e272e")

        tk.Label(root, text="UNIVERSAL AI TRANSLATOR", bg="#1e272e", fg="#00d8d6", font=("Arial", 16, "bold")).pack(pady=15)

        # API Key Input
        tk.Label(root, text="Paste your API Key here (Auto-Detects Provider):", bg="#1e272e", fg="#d2dae2", font=("Arial", 10)).pack(pady=(5, 0))
        
        self.api_var = tk.StringVar()
        self.api_var.trace_add("write", self.on_key_change)
        self.api_entry = tk.Entry(root, textvariable=self.api_var, width=65, show="*", bg="#485460", fg="white", borderwidth=0, font=("Consolas", 10))
        self.api_entry.pack(pady=5, ipady=6)

        # Status Label for API Key
        self.key_status_lbl = tk.Label(root, text="Waiting for API Key...", bg="#1e272e", fg="#808e9b", font=("Arial", 9, "bold"))
        self.key_status_lbl.pack(pady=2)

        # Advanced Settings (Hidden by default, auto-filled)
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

        # File Selection
        self.file_path = ""
        tk.Button(root, text="📂 Select English SRT File", command=self.open_file, bg="#0fb9b1", fg="white", font=("Arial", 10, "bold"), width=30).pack(pady=10)
        self.lbl_status_file = tk.Label(root, text="No file selected", bg="#1e272e", fg="#808e9b")
        self.lbl_status_file.pack()

        # Settings
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

        # Logs
        self.log_box = tk.Text(root, height=10, width=75, bg="#000000", fg="#0be881", font=("Consolas", 9))
        self.log_box.pack(pady=5, padx=20)

        self.btn_start = tk.Button(root, text="🚀 START TRANSLATION", command=self.run_thread, bg="#ff3f34", fg="white", font=("Arial", 12, "bold"), width=35, height=2)
        self.btn_start.pack(pady=10)

        self.provider_type = "Unknown"

    def on_key_change(self, *args):
        key = self.api_var.get().strip()
        if not key:
            self.key_status_lbl.config(text="Waiting for API Key...", fg="#808e9b")
            self.base_url_var.set("")
            self.model_var.set("")
            return

        if key.startswith("AIza"):
            self.provider_type = "Gemini"
            self.key_status_lbl.config(text="✅ Detected: Google Gemini (Auto Model)", fg="#0be881")
            self.base_url_var.set("N/A")
            self.model_var.set("Auto-Detect")
            self.base_url_entry.config(state="disabled")
            self.model_entry.config(state="disabled")
            
        elif key.startswith("gsk_"):
            self.provider_type = "OpenAI_Compatible"
            self.key_status_lbl.config(text="✅ Detected: Groq API", fg="#0be881")
            self.base_url_entry.config(state="normal")
            self.model_entry.config(state="normal")
            self.base_url_var.set("https://api.groq.com/openai/v1")
            self.model_var.set("llama-3.3-70b-versatile")
            
        elif key.startswith("sk-or-"):
            self.provider_type = "OpenAI_Compatible"
            self.key_status_lbl.config(text="✅ Detected: OpenRouter API", fg="#0be881")
            self.base_url_entry.config(state="normal")
            self.model_entry.config(state="normal")
            self.base_url_var.set("https://openrouter.ai/api/v1")
            self.model_var.set("google/gemini-2.5-flash-free") # Best free model on OpenRouter
            
        elif key.startswith("sk-proj-") or key.startswith("sk-svc-"):
            self.provider_type = "OpenAI_Compatible"
            self.key_status_lbl.config(text="✅ Detected: OpenAI (ChatGPT)", fg="#0be881")
            self.base_url_entry.config(state="normal")
            self.model_entry.config(state="normal")
            self.base_url_var.set("https://api.openai.com/v1")
            self.model_var.set("gpt-3.5-turbo")
            
        else:
            self.provider_type = "OpenAI_Compatible"
            self.key_status_lbl.config(text="⚠️ Unknown Key: Please enter Base URL and Model Name manually", fg="#ffdd59")
            self.base_url_entry.config(state="normal")
            self.model_entry.config(state="normal")
            if not self.base_url_var.get():
                self.base_url_var.set("https://api.your-site.com/v1")
            if not self.model_var.get():
                self.model_var.set("model-name-here")

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
            if start_chunk < 1: start_chunk = 1
            
            if start_chunk == 1:
                save_path = filedialog.asksaveasfilename(defaultextension=".srt", initialfile=f"AutoSync_{target}.srt", title="Where to save?")
                if not save_path:
                    self.btn_start.config(state="normal")
                    return
                open(save_path, 'w', encoding='utf-8').close()
            else:
                save_path = filedialog.askopenfilename(title="Select partially translated SRT file", filetypes=[("SRT files", "*.srt")])
                if not save_path:
                    self.btn_start.config(state="normal")
                    return

            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = f.read()

            blocks =[b.strip() for b in re.split(r'\n\s*\n', data.strip()) if b.strip()]
            c_size = int(self.chunk_var.get())
            
            if self.provider_type == "Gemini":
                self.log("Scanning Google API key for best model...")
                genai.configure(api_key=api_key)
                gemini_model_name = 'gemini-pro'
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods and 'flash' in m.name.lower(): 
                        gemini_model_name = m.name
                        break
                self.log(f"Using Google Model: {gemini_model_name}")
            else:
                self.log(f"Using Custom API -> URL: {base_url} | Model: {model_name}")

            total_chunks = (len(blocks)//c_size)+1
            self.log(f"Total Blocks: {len(blocks)} | Total Chunks: {total_chunks}")
            if start_chunk > 1:
                self.log(f"▶️ RESUMING from Chunk {start_chunk}...")

            start_index = (start_chunk - 1) * c_size

            for i in range(start_index, len(blocks), c_size):
                chunk_blocks = blocks[i:i + c_size]
                batch = "\n\n".join(chunk_blocks)
                expected_count = batch.count("-->")
                current_chunk = (i//c_size) + 1
                
                prompt = f"""Translate the following SRT subtitles into natural {target}.
CRITICAL RULES:
1. DO NOT change the sequence numbers.
2. DO NOT change the timestamps.
3. Translate ONLY the text.
4. Keep the exact same SRT formatting.
5. You MUST output exactly {expected_count} subtitles. Do not merge them.

{batch}"""
                
                success = False
                while not success:
                    try:
                        result_text = ""
                        
                        if self.provider_type == "Gemini":
                            model = genai.GenerativeModel(gemini_model_name)
                            response = model.generate_content(prompt)
                            result_text = response.text
                            
                        elif self.provider_type == "OpenAI_Compatible":
                            client = OpenAI(api_key=api_key, base_url=base_url if base_url != "N/A" else None)
                            response = client.chat.completions.create(
                                model=model_name,
                                messages=[{"role": "user", "content": prompt}],
                                temperature=0.3 # Low temperature for strict formatting
                            )
                            result_text = response.choices[0].message.content

                        if result_text:
                            clean = result_text.replace('```srt', '').replace('```', '').strip()
                            actual_count = clean.count("-->")
                            
                            if actual_count != expected_count:
                                raise Exception(f"Format Error: AI merged lines! (Expected {expected_count}, Got {actual_count})")
                            
                            with open(save_path, 'a', encoding='utf-8') as f:
                                f.write(clean + "\n\n")
                                
                            self.log(f"✅ Chunk {current_chunk} success!")
                            success = True
                        else:
                            raise Exception("AI returned empty response.")

                    except Exception as api_err:
                        err_msg = str(api_err)
                        if "402" in err_msg or "Insufficient" in err_msg:
                            self.log(f"❌ Account has 0 balance! Stopping here.")
                            self.btn_start.config(state="normal")
                            return
                        elif "429" in err_msg or "quota" in err_msg.lower():
                            self.log(f"⏳ Free Limit Hit! Sleeping for 60 seconds...")
                            time.sleep(60) 
                        else:
                            self.log(f"⚠️ Error: {err_msg[:40]}... Retrying...")
                            time.sleep(10) 
                
                if i + c_size < len(blocks):
                    self.log("⏳ Waiting for 15 seconds to prevent Rate Limits...")
                    time.sleep(15)

            self.log("🎉 ALL DONE! Full translation completed.")
            messagebox.showinfo("Done", "Translation completed with 100% original sync!")

        except Exception as e:
            self.log(f"CRITICAL Error: {str(e)}")
            messagebox.showerror("Error", str(e))
        finally:
            self.btn_start.config(state="normal")

if __name__ == "__main__":
    root = tk.Tk()
    app = UniversalSubtitleApp(root)
    root.mainloop()
