### 利用BLIP 实现图像描述类任务

import time
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration

#@ 待实现 考虑将用户的问题转化为英文作为参数传入

### ========== 全局参数 ========== ###
BLIP_PATH = './weights/blip-image-captioning-large' # BLIP 推理模型


### ========== 具体实现 ========== ###

# 图像描述
def ImgDescription(params):
    """
    图像描述任务实现。\n
    参数：{'image_path': str, 'weight_path': str (可选)}\n
    """
    blip_path = params.get('weight_path', BLIP_PATH)
    image_path = params['image_path']

    start_time = time.time()

    # 本地模型
    processor = BlipProcessor.from_pretrained(
        blip_path, local_files_only=True)
    model = BlipForConditionalGeneration.from_pretrained(
        blip_path, local_files_only=True)

    raw_image = Image.open(image_path).convert('RGB')

    # conditional image captioning
    text = "This picture show"
    inputs = processor(raw_image, text, return_tensors="pt")

    out = model.generate(**inputs, max_new_tokens=50)
    task_result = processor.decode(out[0], skip_special_tokens=True)
    # print(task_result)

    spend_time = time.time() - start_time
    print(f'推理耗时: {spend_time}')
    
    return task_result