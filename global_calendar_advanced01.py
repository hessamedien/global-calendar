#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Global Calendar by Hessamedien
Developer: Hessamedien
Instagram: https://instagram.com/hessamedien
Version: 2.0.0
Advanced Multi-Calendar System with Simultaneous Display
"""

import sys
import os
import json
import time
import threading
import webbrowser
import datetime
import calendar as py_calendar
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
import tkinter as tk
from tkinter import ttk, messagebox, font, filedialog, simpledialog, colorchooser
from tkinter import PhotoImage
from PIL import Image, ImageTk, ImageDraw, ImageFont
import requests
from bs4 import BeautifulSoup
import jdatetime
import hijri_converter
import pytz
import math
from functools import lru_cache
import winsound
import socket
from urllib.request import urlopen
import urllib.error
from dataclasses import dataclass
from enum import Enum
import itertools

# ============================================================================
# Enums and Data Classes
# ============================================================================

class CalendarType(Enum):
    GREGORIAN = "gregorian"
    PERSIAN = "persian"
    ISLAMIC = "islamic"
    CHINESE = "chinese"
    HINDI = "hindi"
    HEBREW = "hebrew"
    JAPANESE = "japanese"
    KOREAN = "korean"
    INDIAN = "indian"

class DisplayMode(Enum):
    STANDARD = "standard"
    COMPACT = "compact"
    MINIMAL = "minimal"
    DETAILED = "detailed"

class ThemeMode(Enum):
    DARK = "dark"
    LIGHT = "light"
    BLUE = "blue"
    GREEN = "green"
    PURPLE = "purple"
    AUTO = "auto"

@dataclass
class CalendarConfig:
    """Configuration for a single calendar"""
    type: CalendarType
    enabled: bool = True
    show_events: bool = True
    show_holidays: bool = True
    color: str = "#0078d4"
    position: str = "top-left"  # top-left, top-right, bottom-left, bottom-right
    
@dataclass
class DisplayConfig:
    """Display configuration"""
    primary_calendar: CalendarType = CalendarType.GREGORIAN
    secondary_calendars: List[CalendarType] = None
    display_mode: DisplayMode = DisplayMode.STANDARD
    theme: ThemeMode = ThemeMode.AUTO
    show_week_numbers: bool = True
    show_moon_phases: bool = False
    show_sun_times: bool = True
    show_multiple_dates: bool = True
    date_size: int = 14  # Font size for dates
    secondary_date_size: int = 9  # Font size for secondary dates
    
    def __post_init__(self):
        if self.secondary_calendars is None:
            self.secondary_calendars = [CalendarType.PERSIAN, CalendarType.ISLAMIC]

# ============================================================================
# Helper Classes
# ============================================================================

class MultiCalendarConverter:
    """Converter for multiple calendar systems"""
    
    def __init__(self):
        self.cache = {}
        
    def convert_date(self, year: int, month: int, day: int, 
                    from_cal: CalendarType, to_cal: CalendarType) -> Tuple[int, int, int]:
        """Convert date between calendars"""
        cache_key = f"{from_cal.value}_{to_cal.value}_{year}_{month}_{day}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # First convert to Gregorian as intermediate
        if from_cal != CalendarType.GREGORIAN:
            gregorian = self._to_gregorian(year, month, day, from_cal)
        else:
            gregorian = (year, month, day)
        
        # Then convert to target calendar
        if to_cal != CalendarType.GREGORIAN:
            result = self._from_gregorian(*gregorian, to_cal)
        else:
            result = gregorian
        
        self.cache[cache_key] = result
        return result
    
    def _to_gregorian(self, year: int, month: int, day: int, cal_type: CalendarType) -> Tuple[int, int, int]:
        """Convert from various calendars to Gregorian"""
        try:
            if cal_type == CalendarType.PERSIAN:
                gd = jdatetime.date(year, month, day).togregorian()
                return gd.year, gd.month, gd.day
            
            elif cal_type == CalendarType.ISLAMIC:
                gregorian = hijri_converter.Hijri(year, month, day).to_gregorian()
                return gregorian.year, gregorian.month, gregorian.day
            
            elif cal_type == CalendarType.CHINESE:
                # Simplified conversion for Chinese calendar
                # Note: This is approximate, not precise
                chinese_to_gregorian_offset = 2637  # Approximate offset
                gregorian_year = year + chinese_to_gregorian_offset
                return gregorian_year, month, day
            
            elif cal_type == CalendarType.HINDI or cal_type == CalendarType.INDIAN:
                # Simplified conversion for Indian national calendar
                # Vikram Samvat to Gregorian: VS + 57 = Gregorian
                gregorian_year = year + 57
                return gregorian_year, month, day
            
            elif cal_type == CalendarType.HEBREW:
                # Simplified conversion (not precise)
                # Hebrew year - 3760 = Gregorian year (approx)
                gregorian_year = year - 3760
                return gregorian_year, month, day
            
            elif cal_type == CalendarType.JAPANESE:
                # Japanese year + 1988 = Gregorian year for Heisei era
                # This is simplified
                gregorian_year = year + 1988
                return gregorian_year, month, day
            
            elif cal_type == CalendarType.KOREAN:
                # Korean year + 2333 = Gregorian year
                gregorian_year = year + 2333
                return gregorian_year, month, day
            
            else:
                return year, month, day
                
        except Exception:
            return year, month, day
    
    def _from_gregorian(self, year: int, month: int, day: int, cal_type: CalendarType) -> Tuple[int, int, int]:
        """Convert from Gregorian to various calendars"""
        try:
            if cal_type == CalendarType.PERSIAN:
                jd = jdatetime.date.fromgregorian(year=year, month=month, day=day)
                return jd.year, jd.month, jd.day
            
            elif cal_type == CalendarType.ISLAMIC:
                hijri = hijri_converter.Hijri.fromgregorian(year, month, day)
                return hijri.year, hijri.month, hijri.day
            
            elif cal_type == CalendarType.CHINESE:
                # Simplified conversion
                chinese_year = year - 2637  # Approximate
                return chinese_year, month, day
            
            elif cal_type == CalendarType.HINDI or cal_type == CalendarType.INDIAN:
                # Indian national calendar
                indian_year = year - 57
                return indian_year, month, day
            
            elif cal_type == CalendarType.HEBREW:
                # Simplified conversion
                hebrew_year = year + 3760
                return hebrew_year, month, day
            
            elif cal_type == CalendarType.JAPANESE:
                japanese_year = year - 1988
                return japanese_year, month, day
            
            elif cal_type == CalendarType.KOREAN:
                korean_year = year - 2333
                return korean_year, month, day
            
            else:
                return year, month, day
                
        except Exception:
            return year, month, day
    
    def get_all_calendar_dates(self, year: int, month: int, day: int, 
                              primary_cal: CalendarType,
                              secondary_cals: List[CalendarType]) -> Dict[str, Tuple[int, int, int]]:
        """Get dates in all selected calendars"""
        result = {}
        
        # Get primary calendar date
        result[primary_cal.value] = (year, month, day)
        
        # Convert to Gregorian first (if not already Gregorian)
        if primary_cal != CalendarType.GREGORIAN:
            greg_year, greg_month, greg_day = self._to_gregorian(year, month, day, primary_cal)
        else:
            greg_year, greg_month, greg_day = year, month, day
        
        # Convert to each secondary calendar
        for cal in secondary_cals:
            if cal != primary_cal:
                try:
                    cal_date = self._from_gregorian(greg_year, greg_month, greg_day, cal)
                    result[cal.value] = cal_date
                except:
                    result[cal.value] = (0, 0, 0)
        
        return result
    
    def get_calendar_names(self) -> Dict[CalendarType, str]:
        """Get display names for all calendars"""
        return {
            CalendarType.GREGORIAN: "Gregorian",
            CalendarType.PERSIAN: "Persian (Solar Hijri)",
            CalendarType.ISLAMIC: "Islamic (Lunar Hijri)",
            CalendarType.CHINESE: "Chinese",
            CalendarType.HINDI: "Hindi",
            CalendarType.INDIAN: "Indian National",
            CalendarType.HEBREW: "Hebrew",
            CalendarType.JAPANESE: "Japanese",
            CalendarType.KOREAN: "Korean"
        }

class CalendarEventManager:
    """Manager for calendar events and holidays"""
    
    def __init__(self):
        self.events = {}
        self.holidays = {}
        self.api_client = CalendarAPI()
    
    def load_events(self, year: int, calendars: List[CalendarType]):
        """Load events for multiple calendars"""
        for cal in calendars:
            try:
                events = self.api_client.get_events(year, cal.value)
                self.events[cal.value] = events
                
                # Extract holidays
                holidays = [e for e in events if e.get('type') in ['national', 'religious', 'holiday']]
                self.holidays[cal.value] = holidays
            except Exception as e:
                print(f"Error loading events for {cal.value}: {e}")
                self.events[cal.value] = []
                self.holidays[cal.value] = []
    
    def get_events_for_date(self, date_key: str, calendar_type: str) -> List[Dict]:
        """Get events for a specific date"""
        events = self.events.get(calendar_type, [])
        return [e for e in events if e.get('date') == date_key]
    
    def get_holidays_for_date(self, date_key: str, calendar_type: str) -> List[Dict]:
        """Get holidays for a specific date"""
        holidays = self.holidays.get(calendar_type, [])
        return [h for h in holidays if h.get('date') == date_key]

class CalendarAPI:
    """API client for fetching calendar events"""
    
    def __init__(self):
        self.base_url = "https://www.timeanddate.com"
        self.cache = {}
    
    def get_events(self, year: int, calendar_type: str) -> List[Dict]:
        """Get events for a specific year and calendar type"""
        cache_key = f"{calendar_type}_{year}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            events = self._fetch_events(year, calendar_type)
            self.cache[cache_key] = events
            return events
        except Exception as e:
            print(f"Error fetching events: {e}")
            return self._get_default_events(year, calendar_type)
    
    def _fetch_events(self, year: int, calendar_type: str) -> List[Dict]:
        """Fetch events from online sources"""
        events = []
        
        # Add default events based on calendar type
        if calendar_type == CalendarType.PERSIAN.value:
            events = self._get_persian_events(year)
        elif calendar_type == CalendarType.GREGORIAN.value:
            events = self._get_gregorian_events(year)
        elif calendar_type == CalendarType.ISLAMIC.value:
            events = self._get_islamic_events(year)
        elif calendar_type == CalendarType.CHINESE.value:
            events = self._get_chinese_events(year)
        elif calendar_type == CalendarType.HINDI.value:
            events = self._get_hindi_events(year)
        
        # Try to fetch additional events from online
        try:
            online_events = self._fetch_online_events(year, calendar_type)
            events.extend(online_events)
        except:
            pass
        
        return events
    
    def _fetch_online_events(self, year: int, calendar_type: str) -> List[Dict]:
        """Fetch events from online API"""
        events = []
        
        # This is a simplified version - in production, use proper API
        # For now, return empty list
        return events
    
    def _get_persian_events(self, year: int) -> List[Dict]:
        """Get Persian calendar events"""
        events = [
            {"date": f"{year}/1/1", "title": "Nowruz (Persian New Year)", "type": "national"},
            {"date": f"{year}/1/2", "title": "Nowruz Holiday", "type": "national"},
            {"date": f"{year}/1/3", "title": "Nowruz Holiday", "type": "national"},
            {"date": f"{year}/1/4", "title": "Nowruz Holiday", "type": "national"},
            {"date": f"{year}/1/12", "title": "Islamic Republic Day", "type": "national"},
            {"date": f"{year}/1/13", "title": "Nature Day", "type": "national"},
            {"date": f"{year}/3/14", "title": "Demise of Imam Khomeini", "type": "religious"},
            {"date": f"{year}/3/15", "title": "Khordad 15 Uprising", "type": "national"},
            {"date": f"{year}/11/22", "title": "Islamic Revolution Day", "type": "national"},
        ]
        return events
    
    def _get_gregorian_events(self, year: int) -> List[Dict]:
        """Get Gregorian calendar events"""
        events = [
            {"date": f"{year}/1/1", "title": "New Year's Day", "type": "international"},
            {"date": f"{year}/12/25", "title": "Christmas Day", "type": "international"},
            {"date": f"{year}/12/31", "title": "New Year's Eve", "type": "international"},
        ]
        return events
    
    def _get_islamic_events(self, year: int) -> List[Dict]:
        """Get Islamic calendar events"""
        events = [
            {"date": f"{year}/1/1", "title": "Islamic New Year", "type": "religious"},
            {"date": f"{year}/1/10", "title": "Day of Ashura", "type": "religious"},
            {"date": f"{year}/3/12", "title": "Prophet's Birthday", "type": "religious"},
            {"date": f"{year}/7/27", "title": "Isra and Mi'raj", "type": "religious"},
            {"date": f"{year}/9/1-30", "title": "Ramadan", "type": "religious"},
            {"date": f"{year}/10/1", "title": "Eid al-Fitr", "type": "religious"},
            {"date": f"{year}/12/10", "title": "Eid al-Adha", "type": "religious"},
        ]
        return events
    
    def _get_chinese_events(self, year: int) -> List[Dict]:
        """Get Chinese calendar events"""
        events = [
            {"date": f"{year}/1/1", "title": "Chinese New Year", "type": "national"},
            {"date": f"{year}/1/15", "title": "Lantern Festival", "type": "national"},
            {"date": f"{year}/4/5", "title": "Qingming Festival", "type": "national"},
            {"date": f"{year}/5/5", "title": "Dragon Boat Festival", "type": "national"},
            {"date": f"{year}/8/15", "title": "Mid-Autumn Festival", "type": "national"},
        ]
        return events
    
    def _get_hindi_events(self, year: int) -> List[Dict]:
        """Get Hindi calendar events"""
        events = [
            {"date": f"{year}/1/1", "title": "Hindi New Year", "type": "national"},
            {"date": f"{year}/1/14", "title": "Makar Sankranti", "type": "religious"},
            {"date": f"{year}/2/24", "title": "Maha Shivaratri", "type": "religious"},
            {"date": f"{year}/3/8", "title": "Holi", "type": "religious"},
            {"date": f"{year}/8/15", "title": "Independence Day", "type": "national"},
            {"date": f"{year}/10/2", "title": "Gandhi Jayanti", "type": "national"},
            {"date": f"{year}/10/24", "title": "Diwali", "type": "religious"},
        ]
        return events
    
    def _get_default_events(self, year: int, calendar_type: str) -> List[Dict]:
        """Get default events when API fails"""
        if calendar_type == CalendarType.PERSIAN.value:
            return self._get_persian_events(year)
        elif calendar_type == CalendarType.GREGORIAN.value:
            return self._get_gregorian_events(year)
        elif calendar_type == CalendarType.ISLAMIC.value:
            return self._get_islamic_events(year)
        else:
            return []

# ============================================================================
# UI Components
# ============================================================================

class ModernButton(tk.Button):
    """Modern button with Windows 11 style"""
    
    def __init__(self, master=None, **kwargs):
        style = kwargs.pop('style', 'primary')
        super().__init__(master, **kwargs)
        
        colors = {
            'primary': {'bg': '#0078d4', 'fg': 'white', 'hover': '#106ebe'},
            'secondary': {'bg': '#6c757d', 'fg': 'white', 'hover': '#5a6268'},
            'success': {'bg': '#28a745', 'fg': 'white', 'hover': '#218838'},
            'danger': {'bg': '#dc3545', 'fg': 'white', 'hover': '#c82333'},
            'warning': {'bg': '#ffc107', 'fg': 'black', 'hover': '#e0a800'},
            'info': {'bg': '#17a2b8', 'fg': 'white', 'hover': '#138496'},
        }
        
        self.color_config = colors.get(style, colors['primary'])
        
        self.configure(
            bg=self.color_config['bg'],
            fg=self.color_config['fg'],
            font=('Segoe UI', 10),
            relief='flat',
            bd=0,
            padx=15,
            pady=8,
            cursor='hand2'
        )
        
        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)
    
    def on_enter(self, e):
        self['bg'] = self.color_config['hover']
    
    def on_leave(self, e):
        self['bg'] = self.color_config['bg']

class SetupWizard:
    """Setup wizard for initial configuration"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.window = None
        self.current_step = 0
        self.steps = [
            "Welcome",
            "Language Selection",
            "Primary Calendar",
            "Secondary Calendars",
            "Display Settings",
            "Theme Selection",
            "Advanced Settings",
            "Completion"
        ]
        
        self.languages = [
            ("English", "en"),
            ("Persian (فارسی)", "fa"),
            ("Arabic (العربية)", "ar"),
            ("French (Français)", "fr"),
            ("Chinese (中文)", "zh"),
            ("Japanese (日本語)", "ja")
        ]
        
        self.converter = MultiCalendarConverter()
        self.calendar_names = self.converter.get_calendar_names()
        
    def run(self) -> Dict:
        """Run the wizard and return configuration"""
        self.create_window()
        self.show_step(0)
        self.window.mainloop()
        return self.config
    
    def create_window(self):
        """Create wizard window"""
        self.window = tk.Toplevel()
        self.window.title("Global Calendar Setup Wizard")
        self.window.geometry("900x700")
        self.window.resizable(False, False)
        self.window.configure(bg="#f3f3f3")
        
        # Center window
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')
        
        # Prevent closing
        self.window.protocol("WM_DELETE_WINDOW", lambda: None)
    
    def show_step(self, step: int):
        """Show specific step"""
        self.current_step = step
        
        # Clear widgets
        for widget in self.window.winfo_children():
            widget.destroy()
        
        # Header
        header_frame = tk.Frame(self.window, bg="#0078d4", height=80)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text=f"Step {step + 1} of {len(self.steps)}: {self.steps[step]}",
            font=("Segoe UI", 16, "bold"),
            fg="white",
            bg="#0078d4"
        )
        title_label.pack(expand=True, pady=20)
        
        # Progress bar
        progress_frame = tk.Frame(self.window, bg="#f3f3f3")
        progress_frame.pack(fill="x", padx=40, pady=(20, 10))
        
        progress = ttk.Progressbar(
            progress_frame,
            length=820,
            mode='determinate',
            maximum=len(self.steps),
            style="wizard.Horizontal.TProgressbar"
        )
        progress['value'] = step + 1
        progress.pack()
        
        # Style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("wizard.Horizontal.TProgressbar",
                       background='#0078d4',
                       troughcolor='#e1e1e1',
                       bordercolor='#f3f3f3')
        
        # Content
        content_frame = tk.Frame(self.window, bg="#f3f3f3")
        content_frame.pack(fill="both", expand=True, padx=40, pady=20)
        
        # Show step content
        step_methods = [
            self.show_welcome,
            self.show_language_selection,
            self.show_primary_calendar,
            self.show_secondary_calendars,
            self.show_display_settings,
            self.show_theme_selection,
            self.show_advanced_settings,
            self.show_completion
        ]
        
        if step < len(step_methods):
            step_methods[step](content_frame)
        
        # Navigation buttons
        nav_frame = tk.Frame(self.window, bg="#f3f3f3")
        nav_frame.pack(fill="x", padx=40, pady=(0, 20))
        
        if step > 0:
            prev_btn = ModernButton(
                nav_frame,
                text="◄ Previous",
                style="secondary",
                command=lambda: self.show_step(step - 1)
            )
            prev_btn.pack(side="left", padx=5)
        
        if step < len(self.steps) - 1:
            next_btn = ModernButton(
                nav_frame,
                text="Next ►",
                style="primary",
                command=lambda: self.show_step(step + 1)
            )
            next_btn.pack(side="right", padx=5)
        else:
            finish_btn = ModernButton(
                nav_frame,
                text="Finish and Launch",
                style="success",
                command=self.finish_wizard
            )
            finish_btn.pack(side="right", padx=5)
    
    def show_welcome(self, parent):
        """Show welcome step"""
        welcome_text = """Welcome to Global Calendar by Hessamedien!

This is a powerful multi-calendar application with the following features:

• Support for 9 different calendar systems
• Simultaneous display of 2-4 calendars
• Modern Windows 11 inspired interface
• Customizable display settings
• Real-time event updates
• Sunrise/sunset times
• Religious and national holidays

Click 'Next' to continue with setup."""
        
        text_widget = tk.Text(
            parent,
            height=15,
            font=("Segoe UI", 11),
            fg="#333333",
            bg="white",
            relief="flat",
            wrap="word",
            padx=20,
            pady=20
        )
        text_widget.insert("1.0", welcome_text)
        text_widget.config(state="disabled")
        text_widget.pack(fill="both", expand=True)
        
        # Logo
        logo_frame = tk.Frame(parent, bg="#f3f3f3")
        logo_frame.pack(pady=10)
        
        tk.Label(
            logo_frame,
            text="Global Calendar",
            font=("Segoe UI", 18, "bold"),
            fg="#0078d4",
            bg="#f3f3f3"
        ).pack(side="left", padx=5)
        
        tk.Label(
            logo_frame,
            text="by Hessamedien",
            font=("Segoe UI", 14),
            fg="#666666",
            bg="#f3f3f3"
        ).pack(side="left", padx=5)
    
    def show_language_selection(self, parent):
        """Show language selection step"""
        tk.Label(
            parent,
            text="Select Application Language:",
            font=("Segoe UI", 14, "bold"),
            fg="#333333",
            bg="#f3f3f3"
        ).pack(anchor="w", pady=(0, 20))
        
        self.lang_var = tk.StringVar(value=self.config.get("language", "en"))
        
        for lang_name, lang_code in self.languages:
            frame = tk.Frame(parent, bg="#f3f3f3")
            frame.pack(fill="x", pady=5)
            
            rb = tk.Radiobutton(
                frame,
                text=lang_name,
                variable=self.lang_var,
                value=lang_code,
                font=("Segoe UI", 12),
                fg="#333333",
                bg="#f3f3f3",
                selectcolor="#f3f3f3",
                activebackground="#f3f3f3",
                activeforeground="#0078d4"
            )
            rb.pack(side="left")
    
    def show_primary_calendar(self, parent):
        """Show primary calendar selection"""
        tk.Label(
            parent,
            text="Select Primary Calendar:",
            font=("Segoe UI", 14, "bold"),
            fg="#333333",
            bg="#f3f3f3"
        ).pack(anchor="w", pady=(0, 20))
        
        tk.Label(
            parent,
            text="This will be your main calendar display:",
            font=("Segoe UI", 11),
            fg="#666666",
            bg="#f3f3f3"
        ).pack(anchor="w", pady=(0, 20))
        
        self.primary_cal_var = tk.StringVar(
            value=self.config.get("primary_calendar", CalendarType.GREGORIAN.value)
        )
        
        # Grid layout for calendars
        grid_frame = tk.Frame(parent, bg="#f3f3f3")
        grid_frame.pack(fill="both", expand=True)
        
        calendars = list(self.calendar_names.items())
        
        for i, (cal_type, cal_name) in enumerate(calendars):
            row = i // 3
            col = i % 3
            
            frame = tk.Frame(grid_frame, bg="white", relief="raised", bd=1)
            frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            
            # Calendar preview
            preview_frame = tk.Frame(frame, bg="#f8f9fa", height=60)
            preview_frame.pack(fill="x", pady=(5, 0))
            preview_frame.pack_propagate(False)
            
            # Calendar icon/name
            tk.Label(
                preview_frame,
                text=cal_name,
                font=("Segoe UI", 9, "bold"),
                fg="#0078d4",
                bg="#f8f9fa"
            ).pack(expand=True)
            
            # Radio button
            rb = tk.Radiobutton(
                frame,
                text=f"Select {cal_name}",
                variable=self.primary_cal_var,
                value=cal_type.value,
                font=("Segoe UI", 10),
                fg="#333333",
                bg="white",
                selectcolor="white",
                activebackground="white",
                activeforeground="#0078d4"
            )
            rb.pack(pady=5)
            
            grid_frame.columnconfigure(col, weight=1)
            grid_frame.rowconfigure(row, weight=1)
    
    def show_secondary_calendars(self, parent):
        """Show secondary calendars selection"""
        tk.Label(
            parent,
            text="Select Secondary Calendars (2-4):",
            font=("Segoe UI", 14, "bold"),
            fg="#333333",
            bg="#f3f3f3"
        ).pack(anchor="w", pady=(0, 10))
        
        tk.Label(
            parent,
            text="These calendars will be displayed alongside your primary calendar:",
            font=("Segoe UI", 11),
            fg="#666666",
            bg="#f3f3f3"
        ).pack(anchor="w", pady=(0, 20))
        
        # Get primary calendar
        primary_cal = CalendarType(self.primary_cal_var.get())
        
        # Create checkboxes for all calendars except primary
        self.secondary_vars = {}
        
        scroll_frame = tk.Frame(parent, bg="#f3f3f3")
        scroll_frame.pack(fill="both", expand=True)
        
        # Create canvas for scrolling
        canvas = tk.Canvas(scroll_frame, bg="#f3f3f3", highlightthickness=0)
        scrollbar = tk.Scrollbar(scroll_frame, orient="vertical", command=canvas.yview)
        content_frame = tk.Frame(canvas, bg="#f3f3f3")
        
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas.create_window((0, 0), window=content_frame, anchor="nw")
        
        # Configure scrolling
        def configure_scrollregion(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        content_frame.bind("<Configure>", configure_scrollregion)
        
        # Add calendar checkboxes
        default_secondaries = self.config.get("secondary_calendars", 
                                             [CalendarType.PERSIAN.value, CalendarType.ISLAMIC.value])
        
        for i, (cal_type, cal_name) in enumerate(self.calendar_names.items()):
            if cal_type == primary_cal:
                continue  # Skip primary calendar
            
            var = tk.BooleanVar(value=cal_type.value in default_secondaries)
            self.secondary_vars[cal_type.value] = var
            
            frame = tk.Frame(content_frame, bg="#f3f3f3")
            frame.pack(fill="x", pady=5, padx=20)
            
            cb = tk.Checkbutton(
                frame,
                text=cal_name,
                variable=var,
                font=("Segoe UI", 11),
                fg="#333333",
                bg="#f3f3f3",
                selectcolor="#f3f3f3",
                activebackground="#f3f3f3",
                activeforeground="#0078d4"
            )
            cb.pack(side="left")
            
            # Show number indicator
            tk.Label(
                frame,
                text=f"Calendar {len(self.secondary_vars)}",
                font=("Segoe UI", 9),
                fg="#666666",
                bg="#f3f3f3"
            ).pack(side="right")
        
        # Info text
        info_label = tk.Label(
            parent,
            text="✓ Select 2 to 4 calendars\n✓ Selected calendars will show dates in corners\n✓ You can change this later in settings",
            font=("Segoe UI", 10),
            fg="#28a745",
            bg="#f3f3f3",
            justify="left"
        )
        info_label.pack(pady=10)
    
    def show_display_settings(self, parent):
        """Show display settings"""
        tk.Label(
            parent,
            text="Display Settings:",
            font=("Segoe UI", 14, "bold"),
            fg="#333333",
            bg="#f3f3f3"
        ).pack(anchor="w", pady=(0, 20))
        
        # Display mode
        display_frame = tk.LabelFrame(
            parent,
            text="Display Mode",
            font=("Segoe UI", 12),
            fg="#333333",
            bg="#f3f3f3",
            relief="flat"
        )
        display_frame.pack(fill="x", pady=10)
        
        self.display_mode_var = tk.StringVar(
            value=self.config.get("display_mode", DisplayMode.STANDARD.value)
        )
        
        modes = [
            ("Standard", DisplayMode.STANDARD.value, "Normal calendar view with all features"),
            ("Compact", DisplayMode.COMPACT.value, "Compact view for smaller screens"),
            ("Minimal", DisplayMode.MINIMAL.value, "Minimal view showing only dates"),
            ("Detailed", DisplayMode.DETAILED.value, "Detailed view with extra information")
        ]
        
        for i, (name, value, desc) in enumerate(modes):
            frame = tk.Frame(display_frame, bg="#f3f3f3")
            frame.pack(fill="x", pady=5, padx=10)
            
            rb = tk.Radiobutton(
                frame,
                text=name,
                variable=self.display_mode_var,
                value=value,
                font=("Segoe UI", 11),
                fg="#333333",
                bg="#f3f3f3",
                selectcolor="#f3f3f3",
                activebackground="#f3f3f3",
                activeforeground="#0078d4"
            )
            rb.pack(side="left")
            
            tk.Label(
                frame,
                text=desc,
                font=("Segoe UI", 9),
                fg="#666666",
                bg="#f3f3f3"
            ).pack(side="left", padx=10)
        
        # Additional display options
        options_frame = tk.LabelFrame(
            parent,
            text="Additional Options",
            font=("Segoe UI", 12),
            fg="#333333",
            bg="#f3f3f3",
            relief="flat"
        )
        options_frame.pack(fill="x", pady=10)
        
        self.show_week_var = tk.BooleanVar(value=self.config.get("show_week_numbers", True))
        week_cb = tk.Checkbutton(
            options_frame,
            text="Show week numbers",
            variable=self.show_week_var,
            font=("Segoe UI", 11),
            fg="#333333",
            bg="#f3f3f3",
            selectcolor="#f3f3f3",
            activebackground="#f3f3f3"
        )
        week_cb.pack(anchor="w", pady=5, padx=10)
        
        self.show_moon_var = tk.BooleanVar(value=self.config.get("show_moon_phases", False))
        moon_cb = tk.Checkbutton(
            options_frame,
            text="Show moon phases",
            variable=self.show_moon_var,
            font=("Segoe UI", 11),
            fg="#333333",
            bg="#f3f3f3",
            selectcolor="#f3f3f3",
            activebackground="#f3f3f3"
        )
        moon_cb.pack(anchor="w", pady=5, padx=10)
        
        self.show_sun_var = tk.BooleanVar(value=self.config.get("show_sun_times", True))
        sun_cb = tk.Checkbutton(
            options_frame,
            text="Show sunrise/sunset times",
            variable=self.show_sun_var,
            font=("Segoe UI", 11),
            fg="#333333",
            bg="#f3f3f3",
            selectcolor="#f3f3f3",
            activebackground="#f3f3f3"
        )
        sun_cb.pack(anchor="w", pady=5, padx=10)
        
        self.show_multi_var = tk.BooleanVar(value=self.config.get("show_multiple_dates", True))
        multi_cb = tk.Checkbutton(
            options_frame,
            text="Show multiple calendar dates in each cell",
            variable=self.show_multi_var,
            font=("Segoe UI", 11),
            fg="#333333",
            bg="#f3f3f3",
            selectcolor="#f3f3f3",
            activebackground="#f3f3f3"
        )
        multi_cb.pack(anchor="w", pady=5, padx=10)
    
    def show_theme_selection(self, parent):
        """Show theme selection"""
        tk.Label(
            parent,
            text="Select Theme:",
            font=("Segoe UI", 14, "bold"),
            fg="#333333",
            bg="#f3f3f3"
        ).pack(anchor="w", pady=(0, 20))
        
        self.theme_var = tk.StringVar(
            value=self.config.get("theme", ThemeMode.AUTO.value)
        )
        
        # Theme previews
        themes = [
            ("Dark", ThemeMode.DARK.value, "#1e1e1e", "white"),
            ("Light", ThemeMode.LIGHT.value, "#f3f3f3", "#333333"),
            ("Blue", ThemeMode.BLUE.value, "#1e1e1e", "#0078d4"),
            ("Green", ThemeMode.GREEN.value, "#1e1e1e", "#28a745"),
            ("Purple", ThemeMode.PURPLE.value, "#1e1e1e", "#6f42c1"),
            ("Auto", ThemeMode.AUTO.value, "#f3f3f3", "System default based on time")
        ]
        
        # Grid for themes
        grid_frame = tk.Frame(parent, bg="#f3f3f3")
        grid_frame.pack(fill="both", expand=True)
        
        for i, (name, value, bg_color, desc) in enumerate(themes):
            row = i // 3
            col = i % 3
            
            frame = tk.Frame(
                grid_frame,
                bg=bg_color,
                highlightthickness=2,
                highlightbackground="#ddd" if self.theme_var.get() != value else "#0078d4"
            )
            frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            
            # Theme sample
            sample = tk.Frame(frame, bg=bg_color, height=40)
            sample.pack(fill="x", padx=5, pady=(5, 2))
            
            # Radio button
            rb = tk.Radiobutton(
                frame,
                text=name,
                variable=self.theme_var,
                value=value,
                font=("Segoe UI", 10),
                fg="white" if bg_color == "#1e1e1e" else "#333333",
                bg=bg_color,
                selectcolor=bg_color,
                activebackground=bg_color,
                activeforeground="#0078d4"
            )
            rb.pack(pady=2)
            
            # Description
            tk.Label(
                frame,
                text=desc[:20] + "...",
                font=("Segoe UI", 8),
                fg="white" if bg_color == "#1e1e1e" else "#666666",
                bg=bg_color,
                wraplength=100
            ).pack(pady=2)
            
            grid_frame.columnconfigure(col, weight=1)
            grid_frame.rowconfigure(row, weight=1)
    
    def show_advanced_settings(self, parent):
        """Show advanced settings"""
        tk.Label(
            parent,
            text="Advanced Settings:",
            font=("Segoe UI", 14, "bold"),
            fg="#333333",
            bg="#f3f3f3"
        ).pack(anchor="w", pady=(0, 20))
        
        # Date sizes
        size_frame = tk.LabelFrame(
            parent,
            text="Date Sizes",
            font=("Segoe UI", 12),
            fg="#333333",
            bg="#f3f3f3",
            relief="flat"
        )
        size_frame.pack(fill="x", pady=10)
        
        # Primary date size
        primary_frame = tk.Frame(size_frame, bg="#f3f3f3")
        primary_frame.pack(fill="x", pady=5, padx=10)
        
        tk.Label(
            primary_frame,
            text="Primary date size:",
            font=("Segoe UI", 11),
            fg="#333333",
            bg="#f3f3f3"
        ).pack(side="left")
        
        self.primary_size_var = tk.IntVar(value=self.config.get("date_size", 14))
        primary_scale = tk.Scale(
            primary_frame,
            from_=10,
            to=24,
            variable=self.primary_size_var,
            orient="horizontal",
            length=200,
            bg="#f3f3f3",
            fg="#333333"
        )
        primary_scale.pack(side="right")
        
        # Secondary date size
        secondary_frame = tk.Frame(size_frame, bg="#f3f3f3")
        secondary_frame.pack(fill="x", pady=5, padx=10)
        
        tk.Label(
            secondary_frame,
            text="Secondary date size:",
            font=("Segoe UI", 11),
            fg="#333333",
            bg="#f3f3f3"
        ).pack(side="left")
        
        self.secondary_size_var = tk.IntVar(value=self.config.get("secondary_date_size", 9))
        secondary_scale = tk.Scale(
            secondary_frame,
            from_=6,
            to=14,
            variable=self.secondary_size_var,
            orient="horizontal",
            length=200,
            bg="#f3f3f3",
            fg="#333333"
        )
        secondary_scale.pack(side="right")
        
        # Other settings
        other_frame = tk.LabelFrame(
            parent,
            text="Other Settings",
            font=("Segoe UI", 12),
            fg="#333333",
            bg="#f3f3f3",
            relief="flat"
        )
        other_frame.pack(fill="x", pady=10)
        
        self.auto_update_var = tk.BooleanVar(value=self.config.get("auto_update", True))
        update_cb = tk.Checkbutton(
            other_frame,
            text="Auto-update events from internet",
            variable=self.auto_update_var,
            font=("Segoe UI", 11),
            fg="#333333",
            bg="#f3f3f3",
            selectcolor="#f3f3f3",
            activebackground="#f3f3f3"
        )
        update_cb.pack(anchor="w", pady=5, padx=10)
        
        self.notifications_var = tk.BooleanVar(value=self.config.get("notifications", True))
        notify_cb = tk.Checkbutton(
            other_frame,
            text="Show notifications for events",
            variable=self.notifications_var,
            font=("Segoe UI", 11),
            fg="#333333",
            bg="#f3f3f3",
            selectcolor="#f3f3f3",
            activebackground="#f3f3f3"
        )
        notify_cb.pack(anchor="w", pady=5, padx=10)
        
        # Timezone
        timezone_frame = tk.Frame(other_frame, bg="#f3f3f3")
        timezone_frame.pack(fill="x", pady=5, padx=10)
        
        tk.Label(
            timezone_frame,
            text="Timezone:",
            font=("Segoe UI", 11),
            fg="#333333",
            bg="#f3f3f3"
        ).pack(side="left")
        
        self.timezone_var = tk.StringVar(value=self.config.get("timezone", "UTC"))
        timezone_combo = ttk.Combobox(
            timezone_frame,
            textvariable=self.timezone_var,
            values=["UTC", "Asia/Tehran", "Europe/London", "America/New_York", 
                   "Asia/Tokyo", "Australia/Sydney", "Europe/Paris"],
            state="readonly",
            width=20
        )
        timezone_combo.pack(side="right", padx=10)
    
    def show_completion(self, parent):
        """Show completion step"""
        completion_text = """Setup Complete!

Your Global Calendar is now configured with the following settings:

• Language: {}
• Primary Calendar: {}
• Secondary Calendars: {}
• Display Mode: {}
• Theme: {}

The application will now launch with your selected settings.

You can always change these settings from the application's Settings menu.

Developer: Hessamedien
Instagram: @hessamedien

Thank you for choosing Global Calendar!"""
        
        # Get selected values
        language_name = dict(self.languages).get(self.lang_var.get(), self.lang_var.get())
        
        primary_cal_name = "Gregorian"
        for cal_type, name in self.calendar_names.items():
            if cal_type.value == self.primary_cal_var.get():
                primary_cal_name = name
                break
        
        # Get selected secondary calendars
        secondary_cals = []
        for cal_value, var in self.secondary_vars.items():
            if var.get():
                for cal_type, name in self.calendar_names.items():
                    if cal_type.value == cal_value:
                        secondary_cals.append(name[:15])  # Truncate long names
                        break
        
        secondary_text = ", ".join(secondary_cals[:3])  # Show only first 3
        
        # Display mode name
        display_mode_name = {
            DisplayMode.STANDARD.value: "Standard",
            DisplayMode.COMPACT.value: "Compact",
            DisplayMode.MINIMAL.value: "Minimal",
            DisplayMode.DETAILED.value: "Detailed"
        }.get(self.display_mode_var.get(), "Standard")
        
        # Theme name
        theme_name = {
            ThemeMode.DARK.value: "Dark",
            ThemeMode.LIGHT.value: "Light",
            ThemeMode.BLUE.value: "Blue",
            ThemeMode.GREEN.value: "Green",
            ThemeMode.PURPLE.value: "Purple",
            ThemeMode.AUTO.value: "Auto"
        }.get(self.theme_var.get(), "Auto")
        
        formatted_text = completion_text.format(
            language_name,
            primary_cal_name,
            secondary_text,
            display_mode_name,
            theme_name
        )
        
        text_widget = tk.Text(
            parent,
            height=20,
            font=("Segoe UI", 11),
            fg="#333333",
            bg="white",
            relief="flat",
            wrap="word",
            padx=20,
            pady=20
        )
        text_widget.insert("1.0", formatted_text)
        text_widget.config(state="disabled")
        text_widget.pack(fill="both", expand=True)
    
    def finish_wizard(self):
        """Finish wizard and save configuration"""
        # Get secondary calendars
        secondary_calendars = []
        for cal_value, var in self.secondary_vars.items():
            if var.get():
                secondary_calendars.append(cal_value)
        
        # Ensure we have 2-4 calendars total (primary + secondaries)
        if len(secondary_calendars) < 2:
            # Add defaults if not enough selected
            default_cals = [CalendarType.PERSIAN.value, CalendarType.ISLAMIC.value]
            for cal in default_cals:
                if cal not in secondary_calendars and cal != self.primary_cal_var.get():
                    secondary_calendars.append(cal)
                    if len(secondary_calendars) >= 3:  # Max 4 total with primary
                        break
        
        # Limit to max 3 secondary calendars
        secondary_calendars = secondary_calendars[:3]
        
        # Save configuration
        self.config.update({
            "language": self.lang_var.get(),
            "primary_calendar": self.primary_cal_var.get(),
            "secondary_calendars": secondary_calendars,
            "display_mode": self.display_mode_var.get(),
            "theme": self.theme_var.get(),
            "show_week_numbers": self.show_week_var.get(),
            "show_moon_phases": self.show_moon_var.get(),
            "show_sun_times": self.show_sun_var.get(),
            "show_multiple_dates": self.show_multi_var.get(),
            "date_size": self.primary_size_var.get(),
            "secondary_date_size": self.secondary_size_var.get(),
            "auto_update": self.auto_update_var.get(),
            "notifications": self.notifications_var.get(),
            "timezone": self.timezone_var.get(),
            "first_run": False,
            "version": "2.0.0"
        })
        
        # Close window
        self.window.destroy()

class LoadingScreen:
    """Loading screen with progress bar"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.window = None
        self.progress_var = None
        
    def show(self):
        """Show loading screen"""
        self.window = tk.Toplevel()
        self.window.title("Loading Global Calendar...")
        self.window.geometry("500x350")
        self.window.resizable(False, False)
        
        # Set theme-based colors
        theme = self.config.get("theme", ThemeMode.AUTO.value)
        if theme == ThemeMode.DARK.value or (theme == ThemeMode.AUTO.value and self.is_dark_time()):
            bg_color = "#1e1e1e"
            text_color = "#ffffff"
            accent_color = "#0078d4"
        else:
            bg_color = "#f3f3f3"
            text_color = "#333333"
            accent_color = "#0078d4"
        
        self.window.configure(bg=bg_color)
        
        # Remove title bar
        self.window.overrideredirect(True)
        
        # Center window
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')
        
        # Create content
        self.create_content(bg_color, text_color, accent_color)
        self.window.update()
    
    def is_dark_time(self) -> bool:
        """Check if it's dark time (for auto theme)"""
        hour = datetime.now().hour
        return hour < 6 or hour >= 18
    
    def create_content(self, bg_color: str, text_color: str, accent_color: str):
        """Create loading screen content"""
        # Title
        title_frame = tk.Frame(self.window, bg=bg_color)
        title_frame.pack(expand=True, fill="both")
        
        tk.Label(
            title_frame,
            text="Global Calendar",
            font=("Segoe UI", 24, "bold"),
            fg=accent_color,
            bg=bg_color
        ).pack(pady=(40, 5))
        
        tk.Label(
            title_frame,
            text="by Hessamedien",
            font=("Segoe UI", 14),
            fg=text_color,
            bg=bg_color
        ).pack()
        
        # Spinning animation
        self.canvas = tk.Canvas(
            self.window,
            width=80,
            height=80,
            bg=bg_color,
            highlightthickness=0
        )
        self.canvas.pack(pady=20)
        
        # Draw spinning circle
        self.spinner_id = None
        self.spinner_angle = 0
        self.draw_spinner(accent_color)
        
        # Status text
        self.status_label = tk.Label(
            self.window,
            text="Initializing...",
            font=("Segoe UI", 11),
            fg=text_color,
            bg=bg_color
        )
        self.status_label.pack(pady=(0, 10))
        
        # Progress bar
        self.progress_var = tk.IntVar(value=0)
        
        style = ttk.Style()
        style.theme_use('clam')
        style_name = f"Loading.{accent_color.replace('#', '')}"
        style.configure(style_name,
                       background=accent_color,
                       troughcolor='#444444' if bg_color == "#1e1e1e" else '#dddddd',
                       bordercolor=bg_color)
        
        self.progress_bar = ttk.Progressbar(
            self.window,
            style=style_name,
            variable=self.progress_var,
            maximum=100,
            mode='determinate',
            length=400
        )
        self.progress_bar.pack(pady=10)
        
        # Percentage
        self.percent_label = tk.Label(
            self.window,
            text="0%",
            font=("Segoe UI", 10),
            fg=text_color,
            bg=bg_color
        )
        self.percent_label.pack()
        
        # Footer
        tk.Label(
            self.window,
            text="© 2024 Hessamedien - Instagram: @hessamedien",
            font=("Segoe UI", 8),
            fg="#666666",
            bg=bg_color
        ).pack(side="bottom", pady=10)
        
        # Start spinner animation
        self.animate_spinner(accent_color)
    
    def draw_spinner(self, color: str):
        """Draw spinner circle"""
        self.canvas.delete("spinner")
        self.spinner_id = self.canvas.create_arc(
            10, 10, 70, 70,
            start=self.spinner_angle,
            extent=120,
            outline=color,
            width=4,
            style=tk.ARC,
            tags="spinner"
        )
    
    def animate_spinner(self, color: str):
        """Animate spinner"""
        self.spinner_angle = (self.spinner_angle + 10) % 360
        self.draw_spinner(color)
        self.window.after(50, lambda: self.animate_spinner(color))
    
    def update_progress(self, value: int, status: str = None):
        """Update progress bar"""
        if self.progress_var:
            self.progress_var.set(value)
            self.percent_label.config(text=f"{value}%")
            
            if status:
                self.status_label.config(text=status)
            
            self.window.update()
    
    def close(self):
        """Close loading screen"""
        if self.window:
            self.window.destroy()

# ============================================================================
# Main Calendar Application
# ============================================================================

class MultiCalendarApp:
    """Main multi-calendar application"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.root = tk.Tk()
        self.root.title("Global Calendar by Hessamedien")
        
        # Initialize components
        self.converter = MultiCalendarConverter()
        self.event_manager = CalendarEventManager()
        self.calendar_names = self.converter.get_calendar_names()
        
        # Current date and display settings
        self.current_date = datetime.now()
        self.selected_date = self.current_date
        self.primary_calendar = CalendarType(config.get("primary_calendar", CalendarType.GREGORIAN.value))
        self.secondary_calendars = [
            CalendarType(cal) for cal in config.get("secondary_calendars", 
                                                   [CalendarType.PERSIAN.value, CalendarType.ISLAMIC.value])
        ]
        
        # Limit to max 3 secondary calendars
        self.secondary_calendars = self.secondary_calendars[:3]
        
        # Display configuration
        self.display_mode = DisplayMode(config.get("display_mode", DisplayMode.STANDARD.value))
        self.theme = ThemeMode(config.get("theme", ThemeMode.AUTO.value))
        
        # Colors based on theme
        self.setup_theme()
        
        # UI Components
        self.day_frames = []  # For storing day frames
        self.day_labels = []  # For storing day labels
        
        # Build UI
        self.setup_ui()
        
        # Load initial data
        self.load_initial_data()
    
    def setup_theme(self):
        """Setup theme colors"""
        if self.theme == ThemeMode.AUTO:
            # Auto-detect based on time
            hour = datetime.now().hour
            self.theme = ThemeMode.DARK if hour < 6 or hour >= 18 else ThemeMode.LIGHT
        
        theme_colors = {
            ThemeMode.DARK: {
                "bg": "#1e1e1e",
                "fg": "#ffffff",
                "accent": "#0078d4",
                "secondary": "#2b2b2b",
                "text": "#cccccc",
                "highlight": "#333333"
            },
            ThemeMode.LIGHT: {
                "bg": "#f3f3f3",
                "fg": "#333333",
                "accent": "#0078d4",
                "secondary": "#ffffff",
                "text": "#666666",
                "highlight": "#e1e1e1"
            },
            ThemeMode.BLUE: {
                "bg": "#1e1e1e",
                "fg": "#ffffff",
                "accent": "#0078d4",
                "secondary": "#2b2b2b",
                "text": "#cccccc",
                "highlight": "#333333"
            },
            ThemeMode.GREEN: {
                "bg": "#1e1e1e",
                "fg": "#ffffff",
                "accent": "#28a745",
                "secondary": "#2b2b2b",
                "text": "#cccccc",
                "highlight": "#333333"
            },
            ThemeMode.PURPLE: {
                "bg": "#1e1e1e",
                "fg": "#ffffff",
                "accent": "#6f42c1",
                "secondary": "#2b2b2b",
                "text": "#cccccc",
                "highlight": "#333333"
            }
        }
        
        self.colors = theme_colors.get(self.theme, theme_colors[ThemeMode.LIGHT])
        self.root.configure(bg=self.colors["bg"])
    
    def setup_ui(self):
        """Setup user interface"""
        # Window size based on display mode
        if self.display_mode == DisplayMode.COMPACT:
            self.root.geometry("1000x700")
        elif self.display_mode == DisplayMode.MINIMAL:
            self.root.geometry("800x600")
        else:
            self.root.geometry("1200x800")
        
        # Menu bar
        self.setup_menu()
        
        # Header
        self.setup_header()
        
        # Main content
        self.setup_main_content()
        
        # Footer
        self.setup_footer()
        
        # Bind keyboard shortcuts
        self.setup_shortcuts()
    
    def setup_menu(self):
        """Setup menu bar"""
        menubar = tk.Menu(self.root, bg=self.colors["bg"], fg=self.colors["fg"])
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0, bg=self.colors["bg"], fg=self.colors["fg"])
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Save Settings", command=self.save_settings)
        file_menu.add_command(label="Export Calendar", command=self.export_calendar)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.exit_app)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0, bg=self.colors["bg"], fg=self.colors["fg"])
        menubar.add_cascade(label="View", menu=view_menu)
        
        # Display mode submenu
        display_menu = tk.Menu(view_menu, tearoff=0, bg=self.colors["bg"], fg=self.colors["fg"])
        view_menu.add_cascade(label="Display Mode", menu=display_menu)
        
        for mode in DisplayMode:
            display_menu.add_radiobutton(
                label=mode.value.title(),
                variable=tk.StringVar(value=self.display_mode.value),
                value=mode.value,
                command=lambda m=mode: self.change_display_mode(m)
            )
        
        # Theme submenu
        theme_menu = tk.Menu(view_menu, tearoff=0, bg=self.colors["bg"], fg=self.colors["fg"])
        view_menu.add_cascade(label="Theme", menu=theme_menu)
        
        for theme in ThemeMode:
            theme_menu.add_radiobutton(
                label=theme.value.title(),
                variable=tk.StringVar(value=self.theme.value),
                value=theme.value,
                command=lambda t=theme: self.change_theme(t)
            )
        
        view_menu.add_separator()
        
        # Calendar visibility
        view_menu.add_checkbutton(
            label="Show Week Numbers",
            variable=tk.BooleanVar(value=self.config.get("show_week_numbers", True)),
            command=self.toggle_week_numbers
        )
        
        view_menu.add_checkbutton(
            label="Show Multiple Dates",
            variable=tk.BooleanVar(value=self.config.get("show_multiple_dates", True)),
            command=self.toggle_multiple_dates
        )
        
        # Calendars menu
        calendars_menu = tk.Menu(menubar, tearoff=0, bg=self.colors["bg"], fg=self.colors["fg"])
        menubar.add_cascade(label="Calendars", menu=calendars_menu)
        
        # Primary calendar submenu
        primary_menu = tk.Menu(calendars_menu, tearoff=0, bg=self.colors["bg"], fg=self.colors["fg"])
        calendars_menu.add_cascade(label="Primary Calendar", menu=primary_menu)
        
        for cal_type, cal_name in self.calendar_names.items():
            primary_menu.add_radiobutton(
                label=cal_name,
                variable=tk.StringVar(value=self.primary_calendar.value),
                value=cal_type.value,
                command=lambda ct=cal_type: self.change_primary_calendar(ct)
            )
        
        calendars_menu.add_separator()
        
        # Secondary calendars submenu
        secondary_menu = tk.Menu(calendars_menu, tearoff=0, bg=self.colors["bg"], fg=self.colors["fg"])
        calendars_menu.add_cascade(label="Secondary Calendars", menu=secondary_menu)
        
        for cal_type, cal_name in self.calendar_names.items():
            if cal_type != self.primary_calendar:
                var = tk.BooleanVar(value=cal_type in self.secondary_calendars)
                secondary_menu.add_checkbutton(
                    label=cal_name,
                    variable=var,
                    command=lambda ct=cal_type, v=var: self.toggle_secondary_calendar(ct, v)
                )
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0, bg=self.colors["bg"], fg=self.colors["fg"])
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Date Converter", command=self.show_date_converter)
        tools_menu.add_command(label="Calendar Settings", command=self.show_calendar_settings)
        tools_menu.add_command(label="Update Events", command=self.update_events)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0, bg=self.colors["bg"], fg=self.colors["fg"])
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="User Guide", command=self.show_user_guide)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_separator()
        help_menu.add_command(label="Instagram", 
                            command=lambda: webbrowser.open("https://instagram.com/hessamedien"))
    
    def setup_header(self):
        """Setup header with navigation and date"""
        header_frame = tk.Frame(self.root, bg=self.colors["accent"], height=60)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        # Navigation buttons
        nav_frame = tk.Frame(header_frame, bg=self.colors["accent"])
        nav_frame.pack(side="left", padx=10)
        
        prev_year_btn = tk.Button(
            nav_frame,
            text="⟪",
            font=("Segoe UI", 12, "bold"),
            bg=self.colors["accent"],
            fg="white",
            relief="flat",
            command=self.prev_year
        )
        prev_year_btn.pack(side="left", padx=2)
        
        prev_month_btn = tk.Button(
            nav_frame,
            text="◄",
            font=("Segoe UI", 12, "bold"),
            bg=self.colors["accent"],
            fg="white",
            relief="flat",
            command=self.prev_month
        )
        prev_month_btn.pack(side="left", padx=2)
        
        # Current month/year display
        self.date_label = tk.Label(
            nav_frame,
            text="",
            font=("Segoe UI", 14, "bold"),
            fg="white",
            bg=self.colors["accent"]
        )
        self.date_label.pack(side="left", padx=20)
        
        next_month_btn = tk.Button(
            nav_frame,
            text="►",
            font=("Segoe UI", 12, "bold"),
            bg=self.colors["accent"],
            fg="white",
            relief="flat",
            command=self.next_month
        )
        next_month_btn.pack(side="left", padx=2)
        
        next_year_btn = tk.Button(
            nav_frame,
            text="⟫",
            font=("Segoe UI", 12, "bold"),
            bg=self.colors["accent"],
            fg="white",
            relief="flat",
            command=self.next_year
        )
        next_year_btn.pack(side="left", padx=2)
        
        # Today button
        today_btn = ModernButton(
            header_frame,
            text="Today",
            style="success",
            command=self.go_to_today
        )
        today_btn.pack(side="right", padx=20)
        
        # Settings button
        settings_btn = ModernButton(
            header_frame,
            text="⚙",
            style="secondary",
            command=self.show_settings
        )
        settings_btn.pack(side="right", padx=5)
        
        # Update date display
        self.update_date_display()
    
    def setup_main_content(self):
        """Setup main calendar content"""
        main_frame = tk.Frame(self.root, bg=self.colors["bg"])
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Weekday headers
        self.setup_weekday_headers(main_frame)
        
        # Calendar grid
        self.setup_calendar_grid(main_frame)
        
        # Side panel (for detailed view)
        if self.display_mode == DisplayMode.DETAILED:
            self.setup_side_panel(main_frame)
    
    def setup_weekday_headers(self, parent):
        """Setup weekday headers"""
        weekday_frame = tk.Frame(parent, bg=self.colors["bg"])
        weekday_frame.pack(fill="x", pady=(0, 5))
        
        # Week number column (if enabled)
        if self.config.get("show_week_numbers", True):
            week_label = tk.Label(
                weekday_frame,
                text="Week",
                font=("Segoe UI", 10, "bold"),
                fg=self.colors["accent"],
                bg=self.colors["bg"],
                width=8
            )
            week_label.pack(side="left", padx=2)
        
        # Day names
        day_names = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        
        for i, day in enumerate(day_names):
            day_label = tk.Label(
                weekday_frame,
                text=day,
                font=("Segoe UI", 11, "bold"),
                fg=self.colors["accent"],
                bg=self.colors["bg"],
                width=15,
                height=2
            )
            day_label.pack(side="left", fill="both", expand=True, padx=2)
    
    def setup_calendar_grid(self, parent):
        """Setup calendar grid with days"""
        # Clear previous grid
        if hasattr(self, 'calendar_frame'):
            self.calendar_frame.destroy()
        
        self.calendar_frame = tk.Frame(parent, bg=self.colors["bg"])
        self.calendar_frame.pack(fill="both", expand=True)
        
        # Create 6 rows for weeks
        self.day_frames = []
        self.day_labels = []
        
        for week in range(6):
            week_row = []
            week_labels = []
            
            # Week number (if enabled)
            if self.config.get("show_week_numbers", True):
                week_frame = tk.Frame(self.calendar_frame, bg=self.colors["bg"], width=80)
                week_frame.grid(row=week, column=0, padx=2, pady=2, sticky="nsew")
                week_frame.grid_propagate(False)
                
                week_label = tk.Label(
                    week_frame,
                    text="",
                    font=("Segoe UI", 10),
                    fg=self.colors["text"],
                    bg=self.colors["bg"]
                )
                week_label.pack(expand=True)
                week_row.append(week_frame)
            
            # Day cells
            for day in range(7):
                day_frame = tk.Frame(
                    self.calendar_frame,
                    bg=self.colors["secondary"],
                    highlightthickness=1,
                    highlightbackground=self.colors["highlight"]
                )
                day_frame.grid(row=week, column=day + (1 if self.config.get("show_week_numbers", True) else 0), 
                             padx=2, pady=2, sticky="nsew")
                
                # Main date label
                main_label = tk.Label(
                    day_frame,
                    text="",
                    font=("Segoe UI", self.config.get("date_size", 14)),
                    fg=self.colors["fg"],
                    bg=self.colors["secondary"]
                )
                main_label.place(x=10, y=10)
                
                # Secondary dates frame (for multiple calendar display)
                if self.config.get("show_multiple_dates", True):
                    secondary_frame = tk.Frame(day_frame, bg=self.colors["secondary"])
                    secondary_frame.place(x=5, y=5)
                    
                    # Secondary date labels (top-left, top-right, bottom-left, bottom-right)
                    secondary_labels = []
                    positions = [(5, 5), (day_frame.winfo_width() - 30, 5), 
                               (5, day_frame.winfo_height() - 25), 
                               (day_frame.winfo_width() - 30, day_frame.winfo_height() - 25)]
                    
                    for pos in positions:
                        label = tk.Label(
                            secondary_frame,
                            text="",
                            font=("Segoe UI", self.config.get("secondary_date_size", 9)),
                            fg=self.colors["text"],
                            bg=self.colors["secondary"]
                        )
                        label.place(x=pos[0], y=pos[1])
                        secondary_labels.append(label)
                    
                    week_labels.append((main_label, secondary_labels))
                else:
                    week_labels.append((main_label, []))
                
                week_row.append(day_frame)
                
                # Bind click event
                day_frame.bind("<Button-1>", lambda e, w=week, d=day: self.on_day_click(w, d))
                main_label.bind("<Button-1>", lambda e, w=week, d=day: self.on_day_click(w, d))
            
            self.day_frames.append(week_row)
            self.day_labels.append(week_labels)
            
            # Configure grid weights
            if self.config.get("show_week_numbers", True):
                self.calendar_frame.columnconfigure(0, weight=0, minsize=80)
            
            for col in range(7):
                self.calendar_frame.columnconfigure(col + (1 if self.config.get("show_week_numbers", True) else 0), 
                                                  weight=1)
            
            self.calendar_frame.rowconfigure(week, weight=1)
        
        # Update calendar display
        self.update_calendar()
    
    def setup_side_panel(self, parent):
        """Setup side panel for detailed view"""
        side_frame = tk.Frame(parent, bg=self.colors["secondary"], width=300)
        side_frame.pack(side="right", fill="y", padx=(10, 0))
        side_frame.pack_propagate(False)
        
        # Selected date info
        date_info_frame = tk.LabelFrame(
            side_frame,
            text="Selected Date",
            font=("Segoe UI", 12, "bold"),
            fg=self.colors["fg"],
            bg=self.colors["secondary"],
            relief="flat"
        )
        date_info_frame.pack(fill="x", padx=10, pady=10)
        
        self.date_info_text = tk.Text(
            date_info_frame,
            height=10,
            font=("Segoe UI", 10),
            fg=self.colors["fg"],
            bg=self.colors["secondary"],
            relief="flat",
            wrap="word"
        )
        self.date_info_text.pack(fill="both", padx=5, pady=5)
        self.date_info_text.config(state="disabled")
        
        # Events for selected date
        events_frame = tk.LabelFrame(
            side_frame,
            text="Events",
            font=("Segoe UI", 12, "bold"),
            fg=self.colors["fg"],
            bg=self.colors["secondary"],
            relief="flat"
        )
        events_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Scrollable events list
        events_canvas = tk.Canvas(
            events_frame,
            bg=self.colors["secondary"],
            highlightthickness=0
        )
        scrollbar = tk.Scrollbar(events_frame, orient="vertical", command=events_canvas.yview)
        self.events_content = tk.Frame(events_canvas, bg=self.colors["secondary"])
        
        events_canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        events_canvas.pack(side="left", fill="both", expand=True)
        events_canvas.create_window((0, 0), window=self.events_content, anchor="nw")
        
        def configure_scrollregion(event):
            events_canvas.configure(scrollregion=events_canvas.bbox("all"))
        self.events_content.bind("<Configure>", configure_scrollregion)
    
    def setup_footer(self):
        """Setup footer with status and calendar info"""
        footer_frame = tk.Frame(self.root, bg=self.colors["secondary"], height=40)
        footer_frame.pack(fill="x", side="bottom")
        footer_frame.pack_propagate(False)
        
        # Status label
        self.status_label = tk.Label(
            footer_frame,
            text="Ready",
            font=("Segoe UI", 10),
            fg=self.colors["text"],
            bg=self.colors["secondary"]
        )
        self.status_label.pack(side="left", padx=20)
        
        # Current calendars info
        calendars_text = f"Primary: {self.calendar_names[self.primary_calendar]}"
        if self.secondary_calendars:
            secondary_names = [self.calendar_names[cal] for cal in self.secondary_calendars[:2]]
            calendars_text += f" | Secondaries: {', '.join(secondary_names)}"
        
        calendars_label = tk.Label(
            footer_frame,
            text=calendars_text,
            font=("Segoe UI", 9),
            fg=self.colors["text"],
            bg=self.colors["secondary"]
        )
        calendars_label.pack(side="left", padx=20)
        
        # Developer info
        dev_label = tk.Label(
            footer_frame,
            text="Hessamedien © 2024",
            font=("Segoe UI", 9),
            fg=self.colors["accent"],
            bg=self.colors["secondary"],
            cursor="hand2"
        )
        dev_label.pack(side="right", padx=20)
        dev_label.bind("<Button-1>", lambda e: webbrowser.open("https://instagram.com/hessamedien"))
    
    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        self.root.bind("<Left>", lambda e: self.prev_month())
        self.root.bind("<Right>", lambda e: self.next_month())
        self.root.bind("<Up>", lambda e: self.prev_year())
        self.root.bind("<Down>", lambda e: self.next_year())
        self.root.bind("<Home>", lambda e: self.go_to_today())
        self.root.bind("<F1>", lambda e: self.show_user_guide())
        self.root.bind("<F5>", lambda e: self.update_events())
    
    def load_initial_data(self):
        """Load initial calendar data"""
        # Load events for current year and selected calendars
        all_calendars = [self.primary_calendar] + self.secondary_calendars
        threading.Thread(
            target=self.event_manager.load_events,
            args=(self.current_date.year, all_calendars),
            daemon=True
        ).start()
        
        # Update status
        self.status_label.config(text="Loading events...")
    
    def update_calendar(self):
        """Update calendar display"""
        year = self.current_date.year
        month = self.current_date.month
        
        # Update date label
        month_names = {
            CalendarType.GREGORIAN: ["January", "February", "March", "April", "May", "June",
                                   "July", "August", "September", "October", "November", "December"],
            CalendarType.PERSIAN: ["Farvardin", "Ordibehesht", "Khordad", "Tir", "Mordad", "Shahrivar",
                                 "Mehr", "Aban", "Azar", "Dey", "Bahman", "Esfand"],
            CalendarType.ISLAMIC: ["Muharram", "Safar", "Rabi' al-Awwal", "Rabi' al-Thani", 
                                 "Jumada al-Awwal", "Jumada al-Thani", "Rajab", "Sha'ban",
                                 "Ramadan", "Shawwal", "Dhu al-Qi'dah", "Dhu al-Hijjah"]
        }
        
        month_name = month_names.get(self.primary_calendar, month_names[CalendarType.GREGORIAN])[month - 1]
        self.date_label.config(text=f"{month_name} {year}")
        
        # Get calendar data for primary calendar
        if self.primary_calendar == CalendarType.PERSIAN:
            # Persian calendar
            try:
                jd = jdatetime.date.fromgregorian(year=year, month=month, day=1)
                days_in_month = jd.daysinmonth
                first_weekday = (jd.weekday() + 1) % 7  # Sunday=0
            except:
                days_in_month = 30
                first_weekday = 0
        elif self.primary_calendar == CalendarType.ISLAMIC:
            # Islamic calendar (simplified)
            days_in_month = 30 if month % 2 == 0 else 29
            first_weekday = 0
        else:
            # Gregorian and others
            days_in_month = py_calendar.monthrange(year, month)[1]
            first_weekday = datetime(year, month, 1).weekday()  # Monday=0, Sunday=6
        
        # Adjust first weekday for display (Sunday=0)
        if self.primary_calendar != CalendarType.PERSIAN:
            first_weekday = (first_weekday + 1) % 7
        
        # Calculate week numbers
        week_numbers = []
        if self.config.get("show_week_numbers", True):
            for week in range(6):
                day_num = week * 7 - first_weekday + 1
                if 1 <= day_num <= days_in_month:
                    date_obj = datetime(year, month, day_num)
                    week_num = date_obj.isocalendar()[1]
                    week_numbers.append(week_num)
                else:
                    week_numbers.append("")
        
        # Fill calendar grid
        day_num = 1
        today = datetime.now()
        
        for week in range(6):
            # Update week number
            if self.config.get("show_week_numbers", True) and week < len(week_numbers):
                week_label = self.day_frames[week][0].winfo_children()[0]
                week_label.config(text=str(week_numbers[week]))
            
            for day in range(7):
                day_idx = day + (1 if self.config.get("show_week_numbers", True) else 0)
                day_frame = self.day_frames[week][day_idx]
                main_label, secondary_labels = self.day_labels[week][day]
                
                if week == 0 and day < first_weekday:
                    # Days before month
                    main_label.config(text="")
                    day_frame.config(bg=self.colors["bg"])
                    for label in secondary_labels:
                        label.config(text="")
                elif day_num <= days_in_month:
                    # Day in month
                    main_label.config(text=str(day_num))
                    
                    # Check if today
                    is_today = False
                    if self.primary_calendar == CalendarType.PERSIAN:
                        try:
                            persian_today = jdatetime.date.today()
                            jd = jdatetime.date.fromgregorian(year=year, month=month, day=day_num)
                            is_today = (jd.year == persian_today.year and 
                                       jd.month == persian_today.month and 
                                       jd.day == persian_today.day)
                        except:
                            pass
                    else:
                        is_today = (year == today.year and 
                                   month == today.month and 
                                   day_num == today.day)
                    
                    # Set colors
                    if is_today:
                        day_frame.config(bg=self.colors["accent"])
                        main_label.config(bg=self.colors["accent"], fg="white")
                    elif day == 6:  # Saturday
                        day_frame.config(bg=self.colors["highlight"])
                        main_label.config(bg=self.colors["highlight"], fg=self.colors["fg"])
                    else:
                        day_frame.config(bg=self.colors["secondary"])
                        main_label.config(bg=self.colors["secondary"], fg=self.colors["fg"])
                    
                    # Show secondary dates
                    if self.config.get("show_multiple_dates", True) and secondary_labels:
                        # Get dates in all calendars
                        all_dates = self.converter.get_all_calendar_dates(
                            year, month, day_num, self.primary_calendar, self.secondary_calendars
                        )
                        
                        # Display secondary dates in corners
                        for i, (cal_type, date_tuple) in enumerate(list(all_dates.items())[1:5]):  # Max 4 secondary
                            if i < len(secondary_labels):
                                cal_year, cal_month, cal_day = date_tuple
                                label_text = f"{cal_day}"
                                secondary_labels[i].config(text=label_text)
                    
                    day_num += 1
                else:
                    # Days after month
                    main_label.config(text="")
                    day_frame.config(bg=self.colors["bg"])
                    for label in secondary_labels:
                        label.config(text="")
        
        # Update selected date info
        self.update_date_info()
    
    def update_date_display(self):
        """Update date display in header"""
        self.update_calendar()
    
    def update_date_info(self):
        """Update selected date information"""
        if self.display_mode != DisplayMode.DETAILED:
            return
        
        year = self.selected_date.year
        month = self.selected_date.month
        day = self.selected_date.day
        
        # Get dates in all calendars
        all_dates = self.converter.get_all_calendar_dates(
            year, month, day, self.primary_calendar, self.secondary_calendars
        )
        
        # Build info text
        info_text = "Date Information:\n\n"
        
        for cal_type, date_tuple in all_dates.items():
            cal_year, cal_month, cal_day = date_tuple
            cal_name = self.calendar_names.get(CalendarType(cal_type), cal_type)
            info_text += f"{cal_name}: {cal_year}/{cal_month:02d}/{cal_day:02d}\n"
        
        # Add day of week
        weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        weekday = weekday_names[self.selected_date.weekday()]
        info_text += f"\nDay: {weekday}"
        
        # Day of year
        day_of_year = self.selected_date.timetuple().tm_yday
        info_text += f"\nDay of Year: {day_of_year}"
        
        # Week of year
        week_of_year = self.selected_date.isocalendar()[1]
        info_text += f"\nWeek of Year: {week_of_year}"
        
        # Update text widget
        self.date_info_text.config(state="normal")
        self.date_info_text.delete("1.0", tk.END)
        self.date_info_text.insert("1.0", info_text)
        self.date_info_text.config(state="disabled")
        
        # Update events
        self.update_events_display()
    
    def update_events_display(self):
        """Update events display for selected date"""
        if self.display_mode != DisplayMode.DETAILED:
            return
        
        # Clear current events
        for widget in self.events_content.winfo_children():
            widget.destroy()
        
        # Get events for selected date in all calendars
        date_str = f"{self.selected_date.year}/{self.selected_date.month}/{self.selected_date.day}"
        
        all_events = []
        for cal in [self.primary_calendar] + self.secondary_calendars:
            events = self.event_manager.get_events_for_date(date_str, cal.value)
            for event in events:
                event['calendar'] = self.calendar_names[cal]
                all_events.append(event)
        
        if not all_events:
            no_events = tk.Label(
                self.events_content,
                text="No events for this date",
                font=("Segoe UI", 10),
                fg=self.colors["text"],
                bg=self.colors["secondary"]
            )
            no_events.pack(pady=10)
            return
        
        # Display events
        for event in all_events:
            event_frame = tk.Frame(self.events_content, bg=self.colors["secondary"])
            event_frame.pack(fill="x", padx=5, pady=2)
            
            # Event indicator
            indicator_color = {
                "national": "#0078d4",
                "religious": "#28a745",
                "international": "#ffc107",
                "holiday": "#dc3545"
            }.get(event.get("type", "international"), "#6c757d")
            
            indicator = tk.Frame(event_frame, bg=indicator_color, width=3, height=20)
            indicator.pack(side="left", fill="y", padx=(0, 5))
            
            # Event info
            info_text = f"{event['title']}\nCalendar: {event['calendar']}"
            info_label = tk.Label(
                event_frame,
                text=info_text,
                font=("Segoe UI", 9),
                fg=self.colors["fg"],
                bg=self.colors["secondary"],
                anchor="w",
                justify="left"
            )
            info_label.pack(side="left", fill="x", expand=True)
    
    def on_day_click(self, week: int, day: int):
        """Handle day click"""
        year = self.current_date.year
        month = self.current_date.month
        
        # Calculate day number
        if self.primary_calendar == CalendarType.PERSIAN:
            try:
                jd = jdatetime.date.fromgregorian(year=year, month=month, day=1)
                days_in_month = jd.daysinmonth
                first_weekday = (jd.weekday() + 1) % 7
            except:
                days_in_month = 30
                first_weekday = 0
        else:
            days_in_month = py_calendar.monthrange(year, month)[1]
            first_weekday = (datetime(year, month, 1).weekday() + 1) % 7
        
        day_num = week * 7 + day - first_weekday + 1
        
        if 1 <= day_num <= days_in_month:
            self.selected_date = datetime(year, month, day_num)
            self.status_label.config(text=f"Selected: {self.selected_date.strftime('%Y-%m-%d')}")
            self.update_date_info()
    
    def prev_month(self):
        """Go to previous month"""
        if self.current_date.month == 1:
            self.current_date = self.current_date.replace(year=self.current_date.year - 1, month=12)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month - 1)
        
        self.update_date_display()
    
    def next_month(self):
        """Go to next month"""
        if self.current_date.month == 12:
            self.current_date = self.current_date.replace(year=self.current_date.year + 1, month=1)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month + 1)
        
        self.update_date_display()
    
    def prev_year(self):
        """Go to previous year"""
        self.current_date = self.current_date.replace(year=self.current_date.year - 1)
        self.update_date_display()
    
    def next_year(self):
        """Go to next year"""
        self.current_date = self.current_date.replace(year=self.current_date.year + 1)
        self.update_date_display()
    
    def go_to_today(self):
        """Go to today's date"""
        self.current_date = datetime.now()
        self.selected_date = self.current_date
        self.update_date_display()
        self.status_label.config(text="Returned to today")
    
    def change_display_mode(self, mode: DisplayMode):
        """Change display mode"""
        self.display_mode = mode
        self.config["display_mode"] = mode.value
        
        # Rebuild UI
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.setup_ui()
        self.status_label.config(text=f"Display mode changed to {mode.value}")
    
    def change_theme(self, theme: ThemeMode):
        """Change theme"""
        self.theme = theme
        self.config["theme"] = theme.value
        self.setup_theme()
        
        # Rebuild UI
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.setup_ui()
        self.status_label.config(text=f"Theme changed to {theme.value}")
    
    def change_primary_calendar(self, calendar: CalendarType):
        """Change primary calendar"""
        self.primary_calendar = calendar
        self.config["primary_calendar"] = calendar.value
        
        # Remove from secondary if it was there
        if calendar in self.secondary_calendars:
            self.secondary_calendars.remove(calendar)
        
        # Update calendar display
        self.update_date_display()
        self.status_label.config(text=f"Primary calendar changed to {self.calendar_names[calendar]}")
    
    def toggle_secondary_calendar(self, calendar: CalendarType, var: tk.BooleanVar):
        """Toggle secondary calendar"""
        if var.get():
            if calendar not in self.secondary_calendars and len(self.secondary_calendars) < 3:
                self.secondary_calendars.append(calendar)
                self.status_label.config(text=f"Added {self.calendar_names[calendar]} as secondary")
        else:
            if calendar in self.secondary_calendars:
                self.secondary_calendars.remove(calendar)
                self.status_label.config(text=f"Removed {self.calendar_names[calendar]} from secondary")
        
        # Update calendar display
        self.update_date_display()
    
    def toggle_week_numbers(self):
        """Toggle week numbers display"""
        self.config["show_week_numbers"] = not self.config.get("show_week_numbers", True)
        self.update_date_display()
        self.status_label.config(
            text=f"Week numbers {'enabled' if self.config['show_week_numbers'] else 'disabled'}"
        )
    
    def toggle_multiple_dates(self):
        """Toggle multiple dates display"""
        self.config["show_multiple_dates"] = not self.config.get("show_multiple_dates", True)
        self.update_date_display()
        self.status_label.config(
            text=f"Multiple dates {'enabled' if self.config['show_multiple_dates'] else 'disabled'}"
        )
    
    def show_date_converter(self):
        """Show date converter dialog"""
        converter = DateConverterDialog(self.root, self.converter, self.calendar_names, self.colors)
        converter.show()
    
    def show_calendar_settings(self):
        """Show calendar settings dialog"""
        settings = CalendarSettingsDialog(self.root, self.config, self.colors)
        if settings.show():
            # Update configuration
            self.config.update(settings.get_config())
            
            # Update display settings
            if "date_size" in settings.get_config():
                self.update_date_display()
            
            self.status_label.config(text="Calendar settings updated")
    
    def show_settings(self):
        """Show main settings dialog"""
        # This would be a comprehensive settings dialog
        messagebox.showinfo("Settings", "Settings dialog will be implemented in next version")
    
    def update_events(self):
        """Update events from internet"""
        all_calendars = [self.primary_calendar] + self.secondary_calendars
        
        def update_task():
            self.status_label.config(text="Updating events...")
            self.event_manager.load_events(self.current_date.year, all_calendars)
            self.root.after(0, lambda: self.status_label.config(text="Events updated"))
            self.root.after(0, self.update_events_display)
        
        threading.Thread(target=update_task, daemon=True).start()
    
    def show_user_guide(self):
        """Show user guide"""
        guide_text = """Global Calendar User Guide

1. Navigation:
   • Use ◄ ► buttons or arrow keys to navigate months
   • Use ⟪ ⟫ buttons or up/down arrows to navigate years
   • Click 'Today' to return to current date

2. Multiple Calendars:
   • Primary calendar shows main dates
   • Up to 3 secondary calendars show in corners
   • Change calendars from Calendars menu

3. Display Modes:
   • Standard: Normal calendar view
   • Compact: Smaller cells
   • Minimal: Only dates
   • Detailed: With side panel info

4. Features:
   • Click dates to select
   • Week numbers (toggle in View menu)
   • Multiple date display (toggle in View menu)
   • Date converter in Tools menu
   • Auto-update events from internet

5. Tips:
   • Right-click dates for quick actions
   • Use F5 to refresh events
   • Export calendars via File menu

For more help, visit Instagram: @hessamedien"""
        
        guide_window = tk.Toplevel(self.root)
        guide_window.title("User Guide")
        guide_window.geometry("500x600")
        guide_window.configure(bg=self.colors["bg"])
        
        text_widget = tk.Text(
            guide_window,
            font=("Segoe UI", 10),
            fg=self.colors["fg"],
            bg=self.colors["bg"],
            relief="flat",
            wrap="word"
        )
        text_widget.insert("1.0", guide_text)
        text_widget.config(state="disabled")
        text_widget.pack(fill="both", expand=True, padx=20, pady=20)
    
    def show_about(self):
        """Show about dialog"""
        about_text = f"""Global Calendar by Hessamedien
Version: 2.0.0

A powerful multi-calendar application with simultaneous display of 2-4 calendars.

Features:
• Support for 9 calendar systems
• Simultaneous multi-calendar display
• Customizable interface
• Event management
• Date conversion tools
• Multiple display modes

Developer: Hessamedien
Instagram: @hessamedien
Website: https://instagram.com/hessamedien

© 2024 All rights reserved."""
        
        messagebox.showinfo("About Global Calendar", about_text)
    
    def save_settings(self):
        """Save current settings"""
        try:
            with open("calendar_config.json", "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            
            self.status_label.config(text="Settings saved successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")
    
    def export_calendar(self):
        """Export calendar data"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                export_data = {
                    "config": self.config,
                    "current_date": self.current_date.isoformat(),
                    "selected_date": self.selected_date.isoformat(),
                    "calendars": {
                        "primary": self.primary_calendar.value,
                        "secondaries": [cal.value for cal in self.secondary_calendars]
                    }
                }
                
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(export_data, f, indent=4, ensure_ascii=False)
                
                self.status_label.config(text=f"Calendar exported to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export calendar: {str(e)}")
    
    def exit_app(self):
        """Exit application"""
        self.save_settings()
        self.root.quit()
    
    def run(self):
        """Run the application"""
        # Center window
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
        # Set window icon (if exists)
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass
        
        # Run main loop
        self.root.mainloop()

# ============================================================================
# Dialog Classes
# ============================================================================

class DateConverterDialog:
    """Date converter dialog"""
    
    def __init__(self, parent, converter, calendar_names, colors):
        self.parent = parent
        self.converter = converter
        self.calendar_names = calendar_names
        self.colors = colors
        self.dialog = None
    
    def show(self):
        """Show the dialog"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Date Converter")
        self.dialog.geometry("600x500")
        self.dialog.configure(bg=self.colors["bg"])
        self.dialog.resizable(False, False)
        
        # Center dialog
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f'{width}x{height}+{x}+{y}')
        
        # Create content
        self.create_content()
    
    def create_content(self):
        """Create dialog content"""
        # Title
        title_label = tk.Label(
            self.dialog,
            text="Date Converter",
            font=("Segoe UI", 16, "bold"),
            fg=self.colors["accent"],
            bg=self.colors["bg"]
        )
        title_label.pack(pady=20)
        
        # Input frame
        input_frame = tk.Frame(self.dialog, bg=self.colors["bg"])
        input_frame.pack(fill="x", padx=30, pady=10)
        
        # From calendar
        from_frame = tk.Frame(input_frame, bg=self.colors["bg"])
        from_frame.pack(fill="x", pady=10)
        
        tk.Label(
            from_frame,
            text="From Calendar:",
            font=("Segoe UI", 11),
            fg=self.colors["fg"],
            bg=self.colors["bg"]
        ).pack(side="left")
        
        self.from_cal_var = tk.StringVar(value=CalendarType.GREGORIAN.value)
        from_cal_combo = ttk.Combobox(
            from_frame,
            textvariable=self.from_cal_var,
            values=[cal.value for cal in self.calendar_names.keys()],
            state="readonly",
            width=20
        )
        from_cal_combo.pack(side="right")
        
        # Date input
        date_frame = tk.Frame(input_frame, bg=self.colors["bg"])
        date_frame.pack(fill="x", pady=10)
        
        tk.Label(
            date_frame,
            text="Date (YYYY/MM/DD):",
            font=("Segoe UI", 11),
            fg=self.colors["fg"],
            bg=self.colors["bg"]
        ).pack(side="left")
        
        self.date_var = tk.StringVar(value=datetime.now().strftime("%Y/%m/%d"))
        date_entry = tk.Entry(
            date_frame,
            textvariable=self.date_var,
            font=("Segoe UI", 11),
            width=15
        )
        date_entry.pack(side="right")
        
        # To calendars
        to_frame = tk.Frame(self.dialog, bg=self.colors["bg"])
        to_frame.pack(fill="x", padx=30, pady=10)
        
        tk.Label(
            to_frame,
            text="Convert To:",
            font=("Segoe UI", 11),
            fg=self.colors["fg"],
            bg=self.colors["bg"]
        ).pack(anchor="w", pady=(0, 10))
        
        self.to_vars = {}
        checkboxes_frame = tk.Frame(to_frame, bg=self.colors["bg"])
        checkboxes_frame.pack(fill="x")
        
        # Create checkboxes for all calendars
        for i, (cal_type, cal_name) in enumerate(self.calendar_names.items()):
            var = tk.BooleanVar(value=True)
            self.to_vars[cal_type] = var
            
            cb = tk.Checkbutton(
                checkboxes_frame,
                text=cal_name[:20],
                variable=var,
                font=("Segoe UI", 10),
                fg=self.colors["fg"],
                bg=self.colors["bg"],
                selectcolor=self.colors["bg"]
            )
            
            # Arrange in grid
            row = i // 3
            col = i % 3
            cb.grid(row=row, column=col, sticky="w", padx=5, pady=2)
        
        # Convert button
        convert_btn = ModernButton(
            self.dialog,
            text="Convert",
            style="primary",
            command=self.convert_date
        )
        convert_btn.pack(pady=20)
        
        # Result frame
        result_frame = tk.Frame(self.dialog, bg=self.colors["secondary"])
        result_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))
        
        self.result_text = tk.Text(
            result_frame,
            height=10,
            font=("Segoe UI", 10),
            fg=self.colors["fg"],
            bg=self.colors["secondary"],
            relief="flat",
            wrap="word"
        )
        self.result_text.pack(fill="both", expand=True, padx=5, pady=5)
        self.result_text.config(state="disabled")
    
    def convert_date(self):
        """Convert date and show results"""
        try:
            # Parse input date
            date_str = self.date_var.get()
            year, month, day = map(int, date_str.split('/'))
            
            from_cal = CalendarType(self.from_cal_var.get())
            
            # Convert to selected calendars
            results = []
            for cal_type, var in self.to_vars.items():
                if var.get() and cal_type != from_cal:
                    try:
                        converted = self.converter.convert_date(year, month, day, from_cal, cal_type)
                        cal_name = self.calendar_names[cal_type]
                        results.append(f"{cal_name}: {converted[0]}/{converted[1]:02d}/{converted[2]:02d}")
                    except Exception as e:
                        results.append(f"{self.calendar_names[cal_type]}: Error - {str(e)}")
            
            # Display results
            self.result_text.config(state="normal")
            self.result_text.delete("1.0", tk.END)
            
            if results:
                self.result_text.insert("1.0", f"Original ({self.calendar_names[from_cal]}): {date_str}\n\n")
                self.result_text.insert("end", "Converted Dates:\n")
                for result in results:
                    self.result_text.insert("end", f"• {result}\n")
            else:
                self.result_text.insert("1.0", "Please select at least one target calendar.")
            
            self.result_text.config(state="disabled")
            
        except Exception as e:
            messagebox.showerror("Conversion Error", f"Invalid date format or conversion error: {str(e)}")

