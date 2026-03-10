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
        self.root.title("Universal AI Subtitle Master v6 (Auto-Detect)")
        self.root.geometry("650x700")
        self.root.configure(bg="#1e272e")

        tk.Label(root, text="UNIVERSAL AI TRANSLATOR", bg="#1e272e", fg="#00d8d6", font=("Arial", 16, "bold")).pack(pady=15)

        provider_frame = tk.Frame(root, bg="#1e272e")
        provider_frame.pack(pady=5)
        tk.Label(provider_frame, text="Select AI System:", bg="#1e272e", fg="white", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=10)
        self.provider_var = tk.StringVar(value="Google Gemini")
        self.provider_menu = ttk.Combobox(provider_frame, textvariable=self.provider_var, values=["Google Gemini", "OpenAI (ChatGPT)", "DeepSeek"], width=20, state="readonly")
        self.provider_menu.pack(side=tk.LEFT)

        tk.Label(root, text="Enter API Key:", bg="#1e272e", fg="#d2dae2").pack(pady=(15, 0))
        self.api_entry = tk.Entry(root, width=65, show="*", bg="#485460", fg="white", borderwidth=0)
        self.api_entry.pack(pady=5, ipady=6)

        self.file_path = ""
        tk.Button(root, text="📂 Select English SRT File", command=self.open_file, bg="#0fb9b1", fg="white", font=("Arial", 10, "bold"), width=30).pack(pady=15)
        self.lbl_status_file = tk.Label(root, text="No file selected", bg="#1e272e", fg="#808e9b")
        self.lbl_status_file.pack()

        settings_frame = tk.Frame(root, bg="#1e272e")
        settings_frame.pack(pady=20)
        
        tk.Label(settings_frame, text="Chunk Size:", bg="#1e272e", fg="white").grid(row=0, column=0, padx=5)
        self.chunk_var = tk.StringVar(value="30")
        ttk.Combobox(settings_frame, textvariable=self.chunk_var, values=["10", "20", "30", "40", "50"], width=5).grid(row=0, column=1, padx=5)
        
        tk.Label(settings_frame, text="Target Language:", bg="#1e272e", fg="white").grid(row=0, column=2, padx=15)
        self.lang_var = tk.StringVar(value="Sinhala")
        ttk.Combobox(settings_frame, textvariable=self.lang_var, values=["Sinhala", "Tamil", "Hindi"], width=12).grid(row=0, column=3, padx=5)

        self.log_box = tk.Text(root, height=12, width=75, bg="#000000", fg="#0be881", font=("Consolas", 9))
        self.log_box.pack(pady=10, padx=20)

        self.btn_start = tk.Button(root, text="🚀 START TRANSLATION", command=self.run_thread, bg="#ff3f34", fg="white", font=("Arial", 12, "bold"), width=35, height=2)
        self.btn_start.pack(pady=10)

    def log(self, text):
        self.log_box.insert(tk.END, "> " + text + "\n")
        self.log_box.see(tk.END)

    def open_file(self):
        self.file_path = filedialog.askopenfilename(filetypes=[("SRT files", "*.srt")])
        if self.file_path:
            self.lbl_status_file.config(text=os.path.basename(self.file_path), fg="white")

    def run_thread(self):
        if not self.file_path or not self.api_entry.get().strip():
            messagebox.showwarning("Input Error", "Please provide the API Key and select a file.")
            return
        self.btn_start.config(state="disabled")
        threading.Thread(target=self.start_logic, daemon=True).start()

    def start_logic(self):
        provider = self.provider_var.get()
        api_key = self.api_entry.get().strip()
        
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = f.read()

            blocks = re.split(r'\n\s*\n', data.strip())
            c_size = int(self.chunk_var.get())
            target = self.lang_var.get()
            output_content = ""

            self.log(f"System: {provider}")
            
            # --- 100% FIX FOR GEMINI (Auto-Detect Model) ---
            gemini_model_name = None
            if provider == "Google Gemini":
                self.log("Scanning your API key for available models...")
                genai.configure(api_key=api_key)
                try:
                    for m in genai.list_models():
                        if 'generateContent' in m.supported_generation_methods:
                            gemini_model_name = m.name
                            if 'flash' in m.name.lower(): # Prefer flash models
                                break
                    if gemini_model_name:
                        self.log(f"Success! Auto-selected model: {gemini_model_name}")
                    else:
                        raise Exception("No usable models found for this Google Key.")
                except Exception as e:
                    raise Exception(f"Invalid Google API Key or Region Blocked: {e}")

            self.log(f"Total Blocks to Translate: {(len(blocks)//c_size)+1}")

            for i in range(0, len(blocks), c_size):
                batch = "\n\n".join(blocks[i:i + c_size])
                prompt = f"Translate the following SRT subtitles into natural {target}. Preserve SRT numbering and timestamps exactly. Output ONLY the translated SRT text:\n\n{batch}"
                
                try:
                    result_text = ""
                    
                    if provider == "Google Gemini":
                        model = genai.GenerativeModel(gemini_model_name)
                        response = model.generate_content(prompt)
                        result_text = response.text
                        
                    elif provider == "OpenAI (ChatGPT)":
                        client = OpenAI(api_key=api_key)
                        response = client.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=[{"role": "user", "content": prompt}]
                        )
                        result_text = response.choices[0].message.content
                        
                    elif provider == "DeepSeek":
                        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
                        response = client.chat.completions.create(
                            model="deepseek-chat",
                            messages=[{"role": "user", "content": prompt}]
                        )
                        result_text = response.choices[0].message.content

                    if result_text:
                        clean = result_text.replace('```srt', '').replace('```', '').strip()
                        output_content += clean + "\n\n"
                        self.log(f"✅ Chunk { (i//c_size) + 1 } Success")
                    else:
                        self.log(f"⚠️ Chunk { (i//c_size) + 1 } Empty")

                except Exception as api_err:
                    err_msg = str(api_err)
                    # Handing DeepSeek 402 Error Gracefully
                    if "402" in err_msg or "Insufficient" in err_msg:
                        self.log(f"❌ FATAL ERROR: Account has no balance/credits!")
                        messagebox.showerror("No Balance", "Your API account has 0 credits. Please top-up or use a free Google Gemini Key.")
                        self.btn_start.config(state="normal")
                        return # Stop everything
                    else:
                        self.log(f"❌ API Error: Retrying... ({err_msg[:50]})")
                        time.sleep(15) 
                
                time.sleep(8) 

            save_path = filedialog.asksaveasfilename(defaultextension=".srt", initialfile=f"Translated_{target}.srt")
            if save_path:
                with open(save_path, 'w', encoding='utf-8') as f:
                    f.write(output_content)
                self.log("💾 SUCCESS! Translation Saved.")
                messagebox.showinfo("Done", "Translation completed successfully!")

        except Exception as e:
            self.log(f"CRITICAL Error: {str(e)}")
            messagebox.showerror("Error", str(e))
        finally:
            self.btn_start.config(state="normal")

if __name__ == "__main__":
    root = tk.Tk()
    app = UniversalSubtitleApp(root)
    root.mainloop()
