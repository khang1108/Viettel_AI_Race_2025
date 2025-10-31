# from pathlib import Path
# from huggingface_hub import hf_hub_download
# from ultralytics import YOLO

# DOWNLOAD_PATH = Path("./models")
# DOWNLOAD_PATH.mkdir(exist_ok=True)

# model_files = [
#     "yolo11n_doc_layout.pt",
#     "yolo11s_doc_layout.pt",
#     "yolo11m_doc_layout.pt",
# ]
# selected_model_file = model_files[2] # Using the recommended nano model

# # Download the model from the Hugging Face Hub
# model_path = hf_hub_download(
#     repo_id="Armaggheddon/yolo11-document-layout",
#     filename=selected_model_file,
#     repo_type="model",
#     local_dir=DOWNLOAD_PATH,
# )

# # Initialize the YOLO model
# model = YOLO(model_path)

# # Run inference on an image
# # Replace 'path/to/your/document.jpg' with your file
# results = model('page_001.jpg')
# print(results[0].boxes[0])

# # # Save the results
# # results[0].save(filename="result.jpg")

from paddleocr import PaddleOCR
from PIL import Image

import numpy as np

ocr = PaddleOCR(
    use_textline_orientation=True,
    lang='vi',
    device='cpu'
)
img = Image.open("../page_001.jpg")
img = img.convert("RGB")

img = np.array(img)
img = img[:, :, ::-1]

result = ocr.predict(img)
for res in result:
    res.print()
    res.save_to_img("output")  
    res.save_to_json("output")  