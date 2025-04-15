import cv2
import numpy as np
import time
import os
import sys
import traceback
from utils.hand_tracker import HandTracker
from utils.game_engine import GameEngine

def main():
    try:
        print("Starting game initialization...")
        if not os.path.exists('assets'):
            print("Warning: 'assets' directory not found. Creating placeholder directory.")
            os.makedirs('assets', exist_ok=True)
            
        for img_file in ['background.png', 'enemy.png', 'enemy1.png', 'farmer.png', 'crop.png']:
            img_path = os.path.join('assets', img_file)
            if not os.path.exists(img_path):
                print(f"Warning: '{img_path}' not found. Game will use placeholder graphics.")
        
        print("Initializing camera...")
        cap = cv2.VideoCapture(0)
        
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        # Check for camera
        if not cap.isOpened():
            print("Error: Could not open camera.")
            return
        
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"Camera initialized with dimensions: {width}x{height}")
        
        #for hand tracker
        print("Initializing hand tracker...")
        hand_tracker = HandTracker(min_detection_confidence=0.7)
        
        #game engine 
        print("Initializing game engine...")
        game_engine = GameEngine(assets_path='assets')
        print("Game engine initialized successfully!")
        
        cv2.namedWindow('Hand Tracking (Camera View)', cv2.WINDOW_NORMAL)
        cv2.namedWindow('Vision Hero: Defenders of the Farm', cv2.WINDOW_NORMAL)
        
        camera_width = 640
        camera_height = 480
        game_width = 1280
        game_height = 720
    
        cv2.resizeWindow('Hand Tracking (Camera View)', camera_width, camera_height)
        cv2.resizeWindow('Vision Hero: Defenders of the Farm', game_width, game_height)
        cv2.moveWindow('Hand Tracking (Camera View)', 50, 100)
        cv2.moveWindow('Vision Hero: Defenders of the Farm', camera_width + 100, 100)
        last_shoot_time = time.time()
        shoot_cooldown = 0.5 
        
        last_hand_pos = None
        farmer_move_cooldown = 0
        
        movement_sensitivity = 0.5  
        
        print("\n=== Vision Hero: Defenders of the Farm ===")
        print("Game Controls:")
        print("- Pinch thumb and index finger to shoot")
        print("- Open hand fully and move to control farmer")
        print("- Open all fingers for superpower (enhanced attacks)")
        print("- Press 'q' to quit")
        print("- Press 'r' to restart the game")
        print("\nNew Game Rules:")
        print("- Protect your crops from enemies")
        print("- Survive until the timer runs out")
        print("- Destroying enemies adds time to your clock")
        print("- Game ends when time runs out or all crops are destroyed")
        print("\nStarting game. Enjoy!\n")
        
        print("Starting main game loop...")
        while True:
            success, frame = cap.read()
            if not success:
                print("Error: Failed to grab frame.")
                break
                
            frame = cv2.flip(frame, 1)
            
            cv2.putText(frame, "Hand Controls", (20, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
            
            try:
                frame = hand_tracker.find_hands(frame)
                
                lm_list = hand_tracker.find_position(frame)
                
                if lm_list and len(lm_list) >= 21:
                    palm_x, palm_y = lm_list[0][1], lm_list[0][2]
                    
                    # Count fingers which is upp!!
                    fingers_up = hand_tracker.count_fingers_up(lm_list)
                    
                    if fingers_up == 5:
                        game_engine.use_superpower()
                        
                    elif fingers_up >= 4:  
                        game_x = palm_x * (game_engine.width / frame.shape[1])
                        game_y = palm_y * (game_engine.height / frame.shape[0])
                       
                        if hasattr(game_engine, 'last_farmer_pos') and game_engine.last_farmer_pos is not None:
                            
                            current_x = game_engine.farmer.x
                            current_y = game_engine.farmer.y
                            
                            target_x = current_x + (game_x - game_engine.farmer.width/2 - current_x) * movement_sensitivity
                            target_y = current_y + (game_y - game_engine.farmer.height/2 - current_y) * movement_sensitivity
                        else:
                            target_x = game_x - game_engine.farmer.width/2
                            target_y = game_y - game_engine.farmer.height/2
                        
                        game_engine.farmer.set_position(target_x, target_y)
                        game_engine.last_farmer_pos = (target_x, target_y)
                        
                    else:
                        is_pinching = hand_tracker.check_thumb_index_pinch(lm_list, frame)
                        
                        if is_pinching:
                            current_time = time.time()
                            if current_time - last_shoot_time > shoot_cooldown:
                                # Get midpoint between thumb and index finger
                                thumb_tip = lm_list[4][1:3]  
                                index_tip = lm_list[8][1:3]  
                                
                                mid_x = (thumb_tip[0] + index_tip[0]) // 2
                                mid_y = (thumb_tip[1] + index_tip[1]) // 2
                                
                                cv2.circle(frame, (mid_x, mid_y), 10, (0, 0, 255), -1)
                                cv2.line(frame, (mid_x, mid_y), 
                                         (mid_x, mid_y - 50), (0, 0, 255), 2)
                                
                                game_engine.shoot(mid_x, mid_y)
                                last_shoot_time = current_time
        
                                cv2.putText(frame, f"SHOOT at ({mid_x}, {mid_y})", (10, 200),
                                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    last_hand_pos = (palm_x, palm_y)
                    
            except Exception as e:
                print(f"Error in hand tracking: {e}")
                traceback.print_exc()
                lm_list = []
            
            try:
                game_engine.update()
                game_frame = game_engine.render_game_only()
                cv2.imshow('Hand Tracking (Camera View)', frame)
                cv2.imshow('Vision Hero: Defenders of the Farm', game_frame)

            except Exception as e:
                print(f"Error in game logic: {e}")
                traceback.print_exc()
                cv2.imshow('Hand Tracking (Camera View)', frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("Quit key pressed. Exiting game...")
                break
            elif key == ord('r'):
                print("Restarting game...")
                game_engine = GameEngine(assets_path='assets')
                print("Game restarted!")

    except Exception as e:
        print(f"Critical error in game loop: {e}")
        traceback.print_exc()
    finally:
        print("Releasing resources...")
        cap.release()
        cv2.destroyAllWindows()
        print("Game closed.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Fatal error: {e}")
        traceback.print_exc()
        print("Game crashed. Please check error messages above.")
        input("Press Enter to exit...")