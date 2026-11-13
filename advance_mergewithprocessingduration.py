import sys
import os
import subprocess
import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QListWidget, QFileDialog, QMessageBox, QLabel, 
                             QProgressBar, QListWidgetItem, QMenu, QAction, QInputDialog, QShortcut)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QKeySequence

# --- SLEEK & MODERN DARK THEME ---
DARK_STYLESHEET = """
QMainWindow { background-color: #121212; }
QWidget { color: #E0E0E0; font-family: 'Segoe UI', Arial; font-size: 13px; }
QPushButton { background-color: #2D2D2D; border: 1px solid #404040; border-radius: 8px; padding: 10px; font-weight: bold; }
QPushButton:hover { background-color: #404040; border-color: #3D5AFE; }
QPushButton#btnMerge { background-color: #D50000; color: white; font-size: 15px; padding: 15px; border-radius: 8px; font-weight: 900; }
QPushButton#btnMerge:hover { background-color: #FF1744; }
QPushButton#btnMerge:disabled { background-color: #3E2723; color: #9E9E9E; }
QListWidget { background-color: #1E1E1E; border: 1px solid #333333; border-radius: 8px; padding: 10px; outline: none; }
QListWidget::item { background-color: #2C2C2C; border-radius: 6px; margin-bottom: 5px; padding: 10px; }
QListWidget::item:selected { background-color: #1A237E; border: 1px solid #3D5AFE; }
QProgressBar { border: 1px solid #404040; border-radius: 6px; background-color: #1E1E1E; text-align: center; color: white; font-weight: bold; font-size: 12px; }
QProgressBar::chunk { background-color: #D50000; border-radius: 5px; }
QMenu { background-color: #2D2D2D; color: white; border: 1px solid #404040; }
QMenu::item:selected { background-color: #3D5AFE; }
"""

# --- ULTRA FAST BACKGROUND THREAD (WITH LIVE % PROGRESS) ---
class FastMergeThread(QThread):
    finished = pyqtSignal(bool, str)
    progress_update = pyqtSignal(int) # Naya Signal percentage bhejne ke liye

    def __init__(self, output_path, list_file, videos_data, total_duration):
        super().__init__()
        self.output_path = output_path
        self.list_file = list_file
        self.videos_data = videos_data 
        self.total_duration = total_duration # Total video length seconds mein

    def run(self):
        # FAST STREAM COPY WITH PROGRESS MONITORING
        command = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", self.list_file, 
            "-c", "copy", 
            "-metadata", "title=V SUNHARE POWERPLAY Engine",
            "-metadata", "artist=V SUNHARE POWERPLAY",
            "-metadata", "comment=Merged by SunhareTech Pro Tools",
            "-progress", "-", "-nostats", # FFmpeg ko terminal ki jagah code mein progress bhejne ko bolna
            self.output_path
        ]
        
        try:
            # Popen use kiya taaki real-time data read ho sake
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            
            # Live Percentage Calculate Karna
            for line in process.stdout:
                if "out_time_ms=" in line:
                    try:
                        ms_str = line.split("=")[1].strip()
                        if ms_str != "N/A":
                            current_sec = int(ms_str) / 1000000.0 # Microseconds to Seconds
                            if self.total_duration > 0:
                                pct = int((current_sec / self.total_duration) * 100)
                                # Percentage ko 99% tak rok kar rakhein jab tak process puri na ho
                                self.progress_update.emit(min(pct, 99))
                    except: pass
            
            process.wait()
            
            if process.returncode == 0:
                # --- AUTO GENERATE YOUTUBE CHAPTERS ---
                chapters_file = os.path.splitext(self.output_path)[0] + "_Chapters.txt"
                with open(chapters_file, "w", encoding="utf-8") as f:
                    f.write("📺 YOUTUBE TIMESTAMPS (V SUNHARE POWERPLAY)\n")
                    f.write("-" * 50 + "\n\n")
                    
                    current_time = 0.0
                    for v in self.videos_data:
                        time_str = str(datetime.timedelta(seconds=int(current_time)))
                        if time_str.startswith("0:"): time_str = "0" + time_str 
                        
                        filename = os.path.splitext(os.path.basename(v['path']))[0]
                        f.write(f"{time_str} - {filename}\n")
                        
                        actual_duration = v['duration']
                        if v['end'] > 0: actual_duration = v['end'] - v['start']
                        elif v['start'] > 0: actual_duration -= v['start']
                        
                        current_time += actual_duration

                    f.write("\n🔥 Subscribe to V SUNHARE POWERPLAY for more!\n")

                self.finished.emit(True, self.output_path)
            else:
                self.finished.emit(False, "FFmpeg Process Failed.")
        except Exception as e:
            self.finished.emit(False, str(e))

