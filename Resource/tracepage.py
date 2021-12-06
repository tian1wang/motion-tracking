import os

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import QtWidgets
import numpy as np
import cv2
import matplotlib

matplotlib.use('Qt5Agg')

from Resource import Figure_Canvas
from Resource.GUI import Ui_MainWindow

import math


class CameraPageWindow(QtWidgets.QMainWindow, Ui_MainWindow, QWidget):
    CAM_NUM: int

    lower_green = np.array([50, 120, 50])
    upper_green = np.array([77, 255, 255])
    datax = []
    datay = []
    dataz = []
    NUM = 1000  # 最大显示数据量

    internal: int
    Xcm = 0.0
    Ycm = 0.0
    Zcm = 0.0
    real_radius: float
    internal_limit: int

    output_file = None
    file_postfix: int
    current_time: float

    def __init__(self, parent=None):
        super(CameraPageWindow, self).__init__(parent)
        self.timer_camera = QTimer()  # 初始化定时器
        self.trace_camera = QTimer()
        self.cap = cv2.VideoCapture()  # 初始化摄像头
        self.CAM_NUM = 0
        self.internal = 0
        self.file_postfix = 0
        self.setupUi(self)  # 设置malplotlib的连接
        self.initUI()
        self.slot_init()
        # print(os.getcwd())  # 被main调用 所以输出的是main的位置

    def initUI(self):
        self.object_radius.setText("2.1335")
        self.frequency.setText("5")

        self.SurfFigure = Figure_Canvas.Figure_Canvas()
        self.SurfFigureLayout = QGridLayout(self.groupBox)
        self.SurfFigureLayout.addWidget(self.SurfFigure)
        self.SurfFigure.ax.remove()
        self.ax3d = self.SurfFigure.fig.add_subplot(projection='3d')
        self.set_plot()

    def set_plot(self):
        self.ax3d.set_xlim(-5, 50)
        self.ax3d.set_ylim(-30, 30)
        self.ax3d.set_zlim(-30, 30)
        self.ax3d.set_title("Trace Graphic")
        self.ax3d.set_xlabel("x/cm")
        self.ax3d.set_ylabel("y/cm")
        self.ax3d.set_zlabel("z/cm")

    def plot_init(self):
        self.datax = []
        self.datay = []
        self.dataz = []
        self.ax3d.clear()
        self.set_plot()
        self.SurfFigure.draw()

    def slot_init(self):
        self.timer_camera.timeout.connect(self.show_camera)
        self.cameraButton.clicked.connect(self.slotCameraButton)
        self.traceButton.clicked.connect(self.slotTraceButton)
        self.trace_camera.timeout.connect(self.show_trace)

    def show_camera(self):
        ret, img = self.cap.read()
        screen_width = self.cameraLabel.width()
        if screen_width <= 480:
            show = cv2.resize(img, (360, 270))
        elif screen_width <= 720:
            show = cv2.resize(img, (480, 360))
        elif screen_width <= 1080:
            show = cv2.resize(img, (720, 540))
        else:
            show = cv2.resize(img, (1080, 810))

        show = cv2.cvtColor(show, cv2.COLOR_BGR2RGB)
        showImage = QImage(show.data, show.shape[1], show.shape[0], QImage.Format_RGB888)
        self.cameraLabel.setPixmap(QPixmap.fromImage(showImage))

    # 打开摄像头
    def openCamera(self):
        flag = self.cap.open(self.CAM_NUM)
        if flag == False:
            msg = QMessageBox.Warning(self, u'Warning', u'请检测相机与电脑是否连接正确',
                                      buttons=QMessageBox.Ok,
                                      defaultButton=QMessageBox.Ok)
        else:
            self.timer_camera.start(30)
            self.cameraButton.setText('关闭摄像头')

    # 关闭摄像头
    def closeCamera(self):
        self.timer_camera.stop()
        self.cap.release()
        self.cameraLabel.clear()
        self.cameraButton.setText('打开摄像头')
        self.cameraLabel.setText('CCD相机捕捉画面')

    # 打开关闭摄像头控制
    def slotCameraButton(self):
        if self.trace_camera.isActive() == False:
            if self.timer_camera.isActive() == False:
                # 打开摄像头并显示图像信息
                self.openCamera()
            else:
                # 关闭摄像头并清空显示信息
                self.closeCamera()
        else:
            self.closeTrace()

    def slotTraceButton(self):
        if self.trace_camera.isActive() == False:
            if self.timer_camera.isActive() == False:
                self.openTrace()
            else:
                self.closeCamera()
                self.openTrace()
        else:
            self.closeTrace()
            self.openCamera()
        self.coordinateBrowser.setText('此处将显示坐标信息')
        self.real_radius = float(self.object_radius.toPlainText())
        self.internal_limit = 100 / int(self.frequency.toPlainText())

    def openTrace(self):
        flag = self.cap.open(self.CAM_NUM)
        if flag == False:
            msg = QMessageBox.Warning(self, u'Warning', u'请检测相机与电脑是否连接正确',
                                      buttons=QMessageBox.Ok,
                                      defaultButton=QMessageBox.Ok)
        else:
            self.plot_init()
            self.current_time = 0.0
            self.file_postfix += 1
            self.output_file = open(os.path.join(os.getcwd(), f'coordinate_data{self.file_postfix}.txt'), "w")
            self.trace_camera.start(10)
            self.traceButton.setText('停止追踪')
            self.cameraButton.setText('关闭摄像头')

    # 停止追踪
    def closeTrace(self):
        self.trace_camera.stop()
        self.cap.release()
        self.cameraLabel.clear()
        print('\n数据格式： 时间(s) x坐标(cm) y坐标(cm) z坐标(cm)', file=self.output_file)
        self.output_file.close()
        self.traceButton.setText('开始追踪')
        self.cameraLabel.setText('CCD相机捕捉画面')
        self.cameraButton.setText('打开摄像头')
        self.waste_flag=0

    def show_trace(self):
        self.current_time += 0.01

        ret, img = self.cap.read()
        screen_width = self.cameraLabel.width()
        maxx: int
        maxy: int
        if screen_width <= 480:
            maxx = 360
            maxy = 270
        elif screen_width <= 720:
            maxx = 480
            maxy = 360
        elif screen_width <= 1080:
            maxx = 720
            maxy = 540
        else:
            maxx = 1080
            maxy = 810
        show = cv2.resize(img, (maxx, maxy))

        hsv = cv2.cvtColor(show, cv2.COLOR_BGR2HSV)
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.inRange(hsv, self.lower_green, self.upper_green)
        mask = cv2.erode(mask, kernel, iterations=2)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
        mask = cv2.dilate(mask, kernel, iterations=5)
        res = cv2.bitwise_and(show, show, mask=mask)
        cnts, heir = cv2.findContours(mask.copy(), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)[-2:]
        center = None

        if len(cnts) > 0:  # 如果检测出了轮廓，找不到轮廓就不进来
            c = max(cnts, key=cv2.contourArea)  # 以轮廓的面积为条件，找出最大的面积
            ((x, y), radius) = cv2.minEnclosingCircle(c)  # 找出最小的圆
            M = cv2.moments(c)
            center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))  # 用图像的矩求质心
            if radius > 5:
                cv2.circle(show, (int(x), int(y)), int(radius), (0, 255, 255), 2)
                cv2.circle(show, center, 5, (0, 0, 255), -1)
            print(x, y, radius, maxx, maxy)
            self.pixel2centimeter(x, y, maxx, maxy, radius)  # 有轮廓才更新轨迹
            self.update_figure()

            self.internal += 1
            if self.internal > self.internal_limit:  # 设置坐标刷新间隔，以防闪动刷新
                self.show_coordinate()
                self.internal = 0

        show = cv2.cvtColor(show, cv2.COLOR_BGR2RGB)
        showImage = QImage(show.data, show.shape[1], show.shape[0], QImage.Format_RGB888)
        self.cameraLabel.setPixmap(QPixmap.fromImage(showImage))

    def pixel2centimeter(self, x, y, maxx, maxy, radius):
        if x != None and y != None and radius != None:
            self.Xcm = 3.673 * math.pow(((float(radius) * 2.1335) / (self.real_radius * float(maxx))), -0.7374)
            self.Ycm = 12.8 - 22.3 * float(x) / float(maxx) + 2.963 / self.Xcm
            self.Zcm = 7.79 - 15.49 * float(y) / float(maxy) - 7.881 / self.Xcm
        else:
            self.Xcm = 0
            self.Ycm = 0
            self.Zcm = 0

    def show_coordinate(self):
        tmp_x = float('%.1f' % self.Xcm)
        tmp_y = float('%.1f' % self.Ycm)
        tmp_z = float('%.1f' % self.Zcm)
        if tmp_x >= 0:
            pos_fd = '前方'
        else:
            pos_fd = '后方'
        if tmp_z >= 0:
            pos_ud = '上方'
        else:
            pos_ud = '下方'
        if tmp_y >= 0:
            pos_lr = '左侧'
        else:
            pos_lr = '右侧'
        text = f' ( {tmp_x} cm, {tmp_y} cm, {tmp_z} cm )\n\n即物体位于摄像头\n{pos_fd}{math.fabs(tmp_x)} cm；{pos_ud}{math.fabs(tmp_z)} cm；{pos_lr}{math.fabs(tmp_x)} cm\n\n提示: 可点击停止追踪以定格追踪图像'
        self.coordinateBrowser.setText(text)
        tmp_time = float('%.2f' % self.current_time)
        print(f'{tmp_time} {tmp_x} {tmp_y} {tmp_z}', file=self.output_file)  # 时间 x y z

    def update_figure(self):
        if len(self.datax) > self.NUM:
            del self.datax[0]
        if len(self.datay) > self.NUM:
            del self.datay[0]
        if len(self.dataz) > self.NUM:
            del self.dataz[0]
        self.datax.append(self.Xcm)
        self.datay.append(self.Ycm)
        self.dataz.append(self.Zcm)
        self.ax3d.clear()
        self.ax3d.plot(self.datax, self.datay, self.dataz, c='r')
        self.set_plot()
        self.SurfFigure.draw()
