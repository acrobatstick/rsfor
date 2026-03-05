from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
)
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from config import Config
from stage import Stage

import os
import time
import logging


class Bot:
    # TODO: add external configuration of the online rally TODO: run selenium on headless mode
    def __init__(self, logger: logging.Logger, config: Config):
        service = Service(ChromeDriverManager().install())
        self.logger = logger
        self.config = config
        self.driver = webdriver.Chrome(service=service)

    def run(self):
        try:
            self.login()
            self.step_rally()
            self.step_cars()
            self.step_legs()
            self.step_stages()
        finally:
            self.driver.quit()

    def login(self):
        username = os.getenv("RSF_USERNAME")
        password = os.getenv("RSF_PASSWORD")

        if not username or not password:
            raise RuntimeError("RSF_USERNAME and RSF_PASSWORD must be set")

        self.driver.get(
            "https://rallysimfans.hu/rbr/account2.php?centerbox=bejelentkezes2"
        )

        self.logger.info(f"Attempting to login with username: {username}")

        # Login step
        l_username = self.driver.find_element(By.ID, "l_username")
        l_username.send_keys(username)

        l_pass = self.driver.find_element(By.ID, "l_pass")
        l_pass.send_keys(password)

        login_btn = self.driver.find_element(By.ID, "loginButton")
        login_btn.click()

        # TODO: handle if captcha is turned on

        # Check if authorized after login submission by looking for
        # logged in RSF username
        try:
            logged_username = (
                WebDriverWait(self.driver, 5)
                .until(
                    EC.visibility_of_element_located((By.CLASS_NAME, "menue_inactive"))
                )
                .text
            )

            self.logger.info("Logged in successfully")
            time.sleep(2)

        except TimeoutException:
            try:
                error_div = WebDriverWait(self.driver, 1).until(
                    EC.visibility_of_element_located((By.ID, "errorMessages"))
                )

                self.logger.warn(
                    "Error:", error_div.get_attribute("textContent").strip()
                )

            except TimeoutException:
                self.loggger.warn("Neither login success nor error message found.")

    def step_rally(self):
        self.driver.get(
            "https://rallysimfans.hu/rbr/rally_online.php?centerbox=create/rally_create.php&uj=true"
        )
        self.wait_for_state()

        time.sleep(2)

        self.driver.find_element(By.NAME, "rally_name").send_keys(self.config.name)
        self.driver.find_element(By.NAME, "description").send_keys(
            self.config.description
        )
        self.driver.find_element(By.NAME, "password1").send_keys(self.config.password)
        self.driver.find_element(By.NAME, "password2").send_keys(self.config.password)

        damage_checkbox = self.driver.find_element(
            By.CSS_SELECTOR, f"input[name='damage_id'][value='{self.config.damage}']"
        )
        if not damage_checkbox.is_selected():
            damage_checkbox.click()

        Select(self.driver.find_element(By.NAME, "stages")).select_by_value(
            str(self.config.stage_count)
        )
        Select(self.driver.find_element(By.NAME, "legs")).select_by_value(
            str(self.config.leg_count)
        )
        Select(self.driver.find_element(By.NAME, "pacenotes_options")).select_by_value(
            str(self.config.pacenote_opt)
        )
        Select(self.driver.find_element(By.NAME, "road_side_service")).select_by_value(
            str(self.config.roadside_service)
        )

        self.driver.find_element(
            By.CSS_SELECTOR,
            f"button[name='physics_ver'][value='{self.config.physics_ver}']",
        ).click()
        self.wait_for_state()

    def step_cars(self):
        for id in self.config.car_ids:
            try:
                option = self.driver.find_element(
                    By.CSS_SELECTOR, f"select[name='group_id'] option[value='{id}']"
                )
            except NoSuchElementException:
                # If group id not found. it may be a car id. select the car list check
                carlistCheck = self.driver.find_element(By.ID, "carlistCheck")
                if not carlistCheck.is_selected():
                    carlistCheck.click()
            try:
                # Redo selection
                option = self.driver.find_element(
                    By.CSS_SELECTOR, f"select[name='group_id'] option[value='{id}']"
                )
            except NoSuchElementException:
                self.logger.warn(f"Group/Car ID {id} not found, skipping...")
                continue

            option.click()
            self.driver.find_element(
                By.CSS_SELECTOR, "input[type='button'][value='-->>']"
            ).click()

        time.sleep(2)

        self.click_next()
        self.wait_for_state()

    def step_legs(self):
        step = 1
        while step < self.config.leg_count:
            # TODO: handle leg open/close time from config
            time.sleep(1)
            self.click_next()
            self.wait_for_state()
            step += 1

        # TODO: handle super rally and whatever "Leg starts at stage" is from configuration
        # TODO: handle overall leg configuration on last leg step submission
        # TODO: convert timezone provided in configuration to hungary timezone
        self.click_next()
        self.wait_for_state()

    def step_stages(self):
        stages: list[Stage] = self.config.stages
        for i in range(int(self.config.stage_count)):
            stage = stages.pop(0)
            found = False
            for filter in range(1, 4):
                # change stage surface filter to update the stage list
                self.driver.find_element(
                    By.CSS_SELECTOR, f"button[id='surface_filter{filter}']"
                ).click()
                try:
                    stage_el = Select(self.driver.find_element(By.ID, "stage_list"))
                    stage_el.select_by_value(str(stage.stage_id))
                    stage_name = stage_el.first_selected_option.text
                    self.logger.info(f"Selecting {stage_name} as stage no.{i+1}")
                    found = True
                    break
                except NoSuchElementException:
                    self.logger.warning(
                        f"Stage not found in surface type {filter}. Move to next filter"
                    )
                    continue

            if not found:
                raise RuntimeError(f"Could not find stage with id {current_stage_id}")

            # NOTE: ignore wetness for now. use the default selection from stage weather instead
            try:
                Select(
                    self.driver.find_element(By.ID, "tracksettings_list")
                ).select_by_value(stage.weather)
            except NoSuchElementException:
                # use the default value generated from selecting the stage
                pass

            # NOTE: also ignore set tyre, allow setup change

            # handle not configuring some configurations cant be applied on last leg's stage
            if i < int(self.config.stage_count) - 1:
                # surface wear
                self.driver.find_element(
                    By.CSS_SELECTOR, f"input[id='surface{stage.wear}']"
                ).click()

                Select(self.driver.find_element(By.ID, "service_time")).select_by_value(
                    str(stage.service_time)
                )

            # to prevent flooding the online rally list. remove this if the program is fully working
            if i < int(self.config.stage_count) - 1:
                time.sleep(5)
                self.click_next()
                self.wait_for_state()

        time.sleep(10)

    def click_next(self):
        for attempt in range(3):
            try:
                self.driver.find_element(
                    By.CSS_SELECTOR, "input[class='button_1'][value='next']"
                ).click()
                return
            except StaleElementReferenceException:
                time.sleep(0.5)
        raise Exception("Could not click next button after 3 attempts")

    def wait_for_state(self):
        for attempt in range(3):
            try:
                state = (
                    WebDriverWait(self.driver, 10)
                    .until(EC.presence_of_element_located((By.NAME, "state")))
                    .get_attribute("value")
                )
                self.logger.info(f"Entering {state} form state")
                return state
            except StaleElementReferenceException:
                time.sleep(0.5)
        raise Exception("Could not read state after 3 attempts")
