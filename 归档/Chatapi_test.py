import requests

API_KEY = "sk-AencKA6Oy7WnhukWgquDlbis89fhQ5q4Nz8ba4BvYJUjy8LR"
model = 'gpt-4o-mini'
url = "https://api.chatanywhere.tech/v1"

def call_chatgpt(prompt):
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json',
    }
    data = {
        'model': model,
        'messages': [{'role': 'user', 'content': prompt}],
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()

# 示例调用
response = call_chatgpt("请告诉我如何实现YOLO的图像识别。")
print(response)
