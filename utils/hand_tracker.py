import cv2
import mediapipe as mp
import math
import time
import traceback

class HandTracker:
    def __init__(self, static_mode=False, max_hands=2, min_detection_confidence=0.5, min_tracking_confidence=0.5):
        print("Initializing HandTracker...")
        try:
            self.static_mode = static_mode
            self.max_hands = max_hands
            self.min_detection_confidence = min_detection_confidence
            self.min_tracking_confidence = min_tracking_confidence
            
            print(f"MediaPipe Hands parameters: static_mode={static_mode}, max_hands={max_hands}, "
                  f"min_detection_confidence={min_detection_confidence}, "
                  f"min_tracking_confidence={min_tracking_confidence}")
            
            self.mp_hands = mp.solutions.hands
            self.hands = self.mp_hands.Hands(
                static_image_mode=self.static_mode,
                max_num_hands=self.max_hands,
                min_detection_confidence=self.min_detection_confidence,
                min_tracking_confidence=self.min_tracking_confidence
            )
            self.mp_draw = mp.solutions.drawing_utils
            
            # For debugging - track processing time
            self.prev_time = 0
            self.curr_time = 0
            
            # For pinch detection
            self.pinch_threshold = 30  # Reduced threshold to make pinch detection more sensitive
            self.pinch_history = [False] * 3  # Small history to stabilize pinch detection
            
            # For enhanced gesture recognition
            self.gesture_cooldown = 0  # Cooldown for gesture recognition
            
            print("HandTracker initialized successfully")
        except Exception as e:
            print(f"Error initializing HandTracker: {e}")
            traceback.print_exc()
            raise
    
    def check_superpower_gesture(self, lm_list):
        """Check if all fingers are extended (superpower gesture)"""
        try:
            return self.count_fingers_up(lm_list) == 5
                
        except Exception as e:
            print(f"Error in check_superpower_gesture: {e}")
            traceback.print_exc()
            return False
    
    def find_hands(self, img, draw=True):
        try:
            # Start timing
            self.curr_time = time.time()
            fps = 1 / (self.curr_time - self.prev_time) if self.prev_time > 0 else 0
            self.prev_time = self.curr_time
            
            # Make a copy of the image to avoid modifying the original
            img_copy = img.copy()
            
            # Check if image is valid
            if img_copy is None or img_copy.size == 0:
                print("Warning: Empty image received in find_hands")
                return img  # Return original image if copy failed
                
            # Convert BGR image to RGB
            img_rgb = cv2.cvtColor(img_copy, cv2.COLOR_BGR2RGB)
            
            # Process the image
            self.results = self.hands.process(img_rgb)
            
            # Draw FPS on the image (for debugging)
            cv2.putText(img_copy, f'FPS: {int(fps)}', (10, 70), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Draw hand landmarks if found and draw is True
            if self.results.multi_hand_landmarks:
                for hand_landmarks in self.results.multi_hand_landmarks:
                    if draw:
                        # Draw landmarks with custom colors for better visibility
                        self.mp_draw.draw_landmarks(
                            img_copy, 
                            hand_landmarks, 
                            self.mp_hands.HAND_CONNECTIONS,
                            self.mp_draw.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=3),  # Green landmarks
                            self.mp_draw.DrawingSpec(color=(255, 0, 0), thickness=2)  # Blue connections
                        )
                
                # Add indicator that hand is detected
                cv2.putText(img_copy, 'Hand Detected', (10, 110), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # Get finger count and draw it
                lm_list = self.find_position(img_copy)
                if lm_list:
                    fingers_up = self.count_fingers_up(lm_list)
                    gesture = self.get_gesture_name(fingers_up, lm_list)
                    cv2.putText(img_copy, f'Gesture: {gesture}', (10, 150), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            return img_copy
            
        except Exception as e:
            print(f"Error in find_hands: {e}")
            traceback.print_exc()
            return img  # Return original image on error
    
    def find_position(self, img, hand_no=0):
        try:
            lm_list = []
            
            if not hasattr(self, 'results') or self.results is None:
                return lm_list
                
            if self.results.multi_hand_landmarks:
                if len(self.results.multi_hand_landmarks) > hand_no:
                    hand = self.results.multi_hand_landmarks[hand_no]
                    
                    h, w, c = img.shape
                    
                    for id, lm in enumerate(hand.landmark):
                        # Convert landmark to pixel coordinates
                        cx, cy = int(lm.x * w), int(lm.y * h)
                        lm_list.append([id, cx, cy])
            
            return lm_list
            
        except Exception as e:
            print(f"Error in find_position: {e}")
            traceback.print_exc()
            return []
    
    def get_distance(self, p1, p2, img=None, draw=False, r=15, t=3):
        """Calculate distance between two landmarks"""
        try:
            x1, y1 = p1
            x2, y2 = p2
            
            # Calculate distance
            length = math.hypot(x2 - x1, y2 - y1)
            
            # Draw points and line if requested
            if draw and img is not None:
                cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), t)
                cv2.circle(img, (x1, y1), r, (255, 0, 255), cv2.FILLED)
                cv2.circle(img, (x2, y2), r, (255, 0, 255), cv2.FILLED)
            
            return length
        except Exception as e:
            print(f"Error in get_distance: {e}")
            traceback.print_exc()
            return 100  # Return a default value that will cause the gesture to not be detected
    
    def check_thumb_index_pinch(self, lm_list, img=None):
        """
        Check if thumb and index finger are pinched (shooting gesture)
        This is an improved version with visualization
        """
        try:
            if len(lm_list) >= 9:
                # Get thumb tip and index tip positions
                thumb_tip = lm_list[4][1:3]  # x,y coordinates of thumb tip (landmark 4)
                index_tip = lm_list[8][1:3]  # x,y coordinates of index tip (landmark 8)
                
                # Calculate distance between them
                distance = self.get_distance(thumb_tip, index_tip, img, draw=True)
                
                # Determine if pinched - using a tighter threshold
                is_pinched = distance < self.pinch_threshold
                
                # Add to history for stability
                self.pinch_history.append(is_pinched)
                self.pinch_history.pop(0)
                
                # Require 2 of 3 frames to be pinched for stability
                stable_pinch = sum(self.pinch_history) >= 2
                
                # Draw the pinch detection if image is provided
                if img is not None:
                    # Draw circle between thumb and index finger
                    center_x = (thumb_tip[0] + index_tip[0]) // 2
                    center_y = (thumb_tip[1] + index_tip[1]) // 2
                    
                    # Color based on if pinched or not
                    color = (0, 0, 255) if stable_pinch else (0, 255, 0)
                    
                    # Line between thumb and index
                    cv2.line(img, (thumb_tip[0], thumb_tip[1]), (index_tip[0], index_tip[1]), color, 2)
                    
                    # Circle at midpoint with size proportional to distance
                    radius = max(5, min(20, int(distance / 2)))
                    cv2.circle(img, (center_x, center_y), radius, color, -1)
                    
                    # Text indicator
                    if stable_pinch:
                        cv2.putText(img, "PINCH: SHOOT", (center_x - 40, center_y - 20),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                        
                        # Debug: show coordinates of the pinch point
                        cv2.putText(img, f"Coords: ({center_x}, {center_y})", (center_x - 60, center_y + 20),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                
                return stable_pinch
            
            return False
        except Exception as e:
            print(f"Error in check_thumb_index_pinch: {e}")
            traceback.print_exc()
            return False
    
    def count_fingers_up(self, lm_list):
        """Count how many fingers are extended"""
        try:
            if len(lm_list) >= 21:
                # Get finger states (up/down)
                fingers = []
                
                # Thumb (special case - compare with thumb base)
                if lm_list[4][1] < lm_list[3][1]:  # For right hand (flipped image)
                    fingers.append(1)
                else:
                    fingers.append(0)
                    
                # 4 fingers - check if fingertip is above PIP joint
                for tip_id in [8, 12, 16, 20]:  # Index, middle, ring, pinky tips
                    if lm_list[tip_id][2] < lm_list[tip_id-2][2]:  # Tip is higher than PIP joint
                        fingers.append(1)
                    else:
                        fingers.append(0)
                
                # Return total fingers up
                return sum(fingers)
                
            return 0
        except Exception as e:
            print(f"Error in count_fingers_up: {e}")
            traceback.print_exc()
            return 0
    
    def get_gesture_name(self, fingers_up, lm_list):
        """Get a descriptive name for the current gesture"""
        try:
            # If no fingers detected or invalid data
            if fingers_up == 0:
                return "Fist"
                
            # Check for pinch (special case for shooting)
            if self.check_thumb_index_pinch(lm_list, None):
                return "Pinch (Shoot)"
                
            # All fingers up - superpower
            if fingers_up == 5:
                return "Superpower"
                
            # Movement control (4+ fingers)
            if fingers_up >= 4:
                return "Movement"
                
            # Other finger combinations
            if fingers_up == 1:
                return "Pointing"
                
            # Default for other combinations
            return f"{fingers_up} Fingers"
            
        except Exception as e:
            print(f"Error in get_gesture_name: {e}")
            traceback.print_exc()
            return "Unknown"