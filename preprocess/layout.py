from __future__ import annotations

from pathlib import Path
from typing import List

import numpy as np
import torch
from config import Box, Config

try:
    from ultralytics import YOLO
except Exception:
    YOLO = None

try:
    import layoutparser as lp
except Exception:
    lp = None

device = "cuda" if torch.cuda.is_available() else "cpu"
class LayoutAnalyzer:
    """
    Ensemble YOLOv11 fine-tune on DocLayNet dataset + PubLayNet and then using Weighted Box Fusion
    to select the best boxes.
    """

    def __init__(self, cfg: Config):
        '''
        First setup config for two models of Layout Analyzer. 
        This function uses 'ensemble' technique to combine results from both of models
        and then unite them to one. To unite the results, I use 'Weighted Box Fusion' and
        calculate 'IoU' scores.
        '''
        self.cfg = cfg

        self.yolo = (
            YOLO(cfg.yolo_model_weights)
            if (YOLO and cfg.use_yolo and Path(cfg.yolo_model_weights).exists())
            else None
        )

        if lp and cfg.use_publy:
            self.publy = lp.Detectron2LayoutModel(
                config_path=cfg.publy_maskrcnn_cfg,
                model_path=cfg.publy_maskrcnn_model,
                label_map={0: "text", 1: "title", 2: "list", 3: "table", 4: "figure"},
                extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.5],
                device="cuda" if self._has_cuda() else "cpu",
            )
        else:
            self.publy = None

    @staticmethod
    def _is_cuda() -> bool:
        return torch.cuda.is_available()

    def detect(self, images: List[np.ndarray]) -> List[List[Box]]:
        all_pages: List[List[Box]]

        cur: List[Box]
        for p_idx, img in enumerate(images):

            # Generate results by YOLOv11 model
            if self.yolo:
                res = self.yolo.model(img)

                for box in res[0].boxes:
                    # * Change cpu() if run in local
                    coords = box.xyxy.cpu().numpy().astype(int).tolist()
                    x1, y1, x2, y2 = coords[:4]
                    cls = int(box.cls[0].item())
                    score = float(box.conf[0].item())
                    label = res.names[cls]

                    if score >= self.cfg.min_box_score:
                        cur.append(Box(x1, y1, x2, y2, label, score, p_idx))

            # Generate results by PubLayNet model
            if self.publy:
                res = self.publy.detect(img)
                for b in res:
                    x1, y1, x2, y2 = map(int, b.block.coordinates)
                    label = b.type
                    score = float(getattr(b, "score", 0.5))
                    if score >= self.cfg.min_box_score:
                        cur.append(Box(x1, y1, x2, y2, label, score, p_idx))

            # Fuse two results
            fused = self._wbf(cur, iou_thresh=self.cfg.wbf_iou_thresh)
            all_pages.append(fused)

            return all_pages

    # Calculate 'Weighted Box Fusion' score
    def _wbf(boxes: List[Box], iou_thresh: float = 0.5) -> List[Box]:
        out: List[Box] = []
        boxes = sorted(boxes, key=lambda box: box.score, reverse=True)

        used = [False] * len(boxes)
        for i_box, box in enumerate(boxes):
            if used[i_box]:
                continue

            cluster = []
            for j in range(i_box + 1, len(boxes)):
                if used[j]:
                    continue

                if boxes[j].label == box.label and box.iou(boxes[j]) >= iou_thresh:
                    cluster.append(j)

            if len(cluster == 1):
                out.append(box)
                used[i_box] = True
                continue

            sum_x1 = sum_x2 = sum_y1 = sum_y2 = 0.0
            sum_w = 0.0
            sum_score = 0.0

            for k in cluster:
                cur_box = boxes[k]
                w = max(cur_box.score, 1e-06)

                sum_w += w
                sum_score += cur_box.score

                sum_x1 += w * cur_box.x1
                sum_y1 += w * cur_box.y1
                sum_x2 += w * cur_box.x2
                sum_y2 += w * cur_box.y2

            out.append(
                Box(int(sum_x1 / sum_w), int(sum_y1 / sum_w), int(sum_x2 / sum_w)),
                box.label,
                sum_score / len(cluster),
                box.page,
            )
            return [b for b in out if b.x2 - b.x1 > 10 and b.y2 - b.y1 > 10]