class CalendarSettingsDialog:
    """Calendar settings dialog"""
    
    def __init__(self, parent, config, colors):
        self.parent = parent
        self.config = config.copy()
        self.colors = colors
        self.dialog = None
    
    def show(self) -> bool:
        """Show dialog and return True if settings were saved"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Calendar Settings")
        self.dialog.geometry("500x600")
        self.dialog.configure(bg=self.colors["bg"])
        self.dialog.resizable(False, False)
        
        # Center dialog
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f'{width}x{height}+{x}+{y}')
        
        # Create content
        self.create_content()
        
        # Wait for dialog to close
        self.parent.wait_window(self.dialog)
        
        return hasattr(self, 'saved') and self.saved
    
    def create_content(self):
        """Create dialog content"""
        # Title
        title_label = tk.Label(
            self.dialog,
            text="Calendar Display Settings",
            font=("Segoe UI", 16, "bold"),
            fg=self.colors["accent"],
            bg=self.colors["bg"]
        )
        title_label.pack(pady=20)
        
        # Scrollable content
        canvas = tk.Canvas(self.dialog, bg=self.colors["bg"], highlightthickness=0)
        scrollbar = tk.Scrollbar(self.dialog, orient="vertical", command=canvas.yview)
        content_frame = tk.Frame(canvas, bg=self.colors["bg"])
        
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas.create_window((0, 0), window=content_frame, anchor="nw")
        
        def configure_scrollregion(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        content_frame.bind("<Configure>", configure_scrollregion)
        
        # Date sizes
        size_frame = tk.LabelFrame(
            content_frame,
            text="Date Sizes",
            font=("Segoe UI", 12, "bold"),
            fg=self.colors["fg"],
            bg=self.colors["bg"],
            relief="flat"
        )
        size_frame.pack(fill="x", padx=20, pady=10)
        
        # Primary date size
        primary_frame = tk.Frame(size_frame, bg=self.colors["bg"])
        primary_frame.pack(fill="x", pady=10, padx=10)
        
        tk.Label(
            primary_frame,
            text="Primary Date Size:",
            font=("Segoe UI", 11),
            fg=self.colors["fg"],
            bg=self.colors["bg"]
        ).pack(side="left")
        
        self.primary_size = tk.IntVar(value=self.config.get("date_size", 14))
        primary_scale = tk.Scale(
            primary_frame,
            from_=10,
            to=24,
            variable=self.primary_size,
            orient="horizontal",
            length=200,
            bg=self.colors["bg"],
            fg=self.colors["fg"]
        )
        primary_scale.pack(side="right")
        
        # Secondary date size
        secondary_frame = tk.Frame(size_frame, bg=self.colors["bg"])
        secondary_frame.pack(fill="x", pady=10, padx=10)
        
        tk.Label(
            secondary_frame,
            text="Secondary Date Size:",
            font=("Segoe UI", 11),
            fg=self.colors["fg"],
            bg=self.colors["bg"]
        ).pack(side="left")
        
        self.secondary_size = tk.IntVar(value=self.config.get("secondary_date_size", 9))
        secondary_scale = tk.Scale(
            secondary_frame,
            from_=6,
            to=14,
            variable=self.secondary_size,
            orient="horizontal",
            length=200,
            bg=self.colors["bg"],
            fg=self.colors["fg"]
        )
        secondary_scale.pack(side="right")
        
        # Display options
        options_frame = tk.LabelFrame(
            content_frame,
            text="Display Options",
            font=("Segoe UI", 12, "bold"),
            fg=self.colors["fg"],
            bg=self.colors["bg"],
            relief="flat"
        )
        options_frame.pack(fill="x", padx=20, pady=10)
        
        self.show_events = tk.BooleanVar(value=self.config.get("show_events", True))
        events_cb = tk.Checkbutton(
            options_frame,
            text="Show events and holidays",
            variable=self.show_events,
            font=("Segoe UI", 11),
            fg=self.colors["fg"],
            bg=self.colors["bg"],
            selectcolor=self.colors["bg"]
        )
        events_cb.pack(anchor="w", pady=5, padx=10)
        
        self.show_week = tk.BooleanVar(value=self.config.get("show_week_numbers", True))
        week_cb = tk.Checkbutton(
            options_frame,
            text="Show week numbers",
            variable=self.show_week,
            font=("Segoe UI", 11),
            fg=self.colors["fg"],
            bg=self.colors["bg"],
            selectcolor=self.colors["bg"]
        )
        week_cb.pack(anchor="w", pady=5, padx=10)
        
        self.show_multi = tk.BooleanVar(value=self.config.get("show_multiple_dates", True))
        multi_cb = tk.Checkbutton(
            options_frame,
            text="Show multiple calendar dates",
            variable=self.show_multi,
            font=("Segoe UI", 11),
            fg=self.colors["fg"],
            bg=self.colors["bg"],
            selectcolor=self.colors["bg"]
        )
        multi_cb.pack(anchor="w", pady=5, padx=10)
        
        self.show_sun = tk.BooleanVar(value=self.config.get("show_sun_times", True))
        sun_cb = tk.Checkbutton(
            options_frame,
            text="Show sunrise/sunset times",
            variable=self.show_sun,
            font=("Segoe UI", 11),
            fg=self.colors["fg"],
            bg=self.colors["bg"],
            selectcolor=self.colors["bg"]
        )
        sun_cb.pack(anchor="w", pady=5, padx=10)
        
        # Button frame
        button_frame = tk.Frame(content_frame, bg=self.colors["bg"])
        button_frame.pack(fill="x", padx=20, pady=20)
        
        # Save button
        save_btn = ModernButton(
            button_frame,
            text="Save Settings",
            style="primary",
            command=self.save_settings
        )
        save_btn.pack(side="right", padx=5)
        
        # Cancel button
        cancel_btn = ModernButton(
            button_frame,
            text="Cancel",
            style="secondary",
            command=self.cancel
        )
        cancel_btn.pack(side="right", padx=5)
    
    def save_settings(self):
        """Save settings"""
        self.config.update({
            "date_size": self.primary_size.get(),
            "secondary_date_size": self.secondary_size.get(),
            "show_events": self.show_events.get(),
            "show_week_numbers": self.show_week.get(),
            "show_multiple_dates": self.show_multi.get(),
            "show_sun_times": self.show_sun.get()
        })
        
        self.saved = True
        self.dialog.destroy()
    
    def cancel(self):
        """Cancel without saving"""
        self.saved = False
        self.dialog.destroy()
    
    def get_config(self):
        """Get updated configuration"""
        return self.config

# ============================================================================
# Main Application Class
# ============================================================================

class GlobalCalendarApplication:
    """Main application controller"""
    
    def __init__(self):
        self.version = "2.0.0"
        self.developer = "Hessamedien"
        self.instagram_url = "https://instagram.com/hessamedien"
        self.config_file = "global_calendar_config.json"
        self.config = self.load_config()
        self.root = None
        self.loading_screen = None
        self.main_app = None
        
    def load_config(self) -> Dict:
        """Load configuration from file"""
        default_config = {
            "language": "en",
            "primary_calendar": CalendarType.GREGORIAN.value,
            "secondary_calendars": [
                CalendarType.PERSIAN.value,
                CalendarType.ISLAMIC.value,
                CalendarType.CHINESE.value
            ],
            "display_mode": DisplayMode.STANDARD.value,
            "theme": ThemeMode.AUTO.value,
            "show_week_numbers": True,
            "show_moon_phases": False,
            "show_sun_times": True,
            "show_multiple_dates": True,
            "show_events": True,
            "date_size": 14,
            "secondary_date_size": 9,
            "auto_update": True,
            "notifications": True,
            "timezone": "UTC",
            "first_run": True,
            "version": self.version
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    
                    # Update with loaded config, keeping defaults for missing keys
                    for key in default_config:
                        if key not in loaded_config:
                            loaded_config[key] = default_config[key]
                    
                    return loaded_config
        except Exception as e:
            print(f"Error loading configuration: {e}")
        
        return default_config
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving configuration: {e}")
    
    def run_wizard(self):
        """Run setup wizard if first run"""
        if self.config.get("first_run", True):
            wizard = SetupWizard(self.config)
            wizard_result = wizard.run()
            
            if wizard_result:
                self.config.update(wizard_result)
                self.save_config()
    
    def show_loading_screen(self):
        """Show loading screen"""
        self.loading_screen = LoadingScreen(self.config)
        self.loading_screen.show()
        
        # Simulate loading tasks
        def loading_tasks():
            tasks = [
                ("Initializing calendar systems", 10),
                ("Loading configuration", 25),
                ("Setting up user interface", 45),
                ("Loading calendar events", 65),
                ("Preparing display", 85),
                ("Ready", 100)
            ]
            
            for task, progress in tasks:
                self.loading_screen.update_progress(progress, task)
                time.sleep(0.5)
            
            time.sleep(0.5)
            self.loading_screen.close()
        
        threading.Thread(target=loading_tasks, daemon=True).start()
        time.sleep(3)  # Minimum display time
    
    def show_credits(self):
        """Show application credits"""
        credits = f"""
        ========================================
            Global Calendar {self.version}
            Developer: {self.developer}
        ========================================
        
        Thank you for using Global Calendar!
        
        Features:
        • Support for 9 different calendar systems
        • Simultaneous display of 2-4 calendars
        • Multiple display modes and themes
        • Date conversion tools
        • Event and holiday management
        
        Instagram: {self.instagram_url}
        
        © 2024 - All rights reserved.
        """
        
        print(credits)
        
        # Save to file
        with open("credits.txt", "w", encoding="utf-8") as f:
            f.write(credits)
    
    def run(self):
        """Run the main application"""
        try:
            # Print welcome message
            print("=" * 50)
            print("Global Calendar by Hessamedien")
            print("Starting application...")
            print("=" * 50)
            
            # Run setup wizard if first run
            self.run_wizard()
            
            # Show loading screen
            self.show_loading_screen()
            
            # Show credits
            self.show_credits()
            
            # Create and run main application
            self.main_app = MultiCalendarApp(self.config)
            self.main_app.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.main_app.run()
            
        except Exception as e:
            messagebox.showerror("Application Error", f"An error occurred:\n{str(e)}")
            sys.exit(1)
    
    def on_closing(self):
        """Handle application closing"""
        self.save_config()
        
        if self.main_app:
            response = messagebox.askyesnocancel(
                "Exit Global Calendar",
                "Do you want to exit Global Calendar?\n\nSave settings before exiting?"
            )
            
            if response is not None:
                if response:  # Yes, save and exit
                    self.save_config()
                
                self.main_app.root.destroy()
                sys.exit()
        else:
            sys.exit()

# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main entry point"""
    app = GlobalCalendarApplication()
    app.run()

if __name__ == "__main__":
    main()