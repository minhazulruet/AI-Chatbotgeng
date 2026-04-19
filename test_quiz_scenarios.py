import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# Setup Chrome options
chrome_options = Options()
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Initialize WebDriver
driver = webdriver.Chrome(options=chrome_options)

try:
    print("=" * 80)
    print("QUIZ SYSTEM TESTING")
    print("=" * 80)
    
    # Convert file path to file:// URL
    quiz_file = "file:///d:/RA/AI%20Chatbot/frontend/quiz.html"
    print(f"\n[INFO] Opening quiz at: {quiz_file}")
    driver.get(quiz_file)
    
    # Wait for page to load
    time.sleep(3)
    print("[INFO] Page loaded")
    
    # ========== TEST 1: Error Handling ==========
    print("\n" + "=" * 80)
    print("TEST 1: ERROR HANDLING & ERROR MESSAGE DISPLAY")
    print("=" * 80)
    
    # Find form inputs
    print("\n[Step 1] Filling quiz form...")
    topic_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "topicInput"))
    )
    topic_input.clear()
    topic_input.send_keys("Ohm''s Law")
    print("  ✓ Entered topic: 'Ohm''s Law'")
    
    # Set number of questions to 5
    num_questions_input = driver.find_element(By.ID, "numQuestionsInput")
    num_questions_input.clear()
    num_questions_input.send_keys("5")
    print("  ✓ Set number of questions: 5")
    
    # Set difficulty to Easy
    difficulty_select = Select(driver.find_element(By.ID, "difficultySelect"))
    difficulty_select.select_by_value("Easy")
    print("  ✓ Set difficulty: Easy")
    
    # Click Generate Quiz button
    print("\n[Step 2] Clicking 'Generate Quiz' button...")
    generate_btn = driver.find_element(By.ID, "generateBtn")
    generate_btn.click()
    
    # Wait for quiz to load
    print("  ⏳ Waiting for quiz to generate...")
    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, "question-container"))
        )
        print("  ✓ Quiz generated successfully")
    except Exception as e:
        print(f"  ✗ Error waiting for quiz: {e}")
    
    time.sleep(2)
    
    # Select answers and submit
    print("\n[Step 3] Selecting first answer and submitting...")
    options = driver.find_elements(By.CLASS_NAME, "option-button")
    if options:
        options[0].click()
        print("  ✓ Selected first option")
    
    time.sleep(1)
    
    # Submit quiz
    print("\n[Step 4] Submitting quiz...")
    submit_btn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "submitBtn"))
    )
    submit_btn.click()
    print("  ✓ Clicked Submit button")
    
    # Wait for alert
    time.sleep(3)
    print("\n[Step 5] Checking for error messages...")
    
    try:
        alert = driver.switch_to.alert
        alert_text = alert.text
        print(f"\n  🚨 ALERT MESSAGE DETECTED:")
        print(f"  MESSAGE: ''{alert_text}''")
        
        if "[object Object]" in alert_text:
            print("  ✗ ERROR: Message contains '[object Object]' - NOT READABLE")
        else:
            print("  ✓ ERROR MESSAGE IS READABLE")
        
        alert.accept()
        print("  ✓ Alert dismissed")
    except Exception as e:
        print(f"  ℹ No alert detected")
    
    # ========== TEST 2: Take Another Quiz ==========
    print("\n" + "=" * 80)
    print("TEST 2: 'TAKE ANOTHER QUIZ' BUTTON")
    print("=" * 80)
    
    time.sleep(2)
    
    try:
        print("\n[Step 1] Looking for 'Take Another Quiz' button...")
        another_quiz_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "anotherQuizBtn"))
        )
        print("  ✓ Button found")
        
        print("\n[Step 2] Clicking 'Take Another Quiz' button...")
        another_quiz_btn.click()
        print("  ✓ Button clicked")
        
        time.sleep(2)
        
        print("\n[Step 3] Verifying form appears...")
        form_screen = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "formScreen"))
        )
        
        if "active" in form_screen.get_attribute("class"):
            print("  ✓ Form screen is ACTIVE")
        
        print("\n✅ TEST 2 PASSED")
        
    except Exception as e:
        print(f"\n  ✗ Error: {e}")
        print("❌ TEST 2 FAILED")
    
finally:
    print("\n[INFO] Closing browser...")
    driver.quit()
    print("[INFO] Test completed")
