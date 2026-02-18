import customtkinter as ctk
import os
import threading
import yt_dlp

# --- КОНФИГ ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")

class VibeSaverApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # ОКНО
        self.title("VibeSaver")
        self.geometry("360x460")
        self.resizable(False, False)
        self.configure(fg_color="#050505")

        self.ffmpeg_path = os.path.join(os.getcwd(), 'bin', 'ffmpeg.exe')
        self.selected_quality = "1080p (Full HD)"
        self.is_dropdown_open = False

        # --- 1. ЛОГОТИП ---
        self.logo = ctk.CTkLabel(self, 
                                 text="⚡ VIBESAVER ⚡", 
                                 font=("Impact", 28), 
                                 text_color="#00FF66")
        self.logo.place(relx=0.5, y=40, anchor="center")

        # --- КОНТЕЙНЕР ФОРМЫ ---
        self.form_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.form_frame.pack(fill="both", expand=True, padx=30, pady=(80, 20))

        # 2. ИНПУТ
        self.entry_url = ctk.CTkEntry(self.form_frame, placeholder_text="Вставь ссылку...", height=45,
                                      font=("Arial", 14), fg_color="#151515", border_color="#333",
                                      border_width=1, corner_radius=12)
        self.entry_url.pack(fill="x", pady=(0, 15))

        # 3. КНОПКА ВЫБОРА (ТРИГГЕР)
        self.btn_selector = ctk.CTkButton(self.form_frame,
                                          text=f"{self.selected_quality} ▼",
                                          command=self.toggle_dropdown,
                                          height=45,
                                          font=("Arial Bold", 13),
                                          fg_color="#151515",
                                          hover_color="#222",
                                          text_color="white",
                                          corner_radius=12)
        self.btn_selector.pack(fill="x", pady=(0, 15))

        # 4. КНОПКА СКАЧАТЬ
        self.btn_download = ctk.CTkButton(self.form_frame, 
                                          text="СКАЧАТЬ", 
                                          command=self.start_thread,
                                          height=55,
                                          font=("Arial Black", 16),
                                          fg_color="#00FF66",
                                          text_color="black",
                                          hover_color="#00CC52",
                                          corner_radius=12)
        self.btn_download.pack(fill="x", pady=(0, 15))

        # 5. ПРОГРЕСС
        self.progress_bar = ctk.CTkProgressBar(self.form_frame, height=5, progress_color="#00FF66", fg_color="#222")
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", pady=(0, 10))

        # 6. СТАТУС (Теперь он показывает проценты)
        self.status = ctk.CTkLabel(self.form_frame, text="Готов к загрузке", font=("Arial", 12), text_color="#777")
        self.status.pack()

        # 7. ПОДСКАЗКА (Сделал светлее, чтобы было видно)
        ctk.CTkLabel(self, 
                     text="💡 Подсказка: Если ссылка не вставляется — смени раскладку на EN", 
                     font=("Arial", 10), 
                     text_color="#888").pack(side="bottom", pady=15)

        # --- СЛОЙ ВЫПАДАЮЩЕГО СПИСКА ---
        self.dropdown_frame = ctk.CTkFrame(self, 
                                           width=300, 
                                           fg_color="#111", 
                                           corner_radius=12,
                                           border_width=1, 
                                           border_color="#333")
        
        resolutions = ["4K (Ultra HD)", "2K (1440p)", "1080p (Full HD)", "720p (HD)", "480p", "MP3 (Audio Only)"]
        
        for i, res in enumerate(resolutions):
            pad_y = (2, 2)
            if i == 0: pad_y = (10, 2) 
            if i == len(resolutions) - 1: pad_y = (2, 10)
            
            ctk.CTkButton(self.dropdown_frame, text=res, command=lambda r=res: self.select_option(r),
                          fg_color="transparent", hover_color="#00FF66", text_color="white",
                          height=30, anchor="center", corner_radius=8).pack(fill="x", padx=5, pady=pad_y)

        if not os.path.exists(self.ffmpeg_path):
             self.status.configure(text="ОШИБКА: нет bin/ffmpeg.exe", text_color="red")
             self.btn_download.configure(state="disabled")

    # --- ЛОГИКА ---
    def toggle_dropdown(self):
        if self.is_dropdown_open:
            self.dropdown_frame.place_forget()
            self.btn_selector.configure(text=f"{self.selected_quality} ▼")
            self.is_dropdown_open = False
        else:
            self.dropdown_frame.place(x=30, y=190) 
            self.dropdown_frame.lift()
            self.btn_selector.configure(text=f"{self.selected_quality} ▲")
            self.is_dropdown_open = True

    def select_option(self, option):
        self.selected_quality = option
        self.btn_selector.configure(text=f"{option} ▼")
        self.dropdown_frame.place_forget()
        self.is_dropdown_open = False

    def start_thread(self):
        url = self.entry_url.get()
        if not url: return
        self.btn_download.configure(state="disabled", text="...", fg_color="#222", text_color="white")
        self.status.configure(text="Инициализация...", text_color="#00FF66")
        self.progress_bar.set(0)
        threading.Thread(target=self.run_logic, args=(url,)).start()

    def run_logic(self, url):
        qual = self.selected_quality
        
        # --- ХУК ДЛЯ ОТСЛЕЖИВАНИЯ ПРОГРЕССА ---
        def hook(d):
            if d['status'] == 'downloading':
                try:
                    # Берем готовый процент "45.5%"
                    pct_text = d.get('_percent_str', '0%')
                    # Берем сырые байты для бара
                    total = d.get('total_bytes') or d.get('total_bytes_estimate')
                    downloaded = d.get('downloaded_bytes', 0)
                    
                    if total:
                        # Обновляем бар (0.0 - 1.0)
                        self.progress_bar.set(downloaded / total)
                    
                    # Пишем статус: "Загрузка: 45.5%"
                    self.status.configure(text=f"Загрузка: {pct_text}", text_color="white")
                except: pass
            elif d['status'] == 'finished':
                self.status.configure(text="Обработка / Склейка...", text_color="#AAA")

        fmt = ""
        if "4K" in qual: fmt = "bestvideo[height<=2160]+bestaudio/best[height<=2160]"
        elif "2K" in qual: fmt = "bestvideo[height<=1440]+bestaudio/best[height<=1440]"
        elif "1080p" in qual: fmt = "bestvideo[height<=1080]+bestaudio/best[height<=1080]"
        elif "720p" in qual: fmt = "bestvideo[height<=720]+bestaudio/best[height<=720]"
        elif "480p" in qual: fmt = "bestvideo[height<=480]+bestaudio/best[height<=480]"
        else: fmt = "bestaudio/best"

        opts = {'format': fmt, 'outtmpl': '%(title)s.%(ext)s', 'progress_hooks': [hook], 'noplaylist': True, 'ffmpeg_location': self.ffmpeg_path, 'quiet': True, 'no_warnings': True}
        if "MP3" in qual: opts['postprocessors'] = [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}]
        else: opts['merge_output_format'] = 'mp4'; opts['postprocessor_args'] = ['-c:v', 'copy', '-c:a', 'aac']

        try:
            with yt_dlp.YoutubeDL(opts) as ydl: ydl.download([url])
            # ФИНАЛЬНЫЙ СТАТУС
            self.status.configure(text="Файл сохранен в папке с прогой! ✅", text_color="#00FF66")
            self.progress_bar.set(1)
            self.entry_url.delete(0, 'end')
        except Exception as e: 
            print(e)
            self.status.configure(text="Ошибка скачивания ❌", text_color="red")
        finally: 
            self.btn_download.configure(state="normal", text="СКАЧАТЬ", fg_color="#00FF66", text_color="black")

if __name__ == "__main__":
    app = VibeSaverApp()
    app.mainloop()