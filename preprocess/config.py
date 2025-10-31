from typing import Optional
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional

#* ----------------------------------------------------------------
#*                              LAYOUT Analyzers
#* In this part, We use YOLOv11 model, fine-tuned on DocLayNet dataset
#* as the main core and checker is LayoutParser. And to fusions the correct
#* boxes, We use Weighted Boxes Fusion (WBS).
#* ----------------------------------------------------------------
try:
    from ultralytics import YOLO
except Exception:
    YOLO = None

try:
    import layoutparser as lp
except Exception:
    lp = None


#* ----------------------------------------------------------------
#*                      OCR Engines
#* In this project, because of working on Vietnamese PDF files, We 
#* choose PaddleOCR as the main OCR engine and VietOCR as a checker
#* to validate the results from PaddleOCR, which increases the accuracy.
#*
#* Both of models will start extracting text on Pictures that are exported
#* from PDF documents and then they will vote for the best boxes and unite 
#* the results.
#* ----------------------------------------------------------------
try:
    from paddleocr import PaddleOCR
except Exception:
    PaddleOCR = None

try:
    from vietocr.tool.predictor import Predictor as VietOCRPredictor
    from vietocr.tool.config import Cfg as VietOCRCfg
except Exception:
    VietOCRPredictor, VietOCRCfg = None, None


#* ----------------------------------------------------------------
#*                          TABLE Engine
#* We use CAMELOT: PDF Table Extraction as the main core for this part 
#* because of its power and stability.
#* ----------------------------------------------------------------
try:
    import camelot
except Exception:
    camelot = None

#* ================================================================================
class Config:
    dpi: int = 400
    max_workers = 2

    yolo_model_weights = '../models/yolo11m_doc_layout.pt'
    publy_maskrcnn_cfg: Optional[str] = "lp://PubLayNet/mask_rcnn_X_101_32x8d_FPN_3x/config"  
    publy_maskrcnn_model: Optional[str] = "lp://PubLayNet/mask_rcnn_X_101_32x8d_FPN_3x/model"

    wbf_iou_thresh: float = 0.5
    min_box_score: float = 0.3
    
    use_publy: bool = True
    use_yolo: bool = True
    wbf_iou_thresh: float = 0.5
    wbf_vote_thresh: float = 0.1
    min_box_score: float = 0.3

    use_paddle_ocr: bool = True
    paddle_lang: str = "vi"  
    use_vietocr_fallback: bool = True
    vietocr_config: str = "vgg_transformer"
    use_lm_scorer:bool = True

    table_detector_name: str = "microsoft/table-transformer-detection"          
    table_structure_name: str = "microsoft/table-transformer-structure-recognition"

    use_pix2tex: bool = True  

    heading_font_ratio_h1: float = 0.85
    heading_font_ratio_h2: float = 0.70
    heading_font_ratio_h3: float = 0.60

class Box:
    """
    This box will cover layout on document.
    """

    x1: int
    y1: int
    
    x2: int
    y2: int

    label: str
    score: float
    page: int

    def area(self) -> float:
        return max(0, self.x2 - self.x1) * max(0, self.y2 - self.y1)
    
    def iou(self, other: "Box") -> float:
        """
        Calculate Intersection-over-Union (IOU)
        """

        #* Formula: IoU = AreaOfOverlap / AreaOfUnion

        y_max1 = max(self.y1, other.y1)
        y_min2 = max(self.y2, other.y2)

        x_max1 = max(self.x1, other.x1)
        x_min2 = min(self.x2, other.x2)

        inter = max(0, (x_min2 - x_max1) * (y_min2, y_max1))
        union = self.area() + other.area() - inter

        return inter / union
    
class Markdown:
    page: int
    order: int
    kind: str

    bbox: Tuple[int, int, int, int]
    text: Optional[str] = None
    meta: Dict = field(default_factory=dict)
