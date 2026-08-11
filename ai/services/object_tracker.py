import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import logging
from collections import defaultdict, deque
import time

logger = logging.getLogger(__name__)

class Track:
    def __init__(self, track_id: int, bbox: List[float], class_name: str, confidence: float):
        self.track_id = track_id
        self.bbox = bbox  # [x1, y1, x2, y2]
        self.class_name = class_name
        self.confidence = confidence
        self.history = deque(maxlen=30)  # Store last 30 positions
        self.history.append(self.get_center())
        self.time_since_update = 0
        self.hits = 1
        self.hit_streak = 1
        self.age = 0
        self.state = 'tentative'  # tentative, confirmed, deleted
        
    def get_center(self) -> Tuple[float, float]:
        """Get the center point of the bounding box."""
        x1, y1, x2, y2 = self.bbox
        return ((x1 + x2) / 2, (y1 + y2) / 2)
    
    def get_width_height(self) -> Tuple[float, float]:
        """Get width and height of the bounding box."""
        x1, y1, x2, y2 = self.bbox
        return (x2 - x1, y2 - y1)
    
    def predict(self):
        """Predict the next state using constant velocity model."""
        # Simple constant velocity prediction
        if len(self.history) >= 2:
            # Calculate velocity from last two positions
            dx = self.history[-1][0] - self.history[-2][0]
            dy = self.history[-1][1] - self.history[-2][1]
            predicted_center = (
                self.history[-1][0] + dx,
                self.history[-1][1] + dy
            )
            
            # Convert center to bounding box
            w, h = self.get_width_height()
            predicted_bbox = [
                predicted_center[0] - w/2,
                predicted_center[1] - h/2,
                predicted_center[0] + w/2,
                predicted_center[1] + h/2
            ]
            self.bbox = predicted_bbox
        
        self.time_since_update += 1
        self.age += 1
        
        if self.state == 'tentative' and self.hits >= 3:
            self.state = 'confirmed'
        elif self.state == 'confirmed' and self.time_since_update > 1:
            self.state = 'deleted'
    
    def update(self, detection: Dict[str, Any]):
        """Update track with new detection."""
        self.time_since_update = 0
        self.hits += 1
        self.hit_streak += 1
        
        # Update bounding box and confidence
        self.bbox = detection['bbox']
        self.confidence = detection['confidence']
        self.class_name = detection['class_name']
        
        # Update history
        self.history.append(self.get_center())
        
        # Update state
        if self.state == 'tentative' and self.hits >= 3:
            self.state = 'confirmed'

