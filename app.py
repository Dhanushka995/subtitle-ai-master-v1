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

CONFIG_FILE = "sub_master_config_v32.json"

class UniversalSubtitleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Universal AI Subtitle Master v32 (Smart Alignment & Natural Flow)")
        self.root.geometry("700x950")
        self.root.configure(bg="#1e272e")

        self.is_running = False
        self.file_path = ""
        self.current_thread = None

        self.auto_filling_1 = False
        self.auto_filling_2 = False
        self.provider_type_1 = "Unknown"
        self.provider_type_2 = "Unknown"

        # --- HEADER ---
        tk.Label(root, text="UNIVERSAL AI TRANSLATOR", bg="#1e272e", fg="#00d8d6", font=("Arial", 16, "bold")).pack(pady=10)

        # --- SLOT 1 (Primary / Thinker) ---
        slot1_frame = tk.LabelFrame(root, text=" SLOT 1 (Primary Translation / Thinker) ", bg="#2f3640", fg="#feca57", font=("Arial", 10, "bold"), padx=10, pady=10)
        slot1_frame.pack(pady=5, fill="x", padx=20)

        tk.Label(slot1_frame, text="API Key 1:", bg="#2f3640", fg="white").grid(row=0, column=0, sticky="w")
        self.api1_var = tk.StringVar()
        self.api1_var.trace_add("write", self.on_key1_change)
        tk.Entry(slot1_frame, textvariable=self.api1_var, width=65, show="*", bg="#1e272e", fg="white", borderwidth=1).grid(row=0, column=1, padx=5, pady=2)

        self.status1_lbl = tk.Label(slot1_frame, text="Waiting for API Key...", bg="#2f3640", fg="#808e9b", font=("Arial", 9, "bold"))
        self.status1_lbl.grid(row=1, column=1, sticky="w", pady=2)

        tk.Label(slot1_frame, text="Base URL:", bg="#2f3640", fg="white").grid(row=2, column=0, sticky="w")
        self.url1_var = tk.StringVar()
        tk.Entry(slot1_frame, textvariable=self.url1_var, width=50, bg="#1e272e", fg="white").grid(row=2, column=1, sticky="w", padx=5, pady=2)

        tk.Label(slot1_frame, text="Model Name:", bg="#2f3640", fg="white").grid(row=3, column=0, sticky="w")
        self.model1_var = tk.StringVar()
        self.model1_var.trace_add("write", self.on_model1_manual_change)
        tk.Entry(slot1_frame, textvariable=self.model1_var, width=50, bg="#1e272e", fg="white").grid(row=3, column=1, sticky="w", padx=5, pady=2)

        # --- SLOT 2 (Speaker / Fallback) ---
        slot2_frame = tk.LabelFrame(root, text=" SLOT 2 (Speaker / Backup) - Optional ", bg="#2f3640", fg="#ff9ff3", font=("Arial", 10, "bold"), padx=10, pady=10)
        slot2_frame.pack(pady=5, fill="x", padx=20)

        tk.Label(slot2_frame, text="API Key 2:", bg="#2f3640", fg="white").grid(row=0, column=0, sticky="w")
        self.api2_var = tk.StringVar()
        self.api2_var.trace_add("write", self.on_key2_change)
        tk.Entry(slot2_frame, textvariable=self.api2_var, width=65, show="*", bg="#1e272e", fg="white", borderwidth=1).grid(row=0, column=1, padx=5, pady=2)

        self.status2_lbl = tk.Label(slot2_frame, text="Waiting for API Key...", bg="#2f3640", fg="#808e9b", font=("Arial", 9, "bold"))
        self.status2_lbl.grid(row=1, column=1, sticky="w", pady=2)

        tk.Label(slot2_frame, text="Base URL:", bg="#2f3640", fg="white").grid(row=2, column=0, sticky="w")
        self.url2_var = tk.StringVar()
        tk.Entry(slot2_frame, textvariable=self.url2_var, width=50, bg="#1e272e", fg="white").grid(row=2, column=1, sticky="w", padx=5, pady=2)

        tk.Label(slot2_frame, text="Model Name:", bg="#2f3640", fg="white").grid(row=3, column=0, sticky="w")
        self.model2_var = tk.StringVar()
        self.model2_var.trace_add("write", self.on_model2_manual_change)
        tk.Entry(slot2_frame, textvariable=self.model2_var, width=50, bg="#1e272e", fg="white").grid(row=3, column=1, sticky="w", padx=5, pady=2)

        # --- FILE SELECTION ---
        tk.Button(root, text="📂 Select English SRT File", command=self.open_file, bg="#0fb9b1", fg="white", font=("Arial", 10, "bold"), width=30).pack(pady=10)
        self.lbl_status_file = tk.Label(root, text="No file selected", bg="#1e272e", fg="#808e9b")
        self.lbl_status_file.pack()

        # --- SETTINGS ---
        settings_frame = tk.Frame(root, bg="#1e272e")
        settings_frame.pack(pady=5)
        
        tk.Label(settings_frame, text="Chunk Size:", bg="#1e272e", fg="white").grid(row=0, column=0, padx=5)
        self.chunk_var = tk.StringVar(value="40")
        ttk.Combobox(settings_frame, textvariable=self.chunk_var, values=["10", "20", "30", "40", "50"], width=5).grid(row=0, column=1, padx=5)
        
        tk.Label(settings_frame, text="Language:", bg="#1e272e", fg="white").grid(row=0, column=2, padx=15)
        self.lang_var = tk.StringVar(value="Sinhala")
        ttk.Combobox(settings_frame, textvariable=self.lang_var, values=["Sinhala", "Tamil", "Hindi"], width=10).grid(row=0, column=3, padx=5)

        tk.Label(settings_frame, text="Start from Chunk:", bg="#1e272e", fg="#ff9f43").grid(row=1, column=0, columnspan=2, pady=5, sticky="e")
        self.resume_var = tk.StringVar(value="1")
        tk.Entry(settings_frame, textvariable=self.resume_var, width=6, bg="#ff9f43", fg="black", font=("Arial", 10, "bold")).grid(row=1, column=2, sticky="w", pady=5)

        self.delay_enabled = tk.BooleanVar(value=True)
        tk.Checkbutton(settings_frame, text="Enable 15s Delay", variable=self.delay_enabled, bg="#1e272e", fg="#0be881", selectcolor="#1e272e", activebackground="#1e272e").grid(row=2, column=0, columnspan=2, pady=5)

        self.manus_enabled = tk.BooleanVar(value=False)
        tk.Checkbutton(settings_frame, text="Manus Mode (Thinker + Speaker)", variable=self.manus_enabled, bg="#1e272e", fg="#ff9ff3", selectcolor="#1e272e", activebackground="#1e272e").grid(row=2, column=2, columnspan=2, pady=5)

        # --- LOGS ---
        self.log_box = tk.Text(root, height=12, width=75, bg="#000000", fg="#0be881", font=("Consolas", 9))
        self.log_box.pack(pady=5, padx=20)

        # --- CONTROL BUTTONS ---
        btn_frame = tk.Frame(root, bg="#1e272e")
        btn_frame.pack(pady=10)

        self.btn_start = tk.Button(btn_frame, text="START", command=self.start_process, bg="#0984e3", fg="white", font=("Arial", 12, "bold"), width=15, height=2)
        self.btn_start.grid(row=0, column=0, padx=10)

        self.btn_stop = tk.Button(btn_frame, text="STOP", command=self.stop_process, bg="#2d3436", fg="white", font=("Arial", 12, "bold"), width=15, height=2, state="disabled")
        self.btn_stop.grid(row=0, column=1, padx=10)

        self.btn_reset = tk.Button(btn_frame, text="Reset", command=self.reset_all, bg="#d63031", fg="white", font=("Arial", 12, "bold"), width=15, height=2)
        self.btn_reset.grid(row=0, column=2, padx=10)

        self.load_settings()

    def save_settings(self):
        data = {
            "k1": self.api1_var.get(), "u1": self.url1_var.get(), "m1": self.model1_var.get(),
            "k2": self.api2_var.get(), "u2": self.url2_var.get(), "m2": self.model2_var.get()
        }
        try:
            with open(CONFIG_FILE, "w") as f: json.dump(data, f)
        except: pass

    def load_settings(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    self.auto_filling_1 = True
                    self.auto_filling_2 = True
                    if data.get("k1"): self.api1_var.set(data["k1"])
                    if data.get("u1"): self.url1_var.set(data["u1"])
                    if data.get("m1"): self.model1_var.set(data["m1"])
                    if data.get("k2"): self.api2_var.set(data["k2"])
                    if data.get("u2"): self.url2_var.set(data["u2"])
                    if data.get("m2"): self.model2_var.set(data["m2"])
                    self.auto_filling_1 = False
                    self.auto_filling_2 = False
            except: pass

    def log(self, text):
        self.log_box.insert(tk.END, "> " + text + "\n")
        self.log_box.see(tk.END)

    def on_model1_manual_change(self, *args):
        if not self.auto_filling_1 and self.model1_var.get().strip():
            self.status1_lbl.config(text=f"✅ Using Manual Model: {self.model1_var.get()}", fg="#0be881")

    def on_model2_manual_change(self, *args):
        if not self.auto_filling_2 and self.model2_var.get().strip():
            self.status2_lbl.config(text=f"✅ Using Manual Model: {self.model2_var.get()}", fg="#0be881")

    def detect_provider(self, key, url_var, model_var, status_lbl, slot_num):
        if not key:
            status_lbl.config(text="Waiting for API Key...", fg="#808e9b")
            return "Unknown"
            
        if slot_num == 1: self.auto_filling_1 = True
        else: self.auto_filling_2 = True

        provider = "OpenAI_Compatible"
        if key.startswith("AIza"):
            provider = "Gemini"
            status_lbl.config(text="✅ Detected: Google Gemini", fg="#0be881")
            url_var.set("N/A")
            model_var.set("gemini-1.5-flash")
        elif key.startswith("nvapi-"):
            status_lbl.config(text="✅ Detected: NVIDIA API", fg="#0be881")
            url_var.set("https://integrate.api.nvidia.com/v1")
            model_var.set("deepseek-ai/deepseek-v3")
        elif key.startswith("sk-or-"):
            status_lbl.config(text="✅ Detected: OpenRouter", fg="#0be881")
            url_var.set("https://openrouter.ai/api/v1")
            model_var.set("google/gemini-2.0-flash-lite-preview-02-05:free")
        elif key.startswith("gsk_"):
            status_lbl.config(text="✅ Detected: Groq API", fg="#0be881")
            url_var.set("https://api.groq.com/openai/v1")
            model_var.set("llama-3.3-70b-versatile")
        elif key.startswith("hf_"):
            status_lbl.config(text="✅ Detected: Hugging Face", fg="#0be881")
            url_var.set("https://api-inference.huggingface.co/v1")
            model_var.set("Qwen/Qwen2.5-72B-Instruct")
        elif key.startswith("github_pat_") or key.startswith("ghp_"):
            status_lbl.config(text="✅ Detected: GitHub Models", fg="#0be881")
            url_var.set("https://models.inference.ai.azure.com")
            model_var.set("gpt-4o-mini")
        else:
            status_lbl.config(text="⚠️ Unknown Key: Enter URL & Model manually", fg="#ffdd59")
            
        if slot_num == 1: self.auto_filling_1 = False
        else: self.auto_filling_2 = False
        return provider

    def on_key1_change(self, *args):
        self.provider_type_1 = self.detect_provider(self.api1_var.get().strip(), self.url1_var, self.model1_var, self.status1_lbl, 1)

    def on_key2_change(self, *args):
        self.provider_type_2 = self.detect_provider(self.api2_var.get().strip(), self.url2_var, self.model2_var, self.status2_lbl, 2)

    def open_file(self):
        self.file_path = filedialog.askopenfilename(filetypes=[("SRT files", "*.srt")])
        if self.file_path:
            self.lbl_status_file.config(text=os.path.basename(self.file_path), fg="white")

    def reset_all(self):
        if self.is_running:
            messagebox.showwarning("Warning", "Please STOP the translation before resetting.")
            return
        self.auto_filling_1 = True
        self.auto_filling_2 = True
        self.api1_var.set(""); self.url1_var.set(""); self.model1_var.set("")
        self.api2_var.set(""); self.url2_var.set(""); self.model2_var.set("")
        self.auto_filling_1 = False
        self.auto_filling_2 = False
        
        self.file_path = ""
        self.lbl_status_file.config(text="No file selected", fg="#808e9b")
        self.resume_var.set("1")
        self.log_box.delete('1.0', tk.END)
        self.status1_lbl.config(text="Waiting for API Key...", fg="#808e9b")
        self.status2_lbl.config(text="Waiting for API Key...", fg="#808e9b")
        if os.path.exists(CONFIG_FILE): os.remove(CONFIG_FILE)

    def stop_process(self):
        if self.is_running:
            self.is_running = False
            self.log("🛑 STOPPING... Safely aborting after current operation.")
            self.btn_stop.config(state="disabled", text="Stopping...")
            self.root.after(3000, self.force_ui_reset)

    def force_ui_reset(self):
        self.btn_start.config(state="normal")
        self.btn_reset.config(state="normal")
        self.btn_stop.config(state="disabled", text="STOP")

    def start_process(self):
        if not self.file_path or not self.api1_var.get().strip():
            messagebox.showwarning("Input Error", "Please provide at least API Key 1 and select a file.")
            return
        if self.manus_enabled.get() and not self.api2_var.get().strip():
            messagebox.showwarning("Input Error", "Manus Mode requires both Slot 1 and Slot 2 to be filled.")
            return
            
        self.save_settings()
        self.is_running = True
        self.btn_start.config(state="disabled")
        self.btn_reset.config(state="disabled")
        self.btn_stop.config(state="normal", text="STOP")
        
        self.current_thread = threading.Thread(target=self.translation_thread, daemon=True)
        self.current_thread.start()

    def call_ai(self, slot_num, prompt):
        if slot_num == 1:
            key, url, model, provider = self.api1_var.get().strip(), self.url1_var.get().strip(), self.model1_var.get().strip(), self.provider_type_1
        else:
            key, url, model, provider = self.api2_var.get().strip(), self.url2_var.get().strip(), self.model2_var.get().strip(), self.provider_type_2

        # TEMPERATURE INCREASED TO 0.7 FOR MAXIMUM NATURAL CREATIVITY
        if provider == "Gemini":
            genai.configure(api_key=key)
            m = genai.GenerativeModel(model)
            response = m.generate_content(prompt, generation_config={"temperature": 0.7})
            return response.text
        else:
            client = OpenAI(api_key=key, base_url=url if url != "N/A" else None, default_headers={"HTTP-Referer": "https://github.com/Dhanushka995", "X-Title": "SubMaster"})
            response = client.chat.completions.create(model=model, messages=[{"role": "user", "content": prompt}], temperature=0.7)
            return response.choices[0].message.content

    # --- SMART TIME MERGER ---
    def merge_times(self, time1, time2):
        try:
            start = time1.split("-->")[0].strip()
            end = time2.split("-->")[1].strip()
            return f"{start} --> {end}"
        except:
            return time1

    def translation_thread(self):
        try:
            target = self.lang_var.get()
            start_chunk = int(self.resume_var.get())
            if start_chunk < 1: start_chunk = 1
            
            if start_chunk == 1:
                save_path = filedialog.asksaveasfilename(defaultextension=".srt", initialfile=f"FinalSub_{target}.srt")
                if not save_path: raise Exception("Save cancelled")
                open(save_path, 'w', encoding='utf-8').close()
            else:
                save_path = filedialog.askopenfilename(title="Select partially translated SRT file", filetypes=[("SRT files", "*.srt")])
                if not save_path: raise Exception("Resume cancelled")

            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = f.read()

            raw_blocks =[b.strip() for b in re.split(r'\n\s*\n', data.strip()) if b.strip()]
            parsed_blocks =[]
            for b in raw_blocks:
                lines = b.split('\n')
                if len(lines) >= 3:
                    parsed_blocks.append({"index": lines[0].strip(), "time": lines[1].strip(), "text": "\n".join(lines[2:]).strip()})

            c_size = int(self.chunk_var.get())
            total_chunks = (len(parsed_blocks) // c_size) + (1 if len(parsed_blocks) % c_size > 0 else 0)
            
            self.log(f"Total Blocks: {len(parsed_blocks)} | Chunks: {total_chunks}")
            if self.manus_enabled.get(): self.log("🧠 Manus Mode Enabled: Thinker + Speaker")
            else: self.log("⚡ Standard Mode: Natural Flow Enabled")

            if start_chunk > 1: self.log(f"▶️ Resuming from Chunk {start_chunk}...")

            for i in range((start_chunk-1)*c_size, len(parsed_blocks), c_size):
                if not self.is_running or threading.current_thread() != self.current_thread: 
                    break

                chunk = parsed_blocks[i:i + c_size]
                current_chunk_num = (i//c_size)+1
                
                text_payload = ""
                for j, b in enumerate(chunk):
                    text_payload += f"ID_{j}:: {b['text']}\n"
                
                success = False
                while not success and self.is_running and threading.current_thread() == self.current_thread:
                    try:
                        res_text = ""
                        
                        if self.manus_enabled.get():
                            self.log(f"⚙️ Chunk {current_chunk_num}: Thinking (Slot 1)...")
                            prompt1 = f"Analyze the context, tone, and slang of these subtitles. Provide a brief summary of the situation to help a translator. Do NOT translate.\n\n{text_payload}"
                            analysis = self.call_ai(1, prompt1)
                            
                            self.log(f"🗣️ Chunk {current_chunk_num}: Translating (Slot 2)...")
                            prompt2 = f"""You are a highly skilled movie subtitle translator for a Sri Lankan audience.
Context of the scene: [{analysis}]

CRITICAL INSTRUCTIONS:
1. Translate the English text into NATURAL, SPOKEN {target} (සාමාන්‍ය කතා කරන භාෂාව).
2. Focus heavily on natural flow, emotions, and local slang. Do not use robotic or formal book-language.
3. If two lines are better translated as a single sentence, you MAY merge them by combining their translations into the first ID and skipping the second ID.
4. You MUST keep the 'ID_X:: ' prefix for whatever lines you output so I can map them back.

Text to translate:
{text_payload}"""
                            res_text = self.call_ai(2, prompt2)
                        else:
                            prompt = f"""You are a highly skilled movie subtitle translator for a Sri Lankan audience.
Your task is to translate the following English subtitles into NATURAL, SPOKEN {target} (සාමාන්‍ය කතා කරන භාෂාව).

CRITICAL INSTRUCTIONS:
1. Focus heavily on natural flow, emotions, and local slang. Do not use robotic or formal book-language.
2. If two lines are better translated as a single sentence, you MAY merge them by combining their translations into the first ID and skipping the second ID.
3. You MUST keep the 'ID_X:: ' prefix for whatever lines you output so I can map them back.

Text to translate:
{text_payload}"""
                            res_text = self.call_ai(1, prompt)

                        if res_text:
                            clean = res_text.replace('```srt', '').replace('```text', '').replace('```', '').strip()
                            pattern = r"ID_(\d+)\s*::\s*(.*?)(?=ID_\d+\s*::|$)"
                            matches = re.findall(pattern, clean, re.DOTALL)
                            
                            if len(matches) == 0:
                                raise Exception("AI returned no valid IDs. Retrying...")
                            
                            # --- SMART ALIGNMENT LOGIC (NEW) ---
                            translated_dict = {int(m[0]): m[1].strip() for m in matches}
                            valid_blocks =[]
                            
                            for j, orig_block in enumerate(chunk):
                                if j in translated_dict:
                                    valid_blocks.append({
                                        "index": orig_block['index'],
                                        "time": orig_block['time'],
                                        "text": translated_dict[j]
                                    })
                                else:
                                    # AI merged or skipped this line! Extend previous time.
                                    if valid_blocks:
                                        last_block = valid_blocks[-1]
                                        last_block['time'] = self.merge_times(last_block['time'], orig_block['time'])
                                    else:
                                        # If first line is missing, fallback to original
                                        valid_blocks.append({
                                            "index": orig_block['index'],
                                            "time": orig_block['time'],
                                            "text": orig_block['text']
                                        })
                            
                            srt_output = ""
                            for vb in valid_blocks:
                                srt_output += f"{vb['index']}\n{vb['time']}\n{vb['text']}\n\n"
                            
                            with open(save_path, 'a', encoding='utf-8') as f:
                                f.write(srt_output)
                                
                            self.log(f"✅ Chunk {current_chunk_num} success! (Smart Aligned)")
                            success = True
                        else:
                            raise Exception("AI returned empty response.")
                        
                    except Exception as api_err:
                        err_msg = str(api_err)
                        if "402" in err_msg or "Insufficient" in err_msg:
                            self.log(f"❌ Account has 0 balance! Stopping here.")
                            self.is_running = False
                            break
                        elif "429" in err_msg or "quota" in err_msg.lower():
                            self.log(f"⏳ Limit Hit! Sleeping for 60s...")
                            for _ in range(60):
                                if not self.is_running or threading.current_thread() != self.current_thread: break
                                time.sleep(1)
                        else:
                            self.log(f"⚠️ {err_msg[:40]}... Retrying in 15s")
                            for _ in range(15):
                                if not self.is_running or threading.current_thread() != self.current_thread: break
                                time.sleep(1)
                
                if self.is_running and threading.current_thread() == self.current_thread and self.delay_enabled.get() and i + c_size < len(parsed_blocks):
                    self.log("⏳ Delaying 15s for safety...")
                    for _ in range(15):
                        if not self.is_running or threading.current_thread() != self.current_thread: break
                        time.sleep(1)

            if self.is_running and threading.current_thread() == self.current_thread:
                self.log("🎉 ALL DONE! Translation completed.")
                messagebox.showinfo("Done", "Success! Translation completed perfectly.")

        except Exception as e:
            if "cancelled" not in str(e).lower():
                self.log(f"CRITICAL Error: {str(e)}")
                messagebox.showerror("Error", str(e))
        finally:
            if threading.current_thread() == self.current_thread:
                self.is_running = False
                self.root.after(0, self.force_ui_reset)

if __name__ == "__main__":
    root = tk.Tk()
    app = UniversalSubtitleApp(root)
    root.mainloop()
