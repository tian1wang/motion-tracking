import numpy as np
import cv2
import argparse
from collections import deque

cap = cv2.VideoCapture(0)

pts = deque(maxlen=128)

lower_red = np.array([0, 80, 50])
upper_red = np.array([8, 255, 220])

lower_green = np.array([50, 120, 50])
upper_green = np.array([77, 255, 255])

while True:
    ret, img = cap.read()
    img = img[:, :-50]
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)  # 将捕获的视频帧由RBG转HSV

    kernel = np.ones((3, 3), np.uint8)
    # 将处于lower_green 和upper_green 区间外的值全部置为0，区间内的值置为255
    mask = cv2.inRange(hsv, lower_green, upper_green)

    # mask_pencil = cv2.inRange()
    # 对mask图像进行腐蚀，将一些小的白色区域消除，将图像“变瘦”， iterations代表使用erode的次数
    # erode就是让图像中白色部分变小
    mask = cv2.erode(mask, kernel, iterations=2)
    # 开运算 （MORPH_OPEN）:先腐蚀再膨胀
    # 删除不能包含结构元素的对象区域，平滑图像的轮廓，使拐点的地方更加连贯，断开一些狭窄的链接，去掉细小的突出部分。
    # 在这里使用开运算就是为了使除笔头外的噪声区域尽量的消除
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)

    # dilate膨胀就是将白色区域变大，黑色的区域减小
    mask = cv2.dilate(mask, kernel, iterations=5)
    # bitwise_and对二进制数据进行“与”操作，即对图像（灰度图像或彩色图像均可）每个像素值进行二进制“与”操作
    # 与操作后，白色区域的部分就会保存下来，黑色区域（为0）与后就还是为0
    res = cv2.bitwise_and(img, img, mask=mask)

    '''
    findContours() 查找检测物体的轮廓。
    第一个参数是寻找轮廓的图像；
    第二个参数表示轮廓的检索模式，有四种（本文介绍的都是新的cv2接口）：
        cv2.RETR_EXTERNAL表示只检测外轮廓
        cv2.RETR_LIST检测的轮廓不建立等级关系
        cv2.RETR_CCOMP建立两个等级的轮廓，上面的一层为外边界，里面的一层为内孔的边界信息。
        如果内孔内还有一个连通物体，这个物体的边界也在顶层。
        cv2.RETR_TREE建立一个等级树结构的轮廓。
    第三个参数method为轮廓的近似办法
        cv2.CHAIN_APPROX_NONE存储所有的轮廓点，相邻的两个点的像素位置差不超过1，
        即max（abs（x1-x2），abs（y2-y1））==1
        cv2.CHAIN_APPROX_SIMPLE压缩水平方向，垂直方向，对角线方向的元素，只保留该方向的终点坐标，
        例如一个矩形轮廓只需4个点来rs：h保存轮廓信息
        cv2.findContours()函数返回两个值:contouierarchy，一个是轮廓本身，还有一个是每条轮廓对应的属性。
        findContours函数首先返回一个list(即contours)，list中每个元素都是图像中的一个轮廓，用numpy中的ndarray表示
    '''
    cnts, heir = cv2.findContours(mask.copy(), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)[-2:]
    center = None

    if len(cnts) > 0:  # 如果检测出了轮廓
        c = max(cnts, key=cv2.contourArea)  # 以轮廓的面积为条件，找出最大的面积
        ((x, y), radius) = cv2.minEnclosingCircle(c)  # 找出最小的圆

        M = cv2.moments(c)
        center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))  # 用图像的矩求质心
        if radius > 5:
            # cv2.circle(image, center_coordinates, radius, color, thickness)
            cv2.circle(img, (int(x), int(y)), int(radius), (0, 255, 255), 2)
            cv2.circle(img, center, 5, (0, 0, 255), -1)
            # cv2.circle(res, (int(x), int(y)), int(radius), (0, 255, 255), 2)
            # cv2.circle(res, center, 5, (0, 0, 255), -1)

    pts.appendleft(center)
    for i in range(1, len(pts)):
        if pts[i - 1] is None or pts[i] is None:
            # if pts[i - 1] == pts[i]:
            continue
        thick = int(np.sqrt(len(pts) / float(i + 1)) * 2.5)
        cv2.line(img, pts[i - 1], pts[i], (0, 0, 225), thick)  # 画线

    cv2.imshow("img", img)
    cv2.imshow("mask", mask)
    cv2.imshow("res", res)

    k = cv2.waitKey(30) & 0xFF
    if k == 32:
        break

# cleanup the camera and close any open windows
cap.release()
cv2.destroyAllWindows()
