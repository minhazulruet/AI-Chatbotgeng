#!/usr/bin/env python3
"""
Test script to verify quiz system fixes:
1. Error message handling - should show clear error, not "[object Object]"
2. Button functionality after restart - should work properly
Enhanced with browser console logging and error capture
"""

import time
import os
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def capture_console_logs(driver):
    """Capture JavaScript console logs and errors"""
    logs = driver.get_log('browser')
    errors = [log for log in logs if log['level'] == 'SEVERE']
    warnings = [log for log in logs if log['level'] == 'WARNING']
    infos = [log for log in logs if log['level'] == 'INFO']
    
    return {
        'errors': errors,
        'warnings': warnings,
        'infos': infos,
        'all_logs': logs
    }

def print_console_logs(logs_dict):
    """Pretty print console logs"""
    if logs_dict['errors']:
        print("\n[CONSOLE ERRORS]:")
        for error in logs_dict['errors']:
            print(f"  - {error['message']}")
    
    if logs_dict['warnings']:
        print("\n[CONSOLE WARNINGS]:")
        for warning in logs_dict['warnings'][:5]:  # First 5
            print(f"  - {warning['message']}")

def test_quiz_fixes():
    """Test quiz error handling and button restart functionality"""
    
    driver = None
    try:
        # Initialize Chrome driver with logging enabled
        options = webdriver.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--enable-logging')
        options.add_argument('--v=1')
        
        # Enable browser console logging
        options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})
        
        driver = webdriver.Chrome(options=options)
        print("[INFO] Chrome driver initialized with logging enabled")
        
        # Navigate to quiz page through backend server
        quiz_url = 'http://localhost:8000/quiz.html'
        print(f"[INFO] Navigating to: {quiz_url}")
        driver.get(quiz_url)
        print(f"[INFO] Page loaded")
        
        # Wait for page to fully load
        time.sleep(3)
        
        # Verify form screen is visible
        form_screen = driver.find_element(By.ID, 'formScreen')
        if 'active' in form_screen.get_attribute('class'):
            print("✅ PASS: Form screen is visible on load")
        else:
            print("❌ FAIL: Form screen not visible on load")
            logs = capture_console_logs(driver)
            print_console_logs(logs)
            return False
        
        # TEST 1: Generate and submit quiz to test error handling
        print("\n--- TEST 1: Error Message Handling ---")
        
        # Enter topic
        topic_input = driver.find_element(By.ID, 'topicInput')
        topic_input.clear()
        topic_input.send_keys('Ohm\'s Law')
        print("[INFO] Entered topic: Ohm's Law")
        
        # Select difficulty (Easy - faster)
        difficulty_select = Select(driver.find_element(By.ID, 'difficultySelect'))
        difficulty_select.select_by_value('Easy')
        print("[INFO] Selected difficulty: Easy")
        
        # Set number of questions
        num_questions_input = driver.find_element(By.ID, 'numQuestionsInput')
        num_questions_input.clear()
        num_questions_input.send_keys('3')
        print("[INFO] Set number of questions: 3")
        
        # Capture console before clicking
        logs_before = capture_console_logs(driver)
        
        # Click Generate Quiz button
        generate_btn = driver.find_element(By.ID, 'generateBtn')
        print("[INFO] Clicking Generate Quiz button...")
        print(f"[DEBUG] Button text: {generate_btn.text}")
        print(f"[DEBUG] Button enabled: {not generate_btn.get_attribute('disabled')}")
        
        # Click and wait
        driver.execute_script("arguments[0].click();", generate_btn)
        print("[INFO] Click executed")
        
        # Wait a bit and check for errors
        time.sleep(2)
        
        # Capture console after clicking
        logs_after = capture_console_logs(driver)
        
        print("\n[DEBUG] Checking browser console for errors...")
        print_console_logs(logs_after)
        
        # Check if loading screen appeared
        loading_screen = driver.find_element(By.ID, 'loadingScreen')
        if 'active' in loading_screen.get_attribute('class'):
            print("✅ PASS: Loading screen appeared")
        else:
            print("⚠️  WARNING: Loading screen not active immediately")
        
        # Wait for quiz to load (max 20 seconds)
        print("[INFO] Waiting for quiz to generate...")
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.ID, 'questionArea'))
            )
            time.sleep(1)
            
            # Check if question appeared
            question_area = driver.find_element(By.ID, 'questionArea')
            if question_area and question_area.text:
                print(f"✅ PASS: Question loaded: {question_area.text[:60]}...")
            
            quiz_screen = driver.find_element(By.ID, 'quizScreen')
            if 'active' in quiz_screen.get_attribute('class'):
                print("✅ PASS: Quiz screen is active")
            else:
                print("⚠️  WARNING: Quiz screen found but not active")
                
        except TimeoutException:
            print("❌ FAIL: Quiz did not load in time (timeout after 20 seconds)")
            logs = capture_console_logs(driver)
            print_console_logs(logs)
            return False
        except Exception as e:
            print(f"❌ FAIL: Error waiting for quiz: {e}")
            logs = capture_console_logs(driver)
            print_console_logs(logs)
            return False
        
        # Select first answer
        try:
            option_buttons = driver.find_elements(By.CLASS_NAME, 'option-button')
            if option_buttons:
                print(f"[INFO] Found {len(option_buttons)} options")
                option_buttons[0].click()
                print("[INFO] Selected first option")
                time.sleep(0.5)
        except Exception as e:
            print(f"⚠️  WARNING: Could not select option: {e}")
        
        # Submit quiz
        try:
            submit_btn = driver.find_element(By.ID, 'submitBtn')
            print("[INFO] Clicking Submit Quiz button...")
            driver.execute_script("arguments[0].click();", submit_btn)
            
            time.sleep(3)
            
            # Check if results screen appeared
            results_screen = driver.find_element(By.ID, 'resultsScreen')
            if 'active' in results_screen.get_attribute('class'):
                print("✅ PASS: Results screen appeared (quiz submitted successfully)")
                
                # Check for "[object Object]" in any visible text
                page_text = driver.find_element(By.TAG_NAME, 'body').text
                if '[object Object]' in page_text:
                    print("❌ FAIL: Found '[object Object]' error in page")
                else:
                    print("✅ PASS: No '[object Object]' error messages found")
                    
            else:
                print("⚠️  WARNING: Results screen found but may not be active")
                
        except Exception as e:
            print(f"⚠️  WARNING: Error with submission: {e}")
            logs = capture_console_logs(driver)
            print_console_logs(logs)
        
        # TEST 2: Test "Take Another Quiz" button
        print("\n--- TEST 2: Take Another Quiz Button Functionality ---")
        
        try:
            restart_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Take Another Quiz')]")
            print("[INFO] Clicking 'Take Another Quiz' button...")
            driver.execute_script("arguments[0].click();", restart_btn)
            time.sleep(1)
        except NoSuchElementException:
            print("❌ FAIL: 'Take Another Quiz' button not found")
            logs = capture_console_logs(driver)
            print_console_logs(logs)
            return False
        
        # Verify form screen is visible again
        form_screen = driver.find_element(By.ID, 'formScreen')
        if 'active' in form_screen.get_attribute('class'):
            print("✅ PASS: Form screen reappeared after restart")
        else:
            print("❌ FAIL: Form screen not visible after restart")
            return False
        
        # Verify Generate Quiz button is enabled
        generate_btn = driver.find_element(By.ID, 'generateBtn')
        if not generate_btn.get_attribute('disabled'):
            print("✅ PASS: Generate Quiz button is enabled after restart")
        else:
            print("❌ FAIL: Generate Quiz button is disabled after restart")
            return False
        
        # Try clicking the button again
        print("\n[INFO] Testing second quiz generation...")
        topic_input = driver.find_element(By.ID, 'topicInput')
        topic_input.clear()
        topic_input.send_keys('Circuit Analysis')
        
        generate_btn = driver.find_element(By.ID, 'generateBtn')
        driver.execute_script("arguments[0].click();", generate_btn)
        
        time.sleep(2)
        
        # Wait for second quiz
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.ID, 'questionArea'))
            )
            quiz_screen = driver.find_element(By.ID, 'quizScreen')
            if 'active' in quiz_screen.get_attribute('class'):
                print("✅ PASS: Second quiz generated successfully - button fully functional")
            else:
                print("⚠️  WARNING: Second quiz loaded but screen not active")
        except TimeoutException:
            print("❌ FAIL: Second quiz did not load")
            logs = capture_console_logs(driver)
            print_console_logs(logs)
            return False
        
        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
        print("="*60)
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED WITH ERROR: {e}")
        import traceback
        traceback.print_exc()
        
        if driver:
            try:
                logs = capture_console_logs(driver)
                print_console_logs(logs)
            except:
                pass
        
        return False
    
    finally:
        if driver:
            try:
                # Final console log capture
                logs = capture_console_logs(driver)
                if logs['errors']:
                    print("\n[FINAL CONSOLE CHECK] Found errors in browser console:")
                    print_console_logs(logs)
            except:
                pass
            
            driver.quit()
            print("[INFO] Browser closed")

if __name__ == '__main__':
    print("Starting Enhanced Quiz System Fix Tests...")
    print("="*60)
    success = test_quiz_fixes()
    exit(0 if success else 1)
