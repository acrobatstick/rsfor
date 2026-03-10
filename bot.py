from __future__ import annotations

import contextlib
import os
import time
from typing import TYPE_CHECKING

from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import Select, WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

if TYPE_CHECKING:
    import logging

    from config import Config
    from stage import Stage


class MaxAttemptsError(Exception):
    def __init__(self, action: str, attempts: int = 3) -> None:
        msg = f"Could not {action} after {attempts} attempts"
        super().__init__(msg)
        self.action = action
        self.attempts = attempts


class Bot:
    # TODO: add external configuration of the online rally TODO: run selenium on headless mode
    def __init__(self, logger: logging.Logger, config: Config) -> None:
        service = Service(ChromeDriverManager().install())
        self.logger = logger
        self.config = config
        self.driver = Chrome(service=service)  # type: ignore[operator]

    def run(self) -> None:
        try:
            self.login()
            self.step_rally()
            self.step_cars()
            self.step_legs()
            self.step_stages()
        finally:
            self.driver.quit()

    def login(self) -> None:
        username = os.getenv("RSF_USERNAME")
        password = os.getenv("RSF_PASSWORD")

        if not username or not password:
            self.logger.error("RSF username and password is required")
            return

        self.driver.get("https://rallysimfans.hu/rbr/account2.php?centerbox=bejelentkezes2")
        self.logger.info("Attempting to login with username: %s", username)

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
            self.logger.info("Logged in successfully")
            time.sleep(2)

        except TimeoutException:
            try:
                error_div = WebDriverWait(self.driver, 1).until(
                    ec.visibility_of_element_located((By.ID, "errorMessages"))
                )

                error_content = error_div.get_attribute("textContent")
                if error_content is None:
                    return

                self.logger.warning("Error: %s", error_content.strip())

            except TimeoutException:
                self.logger.warning("Neither login success nor error message found.")

    def step_rally(self) -> None:
        self.driver.get("https://rallysimfans.hu/rbr/rally_online.php?centerbox=create/rally_create.php&uj=true")
        self.wait_for_state()

        time.sleep(2)

        self.driver.find_element(By.NAME, "rally_name").send_keys(self.config.name)
        self.driver.find_element(By.NAME, "description").send_keys(self.config.description)
        self.driver.find_element(By.NAME, "password1").send_keys(self.config.password)
        self.driver.find_element(By.NAME, "password2").send_keys(self.config.password)

        damage_checkbox = self.driver.find_element(
            By.CSS_SELECTOR, f"input[name='damage_id'][value='{self.config.damage}']"
        )
        if not damage_checkbox.is_selected():
            damage_checkbox.click()

        Select(self.driver.find_element(By.NAME, "stages")).select_by_value(str(self.config.stage_count))
        Select(self.driver.find_element(By.NAME, "legs")).select_by_value(str(self.config.leg_count))
        Select(self.driver.find_element(By.NAME, "pacenotes_options")).select_by_value(str(self.config.pacenote_opt))
        Select(self.driver.find_element(By.NAME, "road_side_service")).select_by_value(
            str(self.config.roadside_service)
        )

        self.driver.find_element(
            By.CSS_SELECTOR,
            f"button[name='physics_ver'][value='{self.config.physics_ver}']",
        ).click()
        self.wait_for_state()

    def step_cars(self) -> None:
        for car_id in self.config.car_groups:
            try:
                option = self.driver.find_element(By.CSS_SELECTOR, f"select[name='group_id'] option[value='{car_id}']")
            except NoSuchElementException:
                # If group id not found. it may be a car id. select the car list check
                car_list_checkbox = self.driver.find_element(By.ID, "carlistCheck")
                if not car_list_checkbox.is_selected():
                    car_list_checkbox.click()
            try:
                # Redo selection
                option = self.driver.find_element(By.CSS_SELECTOR, f"select[name='group_id'] option[value='{car_id}']")
            except NoSuchElementException:
                self.logger.warning("Group/Car ID %s not found, skipping...", car_id)
                continue

            option.click()
            self.driver.find_element(By.CSS_SELECTOR, "input[type='button'][value='-->>']").click()

        time.sleep(2)

        self.click_next()
        self.wait_for_state()

    def step_legs(self) -> None:
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

    def step_stages(self) -> None:
        stages: list[Stage] = self.config.stages
        for i in range(int(self.config.stage_count)):
            s = stages.pop(0)
            found = False
            for surface_id in range(1, 4):
                # change stage surface filter to update the stage list
                self.driver.find_element(By.CSS_SELECTOR, f"button[id='surface_filter{surface_id}']").click()
                try:
                    stage_el = Select(self.driver.find_element(By.ID, "stage_list"))
                    stage_el.select_by_value(str(s.stage_id))
                    stage_name = stage_el.first_selected_option.text
                    self.logger.info("Selecting %s as stage no.%d", stage_name, i + 1)
                    found = True
                    break
                except NoSuchElementException:
                    self.logger.warning("Stage not found in surface type %d. Move to next filter", surface_id)
                    continue

            if not found:
                self.logger.error("Could not find stage with id %d", s.stage_id)
                return

            # NOTE: ignore wetness for now. use the default selection from stage weather instead
            with contextlib.suppress(NoSuchElementException):
                Select(self.driver.find_element(By.ID, "tracksettings_list")).select_by_value(s.weather)

            # NOTE: also ignore set tyre, allow setup change

            # handle not configuring some configurations cant be applied on last leg's stage
            if i < int(self.config.stage_count) - 1:
                # surface wear
                self.driver.find_element(By.CSS_SELECTOR, f"input[id='surface{s.surface_wear.value}']").click()

                Select(self.driver.find_element(By.ID, "service_time")).select_by_value(str(s.service_time))

            # to prevent flooding the online rally list. remove this if the program is fully working
            if i < int(self.config.stage_count) - 1:
                time.sleep(5)
                self.click_next()
                self.wait_for_state()

        time.sleep(10)

    def click_next(self) -> None:
        attempts = 0
        max_attemps = 3
        while attempts < max_attemps:
            with contextlib.suppress(StaleElementReferenceException):
                self.driver.find_element(By.CSS_SELECTOR, "input[class='button_1'][value='next']").click()
                return
            time.sleep(0.5)
            attempts += 1
        msg = "click next"
        raise MaxAttemptsError(msg)

    def wait_for_state(self) -> str | None:
        attempts = 0
        max_attempts = 3
        while attempts < max_attempts:
            with contextlib.suppress(StaleElementReferenceException):
                state = (
                    WebDriverWait(self.driver, 10)
                    .until(ec.presence_of_element_located((By.NAME, "state")))
                    .get_attribute("value")
                )
                self.logger.info("Entering %s form state", state)
                return state
            time.sleep(0.5)
            attempts += 1
        msg = "read state"
        raise MaxAttemptsError(msg)
