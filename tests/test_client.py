

import random
import string
from hypothesis import HealthCheck, Phase, given, settings,  strategies as st
import pytest
from functional import seq
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
import time

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

    finally:
        driver.quit()

# Hypothesis strategy for generating test cases
@st.composite
def invalid_inputs(draw):
    
    short = draw(st.text(alphabet=string.ascii_letters + string.digits, max_size=3)),  # To short
    with_space = draw(st.text(alphabet=string.ascii_letters + string.digits, min_size=4, max_size=8))  # Length 4-8 characters and contains at least one space
    with_space = with_space[:random.randrange(len(with_space))] + ' ' + with_space[random.randrange(len(with_space))+1:]
    return (draw(st.sampled_from([short, with_space])), draw(st.sampled_from([short, with_space])))

@pytest.fixture(scope="module")
def driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run browser in headless mode for performance
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    yield driver
    driver.quit()

@pytest.mark.room_form
@settings(deadline=None, max_examples=50, print_blob=True,
          phases=(Phase.explicit, Phase.reuse, Phase.generate, Phase.target), suppress_health_check=HealthCheck.all())
@given(parameters=invalid_inputs())
def test_form_submission(parameters, driver):

    host, room = parameters
    
    driver.get("http://localhost:5000")

    # Locate input fields and submit button
    driver.find_element(By.NAME, "host").clear()
    driver.find_element(By.NAME, "room").clear()

    driver.find_element(By.NAME, "host").send_keys(host)
    driver.find_element(By.NAME, "room").send_keys(room)
    driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

    time.sleep(2)  # Wait for the form to be processed

    ## Check for validation errors
    errors = driver.find_elements(By.CSS_SELECTOR, ':invalid')

    if errors:
        error_inputs = seq(errors).filter(lambda x: x.accessible_name == '4 to 8 characters, no spaces').to_list()
        assert len(error_inputs) == 2, f"Wrong number of error: expected 2. actual: {len(error_inputs)}"
    else:
        raise Exception("No Error, expected error")


if __name__ == "__main__":
    pytest.main(["-m", "room_form", __file__])
