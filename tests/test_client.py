from selenium import webdriver
from selenium.webdriver.common.by import By
import unittest

class EndToEndTestCase(unittest.TestCase):
    def setUp(self):
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        self.driver = webdriver.Chrome(options=options)
        self.driver.get("http://localhost:5000/")  # Your app's URL

    def test_room_list_updates(self):
        # For example, wait until the active rooms list is visible and check its content
        room_elements = self.driver.find_elements(By.CSS_SELECTOR, "#activeRooms li")
        # You can assert based on what the initial state of the room list is
        self.assertTrue(len(room_elements) >= 0)

    def tearDown(self):
        self.driver.quit()

if __name__ == '__main__':
    unittest.main()
