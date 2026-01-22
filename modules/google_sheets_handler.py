import logging
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
import os
import json # jsonモジュールをインポート

from .logger import logger

# --- Configuration from user input ---
# Spreadsheet ID extracted from the URL: https://docs.google.com/spreadsheets/d/13Q4ovS5HKXh9qGnHMrePC9o8Gqute1HuBOvmJqW3cKo/edit?gid=0#gid=0
SHEET_ID = '13Q4ovS5HKXh9qGnHMrePC9o8Gqute1HuBOvmJqW3cKo'
WORKSHEET_NAME = 'log'
MIN_LOG_LEVEL = logging.INFO
# Key in st.secrets where the JSON credentials are stored
CREDENTIALS_KEY_IN_SECRETS = 'google_sheets'
# Key in st.session_state to retrieve the user ID
USER_ID_KEY_IN_SESSION_STATE = 'user_id' 

# --- Google Sheets Handler ---
class GoogleSheetsHandler(logging.Handler):
    def __init__(self, sheet_id, worksheet_name, credentials_key_in_secrets, min_level=logging.INFO):
        super().__init__(level=min_level)
        self.sheet_id = sheet_id
        self.worksheet_name = worksheet_name
        self.credentials_key_in_secrets = credentials_key_in_secrets
        self.client = None
        self.worksheet = None
        self._connect_to_sheets()

    def _connect_to_sheets(self):
        try:
            if not hasattr(st, 'secrets') or self.credentials_key_in_secrets not in st.secrets:
                logger.error(f"Credentials key '{self.credentials_key_in_secrets}' not found in Streamlit secrets. Cannot connect to Google Sheets.")
                return

            service_account_info = st.secrets[self.credentials_key_in_secrets]
            
            # Ensure the parsed data is a dictionary before passing to Credentials
            if not isinstance(service_account_info, dict):
                # Convert secrets proxy to a regular dict
                service_account_info = dict(service_account_info)
                logger.debug(f"Credentials for '{self.credentials_key_in_secrets}' loaded and converted to dictionary.")

            # Define scopes for Google Sheets and Drive
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive.file'
            ]
            
            # Use the parsed dictionary and scopes to create credentials
            credentials = Credentials.from_service_account_info(service_account_info, scopes=scopes)
            
            # Authorize gspread client
            self.client = gspread.authorize(credentials)
            
            # Open the spreadsheet and worksheet
            spreadsheet = self.client.open_by_key(self.sheet_id)
            self.worksheet = spreadsheet.worksheet(self.worksheet_name)
            
            # Check if worksheet is empty or headers are missing
            all_values = self.worksheet.get_all_values()
            if not all_values or len(all_values) == 0 or (len(all_values) > 0 and len(all_values[0]) == 0):
                 self.worksheet.append_row(["Timestamp", "User ID", "Category", "Message"])
                 logger.debug(f"Appended headers to empty or headerless worksheet '{self.worksheet_name}'.")

            logger.debug(f"Successfully connected to Google Sheet: ID='{self.sheet_id}', Worksheet='{self.worksheet_name}'")

        except gspread.exceptions.SpreadsheetNotFound:
            logger.error(f"Google Sheet not found. Please check the Sheet ID ('{self.sheet_id}') and ensure the service account has access.")
        except gspread.exceptions.WorksheetNotFound:
            logger.error(f"Worksheet '{self.worksheet_name}' not found in the spreadsheet. Please create it or check the name.")
        except Exception as e:
            logger.error(f"Failed to connect to Google Sheets or prepare worksheet: {e}")
            # Reset client and worksheet to prevent further errors
            self.client = None
            self.worksheet = None

    def emit(self, record):
        if self.client is None or self.worksheet is None:
            # Connection failed or worksheet not found, cannot emit logs
            return

        try:
            # Get user ID from session state. This assumes it's available.
            user_id = "N/A" # Default if not found
            if hasattr(st, 'session_state') and USER_ID_KEY_IN_SESSION_STATE in st.session_state and st.session_state[USER_ID_KEY_IN_SESSION_STATE]:
                user_id = str(st.session_state[USER_ID_KEY_IN_SESSION_STATE])
            
            # Format timestamp and get message
            # Use the formatter from the handler itself if available, otherwise use default
            if self.formatter:
                # Use the handler's formatter if it exists
                timestamp = self.formatter.formatTime(record, '%Y-%m-%d %H:%M:%S')
            else:
                # Fallback to a default formatter if none is set on the handler
                timestamp = logging.Formatter('%(asctime)s', '%Y-%m-%d %H:%M:%S').formatTime(record)
            
            message = record.getMessage()
            # Get category from the record, default to 'System'
            category = getattr(record, 'category', 'System')
            
            # Append row to the sheet
            self.worksheet.append_row([timestamp, user_id, category, message])
        except Exception as e:
            logger.error(f"Failed to append row to Google Sheet: {e}")

# --- Helper function to add the handler ---
def add_google_sheets_handler(logger_instance: logging.Logger, 
                              sheet_id: str, 
                              worksheet_name: str, 
                              credentials_key: str, 
                              min_level: int = logging.INFO):
    """
    Adds a GoogleSheetsHandler to the given logger instance.
    """
    # 既存のGoogleSheetsHandlerを削除して、重複や古いハンドラの残留を防ぐ
    for handler in logger_instance.handlers[:]: # ハンドラリストのコピーをイテレート
        if isinstance(handler, GoogleSheetsHandler):
            logger_instance.removeHandler(handler)
            logger.debug("Removed existing GoogleSheetsHandler.")

    handler = GoogleSheetsHandler(
        sheet_id=sheet_id,
        worksheet_name=worksheet_name,
        credentials_key_in_secrets=credentials_key,
        min_level=min_level
    )
    # Only add handler if connection was successful
    if handler.client and handler.worksheet:
        logger_instance.addHandler(handler)
        logger.debug("GoogleSheetsHandler added to logger.")
    else:
        logger.error("GoogleSheetsHandler was not added due to connection failure.")

