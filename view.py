# -*- coding: utf-8 -*-
# @Time   : 2025/7/1 21:29
# @Author :acc98liu
# @File   : view.py
import os
import sys
import cv2
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage, QIntValidator
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QApplication, QLabel, QFileDialog,
                             QDialog, QLineEdit, QCheckBox, QMessageBox, QSlider)


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("关于")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 添加 "关于" 信息
        about_text = QLabel('应用程序名称：oled图片转换器\n'
                            '\n'
                            '开发者：acc98liu\n'
                            '版本：1.0.2\n'
                            '\n'
                            '说明：该程序用于输出bmp格式的图片，开发初衷是\n'
                            '\n'
                            '为没有ps环境的用户提供方便快捷的图像处理工具\n'
                            '\n'
                            '需搭配江科大oled课程食用 (祝您使用愉快:p)')
        about_text.setAlignment(Qt.AlignCenter)
        layout.addWidget(about_text)

        # 设置布局
        self.setLayout(layout)


class EdgeDetectionDialog(QDialog):
    def __init__(self, parent=None, image=None):
        super().__init__(parent)
        self.image = image
        self.threshold1 = 100
        self.threshold2 = 200
        self.setWindowTitle("边缘检测参数调整")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.slider1 = QSlider(Qt.Horizontal)
        self.slider1.setMinimum(0)
        self.slider1.setMaximum(500)
        self.slider1.setValue(100)
        self.slider1.valueChanged.connect(self.update_image)
        layout.addWidget(QLabel("Low_Val"))
        layout.addWidget(self.slider1)

        self.slider2 = QSlider(Qt.Horizontal)
        self.slider2.setMinimum(0)
        self.slider2.setMaximum(500)
        self.slider2.setValue(200)
        self.slider2.valueChanged.connect(self.update_image)
        layout.addWidget(QLabel("High_Val"))
        layout.addWidget(self.slider2)

        self.update_image()

    def update_image(self):
        self.threshold1 = self.slider1.value()
        self.threshold2 = self.slider2.value()
        if len(self.image.shape) == 2:  # 灰度图
            gray_image = self.image
        else:  # 彩色图
            gray_image = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        edge_image = cv2.Canny(gray_image, self.threshold1, self.threshold2)
        self.parent().update_image_display(edge_image)


class BinarizationDialog(QDialog):
    def __init__(self, parent=None, image=None):
        super().__init__(parent)
        self.image = image
        self.threshold = 128
        self.setWindowTitle("二值化参数调整")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(255)
        self.slider.setValue(128)
        self.slider.valueChanged.connect(self.update_image)
        layout.addWidget(QLabel("Threshold"))
        layout.addWidget(self.slider)

        self.update_image()

    def update_image(self):
        self.threshold = self.slider.value()
        _, binary_image = cv2.threshold(self.image, self.threshold, 255, cv2.THRESH_BINARY)
        self.parent().update_image_display(binary_image)


