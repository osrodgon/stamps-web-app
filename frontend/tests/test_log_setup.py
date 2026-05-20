"""Unit tests for core/log_setup.py."""

import logging
import logging.config
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from core.log_setup import log_setup


class TestLogSetup:
    """Tests for the log_setup() function."""

    @patch("core.log_setup.logging.config.dictConfig")
    @patch("core.log_setup.Path.mkdir")
    @patch("core.log_setup.Path.is_absolute", return_value=False)
    def test_calls_dictConfig_with_version_1(
        self,
        mock_is_absolute: MagicMock,
        mock_mkdir: MagicMock,
        mock_dictConfig: MagicMock,
    ) -> None:
        """log_setup() passes version=1 to dictConfig."""
        log_setup()
        config = mock_dictConfig.call_args[0][0]
        assert config["version"] == 1

    @patch("core.log_setup.logging.config.dictConfig")
    @patch("core.log_setup.Path.mkdir")
    @patch("core.log_setup.Path.is_absolute", return_value=False)
    def test_creates_log_directory(
        self,
        mock_is_absolute: MagicMock,
        mock_mkdir: MagicMock,
        mock_dictConfig: MagicMock,
    ) -> None:
        """log_setup() creates the log directory with parents=True."""
        log_setup()
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    @patch("core.log_setup.logging.config.dictConfig")
    @patch("core.log_setup.Path.mkdir")
    @patch("core.log_setup.Path.is_absolute", return_value=False)
    def test_resolves_relative_path(
        self,
        mock_is_absolute: MagicMock,
        mock_mkdir: MagicMock,
        mock_dictConfig: MagicMock,
    ) -> None:
        """log_setup() resolves relative LOG_FILE_NAME under LOG_BASE_DIR."""
        log_setup()
        config = mock_dictConfig.call_args[0][0]
        filename = config["handlers"]["file"]["filename"]
        assert "logs" in filename
        assert "frontend.log" in filename

    @patch("core.log_setup.logging.config.dictConfig")
    @patch("core.log_setup.Path.mkdir")
    @patch("core.log_setup.Path.is_absolute", return_value=True)
    def test_handles_absolute_path(
        self,
        mock_is_absolute: MagicMock,
        mock_mkdir: MagicMock,
        mock_dictConfig: MagicMock,
    ) -> None:
        """log_setup() uses the path as-is when it is absolute."""
        log_setup()
        mock_dictConfig.assert_called_once()

    @patch("core.log_setup.logging.config.dictConfig")
    @patch("core.log_setup.Path.mkdir")
    @patch("core.log_setup.Path.is_absolute", return_value=False)
    def test_file_handler_uses_rotating_file_handler(
        self,
        mock_is_absolute: MagicMock,
        mock_mkdir: MagicMock,
        mock_dictConfig: MagicMock,
    ) -> None:
        """File handler class is RotatingFileHandler."""
        log_setup()
        config = mock_dictConfig.call_args[0][0]
        assert config["handlers"]["file"]["class"] == "logging.handlers.RotatingFileHandler"

    @patch("core.log_setup.logging.config.dictConfig")
    @patch("core.log_setup.Path.mkdir")
    @patch("core.log_setup.Path.is_absolute", return_value=False)
    def test_file_handler_max_bytes_5mb(
        self,
        mock_is_absolute: MagicMock,
        mock_mkdir: MagicMock,
        mock_dictConfig: MagicMock,
    ) -> None:
        """File handler maxBytes is 5 MB (5242880)."""
        log_setup()
        config = mock_dictConfig.call_args[0][0]
        assert config["handlers"]["file"]["maxBytes"] == 1024 * 1024 * 5

    @patch("core.log_setup.logging.config.dictConfig")
    @patch("core.log_setup.Path.mkdir")
    @patch("core.log_setup.Path.is_absolute", return_value=False)
    def test_file_handler_backup_count_5(
        self,
        mock_is_absolute: MagicMock,
        mock_mkdir: MagicMock,
        mock_dictConfig: MagicMock,
    ) -> None:
        """File handler keeps 5 backup files."""
        log_setup()
        config = mock_dictConfig.call_args[0][0]
        assert config["handlers"]["file"]["backupCount"] == 5

    @patch("core.log_setup.logging.config.dictConfig")
    @patch("core.log_setup.Path.mkdir")
    @patch("core.log_setup.Path.is_absolute", return_value=False)
    def test_file_handler_utf8_encoding(
        self,
        mock_is_absolute: MagicMock,
        mock_mkdir: MagicMock,
        mock_dictConfig: MagicMock,
    ) -> None:
        """File handler uses utf-8 encoding."""
        log_setup()
        config = mock_dictConfig.call_args[0][0]
        assert config["handlers"]["file"]["encoding"] == "utf-8"

    @patch("core.log_setup.logging.config.dictConfig")
    @patch("core.log_setup.Path.mkdir")
    @patch("core.log_setup.Path.is_absolute", return_value=False)
    def test_console_handler_is_stream_handler(
        self,
        mock_is_absolute: MagicMock,
        mock_mkdir: MagicMock,
        mock_dictConfig: MagicMock,
    ) -> None:
        """Console handler class is StreamHandler."""
        log_setup()
        config = mock_dictConfig.call_args[0][0]
        assert config["handlers"]["console"]["class"] == "logging.StreamHandler"

    @patch("core.log_setup.logging.config.dictConfig")
    @patch("core.log_setup.Path.mkdir")
    @patch("core.log_setup.Path.is_absolute", return_value=False)
    def test_console_uses_colored_formatter(
        self,
        mock_is_absolute: MagicMock,
        mock_mkdir: MagicMock,
        mock_dictConfig: MagicMock,
    ) -> None:
        """Console handler uses the colored_console formatter."""
        log_setup()
        config = mock_dictConfig.call_args[0][0]
        assert config["handlers"]["console"]["formatter"] == "colored_console"

    @patch("core.log_setup.logging.config.dictConfig")
    @patch("core.log_setup.Path.mkdir")
    @patch("core.log_setup.Path.is_absolute", return_value=False)
    def test_colored_formatter_uses_colorlog(
        self,
        mock_is_absolute: MagicMock,
        mock_mkdir: MagicMock,
        mock_dictConfig: MagicMock,
    ) -> None:
        """Colored formatter uses colorlog.ColoredFormatter."""
        log_setup()
        config = mock_dictConfig.call_args[0][0]
        formatter = config["formatters"]["colored_console"]
        assert formatter["()"] == "colorlog.ColoredFormatter"

    @patch("core.log_setup.logging.config.dictConfig")
    @patch("core.log_setup.Path.mkdir")
    @patch("core.log_setup.Path.is_absolute", return_value=False)
    def test_color_scheme_has_all_levels(
        self,
        mock_is_absolute: MagicMock,
        mock_mkdir: MagicMock,
        mock_dictConfig: MagicMock,
    ) -> None:
        """Color scheme maps all 5 log levels."""
        log_setup()
        config = mock_dictConfig.call_args[0][0]
        log_colors = config["formatters"]["colored_console"]["log_colors"]
        assert log_colors["DEBUG"] == "cyan"
        assert log_colors["INFO"] == "green"
        assert log_colors["WARNING"] == "yellow"
        assert log_colors["ERROR"] == "red"
        assert log_colors["CRITICAL"] == "red,bg_white"

    @patch("core.log_setup.logging.config.dictConfig")
    @patch("core.log_setup.Path.mkdir")
    @patch("core.log_setup.Path.is_absolute", return_value=False)
    def test_root_logger_has_file_and_console(
        self,
        mock_is_absolute: MagicMock,
        mock_mkdir: MagicMock,
        mock_dictConfig: MagicMock,
    ) -> None:
        """Root logger ('') has both file and console handlers."""
        log_setup()
        config = mock_dictConfig.call_args[0][0]
        root = config["loggers"][""]
        assert "file" in root["handlers"]
        assert "console" in root["handlers"]

    @patch("core.log_setup.logging.config.dictConfig")
    @patch("core.log_setup.Path.mkdir")
    @patch("core.log_setup.Path.is_absolute", return_value=False)
    def test_third_party_loggers_suppressed_to_warning(
        self,
        mock_is_absolute: MagicMock,
        mock_mkdir: MagicMock,
        mock_dictConfig: MagicMock,
    ) -> None:
        """Third-party loggers are set to WARNING level."""
        log_setup()
        config = mock_dictConfig.call_args[0][0]
        suppressed = [
            "watchfiles", "uvicorn.access", "urllib3",
            "asyncio", "flet", "flet_core", "flet_transport",
            "flet_controls", "flet_web",
        ]
        for logger_name in suppressed:
            assert config["loggers"][logger_name]["level"] == "WARNING"

    @patch("core.log_setup.logging.config.dictConfig")
    @patch("core.log_setup.Path.mkdir")
    @patch("core.log_setup.Path.is_absolute", return_value=False)
    def test_third_party_loggers_do_not_propagate(
        self,
        mock_is_absolute: MagicMock,
        mock_mkdir: MagicMock,
        mock_dictConfig: MagicMock,
    ) -> None:
        """Third-party loggers have propagate=False."""
        log_setup()
        config = mock_dictConfig.call_args[0][0]
        suppressed = [
            "watchfiles", "uvicorn.access", "urllib3",
            "asyncio", "flet", "flet_core", "flet_transport",
            "flet_controls", "flet_web",
        ]
        for logger_name in suppressed:
            assert config["loggers"][logger_name]["propagate"] is False

    @patch("core.log_setup.logging.config.dictConfig")
    @patch("core.log_setup.Path.mkdir")
    @patch("core.log_setup.Path.is_absolute", return_value=False)
    def test_disable_existing_loggers_false(
        self,
        mock_is_absolute: MagicMock,
        mock_mkdir: MagicMock,
        mock_dictConfig: MagicMock,
    ) -> None:
        """Config sets disable_existing_loggers to False."""
        log_setup()
        config = mock_dictConfig.call_args[0][0]
        assert config["disable_existing_loggers"] is False

    @patch("core.log_setup.logging.config.dictConfig")
    @patch("core.log_setup.Path.mkdir")
    @patch("core.log_setup.Path.is_absolute", return_value=False)
    def test_standard_formatter_pattern(
        self,
        mock_is_absolute: MagicMock,
        mock_mkdir: MagicMock,
        mock_dictConfig: MagicMock,
    ) -> None:
        """Standard formatter includes asctime,levelname,name,funcName."""
        log_setup()
        config = mock_dictConfig.call_args[0][0]
        fmt = config["formatters"]["standard"]["format"]
        assert "%(asctime)s" in fmt
        assert "%(levelname)s" in fmt
        assert "%(name)s" in fmt
        assert "%(funcName)s" in fmt