class ByteTrack:
    def __init__(self, 
                 track_thresh: float = 0.5, 
                 track_buffer: int = 30,
                 match_thresh: float = 0.8,
                 frame_rate: int = 30):
        """
        Initialize ByteTrack tracker.
        
        Args:
            track_thresh: Detection confidence threshold for tracking
            track_buffer: Number of frames to keep lost tracks
            match_thresh: Matching threshold for data association
            frame_rate: Video frame rate
        """
        self.track_thresh = track_thresh
        self.track_buffer = track_buffer
        self.match_thresh = match_thresh
        self.frame_rate = frame_rate
        
        self.tracked_tracks: List[Track] = []  # List of confirmed tracks
        self.lost_tracks: List[Track] = []     # List of lost tracks
        self.removed_tracks: List[Track] = []  # List of removed tracks
        
        self.frame_id = 0
        self.max_time_lost = int(self.frame_rate * self.track_buffer / 60.0)
        self.next_id = 1
        
        logger.info(f"ByteTrack initialized with track_thresh={track_thresh}, "
                   f"track_buffer={track_buffer}, match_thresh={match_thresh}")
    
    def update(self, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Update tracks with new detections.
        
        Args:
            detections: List of detections from detector
            
        Returns:
            List of tracked objects with track_id added
        """
        self.frame_id += 1
        
        # Separate detections into high and low confidence
        high_conf_dets = [det for det in detections if det['confidence'] >= self.track_thresh]
        low_conf_dets = [det for det in detections if det['confidence'] < self.track_thresh]
        
        # Step 1: Predict current state of existing tracks
        for track in self.tracked_tracks:
            track.predict()
        for track in self.lost_tracks:
            track.predict()
        
        # Step 2: Associate high confidence detections with tracked tracks
        matched, unmatched_dets, unmatched_trks = self._associate_detections_to_tracks(
            high_conf_dets, self.tracked_tracks, self.match_thresh
        )
        
        # Update matched tracks
        for t, trk in matched:
            self.tracked_tracks[t].update(high_conf_dets[trk])
        
        # Step 3: Associate remaining detections with lost tracks
        remaining_unmatched_dets = [high_conf_dets[i] for i in unmatched_dets if i < len(high_conf_dets)]
        matched_lost, unmatched_dets_lost, unmatched_lost_trks = self._associate_detections_to_tracks(
            remaining_unmatched_dets, self.lost_tracks, self.match_thresh * 0.5
        )
        
        # Update matched lost tracks
        for t, trk in matched_lost:
            track = self.lost_tracks[trk]
            self.lost_tracks.remove(track)
            track.update(remaining_unmatched_dets[t])
            self.tracked_tracks.append(track)
        
        # Step 4: Initialize new tracks with unmatched high confidence detections
        for i in unmatched_dets:
            if i < len(high_conf_dets):
                track = Track(
                    track_id=self.next_id,
                    bbox=high_conf_dets[i]['bbox'],
                    class_name=high_conf_dets[i]['class_name'],
                    confidence=high_conf_dets[i]['confidence']
                )
                self.tracked_tracks.append(track)
                self.next_id += 1
        
        # Step 5: Handle low confidence detections
        # Associate with confirmed tracks only
        confirmed_tracks = [t for t in self.tracked_tracks if t.state == 'confirmed']
        if len(confirmed_tracks) > 0 and len(low_conf_dets) > 0:
            matched, unmatched_dets, unmatched_trks = self._associate_detections_to_tracks(
                low_conf_dets, confirmed_tracks, self.match_thresh * 0.5
            )
            
            # Update matched tracks
            for t, trk in matched:
                confirmed_tracks[t].update(low_conf_dets[trk])
        
        # Step 6: Remove lost tracks
        self.tracked_tracks = [t for t in self.tracked_tracks if t.state != 'deleted']
        self.lost_tracks = [t for t in self.lost_tracks if t.time_since_update < self.max_time_lost]
        
        # Move old tracked tracks to lost tracks
        for track in self.tracked_tracks[:]:
            if track.time_since_update >= 1:
                self.tracked_tracks.remove(track)
                self.lost_tracks.append(track)
        
        # Prepare output
        output_tracks = []
        for track in self.tracked_tracks:
            if track.state == 'confirmed':
                output_tracks.append({
                    'track_id': track.track_id,
                    'bbox': track.bbox,
                    'class_name': track.class_name,
                    'confidence': track.confidence,
                    'detection_confidence': track.confidence  # Original detection confidence
                })
        
        return output_tracks
    
    def _associate_detections_to_tracks(self, detections: List[Dict[str, Any]], 
                                      tracks: List[Track], 
                                      thresh: float) -> Tuple[List[Tuple[int, int]], 
                                                              List[int], 
                                                              List[int]]:
        """
        Associate detections to tracks using IoU.
        
        Returns:
            (matches, unmatched_detections, unmatched_tracks)
        """
        if len(tracks) == 0:
            return [], list(range(len(detections))), list(range(len(tracks)))
        
        if len(detections) == 0:
            return [], [], list(range(len(tracks)))
        
        # Compute IoU matrix
        iou_matrix = np.zeros((len(detections), len(tracks)), dtype=np.float32)
        
        for d, det in enumerate(detections):
            for t, trk in enumerate(tracks):
                iou_matrix[d, t] = self._calculate_iou(det['bbox'], trk.bbox)
        
        # Hungarian algorithm or greedy matching
        # For simplicity, we'll use greedy matching
        matched_indices = []
        
        if iou_matrix.size > 0:
            # Find matches above threshold
            if iou_matrix.shape[0] <= iou_matrix.shape[1]:
                # More tracks than detections
                for d in range(len(detections)):
                    t_max = np.argmax(iou_matrix[d])
                    if iou_matrix[d, t_max] >= thresh:
                        matched_indices.append((d, t_max))
                        # Mark as used
                        iou_matrix[:, t_max] = -1
                        iou_matrix[d, :] = -1
            else:
                # More detections than tracks
                for t in range(len(tracks)):
                    d_max = np.argmax(iou_matrix[:, t])
                    if iou_matrix[d_max, t] >= thresh:
                        matched_indices.append((d_max, t))
                        # Mark as used
                        iou_matrix[d_max, :] = -1
                        iou_matrix[:, t] = -1
        
        # Find unmatched detections and tracks
        matched_dets = set([m[0] for m in matched_indices])
        matched_trks = set([m[1] for m in matched_indices])
        
        unmatched_dets = [d for d in range(len(detections)) if d not in matched_dets]
        unmatched_trks = [t for t in range(len(tracks)) if t not in matched_trks]
        
        return matched_indices, unmatched_dets, unmatched_trks
    
    def _calculate_iou(self, bbox1: List[float], bbox2: List[float]) -> float:
        """
        Calculate Intersection over Union (IoU) of two bounding boxes.
        
        Args:
            bbox1: [x1, y1, x2, y2]
            bbox2: [x1, y1, x2, y2]
            
        Returns:
            IoU value between 0 and 1
        """
        # Calculate intersection
        x1 = max(bbox1[0], bbox2[0])
        y1 = max(bbox1[1], bbox2[1])
        x2 = min(bbox1[2], bbox2[2])
        y2 = min(bbox1[3], bbox2[3])
        
        if x2 < x1 or y2 < y1:
            return 0.0
        
        intersection = (x2 - x1) * (y2 - y1)
        
        # Calculate union
        bbox1_area = (bbox1[2] - bbox1[0]) * (bbox1[3] - bbox1[1])
        bbox2_area = (bbox2[2] - bbox2[0]) * (bbox2[3] - bbox2[1])
        union = bbox1_area + bbox2_area - intersection
        
        if union == 0:
            return 0.0
        
        return intersection / union

# Global tracker instance (confidence threshold taken from runtime settings)
from app.config import settings

object_tracker = ByteTrack(track_thresh=settings.CONFIDENCE_THRESHOLD)