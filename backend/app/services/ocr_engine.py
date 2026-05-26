import easyocr
import numpy as np
from typing import Dict, Any, List

class OCREngine:
    def __init__(self, languages: List[str] = ["en"]):
        # Lazy loading reader to save resources at startup
        self.languages = languages
        self._reader = None

    @property
    def reader(self):
        if self._reader is None:
            # gpu=False by default; can be enabled if CUDA is active
            self._reader = easyocr.Reader(self.languages, gpu=False)
        return self._reader

    def extract_text(self, image_path: str) -> Dict[str, Any]:
        """
        Extracts text from the image, preserving position info.
        Returns:
            {
                "raw_text": "all recognized text...",
                "words": [
                    {
                        "text": "word",
                        "confidence": 0.99,
                        "bbox": [x_min, y_min, x_max, y_max]
                    },
                    ...
                ]
            }
        """
        results = self.reader.readtext(image_path)
        
        words = []
        raw_text_parts = []
        
        for bbox, text, confidence in results:
            # bbox is list of 4 points: [[x0, y0], [x1, y1], [x2, y2], [x3, y3]]
            pts = np.array(bbox, dtype=np.int32)
            x_min = int(np.min(pts[:, 0]))
            y_min = int(np.min(pts[:, 1]))
            x_max = int(np.max(pts[:, 0]))
            y_max = int(np.max(pts[:, 1]))
            
            words.append({
                "text": text,
                "confidence": float(confidence),
                "bbox": [x_min, y_min, x_max, y_max]
            })
            raw_text_parts.append(text)
            
        return {
            "raw_text": " \n".join(raw_text_parts),
            "words": words
        }
