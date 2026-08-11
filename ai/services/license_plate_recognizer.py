import logging
import re
from typing import Any, Dict, List, Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)

try:  # PaddleOCR is optional and heavy; installed separately when needed
    from paddleocr import PaddleOCR

    _PADDLEOCR_AVAILABLE = True
except ImportError:
    _PADDLEOCR_AVAILABLE = False


class LicensePlateRecognizer:
    """License plate OCR with graceful fallback.

    Uses PaddleOCR when available; otherwise returns empty results so the
    rest of the pipeline keeps working.
    """

    def __init__(self, lang: str = "en", use_angle_cls: bool = True, use_gpu: Optional[bool] = None):
        self.ocr = None
        self.lang = lang
        self.use_angle_cls = use_angle_cls
        self.plate_patterns = [
            r"^[A-Z]{1,3}[0-9]{1,4}[A-Z]{0,3}$",
            r"^[0-9]{1,4}[A-Z]{1,3}$",
            r"^[A-Z]{2}[0-9]{4}[A-Z]{0,2}$",
            r"^[A-Z]{1,2}[0-9]{1,4}[A-Z]{0,2}$",
        ]
        if _PADDLEOCR_AVAILABLE:
            try:
                if use_gpu is None:
                    use_gpu = self._is_gpu_available()
                self.ocr = PaddleOCR(
                    use_angle_cls=use_angle_cls,
                    lang=lang,
                    use_gpu=use_gpu,
                    show_log=False,
                )
                logger.info("PaddleOCR initialized")
            except Exception as exc:
                logger.warning("PaddleOCR init failed (%s); plate OCR disabled", exc)
                self.ocr = None
        else:
            logger.warning("paddleocr not installed; plate OCR disabled")

    def _is_gpu_available(self) -> bool:
        try:
            import paddle

            return paddle.is_compiled_with_cuda()
        except ImportError:
            return False

    def preprocess_plate_image(self, plate_img: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        blurred = cv2.GaussianBlur(enhanced, (3, 3), 0)
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        kernel = np.ones((2, 2), np.uint8)
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)
        return cleaned

    def extract_text_from_plate(self, plate_img: np.ndarray) -> List[Dict[str, Any]]:
        if self.ocr is None or plate_img is None or plate_img.size == 0:
            return []
        try:
            processed = self.preprocess_plate_image(plate_img)
            results = self.ocr.ocr(processed, cls=True)
            ocr_results = []
            if results and results[0]:
                for line in results[0]:
                    if line is None:
                        continue
                    text = line[1][0]
                    confidence = float(line[1][1])
                    cleaned = re.sub(r"[^A-Z0-9]", "", text.upper())
                    is_valid = any(re.match(pattern, cleaned) for pattern in self.plate_patterns) if cleaned else False
                    ocr_results.append(
                        {
                            "text": cleaned,
                            "confidence": confidence,
                            "is_valid_plate": is_valid,
                            "original_text": text,
                        }
                    )
            return ocr_results
        except Exception as exc:
            logger.error("Error during license plate OCR: %s", exc)
            return []

    def recognize_license_plate(
        self, vehicle_img: np.ndarray, bbox: List[int]
    ) -> Dict[str, Any]:
        empty = {
            "plate_text": None,
            "confidence": 0.0,
            "is_valid_plate": False,
            "plate_bbox": None,
        }
        if self.ocr is None:
            return empty
        try:
            x1, y1, x2, y2 = [int(v) for v in bbox]
            vehicle_roi = vehicle_img[y1:y2, x1:x2]
            if vehicle_roi.size == 0:
                return empty
            h, w = vehicle_roi.shape[:2]
            regions = [
                (int(h * 0.8), h, 0, w),
                (int(h * 0.6), h, 0, w),
                (int(h * 0.5), int(h * 0.8), 0, w),
                (0, h, 0, w),
            ]
            best = dict(empty)
            for y_start, y_end, x_start, x_end in regions:
                region = vehicle_roi[y_start:y_end, x_start:x_end]
                if region.size == 0:
                    continue
                for result in self.extract_text_from_plate(region):
                    if result["is_valid_plate"] and result["confidence"] > best["confidence"]:
                        best = {
                            "plate_text": result["text"],
                            "confidence": result["confidence"],
                            "is_valid_plate": True,
                            "plate_bbox": [x1 + x_start, y1 + y_start, x1 + x_end, y1 + y_end],
                        }
                        break
                if best["plate_text"] is not None and best["confidence"] > 0.5:
                    break
            return best
        except Exception as exc:
            logger.error("Error recognizing license plate: %s", exc)
            return dict(empty)

    def draw_plate_result(
        self, frame: np.ndarray, vehicle_bbox: List[int], plate_result: Dict[str, Any]
    ) -> np.ndarray:
        annotated = frame.copy()
        x1, y1, x2, y2 = [int(v) for v in vehicle_bbox]
        cv2.rectangle(annotated, (x1, y1), (x2, y2), (255, 0, 0), 2)
        if plate_result and plate_result.get("plate_text"):
            if plate_result.get("plate_bbox"):
                px1, py1, px2, py2 = plate_result["plate_bbox"]
                cv2.rectangle(annotated, (px1, py1), (px2, py2), (0, 255, 255), 2)
            text = f"Plate: {plate_result['plate_text']} ({plate_result['confidence']:.2f})"
            cv2.putText(annotated, text, (x1, max(y1 - 10, 20)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        return annotated


license_plate_recognizer = LicensePlateRecognizer()
