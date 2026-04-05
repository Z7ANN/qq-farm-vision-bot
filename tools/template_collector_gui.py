"""模板采集工具 - PyQt6 GUI 版本

使用方法：
1. 打开QQ农场小程序窗口
2. 运行此脚本: python tools/template_collector_gui.py
3. 程序会截取游戏窗口画面
4. 用鼠标框选要保存的模板区域
5. 输入模板名称并保存
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QHBoxLayout,
    QWidget, QPushButton, QLineEdit, QMessageBox, QInputDialog
)
from PyQt6.QtCore import Qt, QRect, QPoint
from PyQt6.QtGui import QPixmap, QPainter, QPen, QImage

from core.window_manager import WindowManager
from core.screen_capture import ScreenCapture


class TemplateSelector(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.start_point = None
        self.end_point = None
        self.selecting = False
        self.original_pixmap = None
        
    def set_image(self, pixmap: QPixmap):
        self.original_pixmap = pixmap
        self.setPixmap(pixmap)
        self.adjustSize()
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_point = event.pos()
            self.selecting = True
            
    def mouseMoveEvent(self, event):
        if self.selecting:
            self.end_point = event.pos()
            self.update()
            
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.selecting = False
            self.end_point = event.pos()
            self.update()
            
    def paintEvent(self, event):
        super().paintEvent(event)
        if self.start_point and self.end_point:
            painter = QPainter(self)
            pen = QPen(Qt.GlobalColor.green, 2)
            painter.setPen(pen)
            rect = QRect(self.start_point, self.end_point).normalized()
            painter.drawRect(rect)
            
            # 显示尺寸
            text = f"{rect.width()}x{rect.height()}"
            painter.drawText(rect.bottomRight() + QPoint(5, 5), text)
            
    def get_selection(self):
        if self.start_point and self.end_point:
            rect = QRect(self.start_point, self.end_point).normalized()
            if rect.width() > 5 and rect.height() > 5:
                return rect
        return None


class TemplateCollectorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.wm = WindowManager()
        self.sc = ScreenCapture()
        self.templates_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "templates"
        )
        os.makedirs(self.templates_dir, exist_ok=True)
        self.current_image = None
        self.saved_count = 0
        
        self.init_ui()
        self.capture_window()
        
    def init_ui(self):
        self.setWindowTitle("QQ农场模板采集工具")
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # 图片显示区域
        self.image_label = TemplateSelector()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.image_label)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("重新截屏 (R)")
        self.refresh_btn.clicked.connect(self.capture_window)
        btn_layout.addWidget(self.refresh_btn)
        
        self.save_btn = QPushButton("保存模板 (S)")
        self.save_btn.clicked.connect(self.save_template)
        btn_layout.addWidget(self.save_btn)
        
        self.quit_btn = QPushButton("退出 (Q)")
        self.quit_btn.clicked.connect(self.close)
        btn_layout.addWidget(self.quit_btn)
        
        layout.addLayout(btn_layout)
        
        # 说明文字
        help_text = QLabel(
            "操作说明：\n"
            "1. 鼠标左键拖拽框选模板区域\n"
            "2. 点击'保存模板'按钮或按 S 键\n"
            "3. 输入模板名称（如 btn_friend_help）\n"
            "4. 点击'重新截屏'或按 R 键刷新画面"
        )
        help_text.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(help_text)
        
        # 快捷键
        self.refresh_btn.setShortcut("R")
        self.save_btn.setShortcut("S")
        self.quit_btn.setShortcut("Q")
        
    def capture_window(self):
        window = self.wm.find_window("QQ经典农场")
        if not window:
            QMessageBox.warning(self, "错误", "未找到QQ农场窗口\n请先打开微信小程序中的QQ农场")
            return
            
        self.wm.activate_window()
        import time
        time.sleep(0.3)
        
        rect = (window.left, window.top, window.width, window.height)
        image = self.sc.capture_region(rect)
        if image is None:
            QMessageBox.warning(self, "错误", "截屏失败")
            return
            
        self.current_image = image
        
        # 转换为 QPixmap
        qimage = QImage(
            image.tobytes(), image.width, image.height,
            QImage.Format.Format_RGB888
        )
        pixmap = QPixmap.fromImage(qimage)
        
        self.image_label.set_image(pixmap)
        self.setWindowTitle(f"QQ农场模板采集工具 - {image.width}x{image.height}")
        
    def save_template(self):
        rect = self.image_label.get_selection()
        if not rect:
            QMessageBox.warning(self, "提示", "请先用鼠标框选一个区域")
            return
            
        if self.current_image is None:
            return
            
        # 裁剪图片
        cropped = self.current_image.crop((
            rect.left(), rect.top(),
            rect.right(), rect.bottom()
        ))
        
        # 输入模板名称
        name, ok = QInputDialog.getText(
            self, "保存模板",
            f"模板尺寸: {rect.width()}x{rect.height()}\n\n"
            "输入模板名称（如 btn_friend_help）：",
            text=""
        )
        
        if ok and name:
            name = name.strip()
            if not name:
                return
                
            filepath = os.path.join(self.templates_dir, f"{name}.png")
            cropped.save(filepath)
            self.saved_count += 1
            
            QMessageBox.information(
                self, "成功",
                f"已保存: {name}.png\n"
                f"位置: {filepath}\n"
                f"尺寸: {rect.width()}x{rect.height()}\n"
                f"已保存 {self.saved_count} 个模板"
            )
            
            # 重置选择
            self.image_label.start_point = None
            self.image_label.end_point = None
            self.image_label.update()


def main():
    app = QApplication(sys.argv)
    window = TemplateCollectorWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
