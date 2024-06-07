import multiprocessing
from tools import Capturer, Monitor, KlbqV10
from multiprocessing import Process
import multiprocessing
import cv2
from win32gui import FindWindow, SetWindowPos, GetWindowText, GetForegroundWindow
import time
import ctypes
import os
import keyboard
from ultralytics import YOLOv10
import threading

isRunning = True
isDebug = True

def changeRunning():
    global isRunning
    isRunning = not isRunning

# 注册快捷键
# keyboard.add_hotkey('alt+1', changeRunning, args=(), suppress=True, timeout=1, trigger_on_release=False)

imgSize = 320
centerPoint = Monitor.resolution.center()
region = (
    centerPoint[0] - imgSize // 2,
    centerPoint[1] - imgSize // 2,
    imgSize,
    imgSize,
)
# region = (1000,1000,2560,1600)
capture = Capturer(title=GetWindowText(GetForegroundWindow()), region=region)

model = YOLOv10(r"S:\code\klbq\best.pt", verbose=False)

driver = ctypes.CDLL(r"S:\code\klbq\MouseControl.dll")

targetX = multiprocessing.Value('d', 0)
targetY = multiprocessing.Value('d', 0)

def movePrecess(detectedEvent, movedEvent, targetX, targetY):
    num_steps = 100
    delay = 0.001
    while True:
        detectedEvent.wait()  # 等待detectedEvent被设置
        print("移动进程执行")
        x = targetX.value
        y = targetY.value
        print("target:", x, y)
        dx = (x) / num_steps
        dy = (y) / num_steps
        dx, dy = int(dx), int(dy)
        if dx>0.2 and dx<1:
            dx = 1
        if dy>0.2 and dy<1:
            dy = 1
        print("dx,dy:", dx, dy)
        for i in range(1, num_steps + 1):
            if x != targetX.value or y != targetY.value or x == 0 or y == 0:
                print("x,y changed", x, y, targetX.value, targetY.value)
                detectedEvent.clear()  # 清除detectedEvent的状态
                movedEvent.set()  # 设置movedEvent的状态，通知进程2执行
                break
            driver.move_R(dx, dy)   
            # time.sleep(delay)
        detectedEvent.clear()  # 清除detectedEvent的状态
        movedEvent.set()  # 设置movedEvent的状态，通知进程2执行

def process2(detectedEvent, movedEvent, targetX, targetY):
    while True:
        movedEvent.wait()  # 等待movedEvent被设置
        print("检测进程执行")
        if not isRunning:
            time.sleep(0.1)
            print("暂停")
            continue
        start_time = time.time()
        frame = capture.backup(region)
        result = model.predict(frame)[0]
        end_time = time.time()
        boxes = result.boxes
        if len(boxes) > 0:
            print("检测到目标")
            closedCenter = (160, 160)
            closedDistance = 9999
            for box in boxes:
                for pos in box.xywh:
                    box_center = (pos[0], pos[1])
                    # if(box_center[0]<200 and box_center[1]>200):
                    #     return False
                    # 计算当前box的中心点和屏幕中心点(160,160)的距离
                    distance = ((box_center[0] - 160) ** 2 + (box_center[1] - 160) ** 2) ** 0.5
                    if distance < closedDistance:
                        closedDistance = distance
                        closedCenter = box_center
            moveX = (closedCenter[0] - 160) * 2
            moveY = (closedCenter[1] - 160) * 2
            ratio = 1
            moveX, moveY = moveX * ratio, moveY * ratio
            # driver.move_R(int(moveX), int(moveY))
            targetX.value, targetY.value = int(moveX), int(moveY)
            print('target:', targetX.value, targetY.value)
        else:
            print("未检测到目标")
            targetX.value, targetY.value = 0, 0
        movedEvent.clear()  # 清除movedEvent的状态
        detectedEvent.set()  # 设置detectedEvent的状态，通知进程1执行
        if isDebug:
            # 绘制yolo结果'
            new_frame = result.plot()
            # 添加FPS
            cv2.putText(
                new_frame,
                f"FPS: {1/(end_time-start_time):.2f}",
                (10, 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                1,
            )
            cv2.imshow("frame", new_frame)
        elif isDebug:
            cv2.imshow("frame", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    cv2.destroyAllWindows()


if __name__ == '__main__':
    detectedEvent = multiprocessing.Event()
    movedEvent = multiprocessing.Event()

    detectedEvent.set()

    p1 = multiprocessing.Process(target=movePrecess, args=(detectedEvent, movedEvent,targetX, targetY))
    p2 = multiprocessing.Process(target=process2, args=(detectedEvent, movedEvent,targetX, targetY))

    p1.start()
    p2.start()

    p1.join()
    p2.join()
