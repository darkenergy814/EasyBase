import os
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor
from PyQt5.QtWidgets import QLabel
import time

from static.landmark_color import color_list


def find_all_images(folder):
    """
    주어진 폴더(및 하위 폴더)에서 이미지 파일을 재귀적으로 검색하고,
    중복을 제거한 후 정렬된 리스트로 반환합니다.
    """
    folder_path = Path(folder)
    valid_exts = {".png", ".jpg", ".jpeg", ".bmp", ".gif"}

    images = {normalize_path(str(file.resolve())) for file in folder_path.rglob("*") if
              file.suffix.lower() in valid_exts}

    return sorted(images)


def normalize_path(path):
    """
    경로를 os.path.normpath와 os.path.normcase를 사용하여 정규화합니다.
    """
    return os.path.normcase(os.path.normpath(path))


class ClickableLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            coords = event.pos()  # 클릭한 위치 (QPoint)
            # 상위 최상위 창의 image_clicked 메서드를 호출
            main_window = self.window()
            if main_window.current_index is not None and hasattr(main_window, 'add_landmark'):
                main_window.add_landmark((coords.x(), coords.y()), main_window.current_index)
        super().mousePressEvent(event)


class ClickableLabelBeta(QLabel):
    def __init__(self, parent, img_path):
        super().__init__(parent)
        self.image = QPixmap(img_path)  # 원본 이미지
        self.setPixmap(self.image)  # QLabel에 이미지 설정
        self.paintingEvent()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            coords = event.pos()  # 클릭한 위치 (QPoint)
            # 상위 최상위 창의 image_clicked 메서드를 호출
            main_window = self.window()
            if main_window.current_index is not None and hasattr(main_window, 'add_landmark'):
                main_window.add_landmark((coords.x(), coords.y()), main_window.current_index)
            self.paintingEvent()

    def paintingEvent(self):
        """점들을 다시 그리기 위한 paintEvent"""
        if self.image.isNull():
            return

        pixmap = self.image.copy()  # 원본 이미지 복사

        if self.window().current_index in self.window().landmark:
            painter = QPainter(pixmap)
            points = self.window().landmark[self.window().current_index]
            for i, point in enumerate(points):

                # pen = QPen(QColor(255, 0, 0))  # 빨간색 점
                pen = QPen(QColor(*color_list[i]))  # 빨간색 점
                pen.setWidth(3)
                painter.setPen(pen)
                painter.drawPoint(point[0], point[1])  # 저장된 좌표에 점 찍기
                painter.drawText(point[0], point[1] - 5, str(i + 1))
                if i == 6:
                    painter.drawRect(points[5][0], points[5][1], points[6][0]-points[5][0], points[6][1]-points[5][1])

            painter.end()
        self.setPixmap(pixmap)  # 업데이트된 이미지 설정
