import os
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor
from PyQt5.QtWidgets import QLabel
from pathlib import Path

from static import color_list


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


def read_labels(root, dataset_path):
    root_path = Path(root)
    file_data = {}

    for file in root_path.rglob(f'*.txt'):
        try:
            # print(str(file.resolve()))
            # 파일 읽기
            content = file.read_text(encoding="utf-8").strip()
            # 공백으로 구분된 숫자들을 리스트로 변환
            numbers = list(map(int, content.split()))
            numbers = list(zip(numbers[::2], numbers[1::2]))

            # 파일 경로를 key로 저장
            name = str(file.resolve())
            name = name.replace(str(Path(root)), str(Path(dataset_path)))
            name = normalize_path(str(Path(name).with_suffix(".png")))
            file_data[name] = numbers
        except Exception as e:
            print(f"파일 {file} 읽기 오류: {e}")

    return file_data

def read_checked_list(root, dataset_path):
    root_path = Path(root)
    file_data = []


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
