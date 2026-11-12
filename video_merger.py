import sys
import os
import subprocess
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QListWidget, QFileDialog, QMessageBox, 
                             QLabel, QListWidgetItem, QProgressBar)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QFont

# --- THEME (Professional Dark Mode) ---
DARK_STYLESHEET = """
QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: 'Segoe UI', Arial, sans-serif;
}
QPushButton {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 8px 12px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #45475a;
}
QPushButton:pressed {
    background-color: #585b70;
}
QPushButton#mergeBtn {
    background-color: #89b4fa;
    color: #11111b;
    font-size: 14px;
    border: none;
    padding: 12px;
}
QPushButton#mergeBtn:hover {
    background-color: #b4befe;
}
QPushButton#mergeBtn:disabled {
    background-color: #45475a;
    color: #a6adc8;
}
QListWidget {
    background-color: #181825;
    border: 1px solid #313244;
    border-radius: 8px;
    padding: 5px;
    outline: none;
}
QListWidget::item {
    background-color: #27273a;
    border-radius: 4px;
    margin: 3px;
    padding: 8px;
}
QListWidget::item:selected {
    background-color: #313244;
    border: 1px solid #89b4fa;
}
QProgressBar {
    border: 1px solid #313244;
    border-radius: 5px;
    text-align: center;
    color: #cdd6f4;
}
QProgressBar::chunk {
    background-color: #89b4fa;
    border-radius: 4px;
}
"""

# --- BACKGROUND THREAD FOR MERGING (Anti-Freeze) ---
class MergeThread(QThread):
    finished = pyqtSignal(bool, str) # status, message

    def __init__(self, list_file, output_path):
        super().__init__()
        self.list_file = list_file
        self.output_path = output_path

    def run(self):
        command = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", self.list_file, "-c", "copy", self.output_path]
        try:
            subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.finished.emit(True, self.output_path)
        except subprocess.CalledProcessError as e:
            self.finished.emit(False, str(e.stderr.decode('utf-8')))

# --- DRAG & DROP WIDGET ---
class DragDropListWidget(QListWidget):
    filesDropped = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragDropMode(QListWidget.InternalMove)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): event.acceptProposedAction()
        else: super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls(): event.acceptProposedAction()
        else: super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            files = [u.toLocalFile() for u in event.mimeData().urls() if u.toLocalFile().lower().endswith(('.mp4', '.mkv', '.avi', '.mov'))]
            if files: self.filesDropped.emit(files)
            event.acceptProposedAction()
        else: super().dropEvent(event)

