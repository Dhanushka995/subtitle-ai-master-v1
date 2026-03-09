import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import google.generativeai as genai
import threading
import time
import re
import os

class SubtitleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Subtitle Master Pro v2")
        self.root.geometry("600x650")
        self.root.configure(bg="#2c3e50")

        tk.Label(root, text="AI SUBTITLE TRANSLATOR", bg="#2c3e50", fg="white", font=("Arial", 14, "bold")).pack(pady=20)
        tk.Label(root, text="Gemini API Key:", bg="#2c3e50", fg="#bdc3c7").pack()
        self.api_entry = tk.Entry(root, width=60, show="*", bg="#34495e", fg="white", borderwidth=0)
        self.api_entry.pack(pady=5, ipady=5)

        self.file_path = ""
        self.btn_file = tk.Button(root, text="Select English SRT File", command=self.open_file, bg="#2980b9", fg="white", width=25)
        self.btn_file.pack(pady=15)
        self.lbl_status_file = tk.Label(root, text="No file selected", bg="#2c3e50", fg="#95a5a6")
        self.lbl_status_file.pack()

        settings_frame = tk.Frame(root, bg="#2c3e50")
        settings_frame.pack(pady=20)
        tk.Label(settings_frame, text="Chunk Size:", bg="#2c3e50", fg="white").grid(row=0, column=0, padx=5)
        self.chunk_var = tk.StringVar(value="30")
        self.chunk_menu = ttk.Combobox(settings_frame, textvariable=self.chunk_var, values=["10", "20", "30", "40", "50"], width=5)
        self.chunk_menu.grid(row=0, column=1, padx=5)
        tk.Label(settings_frame, text="Language:", bg="#2c3e50", fg="white").grid(row=0, column=2, padx=5)
        self.lang_var = tk.StringVar(value="Sinhala")
        self.lang_menu = ttk.Combobox(settings_frame, textvariable=self.lang_var, values=["Sinhala", "Tamil", "Hindi"], width=10)
        self.lang_menu.grid(row=0, column=3, padx=5)

        self.log_box = tk.Text(root, height=12, width=70, bg="#1a1a1a", fg="#2ecc71", font=("Consolas", 9))
        self.log_box.pack(pady=10, padx=20)

        self.btn_start = tk.Button(root, text="START TRANSLATION", command=self.run_thread, bg="#27ae60", fg="white", font=("Arial", 11, "bold"), width=30, height=2)
        self.btn_start.pack(pady=10)

    def log(self, text):
        self.log_box.insert(tk.END, text + "\n")
        self.log_box.see(tk.END)

    def open_file(self):
        self.file_path = filedialog.askopenfilename(filetypes=[("SRT files", "*.srt")])
        if self.file_path:
            self.lbl_status_file.config(text=os.path.basename(self.file_path), fg="white")

    def run_thread(self):
        if not self.file_path or not self.api_entry.get():
            messagebox.showwarning("Warning", "Enter API Key and select a file!")
            return
        self.btn_start.config(state="disabled")
        threading.Thread(target=self.start_logic, daemon=True).start()

    def start_logic(self):
        try:
            genai.configure(api_key=self.api_entry.get())
            # Updated Model to fix 404 Error
            model = genai.GenerativeModel('gemini-1.5-flash-latest')
            
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = f.read()

            blocks = re.split(r'\n\s*\n', data.strip())
            c_size = int(self.chunk_var.get())
            target = self.lang_var.get()
            output_content = ""

            self.log(f"Process Started. Total chunks: {(len(blocks)//c_size)+1}")

            for i in range(0, len(blocks), c_size):
                batch = "\n\n".join(blocks[i:i + c_size])
                prompt = f"Translate the following SRT subtitles to natural {target}. Output ONLY the translated SRT text. Keep timing and numbers original:\n\n{batch}"
                
                try:
                    response = model.generate_content(prompt)
                    if response.text:
                        clean = response.text.replace('```srt', '').replace('```', '').strip()
                        output_content += clean + "\n\n"
                        self.log(f"Completed chunk { (i//c_size) + 1 }")
                except Exception as api_err:
                    self.log(f"Retry: {str(api_err)}")
                    time.sleep(15)
                
                time.sleep(10) # 429 Error Safety

            save_path = filedialog.asksaveasfilename(defaultextension=".srt", initialfile=f"Translated_{target}.srt")
            if save_path:
                with open(save_path, 'w', encoding='utf-8') as f:
                    f.write(output_content)
                self.log("Success! File saved.")
                messagebox.showinfo("Done", "Translation completed!")

        except Exception as e:
            self.log(f"Error: {str(e)}")
            messagebox.showerror("Error", str(e))
        finally:
            self.btn_start.config(state="normal")

if __name__ == "__main__":
    root = tk.Tk()
    app = SubtitleApp(root)
    root.mainloop()
