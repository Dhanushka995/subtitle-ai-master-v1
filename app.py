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
        self.root.title("Universal AI Subtitle Master v11 (Ultimate Pro)")
        self.root.geometry("650x700")
        self.root.configure(bg="#1e272e")

        tk.Label(root, text="UNIVERSAL AI TRANSLATOR", bg="#1e272e", fg="#00d8d6", font=("Arial", 16, "bold")).pack(pady=15)

        provider_frame = tk.Frame(root, bg="#1e272e")
        provider_frame.pack(pady=5)
        tk.Label(provider_frame, text="Select AI System:", bg="#1e272e", fg="white", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=10)
        self.provider_var = tk.StringVar(value="Google Gemini")
        self.provider_menu = ttk.Combobox(provider_frame, textvariable=self.provider_var, values=["Google Gemini", "Groq (Free API)", "OpenAI (ChatGPT)", "DeepSeek"], width=20, state="readonly")
        self.provider_menu.pack(side=tk.LEFT)

        tk.Label(root, text="Enter API Key:", bg="#1e272e", fg="#d2dae2").pack(pady=(15, 0))
        self.api_entry = tk.Entry(root, width=65, show="*", bg="#485460", fg="white", borderwidth=0)
        self.api_entry.pack(pady=5, ipady=6)

        self.file_path = ""
        tk.Button(root, text="📂 Select English SRT File", command=self.open_file, bg="#0fb9b1", fg="white", font=("Arial", 10, "bold"), width=30).pack(pady=15)
        self.lbl_status_file = tk.Label(root, text="No file selected", bg="#1e272e", fg="#808e9b")
        self.lbl_status_file.pack()

        settings_frame = tk.Frame(root, bg="#1e272e")
        settings_frame.pack(pady=15)
        
        tk.Label(settings_frame, text="Chunk Size:", bg="#1e272e", fg="white").grid(row=0, column=0, padx=5)
        self.chunk_var = tk.StringVar(value="40")
        ttk.Combobox(settings_frame, textvariable=self.chunk_var, values=["10", "20", "30", "40", "50"], width=5).grid(row=0, column=1, padx=5)
        
        tk.Label(settings_frame, text="Language:", bg="#1e272e", fg="white").grid(row=0, column=2, padx=15)
        self.lang_var = tk.StringVar(value="Sinhala")
        ttk.Combobox(settings_frame, textvariable=self.lang_var, values=["Sinhala", "Tamil", "Hindi"], width=10).grid(row=0, column=3, padx=5)

        # RESUME FEATURE UI
        tk.Label(settings_frame, text="Start from Chunk:", bg="#1e272e", fg="#ff9f43").grid(row=1, column=0, columnspan=2, pady=10, sticky="e")
        self.resume_var = tk.StringVar(value="1")
        tk.Entry(settings_frame, textvariable=self.resume_var, width=6, bg="#ff9f43", fg="black", font=("Arial", 10, "bold")).grid(row=1, column=2, sticky="w", pady=10)
        tk.Label(settings_frame, text="(Leave 1 to start from beginning)", bg="#1e272e", fg="#808e9b", font=("Arial", 8)).grid(row=1, column=3, sticky="w")

        self.log_box = tk.Text(root, height=10, width=75, bg="#000000", fg="#0be881", font=("Consolas", 9))
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
            target = self.lang_var.get()
            start_chunk = int(self.resume_var.get())
            if start_chunk < 1: start_chunk = 1
            
            if start_chunk == 1:
                save_path = filedialog.asksaveasfilename(defaultextension=".srt", initialfile=f"LiveSync_{target}.srt", title="Where to save the translation?")
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
            
            self.log(f"System: {provider}")
            
            gemini_model_name = None
            if provider == "Google Gemini":
                self.log("Scanning API key for best model...")
                genai.configure(api_key=api_key)
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods and 'flash' in m.name.lower(): 
                        gemini_model_name = m.name
                        break
                if not gemini_model_name: gemini_model_name = 'gemini-pro'

            total_chunks = (len(blocks)//c_size)+1
            self.log(f"Total Blocks: {len(blocks)} | Total Chunks: {total_chunks}")
            if start_chunk > 1:
                self.log(f"▶️ RESUMING translation from Chunk {start_chunk}...")

            start_index = (start_chunk - 1) * c_size

            for i in range(start_index, len(blocks), c_size):
                chunk_blocks = blocks[i:i + c_size]
                batch = "\n\n".join(chunk_blocks)
                expected_count = batch.count("-->")
                current_chunk = (i//c_size) + 1
                
                # STRICT PROMPT FOR FORMAT PROTECTION & TEXT ONLY TRANSLATION
                prompt = f"""Translate the following SRT subtitles into natural {target}.
CRITICAL RULES:
1. DO NOT translate or change the sequence numbers (1, 2, 3...).
2. DO NOT translate or change the timestamps (e.g., 00:00:10,000 --> 00:00:12,000).
3. Translate ONLY the English text into natural, meaningful {target}.
4. Keep the exact same SRT formatting.
5. You MUST output exactly {expected_count} subtitles. Do not merge them.

Subtitles to translate:
{batch}"""
                
                success = False
                while not success:
                    try:
                        result_text = ""
                        
                        if provider == "Google Gemini":
                            model = genai.GenerativeModel(gemini_model_name)
                            response = model.generate_content(prompt)
                            result_text = response.text
                            
                        elif provider == "Groq (Free API)":
                            client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
                            response = client.chat.completions.create(
                                model="llama-3.3-70b-versatile",
                                messages=[{"role": "user", "content": prompt}]
                            )
                            result_text = response.choices[0].message.content
                            
                        elif provider == "OpenAI (ChatGPT)" or provider == "DeepSeek":
                            base = "https://api.deepseek.com" if provider == "DeepSeek" else None
                            m_name = "deepseek-chat" if provider == "DeepSeek" else "gpt-3.5-turbo"
                            client = OpenAI(api_key=api_key, base_url=base)
                            response = client.chat.completions.create(
                                model=m_name,
                                messages=[{"role": "user", "content": prompt}]
                            )
                            result_text = response.choices[0].message.content

                        if result_text:
                            clean = result_text.replace('```srt', '').replace('```', '').strip()
                            actual_count = clean.count("-->")
                            
                            if actual_count != expected_count:
                                raise Exception(f"Format Error: AI merged lines! (Expected {expected_count}, Got {actual_count})")
                            
                            # LIVE SAVE
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
                
                # 15 SECONDS DELAY AFTER EVERY SUCCESSFUL CHUNK
                if i + c_size < len(blocks): # Don't sleep after the very last chunk
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
