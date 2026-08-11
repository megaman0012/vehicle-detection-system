import logging
import queue
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import cv2

from app.backend_client import backend_client
from app.config import settings
from .vehicle_detector import vehicle_detector
from .object_tracker import object_tracker
from .parking_detector import parking_detector
from .license_plate_recognizer import license_plate_recognizer

logger = logging.getLogger(__name__)

VEHICLE_TYPE_MAP = {
    "car": "car",
    "motorcycle": "motorcycle",
    "bus": "bus",
    "truck": "truck",
}


class AIService:
    """Orchestrates per-camera processing threads.

    Reports detections and events to the backend through the REST API instead
    of touching the database directly, keeping this service decoupled.
    """

    def __init__(self):
        self.is_running = False
        self.processing_threads: Dict[str, threading.Thread] = {}
        self.stop_events: Dict[str, threading.Event] = {}
        self.frame_queues: Dict[str, queue.Queue] = {}
        self.result_queues: Dict[str, queue.Queue] = {}
        self.camera_info: Dict[str, Dict[str, Any]] = {}

        self.confidence_threshold = settings.CONFIDENCE_THRESHOLD
        self.frame_skip = settings.FRAME_SKIP
        self.parking_time_threshold = settings.PARKING_TIME_THRESHOLD
        self.report_interval = settings.REPORT_INTERVAL

        self._last_report: Dict[str, float] = {}
        self._reported_track_states: Dict[str, Dict[str, bool]] = {}

        logger.info("AIService initialized")

    def start_camera_processing(
        self,
        camera_id: str,
        rtsp_url: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """Start processing an RTSP camera stream in a background thread."""
        if camera_id in self.processing_threads:
            logger.warning("Camera %s is already being processed", camera_id)
            return

        logger.info("Starting processing for camera %s: %s", camera_id, rtsp_url)
        self.frame_queues[camera_id] = queue.Queue(maxsize=10)
        self.result_queues[camera_id] = queue.Queue()
        self.stop_events[camera_id] = threading.Event()
        self.camera_info[camera_id] = {
            "rtsp_url": rtsp_url,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "frames_processed": 0,
            "detections": 0,
            "status": "starting",
        }

        thread = threading.Thread(
            target=self._process_camera_stream,
            args=(camera_id, rtsp_url, username, password),
            daemon=True,
        )
        self.processing_threads[camera_id] = thread
        thread.start()
        logger.info("Started processing thread for camera %s", camera_id)

    def stop_camera_processing(self, camera_id: str):
        """Stop processing a camera stream."""
        if camera_id not in self.processing_threads:
            logger.warning("Camera %s is not being processed", camera_id)
            return

        logger.info("Stopping processing for camera %s", camera_id)
        stop_event = self.stop_events.get(camera_id)
        if stop_event is not None:
            stop_event.set()
        if camera_id in self.frame_queues:
            try:
                self.frame_queues[camera_id].put_nowait(None)
            except queue.Full:
                pass

        if camera_id in self.processing_threads:
            self.processing_threads[camera_id].join(timeout=5.0)
            del self.processing_threads[camera_id]

        if camera_id in self.stop_events:
            del self.stop_events[camera_id]

        for attr in ("frame_queues", "result_queues", "camera_info", "_last_report", "_reported_track_states"):
            store = getattr(self, attr)
            if camera_id in store:
                del store[camera_id]

        logger.info("Stopped processing for camera %s", camera_id)

    def _process_camera_stream(
        self,
        camera_id: str,
        rtsp_url: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        logger.info("Processing thread started for camera %s", camera_id)

        if username and password and rtsp_url.startswith("rtsp://"):
            rtsp_url = f"rtsp://{username}:{password}@{rtsp_url[7:]}"

        cap = cv2.VideoCapture(rtsp_url)
        if not cap.isOpened():
            logger.error("Failed to open RTSP stream for camera %s", camera_id)
            if camera_id in self.camera_info:
                self.camera_info[camera_id]["status"] = "error: stream not opened"
            return

        logger.info("Successfully opened RTSP stream for camera %s", camera_id)
        if camera_id in self.camera_info:
            self.camera_info[camera_id]["status"] = "running"

        stop_event = self.stop_events.get(camera_id)
        frame_count = 0
        try:
            while stop_event is not None and not stop_event.is_set():
                if camera_id not in self.frame_queues:
                    break
                try:
                    if self.frame_queues[camera_id].get_nowait() is None:
                        break
                except queue.Empty:
                    pass

                ret, frame = cap.read()
                if not ret:
                    logger.warning("Failed to read frame from camera %s", camera_id)
                    time.sleep(0.1)
                    continue

                frame_count += 1
                info = self.camera_info.get(camera_id)
                if info is not None:
                    info["frames_processed"] = frame_count

                if frame_count % (self.frame_skip + 1) != 0:
                    if not self.frame_queues[camera_id].full():
                        self.frame_queues[camera_id].put(
                            {"frame": frame, "detections": [], "timestamp": time.time()}
                        )
                    continue

                detections = self._process_frame_for_vehicles(frame, camera_id)

                if not self.result_queues[camera_id].full():
                    self.result_queues[camera_id].put(
                        {"frame": frame, "detections": detections, "timestamp": time.time()}
                    )
                if not self.frame_queues[camera_id].full():
                    self.frame_queues[camera_id].put(
                        {"frame": frame, "detections": detections, "timestamp": time.time()}
                    )
        except Exception as exc:
            logger.error("Error in processing thread for camera %s: %s", camera_id, exc)
        finally:
            cap.release()
            if camera_id in self.camera_info:
                self.camera_info[camera_id]["status"] = "stopped"
            logger.info("Processing thread ended for camera %s", camera_id)

    def _process_frame_for_vehicles(
        self, frame: Any, camera_id: str
    ) -> List[Dict[str, Any]]:
        try:
            raw_detections = vehicle_detector.detect_vehicles(frame)
            if not raw_detections:
                return []

            tracked_objects = object_tracker.update(raw_detections)
            processed: List[Dict[str, Any]] = []
            now = time.time()

            for obj in tracked_objects:
                track_id = obj["track_id"]
                bbox = obj["bbox"]

                parking_info = parking_detector.update_vehicle_state(track_id, bbox, now)

                plate_result = None
                if parking_info["is_parked"] or parking_info["total_movement"] < 50:
                    plate_result = license_plate_recognizer.recognize_license_plate(frame, bbox)

                result = {
                    "track_id": track_id,
                    "bbox": bbox,
                    "vehicle_type": VEHICLE_TYPE_MAP.get(obj["class_name"], "unknown"),
                    "confidence": obj["confidence"],
                    "is_parked": parking_info["is_parked"],
                    "parked_since": parking_info["parked_since"],
                    "license_plate": plate_result["plate_text"] if plate_result else None,
                    "plate_confidence": plate_result["confidence"] if plate_result else None,
                    "plate_bbox": plate_result["plate_bbox"] if plate_result else None,
                    "detection_time": now,
                }
                processed.append(result)
                self._report_if_due(camera_id, result)

            info = self.camera_info.get(camera_id)
            if info is not None:
                info["detections"] = info.get("detections", 0) + len(processed)
            return processed
        except Exception as exc:
            logger.error("Error processing frame for camera %s: %s", camera_id, exc)
            return []

    def _report_if_due(self, camera_id: str, detection: Dict[str, Any]):
        """Report a detection/event to the backend, rate-limited and de-duplicated."""
        track_id = detection["track_id"]
        key = f"{camera_id}:{track_id}"

        states = self._reported_track_states.setdefault(camera_id, {})
        last_reported_state = states.get(track_id, {})

        now = detection["detection_time"]
        last_ts = self._last_report.get(key, 0.0)

        parked_now = detection["is_parked"]
        was_parked = last_reported_state.get("is_parked", False)
        plate = detection["license_plate"]
        reported_plate = last_reported_state.get("plate")

        should_report = False
        if parked_now and not was_parked:
            should_report = True
        if not parked_now and was_parked:
            should_report = True
        if plate and plate != reported_plate:
            should_report = True
        if now - last_ts >= self.report_interval and not was_parked:
            should_report = True

        if not should_report:
            states[track_id] = {
                "is_parked": parked_now,
                "plate": plate,
                "last_report": now,
            }
            return

        vehicle_payload = {
            "camera_id": camera_id,
            "vehicle_id": f"T-{track_id}",
            "vehicle_type": detection["vehicle_type"],
            "confidence": detection["confidence"],
            "is_parked": parked_now,
            "bbox": detection["bbox"],
            "license_plate": plate,
        }
        ok = backend_client.post_vehicle(vehicle_payload)

        if parked_now and not was_parked:
            backend_client.post_event(
                {
                    "camera_id": camera_id,
                    "event_type": "vehicle_parked",
                    "description": f"Vehículo {detection['vehicle_type']} estacionado (track {track_id})",
                    "license_plate": plate,
                    "meta": {"track_id": track_id, "bbox": detection["bbox"]},
                }
            )
        elif not parked_now and was_parked:
            backend_client.post_event(
                {
                    "camera_id": camera_id,
                    "event_type": "vehicle_left",
                    "description": f"Vehículo {detection['vehicle_type']} abandonó el lugar (track {track_id})",
                    "license_plate": plate,
                    "meta": {"track_id": track_id, "bbox": detection["bbox"]},
                }
            )

        if ok:
            states[track_id] = {
                "is_parked": parked_now,
                "plate": plate,
                "last_report": now,
            }
            self._last_report[key] = now

    def get_latest_results(self, camera_id: str) -> Optional[Dict[str, Any]]:
        if camera_id not in self.result_queues:
            return None
        try:
            results = []
            while not self.result_queues[camera_id].empty():
                results.append(self.result_queues[camera_id].get_nowait())
            latest = results[-1] if results else None
            if latest:
                latest = dict(latest)
                latest.pop("frame", None)
            return latest
        except Exception:
            return None

    def get_frame_for_display(self, camera_id: str) -> Optional[Dict[str, Any]]:
        if camera_id not in self.frame_queues:
            return None
        try:
            frames = []
            while not self.frame_queues[camera_id].empty():
                frames.append(self.frame_queues[camera_id].get_nowait())
            return frames[-1] if frames else None
        except Exception:
            return None

    def get_status(self) -> Dict[str, Any]:
        active = []
        for camera_id, thread in self.processing_threads.items():
            active.append(
                {
                    "camera_id": camera_id,
                    "thread_alive": thread.is_alive(),
                    "info": self.camera_info.get(camera_id),
                }
            )
        return {
            "is_running": self.is_running,
            "active_cameras": active,
            "detector": vehicle_detector.status,
            "ocr_available": license_plate_recognizer.ocr is not None,
            "parking_time_threshold": self.parking_time_threshold,
            "report_interval": self.report_interval,
        }

    def shutdown(self):
        logger.info("Shutting down AI service...")
        self.is_running = False
        for camera_id in list(self.processing_threads.keys()):
            self.stop_camera_processing(camera_id)
        logger.info("AI service shutdown complete")


ai_service = AIService()
