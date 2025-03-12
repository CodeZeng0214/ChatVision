from PySide6.QtCore import QObject, Signal, Slot
import json
import os
import re
import importlib
import inspect

class TaskProcessor(QObject):
    """Processes tasks and coordinates between plugins"""
    result_ready = Signal(dict)  # Signal emitted when results are ready
    parameter_needed = Signal(list, str)  # Signal emitted when parameters are needed
    task_completed = Signal(dict)  # Signal emitted when task is complete with final results
    
    def __init__(self, llm_client=None):
        super().__init__()
        self.llm_client = llm_client
        self.active_task = None
        self.pending_params = None
        self.plugins = {}
        self.load_plugins()
    
    def load_plugins(self):
        """Load available vision task plugins"""
        # This is a simplified version. In a real app, you'd scan a plugins directory
        # and dynamically load modules based on what's available.
        self.plugins = {
            "object_detection": {
                "name": "Object Detection",
                "description": "Detect objects in images using YOLO",
                "enabled": True,
                "keywords": ["detect", "objects", "find", "identify", "what is in"],
                "required_params": ["image_path"],
                "optional_params": ["confidence_threshold"],
                "handler": self.handle_object_detection
            },
            "pose_estimation": {
                "name": "Pose Estimation",
                "description": "Estimate human poses in images",
                "enabled": True,
                "keywords": ["pose", "posture", "body position"],
                "required_params": ["image_path"],
                "optional_params": [],
                "handler": self.handle_pose_estimation
            },
            "image_caption": {
                "name": "Image Captioning",
                "description": "Generate captions for images",
                "enabled": True,
                "keywords": ["caption", "describe", "what is this", "explain"],
                "required_params": ["image_path"],
                "optional_params": ["language"],
                "handler": self.handle_image_caption
            },
            "face_detection": {
                "name": "Face Detection",
                "description": "Detect faces in images",
                "enabled": True,
                "keywords": ["face", "faces", "person", "people"],
                "required_params": ["image_path"],
                "optional_params": [],
                "handler": self.handle_face_detection
            }
        }
    
    def process_task(self, task_info):
        """Process a new task from the chat window"""
        self.active_task = task_info
        
        # Check if media is provided
        if not task_info.get("media_path") and "camera" not in task_info.get("message", "").lower():
            # Determine what kind of media the task needs
            needed_params = self.determine_needed_parameters(task_info.get("message", ""))
            if needed_params:
                self.pending_params = needed_params
                self.parameter_needed.emit(needed_params, "Please provide the following information to complete your request:")
                return
        
        # If it's a camera request but no camera specified
        if "camera" in task_info.get("message", "").lower() and task_info.get("media_path") != "camera":
            self.pending_params = [{
                "name": "camera_id",
                "label": "Select Camera",
                "type": "camera_selector"
            }]
            self.parameter_needed.emit(self.pending_params, "Please select a camera to use:")
            return
        
        # Process with available info
        self.execute_task(task_info)
    
    def determine_needed_parameters(self, message):
        """Determine what parameters are needed based on the message"""
        # Try to identify what kind of task the user is requesting
        task_type = self.identify_task_type(message)
        if not task_type:
            return []  # Can't determine task type
        
        # Get required parameters for this task
        plugin_info = self.plugins.get(task_type)
        if not plugin_info:
            return []
        
        # Check what parameters we need to ask for
        needed_params = []
        
        for param_name in plugin_info.get("required_params", []):
            if param_name == "image_path":
                needed_params.append({
                    "name": "image_path",
                    "label": "Select an image",
                    "type": "image_selector"
                })
        
        return needed_params
    
    def identify_task_type(self, message):
        """Identify what type of vision task the user is requesting"""
        message = message.lower()
        
        for plugin_id, plugin_info in self.plugins.items():
            if not plugin_info["enabled"]:
                continue
                
            for keyword in plugin_info["keywords"]:
                if keyword.lower() in message:
                    return plugin_id
        
        # Default to image caption if we can't determine
        if any(word in message for word in ["what", "explain", "describe"]):
            return "image_caption"
            
        return None
    
    def execute_task(self, task_info):
        """Execute the identified task"""
        # Identify task type
        task_type = self.identify_task_type(task_info.get("message", ""))
        
        if not task_type:
            # Default to image caption if we have an image but no clear task
            if task_info.get("media_path") and task_info.get("media_type") == "image":
                task_type = "image_caption"
            else:
                # No identifiable task and no image, return error
                self.result_ready.emit({"text": "I'm not sure what task you want me to perform. Please be more specific or provide an image."})
                return
        
        # Get the handler for this task type
        plugin_info = self.plugins.get(task_type)
        if not plugin_info or not plugin_info["enabled"]:
            self.result_ready.emit({"text": f"Sorry, the {task_type} plugin is not available."})
            return
            
        # Call the appropriate handler
        if "handler" in plugin_info:
            plugin_info["handler"](task_info)
        
    def handle_object_detection(self, task_info):
        """Handle object detection tasks"""
        # In a real implementation, this would call a YOLO model
        if task_info.get("media_path") and task_info.get("media_type") == "image":
            # Simulate YOLO detection
            objects = ["person", "chair", "laptop", "cup"]
            counts = {"person": 2, "chair": 3, "laptop": 1, "cup": 2}
            
            # Format results
            result_text = "Object Detection Results:\n\n"
            for obj in objects:
                result_text += f"- {obj}: {counts[obj]}\n"
            
            self.result_ready.emit({
                "text": result_text,
                "image_path": task_info["media_path"]  # In real app, would be path to annotated image
            })
        else:
            self.result_ready.emit({"text": "Please provide an image for object detection."})
    
    def handle_pose_estimation(self, task_info):
        """Handle pose estimation tasks"""
        # In a real implementation, this would call a pose estimation model
        if task_info.get("media_path") and task_info.get("media_type") == "image":
            # Simulate pose estimation
            result_text = "Pose Estimation Results:\n\n"
            result_text += "Detected 2 people in the image.\n"
            result_text += "Person 1: Standing with arms raised\n"
            result_text += "Person 2: Sitting position\n"
            
            self.result_ready.emit({
                "text": result_text,
                "image_path": task_info["media_path"]  # In real app, would be path to pose-annotated image
            })
        else:
            self.result_ready.emit({"text": "Please provide an image for pose estimation."})
    
    def handle_image_caption(self, task_info):
        """Handle image captioning tasks"""
        # In a real implementation, this would call BLIP or a similar model
        if task_info.get("media_path") and task_info.get("media_type") == "image":
            # Simulate image captioning
            result_text = "Image Caption:\n\n"
            result_text += "A group of people sitting around a table working on laptops in what appears to be a coffee shop."
            
            self.result_ready.emit({
                "text": result_text,
                "image_path": task_info["media_path"]
            })
        else:
            self.result_ready.emit({"text": "Please provide an image to caption."})
    
    def handle_face_detection(self, task_info):
        """Handle face detection tasks"""
        # In a real implementation, this would call a face detection model
        if task_info.get("media_path") and task_info.get("media_type") == "image":
            # Simulate face detection
            result_text = "Face Detection Results:\n\n"
            result_text += "Detected 3 faces in the image.\n"
            result_text += "Estimated ages: 25-30, 35-40, 20-25\n"
            
            self.result_ready.emit({
                "text": result_text,
                "image_path": task_info["media_path"]  # In real app, would be path to face-annotated image
            })
        else:
            self.result_ready.emit({"text": "Please provide an image for face detection."})

    def request_camera_preview(self):
        """Request to show camera preview in sidebar"""
        self.result_ready.emit({"camera": True})
    
    @Slot(dict)
    def process_parameters(self, params):
        """Process parameters received from the parameter input widget"""
        if self.pending_params and self.active_task:
            # Update active task with the new parameters
            for key, value in params.items():
                self.active_task[key] = value
            
            # Clear pending params
            self.pending_params = None
            
            # Re-execute the task with the new parameters
            self.execute_task(self.active_task)
            
    # Add method to update plugin settings from the plugin manager
    @Slot(str, dict)
    def update_plugin_settings(self, plugin_id, settings):
        """Update settings for a specific plugin"""
        if plugin_id in self.plugins:
            plugin = self.plugins[plugin_id]
            # Update plugin parameters with new settings
            for key, value in settings.items():
                if key in plugin.get("parameters", {}):
                    plugin["parameters"][key]["default"] = value
            
            print(f"Updated settings for plugin {plugin_id}: {settings}")
