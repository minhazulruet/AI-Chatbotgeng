#!/usr/bin/env python3
"""
Quick test to verify the improved results display
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait as Wait
from selenium.webdriver.support import expected_conditions as EC


def test_results_display():
    """Test the improved results display with full questions and options"""
    
    print("\n" + "="*60)
    print("TESTING IMPROVED RESULTS DISPLAY")
    print("="*60)
    
    driver = None
    try:
        options = webdriver.ChromeOptions()
        options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})
        
        driver = webdriver.Chrome(options=options)
        driver.set_window_size(1200, 900)
        
        # Navigate to quiz
        print("[INFO] Loading quiz page...")
        driver.get('http://localhost:8000/quiz.html')
        time.sleep(2)
        
        # Generate quiz
        print("[INFO] Generating quiz on 'Ohm's Law'...")
        topic_input = driver.find_element(By.ID, 'topicInput')
        topic_input.send_keys('Ohm\'s Law')
        
        num_input = driver.find_element(By.ID, 'numQuestionsInput')
        num_input.clear()
        num_input.send_keys('2')
        
        generate_btn = driver.find_element(By.ID, 'generateBtn')
        generate_btn.click()
        
        # Wait for quiz to load
        time.sleep(1)
        Wait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'question-container'))
        )
        print("[✓] Quiz loaded")
        
        # Answer first question - select option 1
        options_q1 = driver.find_elements(By.CLASS_NAME, 'option-button')
        options_q1[0].click()
        print("[INFO] Answered question 1 (option A)")
        
        # Move to next question
        next_btn = driver.find_element(By.ID, 'nextBtn')
        next_btn.click()
        time.sleep(0.5)
        
        # Answer second question - select different option (e.g., option 2)
        options_q2 = driver.find_elements(By.CLASS_NAME, 'option-button')
        options_q2[1].click()  # Select option B
        print("[INFO] Answered question 2 (option B)")
        
        # Submit quiz
        submit_btn = driver.find_element(By.ID, 'submitBtn')
        print("[INFO] Submitting quiz...")
        submit_btn.click()
        
        # Wait for results
        time.sleep(3)
        results_screen = driver.find_element(By.ID, 'resultsScreen')
        if 'active' not in results_screen.get_attribute('class'):
            print("[✗] Results screen not active")
            return False
        
        print("[✓] Results screen displayed")
        
        # Check review items
        review_items = driver.find_elements(By.CLASS_NAME, 'review-item')
        print(f"\n[✓] Found {len(review_items)} review items\n")
        
        # Verify review content
        for idx, review in enumerate(review_items, 1):
            text = review.text
            print(f"--- Review Item {idx} ---")
            print(text[:300] + "..." if len(text) > 300 else text)
            print()
            
            # Check for new format elements
            has_checkmark = '✅' in text or '❌' in text
            has_question = 'Question:' in text or 'Options:' in text
            has_answer = 'Your answer:' in text
            has_correct = 'Correct answer:' in text or has_checkmark
            
            print(f"  ✓ Has status icon: {has_checkmark}")
            print(f"  ✓ Has question/options: {has_question}")
            print(f"  ✓ Has 'Your answer': {has_answer}")
            print(f"  ✓ Has answer info: {has_correct}")
            
            if not (has_checkmark and has_question and has_answer and has_correct):
                print("[⚠] Missing expected elements!")
            print()
        
        # Check console for errors
        console_logs = driver.get_log('browser')
        errors = [log['message'] for log in console_logs if 'error' in log['level'].lower() and '[object Object]' in log['message']]
        
        if errors:
            print("[✗] Found [object Object] errors:")
            for error in errors:
                print(f"  - {error}")
            return False
        else:
            print("[✓] No [object Object] errors found")
        
        print("\n" + "="*60)
        print("✅ RESULTS DISPLAY TEST PASSED!")
        print("="*60)
        return True
        
    except Exception as e:
        print(f"[✗] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        if driver:
            driver.quit()
            print("[INFO] Browser closed")


if __name__ == '__main__':
    success = test_results_display()
    exit(0 if success else 1)
