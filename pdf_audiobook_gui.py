
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import fitz  
import pyttsx3
import os
from tempfile import mkstemp

def extract_text_from_pdf(path):
    doc = fitz.open(path)
    pages = []
    for i in range(doc.page_count):
        page = doc.load_page(i)
        txt = page.get_text("text").strip()
        pages.append(txt)
    doc.close()
    return pages


class TTSPlayer:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.rate = self.engine.getProperty("rate")
        self.volume = self.engine.getProperty("volume")
        self._playing = False
        self._paused = False
        self._stop_flag = False

    def set_rate(self, r):
        self.rate = int(r)
        self.engine.setProperty("rate", self.rate)

    def set_volume(self, v):
        self.volume = float(v)
        self.engine.setProperty("volume", self.volume)

    def play_text(self, text, on_done=None):
        def run():
            self._playing = True
            self._paused = False
            self._stop_flag = False
            self.engine.connect('finished-utterance', lambda name, completed: None)
            self.engine.say(text)
            try:
                self.engine.runAndWait()
            except RuntimeError:
                
                pass
            self._playing = False
            if on_done:
                on_done()
        t = threading.Thread(target=run, daemon=True)
        t.start()

    def stop(self):
        self._stop_flag = True
        try:
            self.engine.stop()
        except Exception:
            pass
        self._playing = False

    def save_to_file(self, text, out_path, on_done=None):
      
        def run():
            try:
                self.engine.save_to_file(text, out_path)
                self.engine.runAndWait()
            except Exception as e:
                print("Save error:", e)
            if on_done:
                on_done()
        t = threading.Thread(target=run, daemon=True)
        t.start()


class PdfAudioApp:
    def __init__(self, root):
        self.root = root
        root.title("PDF → Audiobook Converter")
        root.geometry("720x480")

        self.player = TTSPlayer()
        self.pages = []
        self.current_page = 0

        frm_top = ttk.Frame(root, padding=8)
        frm_top.pack(fill="x")
        ttk.Button(frm_top, text="Open PDF", command=self.open_pdf).pack(side="left")
        ttk.Button(frm_top, text="Play", command=self.play).pack(side="left", padx=6)
        ttk.Button(frm_top, text="Pause/Resume", command=self.pause_resume).pack(side="left")
        ttk.Button(frm_top, text="Stop", command=self.stop).pack(side="left", padx=6)
        ttk.Button(frm_top, text="Export Audio (WAV)", command=self.export_audio).pack(side="left", padx=6)

       
        frm_controls = ttk.Frame(root, padding=8)
        frm_controls.pack(fill="x")
        ttk.Label(frm_controls, text="Rate (words/min):").grid(column=0, row=0, sticky="w")
        self.rate_var = tk.IntVar(value=self.player.rate)
        rate_scale = ttk.Scale(frm_controls, from_=80, to=300, orient="horizontal", variable=self.rate_var, command=self.on_rate_change)
        rate_scale.grid(column=1, row=0, sticky="ew", padx=6)
        frm_controls.columnconfigure(1, weight=1)

        ttk.Label(frm_controls, text="Volume:").grid(column=0, row=1, sticky="w")
        self.vol_var = tk.DoubleVar(value=self.player.volume)
        vol_scale = ttk.Scale(frm_controls, from_=0.0, to=1.0, orient="horizontal", variable=self.vol_var, command=self.on_vol_change)
        vol_scale.grid(column=1, row=1, sticky="ew", padx=6)

        lbl = ttk.Label(root, text="Page Text Preview (editable):")
        lbl.pack(anchor="w", padx=8)
        self.text = tk.Text(root, wrap="word", height=15)
        self.text.pack(fill="both", expand=True, padx=8, pady=4)

       
        frm_nav = ttk.Frame(root, padding=8)
        frm_nav.pack(fill="x")
        self.page_label = ttk.Label(frm_nav, text="Page: 0 / 0")
        self.page_label.pack(side="left")
        ttk.Button(frm_nav, text="Prev", command=self.prev_page).pack(side="right")
        ttk.Button(frm_nav, text="Next", command=self.next_page).pack(side="right", padx=6)

    def open_pdf(self):
        path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if not path:
            return
        try:
            pages = extract_text_from_pdf(path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open PDF: {e}")
            return
       
        pages = [p for p in pages if p.strip()]
        self.pages = pages
        self.current_page = 0
        self.show_page()
        messagebox.showinfo("Loaded", f"Loaded {len(self.pages)} non-empty pages.")

    def show_page(self):
        self.text.delete("1.0", "end")
        if not self.pages:
            self.page_label.config(text="Page: 0 / 0")
            return
        txt = self.pages[self.current_page]
        self.text.insert("1.0", txt)
        self.page_label.config(text=f"Page: {self.current_page+1} / {len(self.pages)}")

    def next_page(self):
        if not self.pages: return
        if self.current_page < len(self.pages)-1:
            self.current_page += 1
            self.show_page()

    def prev_page(self):
        if not self.pages: return
        if self.current_page > 0:
            self.current_page -= 1
            self.show_page()

    def on_rate_change(self, _=None):
        val = self.rate_var.get()
        self.player.set_rate(val)

    def on_vol_change(self, _=None):
        val = self.vol_var.get()
        self.player.set_volume(val)

    def play(self):
        text = self.text.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("No text", "No text to play.")
            return
        self.player.set_rate(self.rate_var.get())
        self.player.set_volume(self.vol_var.get())
        self.player.play_text(text)

    def pause_resume(self):
        
        messagebox.showinfo("Note", "Pause/Resume behavior is limited. Use Stop and Play to restart from current text.")
       

    def stop(self):
        self.player.stop()

    def export_audio(self):
        text = "\n\n".join(self.pages) if self.pages else self.text.get("1.0", "end").strip()
        if not text.strip():
            messagebox.showwarning("No text", "No text to export.")
            return
        out = filedialog.asksaveasfilename(defaultextension=".wav", filetypes=[("WAV audio", "*.wav"), ("MP3 audio", "*.mp3")])
        if not out:
            return
       
        base, ext = os.path.splitext(out)
        if ext.lower() == ".mp3":
            
            tmp_fd, tmp_path = mkstemp(suffix=".wav")
            os.close(tmp_fd)
            def on_done():
                try:
                   
                    from pydub import AudioSegment
                    AudioSegment.from_wav(tmp_path).export(out, format="mp3")
                    os.remove(tmp_path)
                    messagebox.showinfo("Saved", f"Saved MP3 to: {out}")
                except Exception as e:
                    messagebox.showwarning("Saved as WAV instead", f"Could not convert to MP3 automatically: {e}\nSaved WAV at {tmp_path}")
            self.player.save_to_file(text, tmp_path, on_done=on_done)
        else:
            def done_cb():
                messagebox.showinfo("Saved", f"Saved WAV to: {out}")
            self.player.save_to_file(text, out, on_done=done_cb)

if __name__ == "__main__":
    root = tk.Tk()
    app = PdfAudioApp(root)
    root.mainloop()
