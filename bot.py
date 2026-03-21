from __future__ import annotations

import contextlib
import sys
import time
from typing import TYPE_CHECKING

from selenium.common.exceptions import (
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import WebDriver as Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import Select, WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from stage import Surface, Tyre, Wetness

if TYPE_CHECKING:
    import logging

    from selenium.webdriver.remote.webelement import WebElement

    from config import Config
    from stage import Stage


class MaxAttemptsError(Exception):
    def __init__(self, action: str, attempts: int = 3) -> None:
        msg = f"Could not {action} after {attempts} attempts"
        super().__init__(msg)
        self.action = action
        self.attempts = attempts


class Bot:
    def __init__(self, logger: logging.Logger, config: Config) -> None:
        service = Service(ChromeDriverManager().install())
        self.logger = logger
        self.config = config
        self.driver = Chrome(service=service)

    def run(self, creds: tuple[str, str]) -> None:
        try:
            self._login(creds)
            self._step_rally()
            self._step_cars()
            self._step_legs()
            self._step_stages()
        finally:
            self.driver.quit()

    def _login(self, creds: tuple[str, str]) -> None:
        username = creds[0]
        password = creds[1]

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
                    self.logger.warning("Login failed")
                    sys.exit(1)

                self.logger.warning("Error: %s", error_content.strip())
                sys.exit(1)

            except TimeoutException:
                self.logger.fatal("Neither login success nor error message found.")
                sys.exit(1)

    def _step_rally(self) -> None:
        self.driver.get("https://rallysimfans.hu/rbr/rally_online.php?centerbox=create/rally_create.php&uj=true")
        self._wait_for_state()

        time.sleep(2)

        self.logger.info("Initializing rally: %s", self.config.name)

        self.driver.find_element(By.NAME, "rally_name").send_keys(self.config.name)
        self.driver.find_element(By.NAME, "description").send_keys(self.config.description)

        self.driver.find_element(By.NAME, "password1").send_keys(self.config.password)
        self.driver.find_element(By.NAME, "password2").send_keys(self.config.password)

        damage_checkbox = self.driver.find_element(
            By.CSS_SELECTOR, f"input[name='damage_id'][value='{self.config.damage.value}']"
        )
        if not damage_checkbox.is_selected():
            damage_checkbox.click()

        Select(self.driver.find_element(By.NAME, "stages")).select_by_value(str(self.config.stage_count))
        Select(self.driver.find_element(By.NAME, "legs")).select_by_value(str(self.config.leg_count))
        Select(self.driver.find_element(By.NAME, "pacenotes_options")).select_by_value(
            str(self.config.pacenote_opt.value)
        )
        Select(self.driver.find_element(By.NAME, "road_side_service")).select_by_value(
            str(self.config.roadside_service)
        )

        self.driver.find_element(
            By.CSS_SELECTOR,
            f"button[name='physics_ver'][value='{self.config.physics_ver}']",
        ).click()
        self._wait_for_state()

    def _find_car_option(self, cid: str) -> WebElement | None:
        options = self.driver.find_elements(By.CSS_SELECTOR, "select[name='group_id'] option")
        return next((o for o in options if o.get_attribute("value") == cid or o.text.strip() == cid), None)

    def _step_cars(self) -> None:
        for cid in self.config.car_groups:
            option = self._find_car_option(cid)

            if option is None:
                car_list_checkbox = self.driver.find_element(By.ID, "carlistCheck")
                # if the first car id is nowhere to be found, expand the car options
                if not car_list_checkbox.is_selected():
                    car_list_checkbox.click()
                # redo the search again
                option = self._find_car_option(cid)

            if option is None:
                self.logger.error(
                    "Car Groups: ID %r not found, see https://github.com/acrobatstick/rsfor/tree/main?tab=readme-ov-file#groupcar-ids",
                    cid,
                )
                sys.exit(1)

            self.logger.info("Car Groups: %s selected", cid)
            option.click()
            self.driver.find_element(By.CSS_SELECTOR, "input[type='button'][value='-->>']").click()

        time.sleep(2)

        self._click_next()
        self._wait_for_state()

    def _step_legs(self) -> None:
        start_at_list = self.config.generate_legs_start_at()
        at_leg = 1
        while at_leg < self.config.leg_count + 1:
            if at_leg != 1:
                start_at = start_at_list.pop(0)
                self.logger.info("Legs: Leg %d started at stage %d", at_leg, start_at)
                Select(self.driver.find_element(By.NAME, "start_stage_no")).select_by_value(str(start_at))

            # look for superrally at the second leg. I personally don't know why
            # they done this not on the first form step
            if at_leg == 2 and self.config.super_rally:
                Select(self.driver.find_element(By.NAME, "super_rally")).select_by_value("150")

            if self.config.open_time is not None and self.config.close_time:
                open_time = self.driver.find_element(By.NAME, "open_time")
                open_time.clear()
                open_time.send_keys(self.config.datetime_tostr(self.config.open_time))

                close_time = self.driver.find_element(By.NAME, "close_time")
                close_time.clear()
                close_time.send_keys(self.config.datetime_tostr(self.config.close_time))
            else:
                self.logger.warning("Leg open or close time is not provided, using default time")

            time.sleep(5)
            self._click_next()
            self._wait_for_state()
            at_leg += 1
        self._wait_for_state()

    def _select_stage(self, s: Stage, i: int) -> str:
        for surface_id in range(1, 4):
            # change stage surface filter to update the stage list
            self.driver.find_element(By.CSS_SELECTOR, f"button[id='surface_filter{surface_id}']").click()
            stage_el = Select(self.driver.find_element(By.ID, "stage_list"))
            time.sleep(0.5)
            option = next((o for o in stage_el.options if o.get_attribute("value") == str(s.id)), None)
            if option is not None:
                stage_el.select_by_value(str(s.id))
                time.sleep(0.5)
                name = Select(self.driver.find_element(By.ID, "stage_list")).first_selected_option.text
                self.logger.info("Stages(%d): %s selected", i + 1, name)
                return name
            self.logger.debug("Stages: id %d not found in surface type %d, moving to next filter", s.id, surface_id)

        self.logger.error("Stages: Could not find stage with id %d, see https://rallysimfans.hu/rbr/stages.php", s.id)
        sys.exit(1)

    def _select_weather_settings(self, s: Stage) -> None:
        sel = Select(self.driver.find_element(By.ID, "tracksettings_list"))
        weather_words = set(s.weather.lower().split())
        # must compare it set from both weather in the rally page and the weather list inside
        # the stage settings. again, i dont understand the inconsistency from the developers lol.
        option = next((o for o in sel.options if set(o.text.lower().split()) == weather_words), None)
        if option is not None:
            sel.select_by_visible_text(option.text)
        else:
            self.logger.warning(
                "Stages: Weather preset %r not found, skipping weather selection (using default)",
                s.weather,
            )

    def _select_wetness(self, s: Stage) -> None:
        if s.wetness != Wetness.Auto:
            sel = Select(self.driver.find_element(By.NAME, "wetness_id"))
            option = next((o for o in sel.options if o.get_attribute("value") == str(s.wetness.value)), None)
            if option is not None:
                sel.select_by_value(str(s.wetness.value))
            else:
                self.logger.warning("Stages: Wetness %r not found, skipping...", s.wetness)

    def _step_stages(self) -> None:
        stages = self.config.stages()
        for i in range(int(self.config.stage_count)):
            s = stages.pop(0)

            self._select_stage(s, i)
            self._select_weather_settings(s)
            self._select_wetness(s)

            tyre_checkbox = self.driver.find_element(By.NAME, "choose_tyre")
            if tyre_checkbox.is_selected() != s.allow_tyre_change:
                tyre_checkbox.click()

            setup_checkbox = self.driver.find_element(By.NAME, "choose_setup")
            if setup_checkbox.is_selected() != s.allow_setup_change:
                setup_checkbox.click()

            if s.set_tyre != Tyre.Auto:
                tyre_select = Select(self.driver.find_element(By.NAME, "def_tyre_id"))
                default = tyre_select.first_selected_option.text
                if i + 1 in self.config.generate_legs_start_at() and s.set_tyre == Tyre.Keep_Previous:
                    self.logger.warning("Could not keep previous tyre in new leg, using default: %r", default)
                else:
                    tyre_select.select_by_value(str(s.set_tyre.value))

            # handle not configuring some configurations cant be applied on last leg's stage
            if i < int(self.config.stage_count) - 1:
                # surface wear
                if s.surface_wear != Surface.Auto:
                    self.driver.find_element(By.CSS_SELECTOR, f"input[id='surface{s.surface_wear.value}']").click()
                Select(self.driver.find_element(By.ID, "service_time")).select_by_value(str(s.service_time))

            # to prevent flooding the online rally list. remove this if the program is fully working
            if i < int(self.config.stage_count) - 1:
                time.sleep(5)
                self._click_next()
                self._wait_for_state()

        time.sleep(10)

    def _click_next(self) -> None:
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

    def _wait_for_state(self) -> str | None:
        attempts = 0
        max_attempts = 3
        while attempts < max_attempts:
            with contextlib.suppress(StaleElementReferenceException):
                state = (
                    WebDriverWait(self.driver, 10)
                    .until(ec.presence_of_element_located((By.NAME, "state")))
                    .get_attribute("value")
                )
                self.logger.debug("Entering %s form state", state)
                return state
            time.sleep(0.5)
            attempts += 1
        msg = "read state"
        raise MaxAttemptsError(msg)
