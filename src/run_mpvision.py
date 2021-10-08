"""
we run here some mediapipe experiments.
"""
import argparse
from rt import env
import cv2
import time
import json
import mediapipe as mp
mp_face_detection = mp.solutions.face_detection
mp_drawing = mp.solutions.drawing_utils
def do_config(args):
    """print current configuration."""
    print(do_faces.__doc__)
    print(json.dumps(env.config,indent=2))

def do_faces(args):
    """face detection."""
    print(do_faces.__doc__)
    source=env.get_workpath("face-demographics-walking.mp4")
    cap = cv2.VideoCapture(source)
    # Check if camera opened successfully
    if (cap.isOpened()== False):
        print(f"Error opening video stream:{source}")
        return
    fps=float(cap.get(cv2.CAP_PROP_FPS) or 30)
    fps_delay=1/fps
    print(f"fps:{fps},fps_delay:{fps_delay}")        
    with mp_face_detection.FaceDetection(
        model_selection=0, 
        min_detection_confidence=0.5
        ) as face_detection:
        while True:
            msworked=time.time()
            ret, frame = cap.read()
            if ret==False:
                break
            #cv2.imshow(source, frame)
            # Flip the image horizontally for a later selfie-view display, and convert
            # the BGR image to RGB.
            image = cv2.cvtColor(cv2.flip(frame, 1), cv2.COLOR_BGR2RGB)
            # To improve performance, optionally mark the image as not writeable to
            # pass by reference.
            image.flags.writeable = False
            results = face_detection.process(image)

            # Draw the face detection annotations on the image.
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            if results.detections:
                for detection in results.detections:
                    mp_drawing.draw_detection(image, detection)
            cv2.imshow('MediaPipe Face Detection', image)            
            msworked=time.time()-msworked
            msworked=int(msworked*1000)
            msdelay=max(1,int(fps_delay*1000)-msworked)
            #print("msworked:",msworked,msdelay)
            #time.sleep(fps_delay)
            if cv2.waitKey(msdelay) & 0xFF == ord('q'):
                break
    cap.release()
    cv2.destroyAllWindows()

if __name__=="__main__":
    jobs={k.replace("do_",""):v for k,v in locals().items() if k.startswith("do_")}
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("-j","--job",required=True,help="job to perform", choices=jobs.keys())
    args=ap.parse_args()
    env.init()
    override={k:v for (k,v) in vars(args).items() if v is not None or k not in env.config}
    env.config.update(override)
    jobs[args.job](args)
    #with app.app_context():
    #    jobs[args.job]()