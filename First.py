import cv2
import numpy as np
import mediapipe as mp 
from math import hypot
import screen_brightness_control as sbc 
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL


def main():
    
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume)) 
    volRange = volume.GetVolumeRange()
    minVol ,maxVol, _ = volRange 
    
    #setting up the hands model
    mpHands = mp.solutions.hands
    hands = mpHands.Hands(static_image_mode=False, model_complexity= 1, min_detection_confidence= 0.75, min_tracking_confidence= 0.75 , max_num_hands= 2 ) 

    draw = mp.solutions.drawing_utils
    
    cap = cv2.VideoCapture(0)
    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.flip(frame, 1)
            frameRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            processed = hands.process(frameRGB)

            left_landmark_list , right_landmark_list = get_left_right_landmark(frame, processed, draw, mpHands)

            if left_landmark_list : 
                left_distance = get_distance(frame , left_landmark_list)
                b_level = np.interp(left_distance, [50,220] , [0,100] )
                sbc.set_brightness(int(b_level)) 

            if  right_landmark_list : 
                right_distance = get_distance(frame, right_landmark_list) 
                vol = np.interp(right_distance, [50,220] , [minVol , maxVol] )
                volume.SetMasterVolumeLevel(vol, None)  
            
            # print(processed.multi_hand_landmarks) 
            
            cv2.imshow('frame', frame)
            
            if cv2.waitKey(1) & 0xFF == 27:  # ESC key
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()

def get_left_right_landmark(frame, processed, draw, mpHands) :
    left_landmark_list = [] 
    right_landmark_list = [] 

    if processed.multi_hand_landmarks :
        for handlm in processed.multi_hand_landmarks : 
            for idx , found_landmark in enumerate(handlm.landmark) :
                height , width, _ = frame.shape 
                x, y = int(found_landmark.x * width) , int(found_landmark.y * height ) 

                if(idx == 4 or idx == 8 ) : 
                    landmark = [idx, x, y] 

                    if handlm == processed.multi_hand_landmarks[0] : 
                        left_landmark_list.append(landmark) 
                    if len(processed.multi_hand_landmarks) > 1 and handlm == processed.multi_hand_landmarks[1] : 
                        right_landmark_list.append(landmark) 

            draw.draw_landmarks(frame, handlm, mpHands.HAND_CONNECTIONS)

    return left_landmark_list, right_landmark_list 

def get_distance(frame , landmark_list): 
    if len(landmark_list ) < 2 : 
        return 

    (x1, y1) , (x2, y2) = (landmark_list[0][1], landmark_list[0][2]) , (landmark_list[1][1], landmark_list[1][2])

    cv2.circle(frame, (x1, y1), 7, (0, 255 ,0), cv2.FILLED )
    cv2.circle(frame, (x2, y2), 7, (0, 255 ,0), cv2.FILLED )
    cv2.line(frame, (x1, y1),(x2,y2) , (0, 255 ,0), 3 )

    L = hypot(x2-x1, y2-y1)

    return L 


if __name__ == '__main__':
    main()
