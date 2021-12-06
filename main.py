import sys
from PyQt5.QtWidgets import *
from Resource import tracepage

# Author: Wang tianyi

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWin= tracepage.CameraPageWindow()
    myWin.show()
    sys.exit(app.exec_())