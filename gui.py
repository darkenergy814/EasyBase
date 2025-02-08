# gui.py
import os
from PyQt5.QtWidgets import (
    QMainWindow, QAction, QFileDialog, QLabel, QTreeView, QListWidget,
    QFileSystemModel, QWidget, QHBoxLayout, QVBoxLayout, QMessageBox,
    QSizePolicy, QSplitter, QPushButton, QScrollArea, QGridLayout, QCheckBox, QListWidgetItem,
    QMenu, QShortcut
)
from PyQt5.QtGui import QPixmap, QKeySequence
from PyQt5.QtCore import Qt, QDir
from utils import find_all_images, normalize_path, ClickableLabel, ClickableLabelBeta


class ImageViewer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("이미지 뷰어")
        self.setGeometry(100, 100, 800, 600)
        self.current_folder = ""
        self.image_list = []  # 현재 폴더 내 모든 이미지 경로 목록

        # 현재 선택된 이미지 인덱스 (단일 모드)
        self.current_index = 0
        # 현재 페이지 (그리드 모드, 한 페이지에 최대 64개)
        self.current_page = 0
        # 모드: False - 단일 이미지 모드, True - 그리드 모드
        self.grid_mode = False

        self.pixmap = None

        self.checked = []
        self.landmark = {}

        # 체크박스로 선택된 이미지 리스트
        self._init_ui()

    def _init_ui(self):
        # 중앙 위젯 및 메인 레이아웃 (QSplitter 사용)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        main_layout = QHBoxLayout()
        self.central_widget.setLayout(main_layout)

        self.splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self.splitter)

        # 왼쪽 패널 (트리 뷰 + 체크된 파일 리스트)
        self.left_widget = QWidget()
        self.left_layout = QVBoxLayout()
        self.left_widget.setLayout(self.left_layout)

        # 왼쪽 상단: 트리 뷰 (파일 탐색기)
        self.tree_view = QTreeView()
        self.tree_view.hide()  # 폴더 불러오기 전에는 숨김
        self.tree_view.setHeaderHidden(True)

        # 0번 컬럼(파일명)만 보이도록 나머지 컬럼 숨김
        for i in range(1, 4):
            self.tree_view.setColumnHidden(i, True)
        self.model = QFileSystemModel()
        # 디렉토리, 파일, 숨김 파일 모두 표시; 파일 이름 필터는 파일에만 적용 (디렉토리는 항상 보임)
        self.model.setFilter(QDir.Dirs | QDir.NoDotAndDotDot | QDir.Files | QDir.Hidden)
        self.model.setNameFilters(["*.png", "*.jpg", "*.jpeg", "*.bmp", "*.gif"])
        self.model.setNameFilterDisables(True)
        self.tree_view.setModel(self.model)
        self.tree_view.clicked.connect(self.display_selected_image)
        self.tree_view.setMinimumWidth(200)
        self.tree_view.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        # self.splitter.addWidget(self.tree_view)
        self.left_layout.addWidget(self.tree_view)

        # 왼쪽 하단: check 된 이미지 표시 영역
        self.checked_list_widget = QListWidget()
        self.checked_list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.checked_list_widget.customContextMenuRequested.connect(self.show_checked_list_menu)
        self.checked_list_widget.itemDoubleClicked.connect(self.select_image)
        self.left_layout.addWidget(self.checked_list_widget)

        # QSplitter에 왼쪽 패널 추가 (트리 뷰 + 체크 리스트 포함)
        self.splitter.addWidget(self.left_widget)

        # 오른쪽: 단일 이미지 또는 그리드 뷰 영역 (세로 레이아웃)
        self.right_widget = QWidget()
        self.right_layout = QVBoxLayout()
        self.right_widget.setLayout(self.right_layout)
        self.splitter.addWidget(self.right_widget)

        # 단일 이미지 표시용 QLabel
        self.image_label = ClickableLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image_label.setMinimumSize(100, 100)

        # Grid View 토글 버튼 (폴더 불러오기 후에만 보임)
        self.grid_toggle_btn = QPushButton("Grid View")
        self.grid_toggle_btn.clicked.connect(self.toggle_grid_mode)
        self.grid_toggle_btn.hide()

        # 내비게이션 영역 (좌/우 화살표 + 인디케이터 레이블)
        self.nav_widget = QWidget()
        self.nav_layout = QHBoxLayout()
        self.nav_widget.setLayout(self.nav_layout)
        self.prev_btn = QPushButton("<")
        self.prev_btn.clicked.connect(self.prev_clicked)
        self.next_btn = QPushButton(">")
        self.next_btn.clicked.connect(self.next_clicked)
        self.nav_label = QLabel("")
        self.nav_label.setAlignment(Qt.AlignCenter)
        self.nav_layout.addWidget(self.prev_btn)
        self.nav_layout.addWidget(self.nav_label, 1)
        self.nav_layout.addWidget(self.next_btn)
        self.nav_widget.hide()  # 폴더 불러오기 전에는 숨김

        # 초기 오른쪽 영역 구성 (아직 이미지 없음)
        self.update_right_view()

        # splitter 초기 사이즈 (왼쪽:200, 오른쪽: 나머지)
        self.splitter.setSizes([200, self.width() - 200])

        # 상태바
        self.statusBar()

        # 메뉴 설정
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("file")
        open_action = QAction("open root folder", self)
        open_action.triggered.connect(self.open_folder)
        file_menu.addAction(open_action)

        # Export
        export_menu = file_menu.addMenu("Export")
        export_selected_action = QAction("Selected Images", self)
        export_selected_action.triggered.connect(self.export_selected_images)
        export_menu.addAction(export_selected_action)

        export_landmark_action = QAction("landmarks", self)
        export_landmark_action.triggered.connect(self.export_landmark)
        export_menu.addAction(export_landmark_action)

        # shortcut
        undo = QShortcut(QKeySequence("Ctrl+z"), self)
        undo.activated.connect(self.remove_landmark)
        prev = QShortcut(QKeySequence("a"), self)
        prev.activated.connect(self.prev_clicked)
        next = QShortcut(QKeySequence("d"), self)
        next.activated.connect(self.next_clicked)

    def open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "이미지 폴더 선택")
        if folder:
            self.current_folder = folder
            self.tree_view.show()  # 폴더 선택 시 트리 뷰 표시
            self.update_tree_view(folder)
            self.image_list = find_all_images(folder)
            if self.image_list:
                # 이미지가 하나라도 있으면 단일 모드로 시작
                self.grid_mode = False
                self.grid_toggle_btn.setText("Grid View")
                self.current_index = 0
                self.current_page = 0
                self.grid_toggle_btn.show()
                self.nav_widget.show()
            else:
                self.grid_toggle_btn.hide()
                self.nav_widget.hide()
            self.update_right_view()

    def update_tree_view(self, path):
        """Update tree view and set paths, hide column 0 and others"""
        self.model.setRootPath(path)
        index = self.model.index(path)
        self.tree_view.setRootIndex(index)
        for col in range(1, self.model.columnCount(index)):
            self.tree_view.setColumnHidden(col, True)
        self.tree_view.expandAll()

    def expand_to_path(self, file_path):
        """Automatically extend the tree view to the image path"""
        dir_path = os.path.dirname(file_path)
        index = self.model.index(dir_path)
        while index.isValid():
            self.tree_view.expand(index)
            index = index.parent()

    def display_selected_image(self, index):
        """Show selected files in tree view in single mode"""
        path = normalize_path(self.model.filePath(index))
        if os.path.isfile(path) and path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
            # 단일 모드로 전환
            self.grid_mode = False
            self.grid_toggle_btn.setText("Grid View")
            normalized_list = [normalize_path(p) for p in self.image_list]
            path_norm = normalize_path(path)
            if path_norm in normalized_list:
                self.current_index = normalized_list.index(path_norm)
            else:
                self.show_warning("오류", "해당 이미지가 이미지 리스트에 없습니다.")
                return
            self.display_image(path)
            self.expand_to_path(path)
            self.update_right_view()

    def display_image(self, path):
        """Display and resize a single image"""
        self.pixmap = QPixmap(path)
        self.statusBar().showMessage(path)
        self.adjust_image_size()

    def adjust_image_size(self):
        """Auto-resize images in single mode (preserve proportions)"""
        if self.pixmap and not self.grid_mode:
            scaled_pixmap = self.pixmap.scaled(
                self.image_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)

    def update_right_view(self):
        """Update right area: configure single image or grid mode + show navigation"""
        # 오른쪽 레이아웃 초기화
        for i in reversed(range(self.right_layout.count())):
            widget = self.right_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

        if self.grid_mode:
            # 그리드 모드: 한 페이지당 최대 64개 썸네일
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            grid_widget = QWidget()
            grid_layout = QGridLayout(grid_widget)
            grid_layout.setSpacing(5)

            page_size = 64
            start = self.current_page * page_size
            end = min(start + page_size, len(self.image_list))

            for idx, img_path in enumerate(self.image_list[start:end]):
                row = idx // 8
                col = idx % 8

                # 개별 이미지 + 체크박스를 담을 위젯
                thumb_widget = QWidget()
                thumb_layout = QVBoxLayout()
                thumb_layout.setContentsMargins(0, 0, 0, 0)

                # 체크박스 생성
                checkbox = QCheckBox()
                checkbox.setStyleSheet("QCheckBox { background: white; }")  # 체크박스 배경 추가

                # 체크박스를 우측 상단에 배치하는 레이아웃
                checkbox_layout = QHBoxLayout()
                checkbox_layout.addStretch()
                checkbox_layout.addWidget(checkbox)
                checkbox_layout.setContentsMargins(0, 0, 0, 0)

                # 기존에 체크된 상태 반영 및 기능 연결
                checkbox.setChecked(img_path in self.checked)
                checkbox.stateChanged.connect(lambda state, path=img_path: self.checked_list(state, path))

                # 이미지 라벨 생성
                thumb_label = QLabel()
                thumb_label.setFixedSize(150, 150)
                thumb_label.setAlignment(Qt.AlignCenter)

                # 이미지 로드 및 설정
                pix = QPixmap(img_path)
                if not pix.isNull():
                    scaled = pix.scaled(thumb_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    thumb_label.setPixmap(scaled)

                # 위젯 레이아웃 조합
                thumb_layout.addLayout(checkbox_layout)  # 체크박스 추가
                thumb_layout.addWidget(thumb_label)  # 이미지 추가
                thumb_widget.setLayout(thumb_layout)

                # 그리드에 추가
                grid_layout.addWidget(thumb_widget, row, col)

            scroll.setWidget(grid_widget)
            self.right_layout.addWidget(scroll)

            # 내비게이션 표시 (그리드 모드: "이미지 A ~ B / 전체: C")
            indicator = f"이미지 {start + 1} ~ {end} / 전체: {len(self.image_list)}"

        else:
            # 🔹 [단일 이미지 모드]
            if self.image_list:
                img_path = self.image_list[self.current_index]

                # 단일 이미지 표시용 위젯
                single_image_widget = QWidget()
                single_image_layout = QVBoxLayout()
                single_image_layout.setContentsMargins(0, 0, 0, 0)

                # 🔹 체크박스 (오른쪽 상단에 배치)
                checkbox = QCheckBox()
                checkbox.setStyleSheet("QCheckBox { background: white; }")

                checkbox_layout = QHBoxLayout()
                checkbox_layout.addStretch()
                checkbox_layout.addWidget(checkbox)
                checkbox_layout.setContentsMargins(0, 0, 0, 0)

                # 기존에 체크된 상태 반영 및 기능 연결
                checkbox.setChecked(img_path in self.checked)
                checkbox.stateChanged.connect(lambda state, path=img_path: self.checked_list(state, path))

                # 🔹 단일 이미지 QLabel
                # single_image_label = QLabel()
                # single_image_label = ClickableLabel(self)
                single_image_label = ClickableLabelBeta(self, img_path)
                single_image_label.setAlignment(Qt.AlignCenter)
                # single_image_label.setFixedSize(500, 500)  # 단일 이미지 크기 조정

                # # 이미지 로드
                # pix = QPixmap(img_path)
                # if not pix.isNull():
                #     scaled = pix.scaled(single_image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                #     single_image_label.setPixmap(scaled)

                # 위젯 레이아웃 조합
                single_image_layout.addLayout(checkbox_layout)  # 체크박스 추가
                single_image_layout.addWidget(single_image_label)  # 이미지 추가
                single_image_widget.setLayout(single_image_layout)

                self.right_layout.addWidget(single_image_widget)

            # 내비게이션 표시 (단일 모드: "현재: N / 전체: 총개수")
            indicator = f"현재: {self.current_index + 1} / 전체: {len(self.image_list)}"

            # 내비게이션 영역 (좌/우 화살표 + 인디케이터)
        self.nav_label.setText(indicator)
        self.right_layout.addWidget(self.nav_widget)

        # 마지막에 Grid 토글 버튼 추가
        self.right_layout.addWidget(self.grid_toggle_btn)

        # 내비게이션 영역 (좌/우 화살표 + 인디케이터)
        self.nav_label.setText(indicator)
        self.right_layout.addWidget(self.nav_widget)

        # 마지막에 Grid 토글 버튼 추가
        self.right_layout.addWidget(self.grid_toggle_btn)

    def checked_list(self, state, path):
        if state:
            if path not in self.checked:
                self.checked.append(path)
                item = QListWidgetItem(path)
                self.checked_list_widget.addItem(item)
        else:
            if path in self.checked:
                self.checked.remove(path)
                for i in range(self.checked_list_widget.count()):
                    if self.checked_list_widget.item(i).text() == path:
                        self.checked_list_widget.takeItem(i)
                        break

    def toggle_grid_mode(self):
        """Toggle mode when clicking Grid toggle button (single <-> grid)"""
        self.grid_mode = not self.grid_mode
        if self.grid_mode:
            self.grid_toggle_btn.setText("Single View")
            self.current_page = self.current_index // 64 if self.image_list else 0
        else:
            self.grid_toggle_btn.setText("Grid View")
            self.current_index = self.current_page * 64 if self.image_list else 0
        self.update_right_view()

    def prev_clicked(self):
        """Left arrow click: Previous image (single) or previous page (grid)"""
        if not self.image_list:
            return
        if self.grid_mode:
            if self.current_page > 0:
                self.current_page -= 1
                self.update_right_view()
        else:
            if self.current_index > 0:
                self.current_index -= 1
                self.update_right_view()

    def next_clicked(self):
        """Right arrow click: Next image (single) or next page (grid)"""
        if not self.image_list:
            return
        if self.grid_mode:
            if (self.current_page + 1) * 64 < len(self.image_list):
                self.current_page += 1
                self.update_right_view()
        else:
            if self.current_index < len(self.image_list) - 1:
                self.current_index += 1
                self.update_right_view()

    def show_warning(self, title, message):
        QMessageBox.warning(self, title, message, QMessageBox.Ok)

    def export_selected_images(self):
        """export selected file list to .txt file"""
        if not self.checked:
            QMessageBox.warning(self, "Warning", "There's no selected files.")
            return

        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Selected Images", "", "Text Files (*.txt);;All Files (*)", options=options
        )

        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    for path in self.checked:
                        f.write(path + "\n")
                QMessageBox.information(self, "Success", "The File successfully saved!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error saving file: {e}")

    # function for the list
    def select_image(self, item):
        path = item.text()
        self.current_index = self.image_list.index(path)
        self.current_page = self.image_list.index(path) // 64
        self.update_right_view()

    def update_checked_list(self):
        """show checked file list on QListWidget"""
        self.checked_list_widget.clear()
        for path in self.checked:
            item = QListWidgetItem(os.path.basename(path))  # 파일명만 표시
            item.setData(Qt.UserRole, path)  # 원본 경로 저장
            self.checked_list_widget.addItem(item)

    def remove_checked_item(self, item):
        """remove specific file in checked file list"""
        path = item.text()
        if path in self.checked:
            self.checked.remove(path)
            self.update_checked_list()
            self.update_right_view()

    def show_checked_list_menu(self, position):
        """Show context menu on right-click in checked file list"""
        item = self.checked_list_widget.itemAt(position)
        if item:
            menu = QMenu()
            remove_action = QAction("Delete", self)
            remove_action.triggered.connect(lambda: self.remove_checked_item(item))
            menu.addAction(remove_action)
            menu.exec_(self.checked_list_widget.viewport().mapToGlobal(position))

    # function for the labeling
    def add_landmark(self, coords, index):
        if index in self.landmark:
            if len(self.landmark[index]) == 5:
                self.show_warning("Warning", "You already have 5 landmarks.")
                return
            self.landmark[index].append(coords)
        else:
            self.landmark[index] = [coords]

    def remove_landmark(self):
        if self.current_index in self.landmark and len(self.landmark[self.current_index]) != 0:
            self.landmark[self.current_index].pop()
            self.update_right_view()

    def export_landmark(self):
        output_folder = QFileDialog.getExistingDirectory(self, "select output folder", self.current_folder)

        try:
            for index in self.landmark:
                if len(self.landmark[index]) != 0:
                    image_path = normalize_path(self.image_list[index])
                    extender = image_path.split('.')[-1]
                    save_path = image_path.replace(normalize_path(self.current_folder), output_folder).replace(extender, 'txt')

                    # 저장할 폴더가 존재하지 않으면 생성
                    save_dir = os.path.dirname(save_path)
                    if not os.path.exists(save_dir):
                        os.makedirs(save_dir)

                    with open(save_path, "w", encoding="utf-8") as file:  # 'a' 모드: 기존 파일에 내용 추가
                        file.write(' '.join(f"{x} {y}" for x, y in self.landmark[index]) + '\n')
            QMessageBox.information(self, "Success", "The File successfully saved!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error saving file: {e}")
