#!/usr/bin/env python3
"""
Improved test script for quiz system with:
1. Console error capture
2. Screenshot on failure
3. Better error handling
4. Validation of new features (completion check, warning display)
"""

import time
import json
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as Wait
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException


class QuizTestRunner:
    def __init__(self):
        self.driver = None
        self.test_results = []
        self.screenshots_dir = 'd:\\RA\\AI Chatbot\\test_screenshots'
        
        # Create screenshots directory if it doesn't exist
        os.makedirs(self.screenshots_dir, exist_ok=True)
        
    def screenshot(self, name):
        """Take screenshot for debugging"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        path = os.path.join(self.screenshots_dir, f'{name}_{timestamp}.png')
        try:
            self.driver.save_screenshot(path)
            print(f"[SCREENSHOT] Saved to {path}")
            return path
        except Exception as e:
            print(f"[ERROR] Failed to save screenshot: {e}")
            return None
    
    def get_console_logs(self):
        """Get browser console logs"""
        try:
            logs = self.driver.get_log('browser')
            return logs
        except Exception as e:
            print(f"[WARNING] Could not get console logs: {e}")
            return []
    
    def init_browser(self):
        """Initialize Chrome browser with proper options"""
        print("\n[INFO] Initializing Chrome browser...")
        
        options = webdriver.ChromeOptions()
        options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-popup-blocking')
        
        try:
            self.driver = webdriver.Chrome(options=options)
            print("[✓] Chrome browser initialized")
            return True
        except Exception as e:
            print(f"[✗] Failed to initialize browser: {e}")
            return False
    
    def test_quiz_generation_and_validation(self):
        """Test 1: Quiz generation with completion validation"""
        print("\n--- TEST 1: Quiz Generation and Completion Validation ---")
        
        try:
            # Navigate to quiz page
            print("[INFO] Navigating to http://localhost:8000/quiz.html")
            self.driver.get('http://localhost:8000/quiz.html')
            self.driver.set_window_size(1200, 800)
            time.sleep(2)
            
            # Check form is visible
            form_screen = self.driver.find_element(By.ID, 'formScreen')
            if 'active' not in form_screen.get_attribute('class'):
                print("[✗] Form screen not visible")
                self.screenshot('test1_form_not_visible')
                return False
            print("[✓] Form screen visible")
            
            # Enter topic
            topic_input = self.driver.find_element(By.ID, 'topicInput')
            topic_input.clear()
            topic_input.send_keys('Ohm\'s Law')
            print("[INFO] Entered topic: Ohm's Law")
            
            # Set number of questions to 3 (faster test)
            num_input = self.driver.find_element(By.ID, 'numQuestionsInput')
            num_input.clear()
            num_input.send_keys('3')
            print("[INFO] Set number of questions: 3")
            
            # Click Generate Quiz
            generate_btn = self.driver.find_element(By.ID, 'generateBtn')
            print("[INFO] Clicking Generate Quiz button...")
            generate_btn.click()
            
            # Wait for loading screen
            time.sleep(1)
            loading_screen = self.driver.find_element(By.ID, 'loadingScreen')
            if 'active' not in loading_screen.get_attribute('class'):
                print("[⚠] Loading screen may not have appeared")
            else:
                print("[✓] Loading screen appeared")
            
            # Wait for quiz to load (max 20 seconds)
            print("[INFO] Waiting for quiz to load...")
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'question-container'))
            )
            
            quiz_screen = self.driver.find_element(By.ID, 'quizScreen')
            if 'active' not in quiz_screen.get_attribute('class'):
                print("[✗] Quiz screen not active")
                self.screenshot('test1_quiz_not_active')
                return False
            print("[✓] Quiz screen active and loaded")
            self.screenshot('test1_quiz_loaded')
            
            # TEST: Submit button should be disabled initially
            submit_btn = self.driver.find_element(By.ID, 'submitBtn')
            if submit_btn.get_attribute('disabled') is not None:
                print("[✓] Submit button is disabled when no questions answered")
            else:
                print("[⚠] Submit button should be disabled initially")
            
            # Check button text shows unanswered count
            btn_text = submit_btn.text
            if 'unanswered' in btn_text.lower():
                print(f"[✓] Submit button shows unanswered count: '{btn_text}'")
            else:
                print(f"[⚠] Submit button text: '{btn_text}'")
            
            # TEST: Try to submit without answering (should show warning)
            print("[INFO] Testing submit without answering all questions...")
            submit_btn.click()
            time.sleep(1)
            
            # Check if warning appeared
            warnings = self.driver.find_elements(By.TAG_NAME, 'div')
            warning_found = False
            for warning in warnings:
                style = warning.get_attribute('style')
                if style and 'ff9800' in style.lower():  # Orange warning color
                    print(f"[✓] Warning appeared: '{warning.text}'")
                    warning_found = True
                    break
            
            if not warning_found:
                # Check console for warnings
                console_logs = self.get_console_logs()
                if console_logs:
                    print("[INFO] Console logs:")
                    for log in console_logs[:5]:
                        print(f"  - {log['message']}")
            
            # Now answer all questions
            print("[INFO] Answering all questions...")
            for q in range(3):
                # Click first option
                options = self.driver.find_elements(By.CLASS_NAME, 'option-button')
                if options:
                    options[0].click()
                    print(f"[✓] Answered question {q+1}")
                    time.sleep(0.3)
                
                # Move to next if not last
                if q < 2:
                    try:
                        next_btn = self.driver.find_element(By.ID, 'nextBtn')
                        next_btn.click()
                        time.sleep(0.3)
                    except Exception as e:
                        print(f"[⚠] Error moving to next question: {e}")
            
            # Check submit button is now enabled
            submit_btn = self.driver.find_element(By.ID, 'submitBtn')
            if submit_btn.get_attribute('disabled') is None:
                print("[✓] Submit button is now enabled after answering all questions")
            else:
                print("[✗] Submit button still disabled after answering all")
                return False
            
            # Check button text shows all answered
            btn_text = submit_btn.text
            if 'all answered' in btn_text.lower() or '\u2713' in btn_text:
                print(f"[✓] Submit button shows all answered: '{btn_text}'")
            else:
                print(f"[⚠] Submit button text: '{btn_text}'")
            
            # Submit quiz
            print("[INFO] Submitting quiz...")
            submit_btn.click()
            time.sleep(3)
            
            # Check results screen
            try:
                results_screen = self.driver.find_element(By.ID, 'resultsScreen')
                if 'active' in results_screen.get_attribute('class'):
                    print("[✓] Results screen appeared - Quiz submitted successfully!")
                    self.screenshot('test1_results_displayed')
                    
                    # Check for error messages in results
                    console_logs = self.get_console_logs()
                    has_object_error = False
                    for log in console_logs:
                        msg = log['message']
                        if '[object Object]' in msg or '[object,object' in msg:
                            print(f"[✗] FOUND [object Object] error: {msg}")
                            has_object_error = True
                    
                    if not has_object_error:
                        print("[✓] No [object Object] errors in console")
                    
                    return True
                else:
                    print("[✗] Results screen not active")
                    return False
            except TimeoutException:
                print("[✗] Results screen did not appear - timeout")
                console_logs = self.get_console_logs()
                print("[INFO] Console logs:")
                for log in console_logs:
                    print(f"  - {log['message']}")
                self.screenshot('test1_timeout')
                return False
        
        except Exception as e:
            print(f"[✗] Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            self.screenshot('test1_error')
            return False
    
    def test_take_another_quiz(self):
        """Test 2: Take Another Quiz button functionality"""
        print("\n--- TEST 2: Take Another Quiz Button ---")
        
        try:
            # Click "Take Another Quiz" button
            restart_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Take Another Quiz')]")
            print("[INFO] Clicking 'Take Another Quiz' button...")
            restart_btn.click()
            time.sleep(1)
            
            # Check form appeared
            form_screen = self.driver.find_element(By.ID, 'formScreen')
            if 'active' not in form_screen.get_attribute('class'):
                print("[✗] Form screen not active after restart")
                self.screenshot('test2_form_not_active')
                return False
            print("[✓] Form screen appeared after restart")
            
            # Check form is cleared
            topic_input = self.driver.find_element(By.ID, 'topicInput')
            if topic_input.get_attribute('value') == '':
                print("[✓] Topic input cleared")
            else:
                print("[⚠] Topic input not cleared")
            
            # Check button is enabled
            generate_btn = self.driver.find_element(By.ID, 'generateBtn')
            if not generate_btn.get_attribute('disabled'):
                print("[✓] Generate button is enabled")
            else:
                print("[✗] Generate button is disabled")
                return False
            
            # Try generating another quiz
            print("[INFO] Testing second quiz generation...")
            topic_input.clear()
            topic_input.send_keys('Circuit Analysis')
            
            num_input = self.driver.find_element(By.ID, 'numQuestionsInput')
            num_input.clear()
            num_input.send_keys('3')
            
            generate_btn.click()
            print("[INFO] Waiting for second quiz to load...")
            
            time.sleep(1)
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'question-container'))
            )
            
            quiz_screen = self.driver.find_element(By.ID, 'quizScreen')
            if 'active' in quiz_screen.get_attribute('class'):
                print("[✓] Second quiz generated and displayed successfully!")
                self.screenshot('test2_second_quiz')
                return True
            else:
                print("[✗] Quiz screen not active for second quiz")
                return False
        
        except Exception as e:
            print(f"[✗] Test failed with error: {e}")
            self.screenshot('test2_error')
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "="*60)
        print("QUIZ SYSTEM TEST SUITE")
        print("="*60)
        
        if not self.init_browser():
            return False
        
        try:
            results = {
                'test1_quiz_completion_validation': self.test_quiz_generation_and_validation(),
                'test2_take_another_quiz': self.test_take_another_quiz(),
            }
            
            print("\n" + "="*60)
            print("TEST SUMMARY")
            print("="*60)
            
            passed = sum(1 for v in results.values() if v)
            total = len(results)
            
            for test_name, result in results.items():
                status = "✓ PASS" if result else "✗ FAIL"
                print(f"{status}: {test_name}")
            
            print(f"\nTotal: {passed}/{total} tests passed")
            print("="*60)
            
            return all(results.values())
        
        finally:
            if self.driver:
                self.driver.quit()
                print("[INFO] Browser closed")


if __name__ == '__main__':
    runner = QuizTestRunner()
    success = runner.run_all_tests()
    exit(0 if success else 1)
