from ultralytics import YOLOWorld

# Load a pretrained YOLOv8s-worldv2 model
model = YOLOWorld("./weights\YOLO_World\yolov8s-worldv2.pt")

# Run inference with the YOLOv8n model on the 'bus.jpg' image
results = model("./photos\yayazuishou.png")

results[0].show()

