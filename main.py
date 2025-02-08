import sys
from PyQt5.QtWidgets import QApplication
from gui import ImageViewer


def main():
    app = QApplication(sys.argv)
    window = ImageViewer()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
