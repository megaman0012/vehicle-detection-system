import cv2
import numpy as np
from paddleocr import PaddleOCR
import logging
import re
from typing import List, Dict, Any, Optional, Tuple
import time

logger = logging.getLogger(__name__)

class LicensePlateRecognizer:
    def __init__(self, 
                 lang: str = 'en',
                 use_angle_cls: bool = True,
                 use_gpu: bool = None):
        """
        Initialize the license plate recognizer with PaddleOCR.
        
        Args:
            lang: Language for OCR
            use_angle_cls: Whether to use angle classification
            use_gpu: Whether to use GPU (None for auto-detect)
        """
        if use_gpu is None:
            use_gpu = self._is_gpu_available()
        
        logger.info(f"Initializing PaddleOCR with lang={lang}, use_angle_cls={use_angle_cls}, use_gpu={use_gpu}")
        
        self.ocr = PaddleOCR(
            use_angle_cls=use_angle_cls,
            lang=lang,
            use_gpu=use_gpu,
            show_log=False
        )
        
        # Common license plate patterns (can be extended for specific countries)
        self.plate_patterns = [
            r'^[A-Z]{1,3}[0-9]{1,4}[A-Z]{0,3}$',  # General pattern
            r'^[0-9]{1,4}[A-Z]{1,3}$',             # Numbers first
            r'^[A-Z]{2}[0-9]{4}[A-Z]{0,2}$',       # EU style
            r'^[A-Z]{1,2}[0-9]{1,4}[A-Z]{0,2}$',   # US style
        ]
        
        logger.info("LicensePlateRecognizer initialized successfully")
    
    def _is_gpu_available(self) -> bool:
        """Check if GPU is available for PaddleOCR."""
        try:
            import paddle
            return paddle.is_compiled_with_cuda()
        except ImportError:
            return False
    
    def preprocess_plate_image(self, plate_img: np.ndarray) -> np.ndarray:
        """
        Preprocess license plate image for better OCR results.
        
        Args:
            plate_img: Input license plate image (BGR format)
            
        Returns:
            Preprocessed image
        """
        # Convert to grayscale
        gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
        
        # Apply adaptive histogram equalization
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(enhanced, (3, 3), 0)
        
        # Apply threshold to get binary image
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Morphological operations to clean up
        kernel = np.ones((2, 2), np.uint8)
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)
        
        return cleaned
    
    def extract_text_from_plate(self, plate_img: np.ndarray) -> List[Dict[str, Any]]:
        """
        Extract text from license plate image.
        
        Args:
            plate_img: Input license plate image (BGR format)
            
        Returns:
            List of OCR results with text and confidence
        """
        try:
            # Preprocess the image
            processed_img = self.preprocess_plate_image(plate_img)
            
            # Run OCR
            results = self.ocr.ocr(processed_img, cls=True)
            
            # Extract text and confidence
            ocr_results = []
            if results[0] is not None:
                for line in results[0]:
                    if line is not None:
                        text = line[1][0]  # Detected text
                        confidence = line[1][1]  # Confidence score
                        
                        # Clean text: keep only alphanumeric characters
                        cleaned_text = re.sub(r'[^A-Z0-9]', '', text.upper())
                        
                        # Check if it matches common license plate patterns
                        is_valid_plate = any(
                            re.match(pattern, cleaned_text) 
                            for pattern in self.plate_patterns
                        ) if cleaned_text else False
                        
                        ocr_results.append({
                            'text': cleaned_text,
                            'confidence': float(confidence),
                            'is_valid_plate': is_valid_plate,
                            'original_text': text
                        })
            
            return ocr_results
            
        except Exception as e:
            logger.error(f"Error during license plate OCR: {e}")
            return []
    
    def recognize_license_plate(self, 
                              vehicle_img: np.ndarray, 
                              bbox: List[int]) -> Dict[str, Any]:
        """
        Recognize license plate from vehicle image.
        
        Args:
            vehicle_img: Full vehicle image
            bbox: Vehicle bounding box [x1, y1, x2, y2]
            
        Returns:
            Dictionary with recognition results
        """
        x1, y1, x2, y2 = bbox
        
        # Extract vehicle region
        vehicle_roi = vehicle_img[y1:y2, x1:x2]
        
        if vehicle_roi.size == 0:
            return {
                'plate_text': None,
                'confidence': 0.0,
                'is_valid_plate': False,
                'plate_bbox': None
            }
        
        # Typical license plate is in the lower part of the vehicle
        # Try different regions: bottom, lower-middle
        h, w = vehicle_roi.shape[:2]
        
        # Define regions to check for license plate (from bottom up)
        regions_to_check = [
            # Bottom 20%
            (int(h * 0.8), h, 0, w),
            # Bottom 40%
            (int(h * 0.6), h, 0, w),
            # Middle-bottom 30%
            (int(h * 0.5), int(h * 0.8), 0, w),
            # Full region as fallback
            (0, h, 0, w)
        ]
        
        best_result = {
            'plate_text': None,
            'confidence': 0.0,
            'is_valid_plate': False,
            'plate_bbox': None
        }
        
        for y_start, y_end, x_start, x_end in regions_to_check:
            # Extract region
            region = vehicle_roi[y_start:y_end, x_start:x_end]
            
            if region.size == 0:
                continue
            
            # Run OCR on region
            ocr_results = self.extract_text_from_plate(region)
            
            # Find best result
            for result in ocr_results:
                if result['is_valid_plate'] and result['confidence'] > best_result['confidence']:
                    # Convert region coordinates to full image coordinates
                    plate_bbox = [
                        x1 + x_start,
                        y1 + y_start,
                        x1 + x_end,
                        y1 + y_end
                    ]
                    
                    best_result = {
                        'plate_text': result['text'],
                        'confidence': result['confidence'],
                        'is_valid_plate': result['is_valid_plate'],
                        'plate_bbox': plate_bbox
                    }
                    break
            
            # If we found a good result, break
            if best_result['plate_text'] is not None and best_result['confidence'] > 0.5:
                break
        
        return best_result
    
    def draw_plate_result(self, 
                         frame: np.ndarray, 
                         vehicle_bbox: List[int], 
                         plate_result: Dict[str, Any]) -> np.ndarray:
        """
        Draw license plate recognition result on frame.
        
        Args:
            frame: Input frame
            vehicle_bbox: Vehicle bounding box [x1, y1, x2, y2]
            plate_result: Result from recognize_license_plate
            
        Returns:
            Frame with plate recognition drawn
        """
        annotated_frame = frame.copy()
        x1, y1, x2, y2 = vehicle_bbox
        
        # Draw vehicle bounding box
        cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
        
        # Draw license plate info if available
        if plate_result['plate_text'] is not None:
            # Draw plate bounding box if available
            if plate_result['plate_bbox'] is not None:
                px1, py1, px2, py2 = plate_result['plate_bbox']
                cv2.rectangle(annotated_frame, (px1, py1), (px2, py2), (0, 255, 255), 2)
            
            # Draw plate text
            text = f"Plate: {plate_result['plate_text']} ({plate_result['confidence']:.2f})"
            text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            
            # Position text above vehicle
            text_x = x1
            text_y = max(y1 - 10, text_size[1] + 10)
            
            # Draw background rectangle
            cv2.rectangle(annotated_frame, 
                         (text_x, text_y - text_size[1] - 10),
                         (text_x + text_size[0], text_y + 10),
                         (0, 0, 0), -1)
            
            # Draw text
            cv2.putText(annotated_frame, text, (text_x, text_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        return annotated_frame

# Global license plate recognizer instance
license_plate_recognizer = LicensePlateRecognizer()