# --- MAIN APPLICATION ---
class VideoMergerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('SunhareTech Video Studio - Pro Merger')
        self.resize(800, 550)
        self.setStyleSheet(DARK_STYLESHEET)

        layout = QVBoxLayout()

        # Header
        header = QLabel('Drag & Drop Videos Here')
        header.setFont(QFont("Segoe UI", 16, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        # List Widget
        self.listWidget = DragDropListWidget()
        self.listWidget.filesDropped.connect(self.process_added_files)
        layout.addWidget(self.listWidget)

        # Stats Layout
        stats_layout = QHBoxLayout()
        self.lblTotalFiles = QLabel('Files: 0')
        self.lblTotalFiles.setStyleSheet("color: #a6adc8; font-weight: bold;")
        self.lblTotalTime = QLabel('Total Duration: 00:00:00')
        self.lblTotalTime.setStyleSheet("color: #f38ba8; font-weight: bold; font-size: 14px;")
        
        stats_layout.addWidget(self.lblTotalFiles)
        stats_layout.addStretch()
        stats_layout.addWidget(self.lblTotalTime)
        layout.addLayout(stats_layout)

        # Buttons
        btnLayout = QHBoxLayout()
        self.btnAdd = QPushButton('➕ Add Files')
        self.btnAdd.clicked.connect(self.add_videos)
        self.btnUp = QPushButton('⬆️ Up')
        self.btnUp.clicked.connect(self.move_up)
        self.btnDown = QPushButton('⬇️ Down')
        self.btnDown.clicked.connect(self.move_down)
        self.btnRemove = QPushButton('🗑️ Remove')
        self.btnRemove.clicked.connect(self.remove_video)
        
        for btn in [self.btnAdd, self.btnUp, self.btnDown, self.btnRemove]:
            btnLayout.addWidget(btn)
        layout.addLayout(btnLayout)

        # Progress Bar
        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(8)
        layout.addWidget(self.progress)

        # Merge Button
        self.btnMerge = QPushButton('🚀 MERGE & EXPORT')
        self.btnMerge.setObjectName("mergeBtn")
        self.btnMerge.clicked.connect(self.merge_videos)
        layout.addWidget(self.btnMerge)

        self.setLayout(layout)

    # --- ADVANCED VIDEO METADATA (ffprobe) ---
    def get_video_info(self, file_path):
        duration, resolution = 0.0, "Unknown"
        try:
            # Get Duration
            cmd_dur = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', file_path]
            duration = float(subprocess.run(cmd_dur, capture_output=True, text=True).stdout.strip())
            
            # Get Resolution
            cmd_res = ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'csv=s=x:p=0', file_path]
            resolution = subprocess.run(cmd_res, capture_output=True, text=True).stdout.strip()
        except: pass
        return duration, resolution

    def format_size(self, size_bytes):
        if size_bytes < 1024 * 1024: return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024: return f"{size_bytes / (1024 * 1024):.1f} MB"
        else: return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

    def format_time(self, seconds):
        mins, secs = divmod(int(seconds), 60)
        hours, mins = divmod(mins, 60)
        return f"{hours:02d}:{mins:02d}:{secs:02d}" if hours > 0 else f"{mins:02d}:{secs:02d}"

    def process_added_files(self, files):
        self.btnMerge.setText("Analyzing Videos...")
        self.btnMerge.setEnabled(False)
        QApplication.processEvents()

        for f in files:
            dur_sec, res = self.get_video_info(f)
            size_str = self.format_size(os.path.getsize(f))
            file_name = os.path.basename(f)
            
            # Professional Display Format: [Time] | Resolution | Size | Filename
            display_text = f"⏳ {self.format_time(dur_sec)}   |   🖥️ {res}   |   📦 {size_str}   |   🎬 {file_name}"
            
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, {'path': f, 'duration': dur_sec, 'res': res})
            self.listWidget.addItem(item)
            
        self.update_stats()
        self.btnMerge.setText("🚀 MERGE & EXPORT")
        self.btnMerge.setEnabled(True)

    def add_videos(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Videos", "", "Video Files (*.mp4 *.mkv *.avi *.mov)")
        if files: self.process_added_files(files)

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

    def remove_video(self):
        if self.listWidget.currentRow() != -1:
            self.listWidget.takeItem(self.listWidget.currentRow())
            self.update_stats()

    def update_stats(self):
        total_sec = sum(self.listWidget.item(i).data(Qt.UserRole).get('duration', 0) for i in range(self.listWidget.count()))
        self.lblTotalTime.setText(f"Total Duration: {self.format_time(total_sec)}")
        self.lblTotalFiles.setText(f"Files: {self.listWidget.count()}")

    def merge_videos(self):
        if self.listWidget.count() < 2:
            QMessageBox.warning(self, "Warning", "Please add at least 2 videos to merge.")
            return

        videos = [self.listWidget.item(i).data(Qt.UserRole)['path'] for i in range(self.listWidget.count())]
        
        default_out = f"{os.path.splitext(os.path.basename(videos[0]))[0]}_merged.mp4"
        output_path, _ = QFileDialog.getSaveFileName(self, "Export Video As", default_out, "MP4 Video (*.mp4)")
        if not output_path: return

        self.list_file = "concat_list.txt"
        with open(self.list_file, "w", encoding="utf-8") as f:
            for video in videos: f.write(f"file '{os.path.abspath(video).replace('\\', '/')}'\n")

        # UI Updates during processing
        self.btnMerge.setText("⏳ Merging in Background... Please wait")
        self.btnMerge.setEnabled(False)
        self.progress.setRange(0, 0) # Indeterminate progress animation

        # Start Background Thread
        self.thread = MergeThread(self.list_file, output_path)
        self.thread.finished.connect(self.merge_finished)
        self.thread.start()

    def merge_finished(self, success, message):
        self.progress.setRange(0, 100)
        self.progress.setValue(100)
        self.btnMerge.setText("🚀 MERGE & EXPORT")
        self.btnMerge.setEnabled(True)

        if os.path.exists(self.list_file): os.remove(self.list_file)

        if success:
            QMessageBox.information(self, "Success", f"🎉 Export Complete!\n\nSaved at: {message}")
            self.progress.setValue(0)
        else:
            QMessageBox.critical(self, "Error", f"Failed to merge videos.\n\nDetail: {message}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = VideoMergerApp()
    ex.show()
    sys.exit(app.exec_())