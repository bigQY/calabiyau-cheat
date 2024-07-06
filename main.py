from tools import Capturer, Monitor
from multiprocessing import Process
import cv2
from win32gui import GetWindowText, GetForegroundWindow
import time
import ctypes
from ultralytics import YOLO

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


driver = ctypes.CDLL(r"S:\code\klbq\MouseControl.dll")

targetX, targetY = 0, 0  # 全局相对移动参数


def linear_interpolation(num_steps, delay):  # 绝对平滑移动
    while True:
        x = targetX
        y = targetY
        print("target:", x, y)
        dx = (x) / num_steps
        dy = (y) / num_steps
        dx, dy = int(dx), int(dy)
        print("dx,dy:", dx, dy)
        for i in range(1, num_steps + 1):
            if x != targetX or y != targetY or x == 0 or y == 0:
                print("x,y changed", x, y, targetX, targetY)
                break
            driver.move_R(dx, dy)  
            time.sleep(delay)
        
        


def checkBoxes(boxes):
    if len(boxes) <= 0:
        return False
    closedCenter = (160, 160)
    closedDistance = 9999
    for box in boxes:
        if box.conf < 0.4:
            continue
        else:
            for pos in box.xywh:
                box_center = (pos[0], pos[1])
                # 计算当前box的中心点和屏幕中心点(160,160)的距离
                distance = ((box_center[0] - 160) ** 2 + (box_center[1] - 160) ** 2) ** 0.5
                if distance < closedDistance:
                    closedDistance = distance
                    closedCenter = box_center

    moveX = (closedCenter[0] - 160) * 2
    moveY = (closedCenter[1] - 160) * 2
    ratio = 0.15
    maxMove = 100
    if moveX > maxMove:
        moveX = maxMove
    if moveX < -maxMove:
        moveX = -maxMove
    if moveY > maxMove:
        moveY = maxMove
    if moveY < -maxMove:
        moveY = -maxMove
    moveX, moveY = moveX * ratio, moveY * ratio
    driver.move_R(int(moveX), int(moveY))
    
    return True


def loop():
    model = YOLO(r"S:\code\klbqTensorRt\best.pt", task="detect")
    while True:
        if not isRunning:
            time.sleep(0.1)
            print("暂停")
            continue
        start_time = time.time()
        frame = capture.backup(region)
        result = model.predict(frame)[0]
        end_time = time.time()
        print(f"FPS: {1/(end_time-start_time):.2f}")
        if checkBoxes(result.boxes) and isDebug:
            # 绘制yolo结果'
            new_frame = result.plot()
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
            # 添加FPS
            cv2.putText(
                frame,
                f"FPS: {1/(end_time-start_time):.2f}",
                (10, 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 0, 0),
                1,
            )
            cv2.imshow("frame", frame)
            pass
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    cv2.destroyAllWindows()

if __name__ == "__main__":
    pl = Process(target=loop, name="Loop")
    pl.start()
    pl.join()

