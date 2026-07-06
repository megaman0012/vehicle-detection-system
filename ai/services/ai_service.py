import cv2
import numpy as np
import time
import threading
import logging
from typing import List, Dict, Any, Optional
import queue
import json
from datetime import datetime

from backend.database import SessionLocal
from backend.models.detected_vehicle import DetectedVehicle, VehicleType
from backend.models.event import Event, EventType
from backend.models.camera import Camera
from backend.models.zone import Zone
from backend.utils.security import get_password_hash

from .vehicle_detector import vehicle_detector
from .object_tracker import object_tracker
from .parking_detector import parking_detector
from .license_plate_recognizer import license_plate_recognizer

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        """Initialize the AI service."""
        self.is_running = False
        self.processing_threads = {}
        self.frame_queues = {}
        self.result_queues = {}
        
        # Configuration
        self.confidence_threshold = 0.5
        self.frame_skip = 2  # Process every Nth frame to reduce CPU usage
        
        logger.info("AIService initialized")
    
    def start_camera_processing(self, camera_id: int, rtsp_url: str, 
                              username: str = None, password: str = None):
        """
        Start processing a camera stream.
        
        Args:
            camera_id: Database ID of the camera
            rtsp_url: RTSP URL of the camera
            username: Username for camera authentication
            password: Password for camera authentication
        """
        if camera_id in self.processing_threads:
            logger.warning(f"Camera {camera_id} is already being processed")
            return
        
        logger.info(f"Starting processing for camera {camera_id}: {rtsp_url}")
        
        # Create queues for this camera
        frame_queue = queue.Queue(maxsize=10)
        result_queue = queue.Queue()
        
        self.frame_queues[camera_id] = frame_queue
        self.result_queues[camera_id] = result_queue
        
        # Start processing thread
        thread = threading.Thread(
            target=self._process_camera_stream,
            args=(camera_id, rtsp_url, username, password),
            daemon=True
        )
        self.processing_threads[camera_id] = thread
        thread.start()
        
        logger.info(f"Started processing thread for camera {camera_id}")
    
    def stop_camera_processing(self, camera_id: int):
        """
        Stop processing a camera stream.
        
        Args:
            camera_id: Database ID of the camera
        """
        if camera_id not in self.processing_threads:
            logger.warning(f"Camera {camera_id} is not being processed")
            return
        
        logger.info(f"Stopping processing for camera {camera_id}")
        
        # Signal thread to stop
        if camera_id in self.frame_queues:
            self.frame_queues[camera_id].put(None)  # Sentinel value
        
        # Wait for thread to finish
        if camera_id in self.processing_threads:
            self.processing_threads[camera_id].join(timeout=5.0)
            del self.processing_threads[camera_id]
        
        # Clean up queues
        if camera_id in self.frame_queues:
            del self.frame_queues[camera_id]
        if camera_id in self.result_queues:
            del self.result_queues[camera_id]
        
        logger.info(f"Stopped processing for camera {camera_id}")
    
    def _process_camera_stream(self, camera_id: int, rtsp_url: str, 
                             username: str = None, password: str = None):
        """
        Process a camera stream in a separate thread.
        
        Args:
            camera_id: Database ID of the camera
            rtsp_url: RTSP URL of the camera
            username: Username for camera authentication
            password: Password for camera authentication
        """
        logger.info(f"Processing thread started for camera {camera_id}")
        
        # Construct RTSP URL with credentials if provided
        if username and password:
            # Insert credentials into RTSP URL
            if rtsp_url.startswith("rtsp://"):
                rtsp_url = f"rtsp://{username}:{password}@{rtsp_url[7:]}"
        
        # Open video capture
        cap = cv2.VideoCapture(rtsp_url)
        
        if not cap.isOpened():
            logger.error(f"Failed to open RTSP stream for camera {camera_id}: {rtsp_url}")
            return
        
        logger.info(f"Successfully opened RTSP stream for camera {camera_id}")
        
        frame_count = 0
        skip_frames = self.frame_skip
        
        try:
            while self.is_running or (camera_id in self.processing_threads):
                ret, frame = cap.read()
                
                if not ret:
                    logger.warning(f"Failed to read frame from camera {camera_id}")
                    time.sleep(0.1)  # Wait before retrying
                    continue
                
                frame_count += 1
                
                # Skip frames to reduce processing load
                if frame_count % (skip_frames + 1) != 0:
                    # Still put frame in queue for display purposes
                    if not self.frame_queues[camera_id].full():
                        self.frame_queues[camera_id].put({
                            'frame': frame,
                            'detections': [],
                            'timestamp': time.time()
                        })
                    continue
                
                # Process frame for vehicle detection
                detections = self._process_frame_for_vehicles(frame, camera_id)
                
                # Put result in queue
                if not self.result_queues[camera_id].full():
                    self.result_queues[camera_id].put({
                        'frame': frame,
                        'detections': detections,
                        'timestamp': time.time()
                    })
                
                # Also put in frame queue for display (non-blocking)
                if not self.frame_queues[camera_id].full():
                    self.frame_queues[camera_id].put({
                        'frame': frame,
                        'detections': detections,
                        'timestamp': time.time()
                    })
                
        except Exception as e:
            logger.error(f"Error in processing thread for camera {camera_id}: {e}")
        finally:
            cap.release()
            logger.info(f"Processing thread ended for camera {camera_id}")
    
    def _process_frame_for_vehicles(self, frame: np.ndarray, camera_id: int) -> List[Dict[str, Any]]:
        """
        Process a single frame for vehicle detection and tracking.
        
        Args:
            frame: Input frame
            camera_id: Database ID of the camera
            
        Returns:
            List of processed detections with tracking information
        """
        try:
            # Step 1: Detect vehicles using YOLOv8
            raw_detections = vehicle_detector.detect_vehicles(frame)
            
            if not raw_detections:
                return []
            
            # Step 2: Track objects using ByteTrack
            tracked_objects = object_tracker.update(raw_detections)
            
            # Step 3: Update parking status for each tracked object
            processed_detections = []
            db = SessionLocal()
            
            try:
                for obj in tracked_objects:
                    track_id = obj['track_id']
                    bbox = obj['bbox']
                    
                    # Update parking status
                    parking_info = parking_detector.update_vehicle_state(
                        track_id, bbox, time.time()
                    )
                    
                    # Recognize license plate if vehicle is parked or moving slowly
                    plate_result = None
                    if parking_info['is_parked'] or parking_info['total_movement'] < 50:  # Low movement
                        plate_result = license_plate_recognizer.recognize_license_plate(frame, bbox)
                    
                    # Get vehicle type from class name
                    vehicle_type_map = {
                        'car': VehicleType.CAR,
                        'motorcycle': VehicleType.MOTORCYCLE,
                        'bus': VehicleType.BUS,
                        'truck': VehicleType.TRUCK
                    }
                    vehicle_type = vehicle_type_map.get(
                        obj['class_name'], 
                        VehicleType.UNKNOWN
                    )
                    
                    # Prepare detection result
                    detection_result = {
                        'track_id': track_id,
                        'bbox': bbox,
                        'vehicle_type': vehicle_type,
                        'confidence': obj['confidence'],
                        'is_parked': parking_info['is_parked'],
                        'parked_since': parking_info['parked_since'],
                        'license_plate': plate_result['plate_text'] if plate_result else None,
                        'plate_confidence': plate_result['confidence'] if plate_result else None,
                        'plate_bbox': plate_result['plate_bbox'] if plate_result else None,
                        'detection_time': time.time()
                    }
                    
                    processed_detections.append(detection_result)
                    
                    # Save to database (simplified - in production this would be batched)
                    self._save_detection_to_db(db, camera_id, detection_result)
                
                db.commit()
            except Exception as e:
                logger.error(f"Error saving detections to database: {e}")
                db.rollback()
            finally:
                db.close()
            
            return processed_detections
            
        except Exception as e:
            logger.error(f"Error processing frame for camera {camera_id}: {e}")
            return []
    
    def _save_detection_to_db(self, db: SessionLocal, camera_id: int, detection: Dict[str, Any]):
        """
        Save detection results to database.
        
        Args:
            db: Database session
            camera_id: Camera ID
            detection: Detection results
        """
        # This is a simplified version - in production you'd want to:
        # 1. Check if vehicle already exists (by track_id + camera_id + recent time)
        # 2. Update existing record or create new one
        # 3. Create events for parking/unparking
        
        # For now, we'll just log what we would save
        logger.debug(f"Would save detection for camera {camera_id}: "
                    f"track_id={detection['track_id']}, "
                    f"type={detection['vehicle_type']}, "
                    f"parked={detection['is_parked']}, "
                    f"plate={detection['license_plate']}")
    
    def get_latest_results(self, camera_id: int) -> Optional[Dict[str, Any]]:
        """
        Get the latest processing results for a camera.
        
        Args:
            camera_id: Database ID of the camera
            
        Returns:
            Latest results or None if not available
        """
        if camera_id not in self.result_queues:
            return None
        
        try:
            # Get latest result without blocking
            results = []
            while not self.result_queues[camera_id].empty():
                results.append(self.result_queues[camera_id].get_nowait())
            
            return results[-1] if results else None
        except:
            return None
    
    def get_frame_for_display(self, camera_id: int) -> Optional[Dict[str, Any]]:
        """
        Get the latest frame for display purposes.
        
        Args:
            camera_id: Database ID of the camera
            
        Returns:
            Latest frame with detections or None if not available
        """
        if camera_id not in self.frame_queues:
            return None
        
        try:
            # Get latest frame without blocking
            frames = []
            while not self.frame_queues[camera_id].empty():
                frames.append(self.frame_queues[camera_id].get_nowait())
            
            return frames[-1] if frames else None
        except:
            return None
    
    def shutdown(self):
        """Shutdown the AI service and all processing threads."""
        logger.info("Shutting down AI service...")
        self.is_running = False
        
        # Stop all camera processing threads
        camera_ids = list(self.processing_threads.keys())
        for camera_id in camera_ids:
            self.stop_camera_processing(camera_id)
        
        logger.info("AI service shutdown complete")

# Global AI service instance
ai_service = AIService()