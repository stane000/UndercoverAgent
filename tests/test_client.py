

import subprocess
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
import time

# @pytest.mark.run_app
# def test_run_app():
#     app_process = subprocess.Popen(["python", "app.py"])
#     time.sleep(5)  # Wait for the app to start

#     driver = webdriver.Chrome()  # Or any WebDriver you're using
#     driver.get("http://localhost:5000")  # Replace with your app's URL
    
#     # Check the page title or elements to confirm the app is running
#     assert "Expected Title" in driver.title  # Replace with your expected title or element
#     print("Web app is running successfully!")



import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

@pytest.mark.parallel_run
@pytest.mark.parametrize("client_id", range(1, 11))  # Simulate 10 clients
def test_create_room_per_client(client_id):
    """Each simulated client creates ONE room and verifies it."""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run browser in headless mode for performance
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)

    try:
        driver.get("http://localhost:5000")

        room_name = f"Room{client_id}"
        host_name = f"Host{client_id}"

        # Fill out the form
        driver.find_element(By.NAME, "host").send_keys(host_name)
        driver.find_element(By.NAME, "room").send_keys(room_name)
        driver.find_element(By.TAG_NAME, "form").submit()

        # Wait until redirected page displays the correct <h1> with room name
        header = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "created-room")))
         
        assert header is not None, "Header element not found!"
        assert room_name in header.text, f"Room {room_name} not found in header!"

        # # Now navigate back to index page to verify the room is listed
        # driver.get("http://localhost:5000")

        # WebDriverWait(driver, 10).until(
        #     EC.presence_of_element_located((By.CSS_SELECTOR, "#activeRooms li strong"))
        # )
        # room_elements = driver.find_elements(By.CSS_SELECTOR, "#activeRooms li strong")
        # room_names = [room.text for room in room_elements]

        # assert room_name in room_names, f"{room_name} not found on the index page!"
        # print(f"✅ Client {client_id} successfully created and verified {room_name}")

    finally:
        driver.quit()


if __name__ == "__main__":
    pytest.main(["-m", "parallel_run", "-n", "10", __file__])
