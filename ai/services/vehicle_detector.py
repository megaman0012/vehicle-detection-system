import cv2
import numpy as np
from ultralytics import YOLO
import torch
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
import asyncio

logger = logging.getLogger(__name__)

class VehicleDetector:
    def __init__(self, model_path: str = "yolov8n.pt", confidence_threshold: float = 0.5):
        """
        Initialize the vehicle detector with YOLOv8 model.
        
        Args:
            model_path: Path to the YOLOv8 model file
            confidence_threshold: Minimum confidence for detections
        """
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.model = None
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.class_names = {
            2: 'car',
            3: 'motorcycle',
            5: 'bus',
            7: 'truck'
        }
        self._load_model()
    
    def _load_model(self):
        """Load the YOLOv8 model."""
        try:
            logger.info(f"Loading YOLOv8 model from {self.model_path} on {self.device}")
            self.model = YOLO(self.model_path)
            self.model.to(self.device)
            logger.info("YOLOv8 model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load YOLOv8 model: {e}")
            raise
    
    def detect_vehicles(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect vehicles in a frame.
        
        Args:
            frame: Input frame as numpy array (BGR format)
            
        Returns:
            List of detections, each containing:
            - bbox: [x1, y1, x2, y2] bounding box coordinates
            - confidence: Detection confidence
            - class_id: Class ID
            - class_name: Class name (car, motorcycle, bus, truck)
        """
        if self.model is None:
            logger.error("Model not loaded")
            return []
        
        try:
            # Run inference
            results = self.model(frame, conf=self.confidence_threshold, verbose=False)
            
            detections = []
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Get box coordinates
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        confidence = box.conf[0].cpu().numpy()
                        class_id = int(box.cls[0].cpu().numpy())
                        
                        # Filter for vehicle classes only
                        if class_id in self.class_names:
                            detection = {
                                'bbox': [int(x1), int(y1), int(x2), int(y2)],
                                'confidence': float(confidence),
                                'class_id': class_id,
                                'class_name': self.class_names[class_id]
                            }
                            detections.append(detection)
            
            return detections
            
        except Exception as e:
            logger.error(f"Error during vehicle detection: {e}")
            return []
    
    def detect_vehicles_async(self, frame: np.ndarray) -> asyncio.Future:
        """
        Asynchronously detect vehicles in a frame.
        
        Args:
            frame: Input frame as numpy array (BGR format)
            
        Returns:
            Future that will contain the detections
        """
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(None, self.detect_vehicles, frame)
    
    def draw_detections(self, frame: np.ndarray, detections: List[Dict[str, Any]]) -> np.ndarray:
        """
        Draw detections on the frame.
        
        Args:
            frame: Input frame
            detections: List of detections from detect_vehicles
            
        Returns:
            Frame with detections drawn
        """
        annotated_frame = frame.copy()
        
        for detection in detections:
            x1, y1, x2, y2 = detection['bbox']
            confidence = detection['confidence']
            class_name = detection['class_name']
            
            # Draw bounding box
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Draw label
            label = f"{class_name}: {confidence:.2f}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
            cv2.rectangle(annotated_frame, (x1, y1 - label_size[1] - 10), 
                         (x1 + label_size[0], y1), (0, 255, 0), -1)
            cv2.putText(annotated_frame, label, (x1, y1 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
        
        return annotated_frame

# Global detector instance
vehicle_detector = VehicleDetector()