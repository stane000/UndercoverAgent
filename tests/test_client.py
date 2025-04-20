import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

@pytest.fixture
def create_driver():
    """Creates and returns a new WebDriver instance for each client."""
    driver = webdriver.Chrome()  # You can change this to Firefox, Edge, etc.
    driver.get("https://web-production-a2cf.up.railway.app/")
    yield driver
    driver.quit()

@pytest.mark.parametrize("client_id", range(1, 11))  # Simulate 10 clients
def test_create_room_per_client(client_id):
    """Each simulated client creates ONE room."""
    driver = webdriver.Chrome()  # Each test gets a new WebDriver instance
    driver.get("https://web-production-a2cf.up.railway.app/")

    room_name = f"Room{client_id}"
    host_name = f"Host{client_id}"

    # Fill out the form
    driver.find_element(By.NAME, "host").send_keys(host_name)
    driver.find_element(By.NAME, "room").send_keys(room_name)
    driver.find_element(By.TAG_NAME, "form").submit()

    time.sleep(2)  # Allow time for processing

    # Verify room creation
    room_elements = driver.find_elements(By.CSS_SELECTOR, "#activeRooms li strong")
    room_names = [room.text for room in room_elements]

    assert room_name in room_names, f"{room_name} not found!"

    print(f"✅ Client {client_id} successfully created {room_name}")

    driver.quit()  # Close browser instance


if __name__ == "__main__":
    pytest.main(["-s", __file__])  # Run the tests when executed as a standalone script