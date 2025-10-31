from paddleocr import PaddleOCR
from vietocr.tool.predictor import Predictor 
from vietocr.tool.config import Cfg
from PIL import Image
from config import Config, Box, Markdown
from typing import List, Tuple, Optional
from pathlib import Path
from transformers import AutoModelForMaskedLM, AutoTokenizer

import numpy as np
import math
import torch
import cv2, unicodedata

class OCR_Engine:
    def __init__(self, cfg: Config):
        self.config = cfg
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        self.paddle = None

        if self.config.use_paddle_ocr and PaddleOCR:
            self.paddle = PaddleOCR(
                use_textline_orientation=True,
                lang=self.config.paddle_lang, 
                return_word_box=True,
                use_gpu = True if self.device == 'cuda' else False
            )

        if self.config.use_vietocr_fallback and Predictor:
            self.vcfg = Cfg.load_config_from_name(cfg.vietocr_config)
            self.vcfg['cnn']['pretrained'] = True
            self.vcfg['device'] = "cuda" if torch.cuda.is_available() else "cpu"
            self.vietocr_detector = Predictor(self.vcfg)

        if self.config.use_lm_scorer:
            try:
                lm_model_name = "vinai/phobert-large"
                self.lm_model = AutoModelForMaskedLM.from_pretrained(lm_model_name).to(self.device)
                self.lm_tokenizer = AutoTokenizer.from_pretrained(lm_model_name)
                self.lm_model.eval()

            except Exception as e:
                print(f"Warning: Could not load LM model")
                self.lm_model = None
        else:
            self.lm_model = None

    def _get_perplexity(self, text: str) -> float:
        '''
        VietOCR only returns text result, but I need to know
        how much confidence score VietOCR results are. So in this case,
        I use VinAI/PhoBERT LM model to handle this task.
        '''
        if not self.lm_model or not text:
            return float('inf')

        with torch.no_grad():
            inputs = self.lm_tokenizer(text, return_tensors="pt").to(self.device)
            outputs = self.lm_model(**inputs,  labels=inputs['input_ids'] )

            nev_log_likelihood = outputs.loss.item()

            ppl = math.exp(nev_log_likelihood)

            return ppl

    def _paddle_textLines(self, img_bgr):
        items = []

        if hasattr(self.paddle, "predict"):
            results = self.paddle.predict(img_bgr, use_textline_orientation=True)

            for res in results:
                rr = getattr(res, "res", None)

                if isinstance(rr, dict) and "ocr_res" in rr:
                    for ln in rr["ocr_res"]:
                        items.append({
                            "text": ln.get("text", ""),
                            "conf": float(ln.get("score", 0.0)),
                            "bbox": ln.get("box", None)
                        })
    def _convert2line(self, result_item):
        rec_texts = result_item.get('rec_texts', []) or []
        rec_boxes  = result_item.get('rec_boxes', []) or []
        rec_scores = result_item.get('rec_scores', []) or []

    def __process__(self, image_bgr: np.ndarray, mode: str = "paragraph") -> Tuple[str, float]:
        text1, conf1 = "", 0.0
        if hasattr(self.paddle, "predict") and self.paddle:
            result = self.paddle.predict(image_bgr)

            lines, confs = [], []
            for res in result:
                rr = getattr(res, "res", None)
                if isinstance(rr, dict) and "rec_texts" in rr and "rec_scores" in rr:
                    lines.extend(rr["rec_texts"])
                    confs.extend(rr["rec_scores"])

            if lines:
                text1 = self._normalize(" ".join(lines))
                conf1 = float(np.mean(confs)) if confs else 0.0

        text2, conf2 = [], []
        if self.vietocr_detector:
            img_gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
            try:
                text = self.vietocr_detector.predict(img_gray)
            except Exception:
                text2 = ""
            
            if text:
                text2 = self._normalize(text)
                conf2 = self._get_perplexity(text2)
                conf2 = max(0, 1 - (conf2 / 50.0))
        
        if conf2 > conf1 + 0.05 and text2:
            return text2, conf2

        return text1 or text2, max(conf1, conf2)

    @staticmethod
    def _normalize(s: str) -> str:
        s = unicodedata.normalize("NFC", s) # Convert to Pre-composed
        s = s.replace("\u200b", "").replace("\xa0", " ")
        s = " ".join(s.split())

        return s
