import cv2
import mediapipe as mp
import time
import threading
from queue import Queue
import collections
from pynput.keyboard import Key, Controller

d = collections.deque(maxlen=10)
keyboard = Controller()

alt = Key.alt
l_arrow = Key.left
r_arrow = Key.right

swiped = []

class handDetector():
    def __init__(self, mode=False, maxHands=1, modelComplexity=1, detectionCon=0.5, trackCon=0.5):
        self.mode = mode
        self.maxHands = maxHands
        self.modelComplex = modelComplexity
        self.detectionCon = detectionCon
        self.trackCon = trackCon
        self.mpDraw = mp.solutions.drawing_utils

        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(self.mode, self.maxHands, self.modelComplex, 
                                        self.detectionCon, self.trackCon)
    def findHands(self,img, draw = True):
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRGB)
        # print(results.multi_hand_landmarks)

        if self.results.multi_hand_landmarks:
            for handLms in self.results.multi_hand_landmarks:
                if draw:
                    self.mpDraw.draw_landmarks(img, handLms, self.mpHands.HAND_CONNECTIONS)
        return img

    def findPosition(self, img, handNo = 0, draw = True):

        lmlist = []
        if self.results.multi_hand_landmarks:
            myHand = self.results.multi_hand_landmarks[handNo]
            for id, lm in enumerate(myHand.landmark):
                h, w, c = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                lmlist.append([id, cx, cy])
                if draw:
                    cv2.circle(img, (cx, cy), 3, (255, 0, 255), cv2.FILLED)
        return lmlist

def main(out_q):
    pTime = 0
    cTime = 0
    cap = cv2.VideoCapture(0)
    detector = handDetector()

    while True:
        success, img = cap.read()
        img = detector.findHands(img)
        lmlist = detector.findPosition(img)
        if len(lmlist) != 0:
            out_q.put(lmlist[4])
        cTime = time.time()
        fps = 1 / (cTime - pTime)
        pTime = cTime

        cv2.putText(img, str(int(fps)), (10, 70), cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 255), 3)

        cv2.imshow("Image", img)
        cv2.waitKey(1)

def outputCoords(in_q):
    while True:
        data = in_q.get()
        if len(data) != 0:
            d.append(data)
            if len(d) == 10:
                global swiped
                if d[0][1] > d[9][1] + 200 and abs(d[0][2]-d[9][2]) < 100:
                    swiped.append("right")
                    keyboard.press(alt)
                    keyboard.press(r_arrow)
                    keyboard.release(alt)
                    keyboard.release(r_arrow)
                elif d[0][1] < d[9][1] - 200 and abs(d[0][2]-d[9][2]) < 100:
                    swiped.append("left")
                    keyboard.press(alt)
                    keyboard.press(l_arrow)
                    keyboard.release(alt)
                    keyboard.release(l_arrow)
                else:
                    swiped.append("none")
            if len(swiped) == 4:
                # if every item in swiped is the same, then it's a swipe
                if swiped.count(swiped[0]) == 4 and swiped[0] != "none":
                    print(swiped[0])
                swiped = []

q = Queue()

if __name__ == "__main__":
    t1=threading.Thread(target=main, args=(q,))
    t1.start()

    t2=threading.Thread(target=outputCoords, args=(q,))
    t2.start()