class ResizeDialog(QDialog):
    resize_changed = pyqtSignal(int, int)

    def __init__(self, parent=None, original_size=None):
        super().__init__(parent)

        # 确保原始尺寸格式为 (width, height)
        if original_size and len(original_size) == 2:
            self.original_width = original_size[1]
            self.original_height = original_size[0]
            self.aspect_ratio = self.original_width / self.original_height
        else:
            # 默认值
            self.original_width = 100
            self.original_height = 100
            self.aspect_ratio = 1.0

        self.setWindowTitle("调整图像尺寸")
        self.suppress_update = False  # 防止更新循环
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 宽度输入框
        layout.addWidget(QLabel("宽度:"))
        self.width_input = QLineEdit()
        self.width_input.setValidator(QIntValidator(1, 99999))
        self.width_input.textEdited.connect(lambda: self.update_dimension('width'))
        layout.addWidget(self.width_input)

        # 高度输入框
        layout.addWidget(QLabel("高度:"))
        self.height_input = QLineEdit()
        self.height_input.setValidator(QIntValidator(1, 99999))
        self.height_input.textEdited.connect(lambda: self.update_dimension('height'))
        layout.addWidget(self.height_input)

        # 设置初始值
        self.width_input.setText(str(self.original_width))
        self.height_input.setText(str(self.original_height))

        # 锁定比例复选框
        self.lock_ratio_checkbox = QCheckBox("锁定原始比例")
        self.lock_ratio_checkbox.setChecked(True)
        layout.addWidget(self.lock_ratio_checkbox)

        # 应用按钮
        button = QPushButton("应用")
        button.clicked.connect(self.apply_resize)
        layout.addWidget(button)

    def update_dimension(self, changed_field):
        """根据锁定的比例实时更新另一个维度"""
        if not self.lock_ratio_checkbox.isChecked() or self.suppress_update:
            return

        try:
            self.suppress_update = True

            if changed_field == 'width' and self.width_input.text():
                new_width = int(self.width_input.text())
                new_height = int(round(new_width / self.aspect_ratio))
                self.height_input.setText(str(new_height))

            elif changed_field == 'height' and self.height_input.text():
                new_height = int(self.height_input.text())
                new_width = int(round(new_height * self.aspect_ratio))
                self.width_input.setText(str(new_width))

        except ValueError:
            pass
        finally:
            self.suppress_update = False

    def apply_resize(self):
        """应用尺寸修改"""
        try:
            width = int(self.width_input.text())
            height = int(self.height_input.text())

            # 验证尺寸有效性
            if width <= 0 or height <= 0:
                QMessageBox.warning(self, "输入错误", "尺寸必须为正整数")
                return

            self.resize_changed.emit(width, height)
            self.accept()

        except ValueError:
            QMessageBox.warning(self, "输入错误", "请输入有效的整数尺寸")


class LoginPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.image = None
        self.cpyimg = None
        self.temp_img = None
        self.edge_image = None
        self.binary_image = None
        self.threshold1 = 100
        self.threshold2 = 200
        self.binary_threshold = 128
        self.setWindowTitle('oled图片转换器')
        self.setGeometry(100, 100, 1000, 800)
        self.init_win()

    def init_win(self):
        total_layout = QHBoxLayout(self)

        button_layout = QVBoxLayout(self)
        button1 = QPushButton('导入图片')
        button2 = QPushButton('边缘处理')
        button3 = QPushButton('二值化')
        button4 = QPushButton('调整像素')
        button5 = QPushButton('删除操作')
        button6 = QPushButton('导出图片')
        button7 = QPushButton('About')
        button1.setFixedSize(200, 80)
        button2.setFixedSize(200, 80)
        button3.setFixedSize(200, 80)
        button4.setFixedSize(200, 80)
        button5.setFixedSize(200, 80)
        button6.setFixedSize(200, 80)
        button7.setFixedSize(200, 80)
        button_layout.addWidget(button1)
        button_layout.addWidget(button2)
        button_layout.addWidget(button3)
        button_layout.addWidget(button4)
        button_layout.addWidget(button5)
        button_layout.addWidget(button6)
        button_layout.addWidget(button7)

        self.show_img = QLabel('图片展示区')
        self.show_img.setAlignment(Qt.AlignCenter)

        total_layout.addLayout(button_layout)
        total_layout.addWidget(self.show_img)

        button1.clicked.connect(self.import_image)
        button2.clicked.connect(self.edge_detection)
        button3.clicked.connect(self.binarize_image)
        button4.clicked.connect(self.resize_image)
        button5.clicked.connect(self.delet_img)
        button6.clicked.connect(self.output)
        button7.clicked.connect(self.about_item)

    def update_image_display(self, image):
        """
        更新图像显示
        :param image: 需要显示的图像（numpy数组）
        """
        if image is None:
            return

        height, width = image.shape
        bytes_per_line = width
        q_image = QImage(image.data, width, height, bytes_per_line, QImage.Format_Grayscale8)
        pixmap = QPixmap.fromImage(q_image)

        # 计算 QLabel 的宽高比
        label_width = self.show_img.width()
        label_height = self.show_img.height()
        label_aspect_ratio = label_width / label_height

        # 计算图像的宽高比
        image_aspect_ratio = width / height

        # 根据 QLabel 和图像的宽高比，决定是按宽度还是高度缩放
        if image_aspect_ratio > label_aspect_ratio:
            # 图像比 QLabel 宽，按宽度缩放
            scaled_pixmap = pixmap.scaledToWidth(label_width, Qt.SmoothTransformation)
        else:
            # 图像比 QLabel 高，按高度缩放
            scaled_pixmap = pixmap.scaledToHeight(label_height, Qt.SmoothTransformation)

        # 设置 QLabel 的内容
        self.show_img.setPixmap(scaled_pixmap)
        self.show_img.setScaledContents(False)  # 禁用自动缩放

    def import_image(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "选择图片", "", "Image Files (*.png *.jpg *.bmp *.gif)")
        if file_name:
            self.image = cv2.imread(file_name, cv2.IMREAD_GRAYSCALE)
            self.cpyimg = self.image.copy()
            self.update_image_display(self.image)

            img_folder = "img"
            if not os.path.exists(img_folder):
                os.makedirs(img_folder)
            save_path = os.path.join(img_folder, "temp.jpg")
            cv2.imwrite(save_path, self.image)
            print(f"图片已保存到 {save_path}")

    def edge_detection(self):
        if self.image is None:
            print("没有导入图片")
            return

        dialog = EdgeDetectionDialog(self, self.image)
        dialog.exec_()
        self.image = cv2.Canny(self.image, dialog.threshold1, dialog.threshold2)
        self.update_image_display(self.image)

    def update_edge_detection(self, threshold1, threshold2):
        self.threshold1 = threshold1
        self.threshold2 = threshold2
        if len(self.image.shape) == 2:  # 灰度图
            gray_image = self.image
        else:  # 彩色图
            gray_image = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        self.temp_img = cv2.Canny(gray_image, self.threshold1, self.threshold2)
        self.update_image_display(self.temp_img)

        if self.temp_img is not None:
            self.image = self.temp_img
            self.temp_img = None

    def binarize_image(self):
        if self.image is None:
            print("没有导入图片")
            return

        dialog = BinarizationDialog(self, self.image)
        dialog.exec_()
        _, self.image = cv2.threshold(self.image, dialog.threshold, 255, cv2.THRESH_BINARY)
        self.update_image_display(self.image)

    def update_binarization(self, threshold):
        self.binary_threshold = threshold
        _, self.temp_img = cv2.threshold(self.image, self.binary_threshold, 255, cv2.THRESH_BINARY)
        self.update_image_display(self.temp_img)

        if self.temp_img is not None:
            self.image = self.temp_img
            self.temp_img = None

    def resize_image(self):
        try:
            if self.image is None:
                print("没有导入图片")
                return

            dialog = ResizeDialog(self, self.image.shape[:2])
            dialog.resize_changed.connect(self.update_resize)
            dialog.exec_()

            if self.temp_img is not None:
                self.image = self.temp_img
                self.temp_img = None
        except Exception as e:
            print(e)

    def update_resize(self, width, height):
        try:
            self.temp_img = cv2.resize(self.image, (width, height))
            self.update_image_display(self.temp_img)

            if self.temp_img is not None:
                self.image = self.temp_img
                self.temp_img = None
        except Exception as e:
            print(e)

    def delet_img(self):  # 撤销操作
        if self.cpyimg is not None:
            self.image = self.cpyimg.copy()  # 恢复到副本
            self.cpyimg = self.image.copy()  # 更新副本
            self.update_image_display(self.image)
        else:
            print("没有可撤销的操作")

    def output(self):
        if self.image is None:
            print('img not exist')
            return
        img_folder = "output"
        if not os.path.exists(img_folder):
            os.makedirs(img_folder)
        save_path = os.path.join(img_folder, "temp.bmp")
        cv2.imwrite(save_path, self.image)
        print(f"The image has been saved to {save_path}")

    def about_item(self):
        about_dialog = AboutDialog(self)
        about_dialog.exec_()

    def return_to_main(self):
        self.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = LoginPage()
    widget.show()
    sys.exit(app.exec_())
