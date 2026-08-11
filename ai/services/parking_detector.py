import numpy as np
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
import json

logger = logging.getLogger(__name__)

class ParkingDetector:
    def __init__(self, 
                 parking_time_threshold: int = 300,  # 5 minutes in seconds
                 movement_threshold: float = 10.0):   # pixels
        """
        Initialize the parking detector.
        
        Args:
            parking_time_threshold: Time in seconds to consider a vehicle as parked
            movement_threshold: Maximum movement in pixels to consider vehicle stationary
        """
        self.parking_time_threshold = parking_time_threshold
        self.movement_threshold = movement_threshold
        
        # Store vehicle state: {track_id: {first_seen, last_movement, positions, is_parked}}
        self.vehicle_states = defaultdict(dict)
        
        logger.info(f"ParkingDetector initialized with threshold={parking_time_threshold}s, "
                   f"movement_threshold={movement_threshold}px")
    
    def update_vehicle_state(self, 
                           track_id: int, 
                           bbox: List[float], 
                           timestamp: float = None) -> Dict[str, Any]:
        """
        Update the state of a vehicle and determine if it's parked.
        
        Args:
            track_id: Unique identifier for the vehicle
            bbox: Bounding box [x1, y1, x2, y2]
            timestamp: Current timestamp (defaults to time.time())
            
        Returns:
            Dictionary with vehicle state information
        """
        if timestamp is None:
            timestamp = time.time()
        
        # Get center point of bounding box
        x1, y1, x2, y2 = bbox
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        current_position = (center_x, center_y)
        
        # Initialize vehicle state if not exists
        if track_id not in self.vehicle_states:
            self.vehicle_states[track_id] = {
                'first_seen': timestamp,
                'last_movement': timestamp,
                'positions': [],
                'is_parked': False,
                'parked_since': None,
                'total_movement': 0.0
            }
        
        state = self.vehicle_states[track_id]
        
        # Add current position to history
        state['positions'].append(current_position)
        
        # Keep only last 30 positions
        if len(state['positions']) > 30:
            state['positions'] = state['positions'][-30:]
        
        # Calculate movement from last position
        if len(state['positions']) >= 2:
            last_pos = state['positions'][-2]
            movement = np.sqrt(
                (current_position[0] - last_pos[0])**2 + 
                (current_position[1] - last_pos[1])**2
            )
            state['total_movement'] += movement
            
            # If movement exceeds threshold, reset last movement time
            if movement > self.movement_threshold:
                state['last_movement'] = timestamp
        
        # Check if vehicle should be considered parked
        time_since_first_seen = timestamp - state['first_seen']
        time_since_last_movement = timestamp - state['last_movement']
        
        # Vehicle is parked if:
        # 1. It has been seen for at least the minimum time
        # 2. It hasn't moved significantly for the parking threshold time
        if time_since_first_seen >= self.parking_time_threshold:
            if time_since_last_movement >= self.parking_time_threshold:
                if not state['is_parked']:
                    state['is_parked'] = True
                    state['parked_since'] = timestamp
                    logger.info(f"Vehicle {track_id} is now parked")
            else:
                # Vehicle moved recently, not parked
                if state['is_parked']:
                    state['is_parked'] = False
                    state['parked_since'] = None
                    logger.info(f"Vehicle {track_id} is no longer parked")
        else:
            # Not enough time has passed to consider parking
            if state['is_parked']:
                state['is_parked'] = False
                state['parked_since'] = None
        
        return {
            'track_id': track_id,
            'is_parked': state['is_parked'],
            'parked_since': state['parked_since'],
            'time_since_first_seen': time_since_first_seen,
            'time_since_last_movement': time_since_last_movement,
            'total_movement': state['total_movement'],
            'positions': state['positions'][-10:]  # Last 10 positions
        }
    
    def is_vehicle_parked(self, track_id: int) -> bool:
        """Check if a vehicle is currently parked."""
        return self.vehicle_states.get(track_id, {}).get('is_parked', False)
    
    def get_parked_since(self, track_id: int) -> Optional[float]:
        """Get the timestamp when the vehicle started parking."""
        return self.vehicle_states.get(track_id, {}).get('parked_since')
    
    def get_vehicle_info(self, track_id: int) -> Dict[str, Any]:
        """Get complete information about a vehicle."""
        return self.vehicle_states.get(track_id, {})
    
    def reset_vehicle_state(self, track_id: int):
        """Reset the state of a vehicle (when it leaves the scene)."""
        if track_id in self.vehicle_states:
            del self.vehicle_states[track_id]
            logger.debug(f"Reset state for vehicle {track_id}")

# Global parking detector instance (threshold taken from runtime settings)
from app.config import settings

parking_detector = ParkingDetector(
    parking_time_threshold=settings.PARKING_TIME_THRESHOLD
)