# --- MAIN APP ---
class VSunhareStudio(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.setup_shortcuts()

    def setup_shortcuts(self):
        QShortcut(QKeySequence("Delete"), self, self.remove_file)
        QShortcut(QKeySequence("Ctrl+Up"), self, self.move_up)
        QShortcut(QKeySequence("Ctrl+Down"), self, self.move_down)
        QShortcut(QKeySequence("Ctrl+M"), self, self.start_merge)

    def initUI(self):
        self.setWindowTitle('V SUNHARE POWERPLAY - YouTube Production Engine')
        self.resize(850, 550)
        self.setStyleSheet(DARK_STYLESHEET)
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header = QLabel("🔥 V SUNHARE POWERPLAY STUDIO 🔥\nDouble-Click to Preview | Right-Click to Trim | Ctrl+M to Merge")
        header.setStyleSheet("font-size: 15px; font-weight: bold; color: #FF5252; margin-bottom: 10px;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        # Interactive List Widget
        self.listWidget = QListWidget()
        self.listWidget.setAcceptDrops(True)
        self.listWidget.setDragDropMode(QListWidget.InternalMove)
        self.listWidget.itemDoubleClicked.connect(self.preview_video)
        self.listWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.listWidget.customContextMenuRequested.connect(self.show_context_menu) 
        layout.addWidget(self.listWidget)

        # Drag & Drop override
        self.listWidget.dragEnterEvent = lambda e: e.acceptProposedAction() if e.mimeData().hasUrls() else super(QListWidget, self.listWidget).dragEnterEvent(e)
        self.listWidget.dragMoveEvent = lambda e: e.acceptProposedAction() if e.mimeData().hasUrls() else super(QListWidget, self.listWidget).dragMoveEvent(e)
        self.listWidget.dropEvent = self.handle_drop

        # Stats
        self.lblStats = QLabel("Ready.")
        self.lblStats.setStyleSheet("color: #9E9E9E; font-weight: bold;")
        layout.addWidget(self.lblStats)

        # Buttons
        btn_layout = QHBoxLayout()
        self.btnAdd = QPushButton("➕ Add Gameplays")
        self.btnAdd.clicked.connect(self.browse_files)
        
        self.btnRemove = QPushButton("❌ Remove (Del)")
        self.btnRemove.clicked.connect(self.remove_file)

        for btn in [self.btnAdd, self.btnRemove]: btn_layout.addWidget(btn)
        layout.addLayout(btn_layout)

        # PROGRESS BAR (Ab Badi aur Percentage wali hogi)
        self.progress = QProgressBar()
        self.progress.setFixedHeight(22) # Height badha di taaki percentage clearly dikhe
        self.progress.setTextVisible(True)
        self.progress.setFormat("%p%") # Format as percentage
        self.progress.setValue(0)
        layout.addWidget(self.progress)

        self.btnMerge = QPushButton("🚀 FAST MERGE & GENERATE CHAPTERS")
        self.btnMerge.setObjectName("btnMerge")
        self.btnMerge.clicked.connect(self.start_merge)
        layout.addWidget(self.btnMerge)

    # --- ADVANCED LOGIC ---
    def get_duration(self, file_path):
        try:
            cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', file_path]
            return float(subprocess.check_output(cmd, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0).strip())
        except: return 0.0

    def handle_drop(self, e):
        if e.mimeData().hasUrls():
            files = [u.toLocalFile() for u in e.mimeData().urls() if u.toLocalFile().lower().endswith(('.mp4', '.mkv', '.mov', '.avi'))]
            if files: self.add_files_to_list(files)
            e.acceptProposedAction()

    def browse_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Videos", "", "Video Files (*.mp4 *.mkv *.mov *.avi)")
        if files: self.add_files_to_list(files)

    def add_files_to_list(self, files):
        self.lblStats.setText("Analyzing files...")
        QApplication.processEvents()
        
        for f in files:
            file_name = os.path.basename(f)
            dur = self.get_duration(f)
            meta = {'path': f, 'duration': dur, 'start': 0, 'end': 0}
            
            dur_str = str(datetime.timedelta(seconds=int(dur)))
            display_text = f"🎬 {file_name}   |   ⏳ {dur_str}"
            
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, meta)
            self.listWidget.addItem(item)
            
        self.update_stats()

    def update_stats(self):
        self.lblStats.setText(f"Total Videos: {self.listWidget.count()}")

    def preview_video(self, item):
        path = item.data(Qt.UserRole)['path']
        subprocess.Popen(['ffplay', '-autoexit', '-window_title', 'V SUNHARE PREVIEW', path], 
                         creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)

    def show_context_menu(self, position):
        item = self.listWidget.itemAt(position)
        if not item: return

        menu = QMenu()
        trim_act = QAction("✂️ Trim Clip (Set Start/End)", self)
        trim_act.triggered.connect(lambda: self.trim_video(item))
        menu.addAction(trim_act)
        menu.exec_(self.listWidget.viewport().mapToGlobal(position))

    def trim_video(self, item):
        meta = item.data(Qt.UserRole)
        start_sec, ok1 = QInputDialog.getDouble(self, "Trim Start", "Skip first X seconds (e.g. Loading Screen):", meta['start'], 0, meta['duration'], 1)
        if not ok1: return
        
        end_sec, ok2 = QInputDialog.getDouble(self, "Trim End", f"Stop at X seconds (0 for full video. Max {meta['duration']}):", meta['end'], 0, meta['duration'], 1)
        if not ok2: return

        meta['start'] = start_sec
        meta['end'] = end_sec
        item.setData(Qt.UserRole, meta)
        
        filename = os.path.basename(meta['path'])
        dur_str = str(datetime.timedelta(seconds=int(meta['duration'])))
        trim_str = f" [✂️ Trimmed {start_sec}s to {end_sec if end_sec>0 else 'End'}s]" if (start_sec>0 or end_sec>0) else ""
        item.setText(f"🎬 {filename}   |   ⏳ {dur_str}{trim_str}")

    def remove_file(self):
        for item in self.listWidget.selectedItems(): self.listWidget.takeItem(self.listWidget.row(item))
        self.update_stats()

    def move_up(self):
        row = self.listWidget.currentRow()
        if row > 0:
            self.listWidget.insertItem(row - 1, self.listWidget.takeItem(row))
            self.listWidget.setCurrentRow(row - 1)

    def move_down(self):
        row = self.listWidget.currentRow()
        if row < self.listWidget.count() - 1 and row != -1:
            self.listWidget.insertItem(row + 1, self.listWidget.takeItem(row))
            self.listWidget.setCurrentRow(row + 1)

    # --- UI UPDATE FUNCTION ---
    def update_progress_ui(self, value):
        self.progress.setValue(value)
        self.btnMerge.setText(f"⏳ FAST MERGING... {value}%")

    def start_merge(self):
        if self.listWidget.count() < 2:
            QMessageBox.warning(self, "Warning", "Merge karne ke liye kam se kam 2 videos chahiye.")
            return

        videos_data = [self.listWidget.item(i).data(Qt.UserRole) for i in range(self.listWidget.count())]
        ext = os.path.splitext(videos_data[0]['path'])[1]
        default_out = f"VSUNHARE_Final_Upload{ext}"
        
        output_path, _ = QFileDialog.getSaveFileName(self, "Save Merged Video", default_out, f"Video (*{ext})")
        if not output_path: return

        # PREPARE CONCAT LIST & CALCULATE TOTAL TIME
        self.list_file = "concat_list.txt"
        total_duration = 0.0

        with open(self.list_file, "w", encoding="utf-8") as f:
            for v in videos_data:
                # Format fixing logic
                safe_path = os.path.abspath(v['path']).replace("'", "'\\''") 
                f.write(f"file '{safe_path}'\n")
                
                # Trim Logic & Total Time Calculation
                actual = v['duration']
                if v['start'] > 0: 
                    f.write(f"inpoint {v['start']}\n")
                    actual -= v['start']
                if v['end'] > 0: 
                    f.write(f"outpoint {v['end']}\n")
                    actual = v['end'] - v['start'] if v['start'] > 0 else v['end']
                    
                total_duration += actual

        self.btnMerge.setText("⏳ STARTING MERGE... 0%")
        self.btnMerge.setEnabled(False)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)

        # LINK THREAD TO UI
        self.thread = FastMergeThread(output_path, self.list_file, videos_data, total_duration)
        self.thread.progress_update.connect(self.update_progress_ui) # Percentage signal link
        self.thread.finished.connect(self.on_merge_complete)
        self.thread.start()

    def on_merge_complete(self, success, message):
        self.progress.setValue(100)
        self.btnMerge.setText("🚀 FAST MERGE & GENERATE CHAPTERS")
        self.btnMerge.setEnabled(True)
        if os.path.exists(self.list_file): os.remove(self.list_file)

        if success:
            folder = os.path.dirname(message)
            if os.name == 'nt': os.startfile(folder)
            elif sys.platform == 'darwin': subprocess.Popen(['open', folder])
            else: subprocess.Popen(['xdg-open', folder])
            
            QMessageBox.information(self, "V SUNHARE STUDIO", "🎉 Fast Render Successful!\n\n1. YouTube Chapters (.txt) generated.\n2. V SUNHARE metadata applied.")
            self.progress.setValue(0)
        else:
            QMessageBox.critical(self, "Error", f"Processing failed.\nReason: {message}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = VSunhareStudio()
    ex.show()
    sys.exit(app.exec_())
