import torch
from ultralytics import YOLO

OBJ_LIST = ['person', 'car', 'bus', 'truck']
DETECTOR_PATH = './weights/YOLOv8\yolov8x_UAV.pt'

class baseDet(object):
    def __init__(self):
        self.img_size = 640
        self.conf = 0.25
        self.iou = 0.70

    def init_model(self):
        raise EOFError("Undefined model type.")

    def preprocess(self):
        raise EOFError("Undefined model type.")

    def detect(self):
        raise EOFError("Undefined model type.")


class Detector(baseDet):
    def __init__(self, weight_path):
        super(Detector, self).__init__()
        self.init_model(weight_path)

    def init_model(self, weight_path):
        self.weights = weight_path
        self.device = 0 if torch.cuda.is_available() else 'cpu'
        self.model = YOLO(self.weights)
        self.m = self.model
        self.names = self.model.module.names if hasattr(self.model, 'module') else self.model.names

    def detect(self, im):
        res = self.model.predict(im, imgsz=self.img_size, conf=self.conf,
                                     iou=self.iou, device=self.device, verbose=False, line_width=2)
                    
        detected_boxes = res[0].boxes
        pred_boxes = []
        for box in detected_boxes:
            xyxy = box.xyxy.cpu() 
            #print(xyxy)
            confidence = box.conf.cpu() 
            class_id = box.cls  # get the class id
            class_id_cpu = class_id.cpu()  # move the value to CPU
            class_id_int = int(class_id_cpu.item())  # convert to integer
            lbl = self.names[class_id_int]
            if not lbl in OBJ_LIST:
                continue
            x1, y1, x2, y2 = xyxy[0].numpy()
            pred_boxes.append(
                 (x1, y1, x2, y2, lbl, confidence))
        return im, pred_boxes

