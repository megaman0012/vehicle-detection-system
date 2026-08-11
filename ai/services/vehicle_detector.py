import logging
from typing import Any, Dict, List, Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)

try:  # Optional heavy dependencies: available only when installed in the image
    from ultralytics import YOLO
    import torch

    _ULTRAYLTICS_AVAILABLE = True
except ImportError:
    _ULTRAYLTICS_AVAILABLE = False

VEHICLE_CLASS_NAMES = {
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
}


class VehicleDetector:
    """Vehicle detector with graceful fallback.

    Uses YOLOv8 when `ultralytics` is installed and a model file is present;
    otherwise falls back to a lightweight OpenCV motion/background detector so
    the rest of the pipeline can be exercised without the heavy ML stack.
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        confidence_threshold: float = 0.5,
        device: str = "cpu",
    ):
        self.confidence_threshold = confidence_threshold
        self.device = device
        self.model_path = model_path
        self.model = None
        self._model_error: Optional[str] = None
        self._fallback_subtractor = None
        self._fallback_used = False
        self._min_contour_area = 1500
        self._init()

    def _init(self):
        if not _ULTRAYLTICS_AVAILABLE:
            self._model_error = "ultralytics/torch not installed"
            logger.warning(
                "%s: falling back to OpenCV motion detector", self._model_error
            )
            return
        try:
            import os

            model_path = self.model_path or os.getenv(
                "MODEL_PATH", "/app/models"
            )
            if isinstance(model_path, str) and not os.path.isfile(model_path):
                candidates = ["yolov8n.pt", "yolov8s.pt", "best.pt"]
                for name in candidates:
                    candidate = os.path.join(model_path, name)
                    if os.path.isfile(candidate):
                        model_path = candidate
                        break
                else:
                    self._model_error = (
                        f"No YOLO model found in {model_path}; using fallback detector"
                    )
                    logger.warning(self._model_error)
                    return
            self.model = YOLO(model_path)
            self.model.to(self.device)
            logger.info("YOLOv8 model loaded from %s on %s", model_path, self.device)
        except Exception as exc:
            self._model_error = f"Failed to load YOLOv8 model: {exc}"
            logger.warning("%s; using fallback detector", self._model_error)

    def _fallback_detect(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """Detect moving blobs using background subtraction (no ML required)."""
        if self._fallback_subtractor is None:
            self._fallback_subtractor = cv2.createBackgroundSubtractorMOG2()
        fg_mask = self._fallback_subtractor.apply(frame)
        _, thresh = cv2.threshold(fg_mask, 200, 255, cv2.THRESH_BINARY)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15)))
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        detections = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < self._min_contour_area:
                continue
            x, y, w, h = cv2.boundingRect(contour)
            if w < 30 or h < 30:
                continue
            detections.append(
                {
                    "bbox": [int(x), int(y), int(x + w), int(y + h)],
                    "confidence": min(0.9, 0.5 + area / 200000.0),
                    "class_id": 2,
                    "class_name": "car",
                }
            )
        self._fallback_used = True
        return detections

    def detect_vehicles(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """Detect vehicles in a BGR frame. Returns a list of detections."""
        if self.model is None:
            return self._fallback_detect(frame)
        try:
            results = self.model(frame, conf=self.confidence_threshold, verbose=False)
            detections = []
            for result in results:
                boxes = result.boxes
                if boxes is None:
                    continue
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    confidence = float(box.conf[0].cpu().numpy())
                    class_id = int(box.cls[0].cpu().numpy())
                    if class_id not in VEHICLE_CLASS_NAMES:
                        continue
                    detections.append(
                        {
                            "bbox": [int(x1), int(y1), int(x2), int(y2)],
                            "confidence": confidence,
                            "class_id": class_id,
                            "class_name": VEHICLE_CLASS_NAMES[class_id],
                        }
                    )
            return detections
        except Exception as exc:
            logger.error("Error during vehicle detection: %s", exc)
            return []

    def draw_detections(
        self, frame: np.ndarray, detections: List[Dict[str, Any]]
    ) -> np.ndarray:
        annotated = frame.copy()
        for detection in detections:
            x1, y1, x2, y2 = detection["bbox"]
            confidence = detection["confidence"]
            class_name = detection["class_name"]
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
            label = f"{class_name}: {confidence:.2f}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
            cv2.rectangle(
                annotated,
                (x1, y1 - label_size[1] - 10),
                (x1 + label_size[0], y1),
                (0, 255, 0),
                -1,
            )
            cv2.putText(
                annotated,
                label,
                (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 0),
                2,
            )
        return annotated

    @property
    def status(self) -> Dict[str, Any]:
        if self.model is not None:
            return {"engine": "yolov8", "model": self.model_path}
        return {"engine": "opencv-fallback", "reason": self._model_error}


vehicle_detector = VehicleDetector()
