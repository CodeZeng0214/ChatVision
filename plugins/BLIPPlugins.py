### 利用BLIP 实现图像描述类插件

import time
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration
from core.Plugin import Plugin

#@ 待实现 考虑将用户的问题转化为英文作为参数传入

### ========== 全局参数 ========== ###
BLIP_PATH = './weights/blip-image-captioning-large' # BLIP 推理模型


### ========== 具体实现 ========== ###

class ImgDescriptionPlugin(Plugin):
    """ 图像描述插件实现。\n
    参数：{'image_path': str, 'weight_path': str (可选)}\n
    """
    def __init__(self):
        super().__init__('ImageDescription', 
                         [{'name': 'image_path', 'description': '待描述的图像路径', 'required': True},
                          {'name': 'weight_path', 'description': 'BLIP权重路径', 'required': False}],
                         "使用BLIP进行图像描述。")
        self.execute = self.ImgDescription
    
    # 图像描述
    def ImgDescription(self, params):
        """
        图像描述插件实现。\n
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

        print("正在分析图像")
        out = model.generate(**inputs, max_new_tokens=50)
        plugin_result = processor.decode(out[0], skip_special_tokens=True)
        print("分析完成")

        spend_time = time.time() - start_time

        return plugin_result
