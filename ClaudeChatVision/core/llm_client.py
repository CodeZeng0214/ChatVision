import json
import requests
import os
import time

class LLMClient:
    """Minimal LLM client that can be used for generating responses"""
    def __init__(self):
        # Default configuration - can be changed through settings
        self.base_url = "https://api.chatanywhere.tech/v1"
        self.api_key = "sk-AencKA6Oy7WnhukWgquDlbis89fhQ5q4Nz8ba4BvYJUjy8LR"
        self.model = "gpt-4o-mini"
        self.enabled = False  # Disabled by default to avoid accidental API calls
    
    def generate_response(self, prompt, system_message=None):
        """Generate a response using the LLM"""
        if not self.enabled:
            return "LLM integration is disabled. (Placeholder response)"
        
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            messages = []
            
            # Add system message if provided
            if system_message:
                messages.append({"role": "system", "content": system_message})
            
            # Add user prompt
            messages.append({"role": "user", "content": prompt})
            
            data = {
                "model": self.model,
                "messages": messages
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                print(f"Error: {response.status_code}")
                print(response.text)
                return f"Error calling LLM API: {response.status_code}"
                
        except Exception as e:
            print(f"Exception: {e}")
            return f"Error: {str(e)}"
    
    def format_vision_results(self, task_type, results_data):
        """Format vision processing results into natural language"""
        if not self.enabled:
            # If LLM is disabled, return a simple formatted string
            return self._simple_format_results(task_type, results_data)
        
        # Prepare prompt for the LLM to format the results
        prompt = f"Below are the results from a {task_type} task. Please format these results in a natural, conversational way:\n\n"
        prompt += json.dumps(results_data, indent=2)
        
        system_message = "You are an assistant that formats technical results into natural language responses. Keep your answers concise and friendly."
        
        return self.generate_response(prompt, system_message)
    
    def _simple_format_results(self, task_type, results_data):
        """Simple formatter for when LLM is disabled"""
        if task_type == "object_detection":
            text = "I detected the following objects:\n"
            for obj, count in results_data.get("objects", {}).items():
                text += f"- {count}x {obj}\n"
            return text
            
        elif task_type == "pose_estimation":
            return "I analyzed the poses in the image: " + results_data.get("summary", "No results available.")
            
        elif task_type == "image_caption":
            return "Image description: " + results_data.get("caption", "No caption available.")
            
        else:
            return "Results: " + str(results_data)
    
    def update_settings(self, settings):
        """Update LLM client settings"""
        if "base_url" in settings:
            self.base_url = settings["base_url"]
        if "api_key" in settings:
            self.api_key = settings["api_key"]
        if "model" in settings:
            self.model = settings["model"]
        if "enabled" in settings:
            self.enabled = settings["enabled"]
    
    def process_user_query(self, query, task_results=None):
        """Process a user query with optional task results context"""
        if not self.enabled:
            # Return simple response if LLM is disabled
            if task_results:
                return f"I've processed your request using {task_results.get('task_type', 'vision processing')}. See the results in the sidebar."
            else:
                return "I'm here to help with your vision processing tasks. Please provide an image or specify a task."
        
        # Build context from task results if available
        context = ""
        if task_results:
            context = f"Task type: {task_results.get('task_type', 'unknown')}\n"
            context += f"Results: {json.dumps(task_results, indent=2)}\n\n"
        
        # Prepare prompt
        prompt = f"{context}User query: {query}\n\nPlease respond to the user query based on the task results."
        
        system_message = "You are an assistant specializing in computer vision tasks. Respond to the user based on the results of vision processing tasks."
        
        return self.generate_response(prompt, system_message)
