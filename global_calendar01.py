#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تقویم جهانی Hessamedien
توسعه‌دهنده: Hessamedien
صفحه اینستاگرام: https://instagram.com/hessamedien
نسخه: 1.0.0
"""

import sys
import os
import json
import time
import threading
import webbrowser
import datetime
import calendar as py_calendar
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import tkinter as tk
from tkinter import ttk, messagebox, font, filedialog, simpledialog
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

# ============================================================================
# کلاس‌های کمکی و ابزارها
# ============================================================================

class DateConverter:
    """مبدل تاریخ بین تقویم‌های مختلف"""
    
    @staticmethod
    def gregorian_to_persian(year, month, day):
        """تبدیل میلادی به شمسی"""
        try:
            jd = jdatetime.date.fromgregorian(year=year, month=month, day=day)
            return jd.year, jd.month, jd.day
        except:
            return year, month, day
    
    @staticmethod
    def persian_to_gregorian(year, month, day):
        """تبدیل شمسی به میلادی"""
        try:
            gd = jdatetime.date(year, month, day).togregorian()
            return gd.year, gd.month, gd.day
        except:
            return year, month, day
    
    @staticmethod
    def gregorian_to_hijri(year, month, day):
        """تبدیل میلادی به قمری"""
        try:
            hijri = hijri_converter.Hijri.fromgregorian(year, month, day)
            return hijri.year, hijri.month, hijri.day
        except:
            return year, month, day
    
    @staticmethod
    def hijri_to_gregorian(year, month, day):
        """تبدیل قمری به میلادی"""
        try:
            gregorian = hijri_converter.Hijri(year, month, day).to_gregorian()
            return gregorian.year, gregorian.month, gregorian.day
        except:
            return year, month, day
    
    @staticmethod
    def gregorian_to_chinese(year, month, day):
        """تبدیل میلادی به چینی (ساده شده)"""
        # این یک تبدیل ساده است. برای تبدیل دقیق نیاز به الگوریتم پیچیده‌تر است
        chinese_years = ["موش", "گاو", "ببر", "خرگوش", "اژدها", "مار", "اسب", 
                        "بز", "میمون", "خروس", "سگ", "خوک"]
        year_diff = year - 1900
        animal_index = (year_diff + 8) % 12
        return f"{chinese_years[animal_index]} {year}"
    
    @staticmethod
    def get_day_info(year, month, day):
        """دریافت اطلاعات روز"""
        date_obj = datetime(year, month, day)
        
        # روز هفته
        weekdays = ["دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه", "شنبه", "یکشنبه"]
        weekday = weekdays[date_obj.weekday()]
        
        # روز سال
        day_of_year = date_obj.timetuple().tm_yday
        
        # هفته سال
        week_of_year = date_obj.isocalendar()[1]
        
        return {
            'weekday': weekday,
            'day_of_year': day_of_year,
            'week_of_year': week_of_year,
            'is_weekend': date_obj.weekday() >= 5
        }

class CalendarAPI:
    """API برای دریافت مناسبت‌های تقویم"""
    
    def __init__(self):
        self.base_url = "https://www.timeanddate.com/holidays"
        self.cache = {}
    
    def get_events(self, year, calendar_type="persian"):
        """دریافت مناسبت‌های سال"""
        cache_key = f"{calendar_type}_{year}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            events = self._fetch_online_events(year, calendar_type)
        except:
            events = self._get_default_events(year, calendar_type)
        
        self.cache[cache_key] = events
        return events
    
    def _fetch_online_events(self, year, calendar_type):
        """دریافت مناسبت‌ها از اینترنت"""
        events = []
        
        try:
            if calendar_type == "persian":
                # مناسبت‌های ایرانی
                persian_events = [
                    {"date": f"{year}/1/1", "title": "عید نوروز", "type": "national"},
                    {"date": f"{year}/1/2", "title": "عید نوروز", "type": "national"},
                    {"date": f"{year}/1/3", "title": "عید نوروز", "type": "national"},
                    {"date": f"{year}/1/4", "title": "عید نوروز", "type": "national"},
                    {"date": f"{year}/1/12", "title": "روز جمهوری اسلامی", "type": "national"},
                    {"date": f"{year}/1/13", "title": "روز طبیعت", "type": "national"},
                    {"date": f"{year}/3/14", "title": "رحلت امام خمینی", "type": "religious"},
                    {"date": f"{year}/3/15", "title": "قیام ۱۵ خرداد", "type": "national"},
                    {"date": f"{year}/11/22", "title": "پیروزی انقلاب اسلامی", "type": "national"}
                ]
                events.extend(persian_events)
            
            elif calendar_type == "gregorian":
                # مناسبت‌های جهانی
                url = f"{self.base_url}/iran/{year}"
                response = requests.get(url, timeout=10)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                table = soup.find('table', {'id': 'holidays-table'})
                if table:
                    rows = table.find_all('tr')[1:]  # حذف هدر
                    for row in rows:
                        cols = row.find_all('td')
                        if len(cols) >= 3:
                            date_str = cols[0].text.strip()
                            title = cols[2].text.strip()
                            events.append({
                                "date": date_str,
                                "title": title,
                                "type": "international"
                            })
            
            elif calendar_type == "islamic":
                # مناسبت‌های اسلامی
                islamic_events = [
                    {"date": f"{year}/1/1", "title": "اول محرم", "type": "religious"},
                    {"date": f"{year}/1/9", "title": "تاسوعا", "type": "religious"},
                    {"date": f"{year}/1/10", "title": "عاشورا", "type": "religious"},
                    {"date": f"{year}/3/12", "title": "میلاد پیامبر اسلام", "type": "religious"},
                    {"date": f"{year}/3/17", "title": "میلاد امام صادق", "type": "religious"},
                    {"date": f"{year}/7/13", "title": "میلاد امام حسن مجتبی", "type": "religious"},
                    {"date": f"{year}/7/27", "title": "مبعث پیامبر اسلام", "type": "religious"},
                    {"date": f"{year}/9/21", "title": "شهادت امام علی", "type": "religious"},
                    {"date": f"{year}/10/1", "title": "عید فطر", "type": "religious"},
                    {"date": f"{year}/12/10", "title": "عید قربان", "type": "religious"},
                    {"date": f"{year}/12/18", "title": "عید غدیر", "type": "religious"}
                ]
                events.extend(islamic_events)
        
        except Exception as e:
            print(f"خطا در دریافت مناسبت‌ها: {e}")
        
        return events
    
    def _get_default_events(self, year, calendar_type):
        """مناسبت‌های پیش‌فرض در صورت عدم اتصال"""
        events = []
        
        if calendar_type == "persian":
            events = [
                {"date": f"{year}/1/1", "title": "عید نوروز", "type": "national"},
                {"date": f"{year}/1/2", "title": "عید نوروز", "type": "national"},
                {"date": f"{year}/1/3", "title": "عید نوروز", "type": "national"},
                {"date": f"{year}/1/4", "title": "عید نوروز", "type": "national"},
                {"date": f"{year}/1/12", "title": "روز جمهوری اسلامی", "type": "national"},
                {"date": f"{year}/1/13", "title": "روز طبیعت", "type": "national"},
            ]
        
        return events

class SunriseSunsetCalculator:
    """محاسبه طلوع و غروب خورشید"""
    
    @staticmethod
    def calculate(lat, lon, date_obj=None):
        """محاسبه زمان طلوع و غروب"""
        if date_obj is None:
            date_obj = datetime.now()
        
        # محاسبات ساده شده
        # در نسخه واقعی از فرمول دقیق استفاده می‌شود
        
        # فرضی: طلوع در ۶ صبح و غروب در ۶ عصر
        sunrise = date_obj.replace(hour=6, minute=0, second=0)
        sunset = date_obj.replace(hour=18, minute=0, second=0)
        
        # تنظیم بر اساس عرض جغرافیایی
        if lat > 0:  # نیمکره شمالی
            if date_obj.month in [6, 7, 8]:  # تابستان
                sunrise = sunrise.replace(hour=5, minute=30)
                sunset = sunset.replace(hour=19, minute=30)
            else:  # زمستان
                sunrise = sunrise.replace(hour=7, minute=30)
                sunset = sunset.replace(hour=16, minute=30)
        
        return {
            'sunrise': sunrise.strftime('%H:%M'),
            'sunset': sunset.strftime('%H:%M'),
            'day_length': '12:30'  # طول روز فرضی
        }

# ============================================================================
# کلاس‌های رابط کاربری
# ============================================================================

class ModernButton(tk.Button):
    """دکمه مدرن با استایل ویندوز ۱۱"""
    
    def __init__(self, master=None, **kwargs):
        style = kwargs.pop('style', 'primary')
        super().__init__(master, **kwargs)
        
        self.default_bg = {
            'primary': '#0078d4',
            'secondary': '#6c757d',
            'success': '#28a745',
            'danger': '#dc3545',
            'warning': '#ffc107',
            'info': '#17a2b8',
            'light': '#f8f9fa',
            'dark': '#343a40'
        }.get(style, '#0078d4')
        
        self.hover_bg = self._adjust_color(self.default_bg, 20)
        self.active_bg = self._adjust_color(self.default_bg, -20)
        
        self.configure(
            bg=self.default_bg,
            fg='white' if style not in ['light', 'warning'] else 'black',
            font=('Segoe UI', 10),
            relief='flat',
            bd=0,
            padx=20,
            pady=8,
            cursor='hand2'
        )
        
        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)
        self.bind('<ButtonPress-1>', self.on_press)
        self.bind('<ButtonRelease-1>', self.on_release)
    
    def _adjust_color(self, hex_color, adjustment):
        """تغییر روشنایی رنگ"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        new_rgb = tuple(max(0, min(255, x + adjustment)) for x in rgb)
        return '#%02x%02x%02x' % new_rgb
    
    def on_enter(self, e):
        self['bg'] = self.hover_bg
    
    def on_leave(self, e):
        self['bg'] = self.default_bg
    
    def on_press(self, e):
        self['bg'] = self.active_bg
    
    def on_release(self, e):
        self['bg'] = self.hover_bg if self.winfo_containing(e.x_root, e.y_root) == self else self.default_bg

class SetupWizard:
    """ویزارد تنظیمات اولیه"""
    
    def __init__(self, config):
        self.config = config
        self.wizard_window = None
        self.current_step = 0
        self.steps = [
            "خوش آمدگویی",
            "انتخاب زبان",
            "انتخاب تقویم",
            "انتخاب تم",
            "تنظیمات پیشرفته",
            "تکمیل نصب"
        ]
        
        # گزینه‌های موجود
        self.languages = [
            ("فارسی", "fa"),
            ("انگلیسی", "en"),
            ("عربی", "ar"),
            ("فرانسوی", "fr")
        ]
        
        self.calendars = [
            ("میلادی", "gregorian"),
            ("هجری شمسی", "persian"),
            ("هجری قمری", "islamic"),
            ("چینی", "chinese"),
            ("هندی", "indian"),
            ("ژاپنی", "japanese"),
            ("کره‌ای", "korean"),
            ("عبری", "hebrew")
        ]
        
        self.themes = [
            ("تیره ویندوز ۱۱", "win11_dark"),
            ("روشن ویندوز ۱۱", "win11_light"),
            ("آبی", "blue"),
            ("سبز", "green"),
            ("بنفش", "purple")
        ]
    
    def run(self):
        """اجرای ویزارد"""
        self.create_window()
        self.show_step(0)
        self.wizard_window.mainloop()
    
    def create_window(self):
        """ایجاد پنجره ویزارد"""
        self.wizard_window = tk.Toplevel()
        self.wizard_window.title("تنظیمات اولیه تقویم جهانی")
        self.wizard_window.geometry("800x600")
        self.wizard_window.resizable(False, False)
        self.wizard_window.configure(bg="#1e1e1e")
        
        # مرکز کردن پنجره
        self.wizard_window.update_idletasks()
        width = self.wizard_window.winfo_width()
        height = self.wizard_window.winfo_height()
        x = (self.wizard_window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.wizard_window.winfo_screenheight() // 2) - (height // 2)
        self.wizard_window.geometry(f'{width}x{height}+{x}+{y}')
        
        # جلوگیری از بستن
        self.wizard_window.protocol("WM_DELETE_WINDOW", lambda: None)
    
    def show_step(self, step):
        """نمایش مرحله"""
        self.current_step = step
        
        # پاک کردن ویجت‌ها
        for widget in self.wizard_window.winfo_children():
            widget.destroy()
        
        # هدر
        header_frame = tk.Frame(self.wizard_window, bg="#0078d4", height=80)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text=f"مرحله {step + 1} از {len(self.steps)}: {self.steps[step]}",
            font=("Segoe UI", 16, "bold"),
            fg="white",
            bg="#0078d4"
        )
        title_label.pack(expand=True, pady=20)
        
        # نوار پیشرفت
        progress_frame = tk.Frame(self.wizard_window, bg="#1e1e1e")
        progress_frame.pack(fill="x", padx=40, pady=(20, 10))
        
        progress = ttk.Progressbar(
            progress_frame,
            length=720,
            mode='determinate',
            maximum=len(self.steps),
            style="custom.Horizontal.TProgressbar"
        )
        progress['value'] = step + 1
        progress.pack()
        
        # استایل برای نوار پیشرفت
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("custom.Horizontal.TProgressbar",
                       background='#0078d4',
                       troughcolor='#333333',
                       bordercolor='#1e1e1e',
                       lightcolor='#0078d4',
                       darkcolor='#0078d4')
        
        # محتوا
        content_frame = tk.Frame(self.wizard_window, bg="#1e1e1e")
        content_frame.pack(fill="both", expand=True, padx=40, pady=20)
        
        if step == 0:
            self.show_welcome(content_frame)
        elif step == 1:
            self.show_language_selection(content_frame)
        elif step == 2:
            self.show_calendar_selection(content_frame)
        elif step == 3:
            self.show_theme_selection(content_frame)
        elif step == 4:
            self.show_advanced_settings(content_frame)
        elif step == 5:
            self.show_completion(content_frame)
        
        # دکمه‌های ناوبری
        nav_frame = tk.Frame(self.wizard_window, bg="#1e1e1e")
        nav_frame.pack(fill="x", padx=40, pady=(0, 20))
        
        if step > 0:
            prev_btn = ModernButton(
                nav_frame,
                text="◄ قبلی",
                style="secondary",
                command=lambda: self.show_step(step - 1)
            )
            prev_btn.pack(side="left", padx=5)
        
        if step < len(self.steps) - 1:
            next_btn = ModernButton(
                nav_frame,
                text="بعدی ►",
                style="primary",
                command=lambda: self.show_step(step + 1)
            )
            next_btn.pack(side="right", padx=5)
        else:
            finish_btn = ModernButton(
                nav_frame,
                text="اتمام و اجرای برنامه",
                style="success",
                command=self.finish
            )
            finish_btn.pack(side="right", padx=5)
    
    def show_welcome(self, parent):
        """نمایش مرحله خوش‌آمدگویی"""
        welcome_text = """به برنامه تقویم جهانی Hessamedien خوش آمدید!

این برنامه یک تقویم جامع با ویژگی‌های زیر است:
• پشتیبانی از ۸ تقویم مختلف (میلادی، شمسی، قمری، چینی، هندی و ...)
• نمایش اوقات شرعی و طلوع/غروب خورشید
• نمایش مناسبت‌های ملی و مذهبی
• رابط کاربری مدرن مطابق با ویندوز ۱۱
• قابلیت شخصی‌سازی کامل
• دریافت خودکار مناسبت‌ها از اینترنت

برای ادامه، روی دکمه 'بعدی' کلیک کنید."""
        
        text_widget = tk.Text(
            parent,
            height=15,
            font=("Segoe UI", 11),
            fg="white",
            bg="#2b2b2b",
            relief="flat",
            wrap="word",
            padx=20,
            pady=20
        )
        text_widget.insert("1.0", welcome_text)
        text_widget.config(state="disabled")
        text_widget.pack(fill="both", expand=True)
        
        # لوگوی برنامه
        logo_frame = tk.Frame(parent, bg="#1e1e1e")
        logo_frame.pack(pady=10)
        
        tk.Label(
            logo_frame,
            text="تقویم جهانی",
            font=("Segoe UI", 18, "bold"),
            fg="#0078d4",
            bg="#1e1e1e"
        ).pack(side="left", padx=5)
        
        tk.Label(
            logo_frame,
            text="Hessamedien",
            font=("Segoe UI", 14),
            fg="#cccccc",
            bg="#1e1e1e"
        ).pack(side="left", padx=5)
    
    def show_language_selection(self, parent):
        """نمایش انتخاب زبان"""
        tk.Label(
            parent,
            text="زبان برنامه را انتخاب کنید:",
            font=("Segoe UI", 14, "bold"),
            fg="white",
            bg="#1e1e1e"
        ).pack(anchor="w", pady=(0, 20))
        
        self.lang_var = tk.StringVar(value=self.config.get("language", "fa"))
        
        for lang_name, lang_code in self.languages:
            frame = tk.Frame(parent, bg="#1e1e1e")
            frame.pack(fill="x", pady=5)
            
            rb = tk.Radiobutton(
                frame,
                text=lang_name,
                variable=self.lang_var,
                value=lang_code,
                font=("Segoe UI", 12),
                fg="white",
                bg="#1e1e1e",
                selectcolor="#1e1e1e",
                activebackground="#1e1e1e",
                activeforeground="#0078d4",
                indicatoron=1
            )
            rb.pack(side="left")
    
    def show_calendar_selection(self, parent):
        """نمایش انتخاب تقویم"""
        tk.Label(
            parent,
            text="تقویم پیش‌فرض را انتخاب کنید:",
            font=("Segoe UI", 14, "bold"),
            fg="white",
            bg="#1e1e1e"
        ).pack(anchor="w", pady=(0, 20))
        
        self.cal_var = tk.StringVar(value=self.config.get("calendar_type", "persian"))
        
        # شبکه ۲ در ۴
        grid_frame = tk.Frame(parent, bg="#1e1e1e")
        grid_frame.pack(fill="both", expand=True)
        
        for i, (cal_name, cal_code) in enumerate(self.calendars):
            row = i // 4
            col = i % 4
            
            frame = tk.Frame(grid_frame, bg="#2b2b2b", relief="raised", bd=1)
            frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            
            rb = tk.Radiobutton(
                frame,
                text=cal_name,
                variable=self.cal_var,
                value=cal_code,
                font=("Segoe UI", 10),
                fg="white",
                bg="#2b2b2b",
                selectcolor="#2b2b2b",
                activebackground="#2b2b2b",
                activeforeground="#0078d4"
            )
            rb.pack(padx=10, pady=10)
            
            grid_frame.columnconfigure(col, weight=1)
            grid_frame.rowconfigure(row, weight=1)
    
    def show_theme_selection(self, parent):
        """نمایش انتخاب تم"""
        tk.Label(
            parent,
            text="تم برنامه را انتخاب کنید:",
            font=("Segoe UI", 14, "bold"),
            fg="white",
            bg="#1e1e1e"
        ).pack(anchor="w", pady=(0, 20))
        
        self.theme_var = tk.StringVar(value=self.config.get("theme", "win11_dark"))
        
        # نمایش تم‌ها
        themes_frame = tk.Frame(parent, bg="#1e1e1e")
        themes_frame.pack(fill="both", expand=True)
        
        theme_colors = {
            "win11_dark": ("#1e1e1e", "#0078d4", "تیره ویندوز ۱۱"),
            "win11_light": ("#f3f3f3", "#0078d4", "روشن ویندوز ۱۱"),
            "blue": ("#1e1e1e", "#0078d4", "آبی"),
            "green": ("#1e1e1e", "#107c10", "سبز"),
            "purple": ("#1e1e1e", "#8661c5", "بنفش")
        }
        
        for i, (theme_name, theme_code) in enumerate(self.themes):
            row = i // 2
            col = i % 2
            
            frame = tk.Frame(
                themes_frame,
                bg=theme_colors[theme_code][0],
                highlightthickness=2,
                highlightbackground="#555" if self.theme_var.get() != theme_code else theme_colors[theme_code][1]
            )
            frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            
            # نمونه رنگ
            color_sample = tk.Frame(frame, bg=theme_colors[theme_code][1], height=30)
            color_sample.pack(fill="x", padx=5, pady=(5, 2))
            
            rb = tk.Radiobutton(
                frame,
                text=theme_colors[theme_code][2],
                variable=self.theme_var,
                value=theme_code,
                font=("Segoe UI", 10),
                fg="white" if theme_code != "win11_light" else "black",
                bg=theme_colors[theme_code][0],
                selectcolor=theme_colors[theme_code][0],
                activebackground=theme_colors[theme_code][0],
                activeforeground=theme_colors[theme_code][1]
            )
            rb.pack(pady=5)
            
            themes_frame.columnconfigure(col, weight=1)
            themes_frame.rowconfigure(row, weight=1)
    
    def show_advanced_settings(self, parent):
        """نمایش تنظیمات پیشرفته"""
        tk.Label(
            parent,
            text="تنظیمات پیشرفته:",
            font=("Segoe UI", 14, "bold"),
            fg="white",
            bg="#1e1e1e"
        ).pack(anchor="w", pady=(0, 20))
        
        # منطقه زمانی
        tz_frame = tk.Frame(parent, bg="#1e1e1e")
        tz_frame.pack(fill="x", pady=10)
        
        tk.Label(
            tz_frame,
            text="منطقه زمانی:",
            font=("Segoe UI", 11),
            fg="white",
            bg="#1e1e1e",
            width=15
        ).pack(side="left")
        
        self.tz_var = tk.StringVar(value=self.config.get("timezone", "Asia/Tehran"))
        tz_combo = ttk.Combobox(
            tz_frame,
            textvariable=self.tz_var,
            values=["Asia/Tehran", "UTC", "Europe/London", "America/New_York", 
                   "Asia/Dubai", "Asia/Tokyo", "Europe/Paris", "Australia/Sydney"],
            state="readonly",
            width=30
        )
        tz_combo.pack(side="left", padx=10)
        
        # چک‌باکس‌ها
        options_frame = tk.Frame(parent, bg="#1e1e1e")
        options_frame.pack(fill="x", pady=10)
        
        self.show_events_var = tk.BooleanVar(value=self.config.get("show_events", True))
        events_cb = tk.Checkbutton(
            options_frame,
            text="نمایش مناسبت‌های تقویم",
            variable=self.show_events_var,
            font=("Segoe UI", 11),
            fg="white",
            bg="#1e1e1e",
            selectcolor="#1e1e1e",
            activebackground="#1e1e1e",
            activeforeground="white"
        )
        events_cb.pack(anchor="w", pady=5)
        
        self.show_sun_var = tk.BooleanVar(value=self.config.get("show_sunrise_sunset", True))
        sun_cb = tk.Checkbutton(
            options_frame,
            text="نمایش طلوع و غروب خورشید",
            variable=self.show_sun_var,
            font=("Segoe UI", 11),
            fg="white",
            bg="#1e1e1e",
            selectcolor="#1e1e1e",
            activebackground="#1e1e1e",
            activeforeground="white"
        )
        sun_cb.pack(anchor="w", pady=5)
        
        self.notify_var = tk.BooleanVar(value=self.config.get("notifications", True))
        notify_cb = tk.Checkbutton(
            options_frame,
            text="اعلان مناسبت‌ها",
            variable=self.notify_var,
            font=("Segoe UI", 11),
            fg="white",
            bg="#1e1e1e",
            selectcolor="#1e1e1e",
            activebackground="#1e1e1e",
            activeforeground="white"
        )
        notify_cb.pack(anchor="w", pady=5)
        
        self.auto_update_var = tk.BooleanVar(value=self.config.get("auto_update", True))
        update_cb = tk.Checkbutton(
            options_frame,
            text="بروزرسانی خودکار از اینترنت",
            variable=self.auto_update_var,
            font=("Segoe UI", 11),
            fg="white",
            bg="#1e1e1e",
            selectcolor="#1e1e1e",
            activebackground="#1e1e1e",
            activeforeground="white"
        )
        update_cb.pack(anchor="w", pady=5)
    
    def show_completion(self, parent):
        """نمایش مرحله تکمیل"""
        completion_text = f"""تنظیمات اولیه با موفقیت تکمیل شد!

خلاصه تنظیمات شما:
• زبان: {dict(self.languages).get(self.lang_var.get(), self.lang_var.get())}
• تقویم پیش‌فرض: {dict(self.calendars).get(self.cal_var.get(), self.cal_var.get())}
• تم: {dict(self.themes).get(self.theme_var.get(), self.theme_var.get())}
• منطقه زمانی: {self.tz_var.get()}

برنامه آماده اجراست. برای شروع روی دکمه 'اتمام' کلیک کنید.

توسعه‌دهنده: Hessamedien
صفحه اینستاگرام: https://instagram.com/hessamedien"""
        
        text_widget = tk.Text(
            parent,
            height=12,
            font=("Segoe UI", 11),
            fg="white",
            bg="#2b2b2b",
            relief="flat",
            wrap="word",
            padx=20,
            pady=20
        )
        text_widget.insert("1.0", completion_text)
        text_widget.config(state="disabled")
        text_widget.pack(fill="both", expand=True)
    
    def finish(self):
        """اتمام ویزارد"""
        # ذخیره تنظیمات
        self.config["language"] = self.lang_var.get()
        self.config["calendar_type"] = self.cal_var.get()
        self.config["theme"] = self.theme_var.get()
        self.config["timezone"] = self.tz_var.get()
        self.config["show_events"] = self.show_events_var.get()
        self.config["show_sunrise_sunset"] = self.show_sun_var.get()
        self.config["notifications"] = self.notify_var.get()
        self.config["auto_update"] = self.auto_update_var.get()
        self.config["first_run"] = False
        
        # بستن پنجره
        self.wizard_window.destroy()
    
    def get_config(self):
        """دریافت تنظیمات نهایی"""
        return self.config

class LoadingScreen:
    """صفحه لودینگ"""
    
    def __init__(self):
        self.window = None
        self.progress_var = None
    
    def show(self):
        """نمایش صفحه لودینگ"""
        self.window = tk.Toplevel()
        self.window.title("در حال بارگذاری...")
        self.window.geometry("500x350")
        self.window.resizable(False, False)
        self.window.configure(bg="#1e1e1e")
        
        # حذف نوار عنوان
        self.window.overrideredirect(True)
        
        # مرکز کردن
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')
        
        # ایجاد محتوا
        self.create_content()
        self.window.update()
    
    def create_content(self):
        """ایجاد محتوای صفحه لودینگ"""
        # عنوان
        title_frame = tk.Frame(self.window, bg="#1e1e1e")
        title_frame.pack(expand=True, fill="both")
        
        tk.Label(
            title_frame,
            text="تقویم جهانی",
            font=("Segoe UI", 24, "bold"),
            fg="#0078d4",
            bg="#1e1e1e"
        ).pack(pady=(40, 5))
        
        tk.Label(
            title_frame,
            text="Hessamedien",
            font=("Segoe UI", 18),
            fg="#cccccc",
            bg="#1e1e1e"
        ).pack()
        
        # انیمیشن دایره‌ای لودینگ
        self.canvas = tk.Canvas(
            self.window,
            width=80,
            height=80,
            bg="#1e1e1e",
            highlightthickness=0
        )
        self.canvas.pack(pady=20)
        
        # نقاشی دایره لودینگ
        self.loading_arc = self.canvas.create_arc(
            10, 10, 70, 70,
            start=0,
            extent=0,
            outline="#0078d4",
            width=4,
            style=tk.ARC
        )
        
        # متن وضعیت
        self.status_label = tk.Label(
            self.window,
            text="در حال بارگذاری...",
            font=("Segoe UI", 11),
            fg="#aaaaaa",
            bg="#1e1e1e"
        )
        self.status_label.pack(pady=(0, 10))
        
        # نوار پیشرفت
        self.progress_var = tk.IntVar(value=0)
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Loading.Horizontal.TProgressbar",
                       background='#0078d4',
                       troughcolor='#333333',
                       bordercolor='#1e1e1e',
                       lightcolor='#0078d4',
                       darkcolor='#0078d4')
        
        self.progress_bar = ttk.Progressbar(
            self.window,
            style="Loading.Horizontal.TProgressbar",
            variable=self.progress_var,
            maximum=100,
            mode='determinate',
            length=400
        )
        self.progress_bar.pack(pady=10)
        
        # درصد
        self.percent_label = tk.Label(
            self.window,
            text="0%",
            font=("Segoe UI", 10),
            fg="#888888",
            bg="#1e1e1e"
        )
        self.percent_label.pack()
        
        # زیرنویس
        tk.Label(
            self.window,
            text="© 2024 Hessamedien - Instagram: @hessamedien",
            font=("Segoe UI", 8),
            fg="#666666",
            bg="#1e1e1e"
        ).pack(side="bottom", pady=10)
        
        # شروع انیمیشن
        self.animate_loading(0)
    
    def animate_loading(self, angle):
        """انیمیشن دایره لودینگ"""
        self.canvas.delete(self.loading_arc)
        self.loading_arc = self.canvas.create_arc(
            10, 10, 70, 70,
            start=angle,
            extent=120,
            outline="#0078d4",
            width=4,
            style=tk.ARC
        )
        
        new_angle = (angle + 10) % 360
        self.window.after(50, lambda: self.animate_loading(new_angle))
    
    def update_progress(self, value):
        """بروزرسانی مقدار پیشرفت"""
        if self.progress_var:
            self.progress_var.set(value)
            self.percent_label.config(text=f"{value}%")
            
            # بروزرسانی متن وضعیت
            status_messages = [
                "در حال بارگذاری...",
                "در حال آماده‌سازی رابط کاربری...",
                "در حال بارگذاری تقویم‌ها...",
                "در حال دریافت مناسبت‌ها...",
                "در حال اعمال تنظیمات...",
                "آماده سازی نهایی..."
            ]
            
            index = min(int(value / 20), len(status_messages) - 1)
            self.status_label.config(text=status_messages[index])
            
            if self.window:
                self.window.update()
    
    def close(self):
        """بستن صفحه لودینگ"""
        if self.window:
            self.window.destroy()

class MainWindow:
    """پنجره اصلی برنامه"""
    
    def __init__(self, config, app_instance):
        self.config = config
        self.app = app_instance
        self.window = tk.Tk()
        self.window.title("تقویم جهانی Hessamedien")
        
        # تنظیم تم
        self.theme = config.get("theme", "win11_dark")
        self.apply_theme()
        
        # ابزارها
        self.date_converter = DateConverter()
        self.calendar_api = CalendarAPI()
        self.sun_calculator = SunriseSunsetCalculator()
        
        # متغیرها
        self.current_date = datetime.now()
        self.selected_date = self.current_date
        self.current_calendar = config.get("calendar_type", "persian")
        self.events = []
        self.notifications = []
        
        # ایجاد رابط کاربری
        self.setup_ui()
        
        # بارگذاری اولیه
        self.load_data()
    
    def apply_theme(self):
        """اعمال تم انتخاب شده"""
        themes = {
            "win11_dark": {
                "bg": "#1e1e1e",
                "fg": "#ffffff",
                "accent": "#0078d4",
                "secondary": "#2b2b2b",
                "text": "#cccccc"
            },
            "win11_light": {
                "bg": "#f3f3f3",
                "fg": "#000000",
                "accent": "#0078d4",
                "secondary": "#ffffff",
                "text": "#333333"
            },
            "blue": {
                "bg": "#1e1e1e",
                "fg": "#ffffff",
                "accent": "#0078d4",
                "secondary": "#2b2b2b",
                "text": "#cccccc"
            },
            "green": {
                "bg": "#1e1e1e",
                "fg": "#ffffff",
                "accent": "#107c10",
                "secondary": "#2b2b2b",
                "text": "#cccccc"
            },
            "purple": {
                "bg": "#1e1e1e",
                "fg": "#ffffff",
                "accent": "#8661c5",
                "secondary": "#2b2b2b",
                "text": "#cccccc"
            }
        }
        
        self.theme_colors = themes.get(self.theme, themes["win11_dark"])
        self.window.configure(bg=self.theme_colors["bg"])
    
    def setup_ui(self):
        """ایجاد رابط کاربری"""
        # تنظیم اندازه پنجره
        self.window.geometry("1200x800")
        
        # نوار منو
        self.setup_menu()
        
        # هدر
        self.setup_header()
        
        # بدنه اصلی
        self.setup_main_body()
        
        # فوتر
        self.setup_footer()
    
    def setup_menu(self):
        """ایجاد منوی برنامه"""
        menubar = tk.Menu(self.window)
        self.window.config(menu=menubar)
        
        # منوی فایل
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="فایل", menu=file_menu)
        file_menu.add_command(label="ذخیره", command=self.save_data)
        file_menu.add_command(label="خروجی چاپ", command=self.print_calendar)
        file_menu.add_separator()
        file_menu.add_command(label="خروج", command=self.app.on_closing)
        
        # منوی نمایش
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="نمایش", menu=view_menu)
        
        # زیرمنوی تقویم
        calendar_submenu = tk.Menu(view_menu, tearoff=0)
        view_menu.add_cascade(label="نوع تقویم", menu=calendar_submenu)
        
        calendar_types = [
            ("میلادی", "gregorian"),
            ("هجری شمسی", "persian"),
            ("هجری قمری", "islamic"),
            ("چینی", "chinese"),
            ("هندی", "indian")
        ]
        
        for name, code in calendar_types:
            calendar_submenu.add_radiobutton(
                label=name,
                variable=tk.StringVar(value=self.current_calendar),
                value=code,
                command=lambda c=code: self.change_calendar(c)
            )
        
        # زیرمنوی تم
        theme_submenu = tk.Menu(view_menu, tearoff=0)
        view_menu.add_cascade(label="تم", menu=theme_submenu)
        
        themes = [
            ("تیره ویندوز ۱۱", "win11_dark"),
            ("روشن ویندوز ۱۱", "win11_light"),
            ("آبی", "blue"),
            ("سبز", "green"),
            ("بنفش", "purple")
        ]
        
        for name, code in themes:
            theme_submenu.add_radiobutton(
                label=name,
                variable=tk.StringVar(value=self.theme),
                value=code,
                command=lambda c=code: self.change_theme(c)
            )
        
        view_menu.add_separator()
        view_menu.add_checkbutton(label="نمایش مناسبت‌ها", 
                                 variable=tk.BooleanVar(value=self.config.get("show_events", True)),
                                 command=self.toggle_events)
        view_menu.add_checkbutton(label="نمایش طلوع/غروب", 
                                 variable=tk.BooleanVar(value=self.config.get("show_sunrise_sunset", True)),
                                 command=self.toggle_sun_times)
        
        # منوی ابزارها
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ابزارها", menu=tools_menu)
        tools_menu.add_command(label="مبدل تاریخ", command=self.show_date_converter)
        tools_menu.add_command(label="تنظیمات منطقه", command=self.show_location_settings)
        tools_menu.add_command(label="تنظیمات اعلان", command=self.show_notification_settings)
        
        # منوی راهنما
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="راهنما", menu=help_menu)
        help_menu.add_command(label="راهنمای برنامه", command=self.show_help)
        help_menu.add_command(label="درباره برنامه", command=self.show_about)
        help_menu.add_separator()
        help_menu.add_command(label="صفحه اینستاگرام", 
                             command=lambda: webbrowser.open("https://instagram.com/hessamedien"))
    
    def setup_header(self):
        """ایجاد هدر برنامه"""
        header_frame = tk.Frame(self.window, bg=self.theme_colors["accent"], height=60)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        # عنوان
        title_label = tk.Label(
            header_frame,
            text="تقویم جهانی Hessamedien",
            font=("Segoe UI", 18, "bold"),
            fg="white",
            bg=self.theme_colors["accent"]
        )
        title_label.pack(side="right", padx=20)
        
        # تاریخ جاری
        self.date_label = tk.Label(
            header_frame,
            text=self.format_date(self.current_date),
            font=("Segoe UI", 12),
            fg="white",
            bg=self.theme_colors["accent"]
        )
        self.date_label.pack(side="left", padx=20)
        
        # زمان جاری
        self.time_label = tk.Label(
            header_frame,
            text=datetime.now().strftime("%H:%M:%S"),
            font=("Segoe UI", 12),
            fg="white",
            bg=self.theme_colors["accent"]
        )
        self.time_label.pack(side="left", padx=10)
        
        # بروزرسانی زمان
        self.update_time()
    
    def setup_main_body(self):
        """ایجاد بدنه اصلی"""
        main_frame = tk.Frame(self.window, bg=self.theme_colors["bg"])
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # پنل سمت چپ
        left_panel = tk.Frame(main_frame, bg=self.theme_colors["secondary"], width=300)
        left_panel.pack(side="left", fill="y", padx=(0, 10))
        left_panel.pack_propagate(False)
        
        self.setup_left_panel(left_panel)
        
        # پنل مرکزی (تقویم)
        center_panel = tk.Frame(main_frame, bg=self.theme_colors["bg"])
        center_panel.pack(side="left", fill="both", expand=True)
        
        self.setup_calendar_panel(center_panel)
        
        # پنل سمت راست
        right_panel = tk.Frame(main_frame, bg=self.theme_colors["secondary"], width=300)
        right_panel.pack(side="right", fill="y", padx=(10, 0))
        right_panel.pack_propagate(False)
        
        self.setup_right_panel(right_panel)
    
    def setup_left_panel(self, parent):
        """ایجاد پنل سمت چپ"""
        # ناوبری ماه
        nav_frame = tk.Frame(parent, bg=self.theme_colors["secondary"])
        nav_frame.pack(fill="x", padx=10, pady=10)
        
        prev_btn = ModernButton(
            nav_frame,
            text="◄ ماه قبل",
            style="primary",
            command=self.prev_month
        )
        prev_btn.pack(side="left", padx=5)
        
        next_btn = ModernButton(
            nav_frame,
            text="ماه بعد ►",
            style="primary",
            command=self.next_month
        )
        next_btn.pack(side="right", padx=5)
        
        # نمایش ماه و سال
        self.month_year_label = tk.Label(
            nav_frame,
            text="",
            font=("Segoe UI", 14, "bold"),
            fg=self.theme_colors["text"],
            bg=self.theme_colors["secondary"]
        )
        self.month_year_label.pack(expand=True)
        
        # انتخابگر تاریخ
        date_frame = tk.Frame(parent, bg=self.theme_colors["secondary"])
        date_frame.pack(fill="x", padx=10, pady=10)
        
        tk.Label(
            date_frame,
            text="انتخاب تاریخ:",
            font=("Segoe UI", 12),
            fg=self.theme_colors["text"],
            bg=self.theme_colors["secondary"]
        ).pack(anchor="w")
        
        # تقویم کوچک
        self.mini_calendar = tk.Frame(date_frame, bg=self.theme_colors["secondary"])
        self.mini_calendar.pack(fill="x", pady=5)
        
        # دکمه امروز
        today_btn = ModernButton(
            date_frame,
            text="امروز",
            style="success",
            command=self.go_to_today
        )
        today_btn.pack(fill="x", pady=5)
        
        # اطلاعات روز
        info_frame = tk.LabelFrame(
            parent,
            text="اطلاعات روز",
            font=("Segoe UI", 12),
            fg=self.theme_colors["text"],
            bg=self.theme_colors["secondary"],
            relief="flat"
        )
        info_frame.pack(fill="x", padx=10, pady=10)
        
        self.day_info_text = tk.Text(
            info_frame,
            height=8,
            font=("Segoe UI", 10),
            fg=self.theme_colors["text"],
            bg=self.theme_colors["secondary"],
            relief="flat",
            wrap="word"
        )
        self.day_info_text.pack(fill="both", padx=5, pady=5)
        self.day_info_text.config(state="disabled")
    
    def setup_calendar_panel(self, parent):
        """ایجاد پنل تقویم"""
        # هفته‌ها
        weekdays_frame = tk.Frame(parent, bg=self.theme_colors["bg"])
        weekdays_frame.pack(fill="x")
        
        weekdays = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه"]
        for day in weekdays:
            day_label = tk.Label(
                weekdays_frame,
                text=day,
                font=("Segoe UI", 11, "bold"),
                fg=self.theme_colors["accent"],
                bg=self.theme_colors["bg"],
                width=15,
                height=2
            )
            day_label.pack(side="left", fill="both", expand=True)
        
        # روزهای ماه
        self.calendar_frame = tk.Frame(parent, bg=self.theme_colors["bg"])
        self.calendar_frame.pack(fill="both", expand=True)
        
        # ایجاد 6 ردیف برای روزها
        self.day_buttons = []
        for i in range(6):
            row = []
            for j in range(7):
                btn_frame = tk.Frame(self.calendar_frame, bg=self.theme_colors["bg"])
                btn_frame.grid(row=i, column=j, padx=2, pady=2, sticky="nsew")
                
                btn = tk.Label(
                    btn_frame,
                    text="",
                    font=("Segoe UI", 11),
                    width=5,
                    height=3,
                    relief="flat",
                    cursor="hand2"
                )
                btn.pack(fill="both", expand=True)
                btn.bind("<Button-1>", lambda e, r=i, c=j: self.on_day_click(r, c))
                
                row.append(btn)
            
            self.day_buttons.append(row)
            
            # تنظیم وزن سطرها و ستون‌ها
            self.calendar_frame.rowconfigure(i, weight=1)
            self.calendar_frame.columnconfigure(j, weight=1)
    
    def setup_right_panel(self, parent):
        """ایجاد پنل سمت راست"""
        # مناسبت‌ها
        events_frame = tk.LabelFrame(
            parent,
            text="مناسبت‌ها",
            font=("Segoe UI", 12),
            fg=self.theme_colors["text"],
            bg=self.theme_colors["secondary"],
            relief="flat"
        )
        events_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # اسکرول‌بار برای مناسبت‌ها
        events_canvas = tk.Canvas(
            events_frame,
            bg=self.theme_colors["secondary"],
            highlightthickness=0
        )
        scrollbar = tk.Scrollbar(events_frame, orient="vertical", command=events_canvas.yview)
        self.events_content = tk.Frame(events_canvas, bg=self.theme_colors["secondary"])
        
        events_canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        events_canvas.pack(side="left", fill="both", expand=True)
        
        events_canvas.create_window((0, 0), window=self.events_content, anchor="nw")
        
        def configure_scrollregion(event):
            events_canvas.configure(scrollregion=events_canvas.bbox("all"))
        
        self.events_content.bind("<Configure>", configure_scrollregion)
        
        # اطلاعات نجومی
        if self.config.get("show_sunrise_sunset", True):
            astro_frame = tk.LabelFrame(
                parent,
                text="اطلاعات نجومی",
                font=("Segoe UI", 12),
                fg=self.theme_colors["text"],
                bg=self.theme_colors["secondary"],
                relief="flat"
            )
            astro_frame.pack(fill="x", padx=10, pady=10)
            
            self.sun_info_text = tk.Text(
                astro_frame,
                height=6,
                font=("Segoe UI", 10),
                fg=self.theme_colors["text"],
                bg=self.theme_colors["secondary"],
                relief="flat",
                wrap="word"
            )
            self.sun_info_text.pack(fill="both", padx=5, pady=5)
            self.sun_info_text.config(state="disabled")
        
        # مبدل سریع
        converter_frame = tk.LabelFrame(
            parent,
            text="مبدل سریع تاریخ",
            font=("Segoe UI", 12),
            fg=self.theme_colors["text"],
            bg=self.theme_colors["secondary"],
            relief="flat"
        )
        converter_frame.pack(fill="x", padx=10, pady=10)
        
        # ورودی تاریخ
        input_frame = tk.Frame(converter_frame, bg=self.theme_colors["secondary"])
        input_frame.pack(fill="x", padx=5, pady=5)
        
        tk.Label(
            input_frame,
            text="تاریخ:",
            font=("Segoe UI", 10),
            fg=self.theme_colors["text"],
            bg=self.theme_colors["secondary"]
        ).pack(side="left")
        
        self.converter_date = tk.Entry(input_frame, width=15, font=("Segoe UI", 10))
        self.converter_date.pack(side="left", padx=5)
        self.converter_date.insert(0, self.current_date.strftime("%Y/%m/%d"))
        
        convert_btn = ModernButton(
            converter_frame,
            text="تبدیل",
            style="info",
            command=self.quick_convert
        )
        convert_btn.pack(fill="x", padx=5, pady=5)
        
        # نتیجه
        self.converter_result = tk.Text(
            converter_frame,
            height=4,
            font=("Segoe UI", 9),
            fg=self.theme_colors["text"],
            bg=self.theme_colors["secondary"],
            relief="flat",
            wrap="word"
        )
        self.converter_result.pack(fill="both", padx=5, pady=5)
        self.converter_result.config(state="disabled")
    
    def setup_footer(self):
        """ایجاد فوتر"""
        footer_frame = tk.Frame(self.window, bg=self.theme_colors["secondary"], height=40)
        footer_frame.pack(fill="x", side="bottom")
        footer_frame.pack_propagate(False)
        
        # وضعیت
        self.status_label = tk.Label(
            footer_frame,
            text="آماده",
            font=("Segoe UI", 10),
            fg=self.theme_colors["text"],
            bg=self.theme_colors["secondary"]
        )
        self.status_label.pack(side="right", padx=20)
        
        # اطلاعات سازنده
        creator_label = tk.Label(
            footer_frame,
            text="توسعه‌دهنده: Hessamedien",
            font=("Segoe UI", 10),
            fg=self.theme_colors["accent"],
            bg=self.theme_colors["secondary"],
            cursor="hand2"
        )
        creator_label.pack(side="left", padx=20)
        creator_label.bind("<Button-1>", lambda e: webbrowser.open("https://instagram.com/hessamedien"))
        
        # نسخه
        version_label = tk.Label(
            footer_frame,
            text="نسخه 1.0.0",
            font=("Segoe UI", 10),
            fg=self.theme_colors["text"],
            bg=self.theme_colors["secondary"]
        )
        version_label.pack(side="left", padx=20)
    
    def load_data(self):
        """بارگذاری داده‌ها"""
        # به‌روزرسانی تقویم
        self.update_calendar()
        
        # دریافت مناسبت‌ها
        if self.config.get("show_events", True):
            threading.Thread(target=self.load_events, daemon=True).start()
        
        # دریافت اطلاعات نجومی
        if self.config.get("show_sunrise_sunset", True):
            self.update_astronomical_info()
    
    def update_calendar(self):
        """به‌روزرسانی نمایش تقویم"""
        year = self.selected_date.year
        month = self.selected_date.month
        
        # به‌روزرسانی عنوان ماه و سال
        month_names = {
            "gregorian": ["ژانویه", "فوریه", "مارس", "آوریل", "مه", "ژوئن", 
                         "ژوئیه", "آگوست", "سپتامبر", "اکتبر", "نوامبر", "دسامبر"],
            "persian": ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
                       "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"],
            "islamic": ["محرم", "صفر", "ربیع‌الاول", "ربیع‌الثانی", "جمادی‌الاول", 
                       "جمادی‌الثانی", "رجب", "شعبان", "رمضان", "شوال", "ذی‌القعده", "ذی‌الحجه"]
        }
        
        cal_type = self.current_calendar
        if cal_type in month_names:
            month_name = month_names[cal_type][month - 1]
        else:
            month_name = f"ماه {month}"
        
        self.month_year_label.config(text=f"{month_name} {year}")
        
        # محاسبه روزهای ماه
        if cal_type == "persian":
            # تقویم شمسی
            try:
                jd = jdatetime.date(year, month, 1)
                days_in_month = jd.daysinmonth
                first_weekday = (jd.weekday() + 2) % 7  # تنظیم برای شروع از شنبه
            except:
                days_in_month = 30
                first_weekday = 0
        elif cal_type == "islamic":
            # تقویم قمری (ساده شده)
            days_in_month = 30 if month % 2 == 0 else 29
            first_weekday = 0  # فرضی
        else:
            # تقویم میلادی و سایرین
            days_in_month = py_calendar.monthrange(year, month)[1]
            first_weekday = (datetime(year, month, 1).weekday() + 2) % 7  # شروع از شنبه
        
        # پر کردن روزها
        day_num = 1
        today = datetime.now()
        
        for i in range(6):
            for j in range(7):
                btn = self.day_buttons[i][j]
                day_frame = btn.master
                
                if i == 0 and j < first_weekday:
                    # روزهای قبل از ماه
                    btn.config(text="", bg=self.theme_colors["bg"])
                    day_frame.config(bg=self.theme_colors["bg"])
                elif day_num <= days_in_month:
                    # روزهای ماه
                    btn.config(text=str(day_num))
                    
                    # بررسی امروز
                    is_today = False
                    if cal_type == "persian":
                        try:
                            persian_today = jdatetime.date.today()
                            is_today = (year == persian_today.year and 
                                       month == persian_today.month and 
                                       day_num == persian_today.day)
                        except:
                            pass
                    elif cal_type == "gregorian":
                        is_today = (year == today.year and 
                                   month == today.month and 
                                   day_num == today.day)
                    
                    # تنظیم رنگ
                    if is_today:
                        bg_color = self.theme_colors["accent"]
                        fg_color = "white"
                    elif j == 6:  # جمعه
                        bg_color = "#3a3a3a" if self.theme == "win11_dark" else "#f0f0f0"
                        fg_color = "#ff6b6b" if self.theme == "win11_dark" else "#ff0000"
                    else:
                        bg_color = self.theme_colors["secondary"]
                        fg_color = self.theme_colors["text"]
                    
                    btn.config(bg=bg_color, fg=fg_color)
                    day_frame.config(bg=bg_color)
                    
                    # بررسی مناسبت
                    event_date = f"{year}/{month}/{day_num}"
                    has_event = any(event["date"] == event_date for event in self.events)
                    
                    if has_event:
                        btn.config(fg="#ffcc00")  # رنگ زرد برای مناسبت
                    
                    day_num += 1
                else:
                    # روزهای بعد از ماه
                    btn.config(text="", bg=self.theme_colors["bg"])
                    day_frame.config(bg=self.theme_colors["bg"])
        
        # به‌روزرسانی اطلاعات روز انتخابی
        self.update_day_info()
    
    def load_events(self):
        """بارگذاری مناسبت‌ها"""
        try:
            year = self.selected_date.year
            events = self.calendar_api.get_events(year, self.current_calendar)
            self.events = events
            
            # به‌روزرسانی نمایش مناسبت‌ها
            self.update_events_display()
            
            # به‌روزرسانی وضعیت
            self.status_label.config(text=f"{len(events)} مناسبت بارگذاری شد")
        except Exception as e:
            self.status_label.config(text=f"خطا در بارگذاری مناسبت‌ها: {e}")
    
    def update_events_display(self):
        """به‌روزرسانی نمایش مناسبت‌ها"""
        # پاک کردن ویجت‌های قبلی
        for widget in self.events_content.winfo_children():
            widget.destroy()
        
        if not self.events:
            no_events = tk.Label(
                self.events_content,
                text="هیچ مناسبتی برای نمایش وجود ندارد",
                font=("Segoe UI", 10),
                fg=self.theme_colors["text"],
                bg=self.theme_colors["secondary"]
            )
            no_events.pack(pady=10)
            return
        
        # نمایش مناسبت‌های ماه جاری
        month_events = []
        for event in self.events:
            try:
                event_date = event["date"]
                if f"/{self.selected_date.month}/" in event_date:
                    month_events.append(event)
            except:
                pass
        
        # مرتب‌سازی بر اساس تاریخ
        month_events.sort(key=lambda x: x["date"])
        
        for event in month_events[:10]:  # حداکثر 10 مناسبت
            event_frame = tk.Frame(self.events_content, bg=self.theme_colors["secondary"])
            event_frame.pack(fill="x", padx=5, pady=2)
            
            # نشانگر نوع مناسبت
            color = "#0078d4" if event.get("type") == "national" else "#28a745"
            indicator = tk.Frame(event_frame, bg=color, width=3, height=20)
            indicator.pack(side="left", fill="y", padx=(0, 5))
            
            # اطلاعات مناسبت
            info_label = tk.Label(
                event_frame,
                text=f"{event['date']}: {event['title'][:30]}...",
                font=("Segoe UI", 9),
                fg=self.theme_colors["text"],
                bg=self.theme_colors["secondary"],
                anchor="w"
            )
            info_label.pack(side="left", fill="x", expand=True)
            
            # دکمه اطلاعات بیشتر
            more_btn = tk.Button(
                event_frame,
                text="...",
                font=("Segoe UI", 8),
                fg=self.theme_colors["accent"],
                bg=self.theme_colors["secondary"],
                relief="flat",
                cursor="hand2"
            )
            more_btn.pack(side="right")
            more_btn.bind("<Button-1>", lambda e, ev=event: self.show_event_details(ev))
    
    def update_day_info(self):
        """به‌روزرسانی اطلاعات روز"""
        year = self.selected_date.year
        month = self.selected_date.month
        day = self.selected_date.day
        
        # اطلاعات روز
        day_info = self.date_converter.get_day_info(year, month, day)
        
        # تاریخ در تقویم‌های مختلف
        if self.current_calendar == "persian":
            gregorian_date = self.date_converter.persian_to_gregorian(year, month, day)
            hijri_date = self.date_converter.gregorian_to_hijri(*gregorian_date)
            chinese_date = self.date_converter.gregorian_to_chinese(*gregorian_date)
            
            info_text = f"""
            تاریخ شمسی: {year}/{month:02d}/{day:02d}
            روز هفته: {day_info['weekday']}
            
            تاریخ میلادی: {gregorian_date[0]}/{gregorian_date[1]:02d}/{gregorian_date[2]:02d}
            تاریخ قمری: {hijri_date[0]}/{hijri_date[1]:02d}/{hijri_date[2]:02d}
            سال چینی: {chinese_date}
            
            روز {day_info['day_of_year']} از سال
            هفته {day_info['week_of_year']} از سال
            """
        else:
            info_text = f"""
            تاریخ: {year}/{month:02d}/{day:02d}
            روز هفته: {day_info['weekday']}
            
            روز {day_info['day_of_year']} از سال
            هفته {day_info['week_of_year']} از سال
            """
        
        self.day_info_text.config(state="normal")
        self.day_info_text.delete("1.0", tk.END)
        self.day_info_text.insert("1.0", info_text)
        self.day_info_text.config(state="disabled")
    
    def update_astronomical_info(self):
        """به‌روزرسانی اطلاعات نجومی"""
        # موقعیت فرضی (تهران)
        lat = 35.6892
        lon = 51.3890
        
        sun_times = self.sun_calculator.calculate(lat, lon, self.selected_date)
        
        info_text = f"""
        طلوع خورشید: {sun_times['sunrise']}
        غروب خورشید: {sun_times['sunset']}
        طول روز: {sun_times['day_length']}
        
        موقعیت:
        عرض جغرافیایی: {lat}°
        طول جغرافیایی: {lon}°
        شهر: تهران
        """
        
        if hasattr(self, 'sun_info_text'):
            self.sun_info_text.config(state="normal")
            self.sun_info_text.delete("1.0", tk.END)
            self.sun_info_text.insert("1.0", info_text)
            self.sun_info_text.config(state="disabled")
    
    def update_time(self):
        """به‌روزرسانی زمان"""
        current_time = datetime.now().strftime("%H:%M:%S")
        self.time_label.config(text=current_time)
        self.window.after(1000, self.update_time)
    
    def format_date(self, date_obj):
        """فرمت‌دهی تاریخ"""
        if self.current_calendar == "persian":
            try:
                jd = jdatetime.date.fromgregorian(
                    year=date_obj.year,
                    month=date_obj.month,
                    day=date_obj.day
                )
                return f"{jd.year}/{jd.month:02d}/{jd.day:02d}"
            except:
                return date_obj.strftime("%Y/%m/%d")
        else:
            return date_obj.strftime("%Y/%m/%d")
    
    # ============================================================================
    # کنترل‌های تعاملی
    # ============================================================================
    
    def prev_month(self):
        """ماه قبل"""
        if self.current_calendar == "persian":
            # برای تقویم شمسی
            try:
                jd = jdatetime.date.fromgregorian(
                    year=self.selected_date.year,
                    month=self.selected_date.month,
                    day=self.selected_date.day
                )
                if jd.month == 1:
                    new_year = jd.year - 1
                    new_month = 12
                else:
                    new_year = jd.year
                    new_month = jd.month - 1
                
                new_date = jdatetime.date(new_year, new_month, 1).togregorian()
                self.selected_date = new_date
            except:
                # در صورت خطا، یک ماه از میلادی کم می‌کنیم
                if self.selected_date.month == 1:
                    self.selected_date = self.selected_date.replace(year=self.selected_date.year - 1, month=12)
                else:
                    self.selected_date = self.selected_date.replace(month=self.selected_date.month - 1)
        else:
            # برای سایر تقویم‌ها
            if self.selected_date.month == 1:
                self.selected_date = self.selected_date.replace(year=self.selected_date.year - 1, month=12)
            else:
                self.selected_date = self.selected_date.replace(month=self.selected_date.month - 1)
        
        self.update_calendar()
        self.load_events()
    
    def next_month(self):
        """ماه بعد"""
        if self.current_calendar == "persian":
            # برای تقویم شمسی
            try:
                jd = jdatetime.date.fromgregorian(
                    year=self.selected_date.year,
                    month=self.selected_date.month,
                    day=self.selected_date.day
                )
                if jd.month == 12:
                    new_year = jd.year + 1
                    new_month = 1
                else:
                    new_year = jd.year
                    new_month = jd.month + 1
                
                new_date = jdatetime.date(new_year, new_month, 1).togregorian()
                self.selected_date = new_date
            except:
                # در صورت خطا، یک ماه به میلادی اضافه می‌کنیم
                if self.selected_date.month == 12:
                    self.selected_date = self.selected_date.replace(year=self.selected_date.year + 1, month=1)
                else:
                    self.selected_date = self.selected_date.replace(month=self.selected_date.month + 1)
        else:
            # برای سایر تقویم‌ها
            if self.selected_date.month == 12:
                self.selected_date = self.selected_date.replace(year=self.selected_date.year + 1, month=1)
            else:
                self.selected_date = self.selected_date.replace(month=self.selected_date.month + 1)
        
        self.update_calendar()
        self.load_events()
    
    def go_to_today(self):
        """برو به امروز"""
        self.selected_date = datetime.now()
        self.update_calendar()
        self.load_events()
        self.status_label.config(text="برو به امروز")
    
    def on_day_click(self, row, col):
        """روز کلیک شده"""
        # محاسبه روز بر اساس موقعیت در شبکه
        year = self.selected_date.year
        month = self.selected_date.month
        
        if self.current_calendar == "persian":
            try:
                jd = jdatetime.date.fromgregorian(year=year, month=month, day=1)
                days_in_month = jd.daysinmonth
                first_weekday = (jd.weekday() + 2) % 7
            except:
                days_in_month = 30
                first_weekday = 0
        else:
            days_in_month = py_calendar.monthrange(year, month)[1]
            first_weekday = (datetime(year, month, 1).weekday() + 2) % 7
        
        day_num = (row * 7) + col - first_weekday + 1
        
        if 1 <= day_num <= days_in_month:
            self.selected_date = datetime(year, month, day_num)
            self.update_day_info()
            self.status_label.config(text=f"روز {day_num} انتخاب شد")
    
    def change_calendar(self, calendar_type):
        """تغییر نوع تقویم"""
        self.current_calendar = calendar_type
        self.config["calendar_type"] = calendar_type
        self.update_calendar()
        self.load_events()
        self.status_label.config(text=f"تقویم تغییر کرد به: {calendar_type}")
    
    def change_theme(self, theme):
        """تغییر تم"""
        self.theme = theme
        self.config["theme"] = theme
        self.apply_theme()
        
        # به‌روزرسانی تمام ویجت‌ها
        self.update_calendar()
        self.status_label.config(text=f"تم تغییر کرد به: {theme}")
    
    def toggle_events(self):
        """تغییر حالت نمایش مناسبت‌ها"""
        self.config["show_events"] = not self.config.get("show_events", True)
        if self.config["show_events"]:
            self.load_events()
        else:
            self.events = []
            self.update_events_display()
    
    def toggle_sun_times(self):
        """تغییر حالت نمایش طلوع/غروب"""
        self.config["show_sunrise_sunset"] = not self.config.get("show_sunrise_sunset", True)
        if self.config["show_sunrise_sunset"]:
            self.update_astronomical_info()
    
    def quick_convert(self):
        """تبدیل سریع تاریخ"""
        date_str = self.converter_date.get()
        
        try:
            if "/" in date_str:
                parts = date_str.split("/")
                year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
            else:
                year, month, day = datetime.now().year, datetime.now().month, datetime.now().day
            
            # تبدیل به میلادی
            if self.current_calendar == "persian":
                gregorian = self.date_converter.persian_to_gregorian(year, month, day)
                hijri = self.date_converter.gregorian_to_hijri(*gregorian)
                result = f"""
                میلادی: {gregorian[0]}/{gregorian[1]:02d}/{gregorian[2]:02d}
                قمری: {hijri[0]}/{hijri[1]:02d}/{hijri[2]:02d}
                """
            elif self.current_calendar == "islamic":
                gregorian = self.date_converter.hijri_to_gregorian(year, month, day)
                persian = self.date_converter.gregorian_to_persian(*gregorian)
                result = f"""
                میلادی: {gregorian[0]}/{gregorian[1]:02d}/{gregorian[2]:02d}
                شمسی: {persian[0]}/{persian[1]:02d}/{persian[2]:02d}
                """
            else:
                persian = self.date_converter.gregorian_to_persian(year, month, day)
                hijri = self.date_converter.gregorian_to_hijri(year, month, day)
                result = f"""
                شمسی: {persian[0]}/{persian[1]:02d}/{persian[2]:02d}
                قمری: {hijri[0]}/{hijri[1]:02d}/{hijri[2]:02d}
                """
            
            self.converter_result.config(state="normal")
            self.converter_result.delete("1.0", tk.END)
            self.converter_result.insert("1.0", result)
            self.converter_result.config(state="disabled")
            
        except Exception as e:
            messagebox.showerror("خطا", f"فرمت تاریخ نامعتبر است: {e}")
    
    def show_date_converter(self):
        """نمایش مبدل تاریخ پیشرفته"""
        converter_window = tk.Toplevel(self.window)
        converter_window.title("مبدل تاریخ پیشرفته")
        converter_window.geometry("400x500")
        converter_window.configure(bg=self.theme_colors["bg"])
        
        # مرکز کردن پنجره
        converter_window.update_idletasks()
        width = converter_window.winfo_width()
        height = converter_window.winfo_height()
        x = (converter_window.winfo_screenwidth() // 2) - (width // 2)
        y = (converter_window.winfo_screenheight() // 2) - (height // 2)
        converter_window.geometry(f'{width}x{height}+{x}+{y}')
        
        # محتوا
        tk.Label(
            converter_window,
            text="مبدل تاریخ پیشرفته",
            font=("Segoe UI", 14, "bold"),
            fg=self.theme_colors["accent"],
            bg=self.theme_colors["bg"]
        ).pack(pady=20)
        
        # ورودی تاریخ
        input_frame = tk.Frame(converter_window, bg=self.theme_colors["bg"])
        input_frame.pack(pady=10)
        
        tk.Label(
            input_frame,
            text="تاریخ ورودی:",
            font=("Segoe UI", 11),
            fg=self.theme_colors["text"],
            bg=self.theme_colors["bg"]
        ).grid(row=0, column=0, padx=5, pady=5)
        
        year_var = tk.StringVar(value=str(datetime.now().year))
        month_var = tk.StringVar(value=str(datetime.now().month))
        day_var = tk.StringVar(value=str(datetime.now().day))
        
        tk.Entry(input_frame, textvariable=year_var, width=8).grid(row=0, column=1, padx=2)
        tk.Entry(input_frame, textvariable=month_var, width=5).grid(row=0, column=2, padx=2)
        tk.Entry(input_frame, textvariable=day_var, width=5).grid(row=0, column=3, padx=2)
        
        # نوع تقویم ورودی
        tk.Label(
            input_frame,
            text="نوع تقویم:",
            font=("Segoe UI", 11),
            fg=self.theme_colors["text"],
            bg=self.theme_colors["bg"]
        ).grid(row=1, column=0, padx=5, pady=5)
        
        input_cal_var = tk.StringVar(value="persian")
        cal_types = [("شمسی", "persian"), ("میلادی", "gregorian"), ("قمری", "islamic")]
        
        for i, (name, code) in enumerate(cal_types):
            tk.Radiobutton(
                input_frame,
                text=name,
                variable=input_cal_var,
                value=code,
                fg=self.theme_colors["text"],
                bg=self.theme_colors["bg"]
            ).grid(row=1, column=i+1, padx=5)
        
        # دکمه تبدیل
        convert_btn = ModernButton(
            converter_window,
            text="تبدیل",
            style="primary",
            command=lambda: self.advanced_convert(
                year_var.get(), month_var.get(), day_var.get(),
                input_cal_var.get(), result_text
            )
        )
        convert_btn.pack(pady=10)
        
        # نمایش نتیجه
        result_frame = tk.Frame(converter_window, bg=self.theme_colors["secondary"])
        result_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        result_text = tk.Text(
            result_frame,
            height=15,
            font=("Segoe UI", 10),
            fg=self.theme_colors["text"],
            bg=self.theme_colors["secondary"],
            relief="flat",
            wrap="word"
        )
        result_text.pack(fill="both", expand=True, padx=5, pady=5)
        result_text.config(state="disabled")
    
    def advanced_convert(self, year_str, month_str, day_str, input_cal, result_widget):
        """تبدیل پیشرفته تاریخ"""
        try:
            year = int(year_str)
            month = int(month_str)
            day = int(day_str)
            
            if input_cal == "persian":
                gregorian = self.date_converter.persian_to_gregorian(year, month, day)
                hijri = self.date_converter.gregorian_to_hijri(*gregorian)
                result = f"""
                تاریخ ورودی (شمسی): {year}/{month:02d}/{day:02d}
                
                نتایج تبدیل:
                میلادی: {gregorian[0]}/{gregorian[1]:02d}/{gregorian[2]:02d}
                قمری: {hijri[0]}/{hijri[1]:02d}/{hijri[2]:02d}
                چینی: {self.date_converter.gregorian_to_chinese(*gregorian)}
                """
            elif input_cal == "islamic":
                gregorian = self.date_converter.hijri_to_gregorian(year, month, day)
                persian = self.date_converter.gregorian_to_persian(*gregorian)
                result = f"""
                تاریخ ورودی (قمری): {year}/{month:02d}/{day:02d}
                
                نتایج تبدیل:
                میلادی: {gregorian[0]}/{gregorian[1]:02d}/{gregorian[2]:02d}
                شمسی: {persian[0]}/{persian[1]:02d}/{persian[2]:02d}
                چینی: {self.date_converter.gregorian_to_chinese(*gregorian)}
                """
            else:  # میلادی
                persian = self.date_converter.gregorian_to_persian(year, month, day)
                hijri = self.date_converter.gregorian_to_hijri(year, month, day)
                result = f"""
                تاریخ ورودی (میلادی): {year}/{month:02d}/{day:02d}
                
                نتایج تبدیل:
                شمسی: {persian[0]}/{persian[1]:02d}/{persian[2]:02d}
                قمری: {hijri[0]}/{hijri[1]:02d}/{hijri[2]:02d}
                چینی: {self.date_converter.gregorian_to_chinese(year, month, day)}
                """
            
            result_widget.config(state="normal")
            result_widget.delete("1.0", tk.END)
            result_widget.insert("1.0", result)
            result_widget.config(state="disabled")
            
        except Exception as e:
            messagebox.showerror("خطا", f"خطا در تبدیل تاریخ: {e}")
    
    def show_location_settings(self):
        """تنظیمات منطقه"""
        settings_window = tk.Toplevel(self.window)
        settings_window.title("تنظیمات منطقه")
        settings_window.geometry("400x300")
        settings_window.configure(bg=self.theme_colors["bg"])
        
        # مرکز کردن
        settings_window.update_idletasks()
        width = settings_window.winfo_width()
        height = settings_window.winfo_height()
        x = (settings_window.winfo_screenwidth() // 2) - (width // 2)
        y = (settings_window.winfo_screenheight() // 2) - (height // 2)
        settings_window.geometry(f'{width}x{height}+{x}+{y}')
        
        # محتوا
        tk.Label(
            settings_window,
            text="تنظیمات منطقه",
            font=("Segoe UI", 14, "bold"),
            fg=self.theme_colors["accent"],
            bg=self.theme_colors["bg"]
        ).pack(pady=20)
        
        # منطقه زمانی
        tz_frame = tk.Frame(settings_window, bg=self.theme_colors["bg"])
        tz_frame.pack(fill="x", padx=20, pady=10)
        
        tk.Label(
            tz_frame,
            text="منطقه زمانی:",
            font=("Segoe UI", 11),
            fg=self.theme_colors["text"],
            bg=self.theme_colors["bg"]
        ).pack(side="left")
        
        tz_var = tk.StringVar(value=self.config.get("timezone", "Asia/Tehran"))
        tz_combo = ttk.Combobox(
            tz_frame,
            textvariable=tz_var,
            values=["Asia/Tehran", "UTC", "Europe/London", "America/New_York"],
            state="readonly",
            width=20
        )
        tz_combo.pack(side="right")
        
        # موقعیت جغرافیایی
        loc_frame = tk.Frame(settings_window, bg=self.theme_colors["bg"])
        loc_frame.pack(fill="x", padx=20, pady=10)
        
        tk.Label(
            loc_frame,
            text="موقعیت جغرافیایی:",
            font=("Segoe UI", 11),
            fg=self.theme_colors["text"],
            bg=self.theme_colors["bg"]
        ).pack(anchor="w")
        
        lat_frame = tk.Frame(loc_frame, bg=self.theme_colors["bg"])
        lat_frame.pack(fill="x", pady=5)
        
        tk.Label(
            lat_frame,
            text="عرض جغرافیایی:",
            font=("Segoe UI", 10),
            fg=self.theme_colors["text"],
            bg=self.theme_colors["bg"]
        ).pack(side="left")
        
        lat_var = tk.StringVar(value="35.6892")
        tk.Entry(lat_frame, textvariable=lat_var, width=15).pack(side="right")
        
        lon_frame = tk.Frame(loc_frame, bg=self.theme_colors["bg"])
        lon_frame.pack(fill="x", pady=5)
        
        tk.Label(
            lon_frame,
            text="طول جغرافیایی:",
            font=("Segoe UI", 10),
            fg=self.theme_colors["text"],
            bg=self.theme_colors["bg"]
        ).pack(side="left")
        
        lon_var = tk.StringVar(value="51.3890")
        tk.Entry(lon_frame, textvariable=lon_var, width=15).pack(side="right")
        
        # دکمه ذخیره
        save_btn = ModernButton(
            settings_window,
            text="ذخیره تنظیمات",
            style="success",
            command=lambda: self.save_location_settings(
                tz_var.get(), lat_var.get(), lon_var.get(), settings_window
            )
        )
        save_btn.pack(pady=20)
    
    def save_location_settings(self, timezone, lat, lon, window):
        """ذخیره تنظیمات منطقه"""
        self.config["timezone"] = timezone
        try:
            self.config["latitude"] = float(lat)
            self.config["longitude"] = float(lon)
        except:
            pass
        
        window.destroy()
        messagebox.showinfo("ذخیره شد", "تنظیمات منطقه با موفقیت ذخیره شد.")
    
    def show_notification_settings(self):
        """تنظیمات اعلان"""
        messagebox.showinfo("تنظیمات اعلان", "این بخش در نسخه بعدی اضافه خواهد شد.")
    
    def show_event_details(self, event):
        """نمایش جزئیات مناسبت"""
        details = f"""
        مناسبت: {event.get('title', 'نامشخص')}
        تاریخ: {event.get('date', 'نامشخص')}
        نوع: {event.get('type', 'عمومی')}
        
        توضیحات:
        {event.get('description', 'توضیحی موجود نیست')}
        """
        
        messagebox.showinfo("جزئیات مناسبت", details)
    
    def show_help(self):
        """نمایش راهنما"""
        help_text = """
        راهنمای استفاده از تقویم جهانی Hessamedien
        
        ویژگی‌های اصلی:
        1. نمایش ۸ تقویم مختلف
        2. تبدیل تاریخ بین تقویم‌ها
        3. نمایش مناسبت‌های ملی و مذهبی
        4. نمایش اوقات شرعی و طلوع/غروب
        5. رابط کاربری مدرن ویندوز ۱۱
        
        روش استفاده:
        - برای تغییر ماه از دکمه‌های ماه قبل/بعد استفاده کنید
        - برای تغییر تقویم از منوی نمایش > نوع تقویم استفاده کنید
        - برای تغییر تم از منوی نمایش > تم استفاده کنید
        - برای تبدیل تاریخ از ابزار مبدل سریع استفاده کنید
        
        توسعه‌دهنده: Hessamedien
        صفحه اینستاگرام: https://instagram.com/hessamedien
        """
        
        help_window = tk.Toplevel(self.window)
        help_window.title("راهنمای برنامه")
        help_window.geometry("500x400")
        help_window.configure(bg=self.theme_colors["bg"])
        
        # مرکز کردن
        help_window.update_idletasks()
        width = help_window.winfo_width()
        height = help_window.winfo_height()
        x = (help_window.winfo_screenwidth() // 2) - (width // 2)
        y = (help_window.winfo_screenheight() // 2) - (height // 2)
        help_window.geometry(f'{width}x{height}+{x}+{y}')
        
        # محتوا
        text_widget = tk.Text(
            help_window,
            font=("Segoe UI", 10),
            fg=self.theme_colors["text"],
            bg=self.theme_colors["bg"],
            relief="flat",
            wrap="word",
            padx=20,
            pady=20
        )
        text_widget.insert("1.0", help_text)
        text_widget.config(state="disabled")
        text_widget.pack(fill="both", expand=True)
    
    def show_about(self):
        """نمایش درباره برنامه"""
        about_text = f"""
        تقویم جهانی Hessamedien
        نسخه: 1.0.0
        
        یک برنامه تقویم جامع با ویژگی‌های پیشرفته
        
        امکانات:
        • پشتیبانی از ۸ تقویم مختلف
        • نمایش مناسبت‌های ملی و مذهبی
        • نمایش اوقات شرعی و طلوع/غروب
        • رابط کاربری مدرن ویندوز ۱۱
        • قابلیت شخصی‌سازی کامل
        • دریافت خودکار مناسبت‌ها
        
        توسعه‌دهنده: Hessamedien
        صفحه اینستاگرام: https://instagram.com/hessamedien
        
        © 2024 - کلیه حقوق محفوظ است
        """
        
        about_window = tk.Toplevel(self.window)
        about_window.title("درباره برنامه")
        about_window.geometry("400x300")
        about_window.configure(bg=self.theme_colors["bg"])
        
        # مرکز کردن
        about_window.update_idletasks()
        width = about_window.winfo_width()
        height = about_window.winfo_height()
        x = (about_window.winfo_screenwidth() // 2) - (width // 2)
        y = (about_window.winfo_screenheight() // 2) - (height // 2)
        about_window.geometry(f'{width}x{height}+{x}+{y}')
        
        # لوگو/عنوان
        tk.Label(
            about_window,
            text="تقویم جهانی",
            font=("Segoe UI", 18, "bold"),
            fg=self.theme_colors["accent"],
            bg=self.theme_colors["bg"]
        ).pack(pady=(20, 5))
        
        tk.Label(
            about_window,
            text="Hessamedien",
            font=("Segoe UI", 14),
            fg=self.theme_colors["text"],
            bg=self.theme_colors["bg"]
        ).pack(pady=(0, 20))
        
        # متن درباره
        text_widget = tk.Text(
            about_window,
            height=10,
            font=("Segoe UI", 9),
            fg=self.theme_colors["text"],
            bg=self.theme_colors["bg"],
            relief="flat",
            wrap="word"
        )
        text_widget.insert("1.0", about_text)
        text_widget.config(state="disabled")
        text_widget.pack(fill="both", padx=20, pady=10)
        
        # دکمه بستن
        close_btn = ModernButton(
            about_window,
            text="بستن",
            style="primary",
            command=about_window.destroy
        )
        close_btn.pack(pady=10)
    
    def save_data(self):
        """ذخیره داده‌ها"""
        try:
            with open("calendar_data.json", "w", encoding="utf-8") as f:
                data = {
                    "config": self.config,
                    "events": self.events,
                    "last_sync": datetime.now().isoformat()
                }
                json.dump(data, f, indent=4, ensure_ascii=False)
            
            self.status_label.config(text="داده‌ها با موفقیت ذخیره شد")
            messagebox.showinfo("ذخیره", "داده‌های برنامه با موفقیت ذخیره شدند.")
        except Exception as e:
            messagebox.showerror("خطا", f"خطا در ذخیره داده‌ها: {e}")
    
    def print_calendar(self):
        """چاپ تقویم"""
        # ایجاد یک پنجره برای پیش‌نمایش چاپ
        print_window = tk.Toplevel(self.window)
        print_window.title("پیش‌نمایش چاپ")
        print_window.geometry("800x600")
        print_window.configure(bg="white")
        
        # مرکز کردن
        print_window.update_idletasks()
        width = print_window.winfo_width()
        height = print_window.winfo_height()
        x = (print_window.winfo_screenwidth() // 2) - (width // 2)
        y = (print_window.winfo_screenheight() // 2) - (height // 2)
        print_window.geometry(f'{width}x{height}+{x}+{y}')
        
        # محتوا
        year = self.selected_date.year
        month = self.selected_date.month
        
        print_text = f"""
        ============================================
                    تقویم {month}/{year}
                    Hessamedien
        ============================================
        
        تاریخ: {self.format_date(self.selected_date)}
        تقویم: {self.current_calendar}
        
        مناسبت‌های این ماه:
        """
        
        # اضافه کردن مناسبت‌ها
        month_events = [e for e in self.events if f"/{month}/" in e.get("date", "")]
        for event in month_events:
            print_text += f"- {event['date']}: {event['title']}\n"
        
        # نمایش در پنجره
        text_widget = tk.Text(
            print_window,
            font=("Courier New", 10),
            fg="black",
            bg="white",
            relief="flat",
            wrap="word"
        )
        text_widget.insert("1.0", print_text)
        text_widget.pack(fill="both", expand=True, padx=20, pady=20)
        
        # دکمه‌ها
        btn_frame = tk.Frame(print_window, bg="white")
        btn_frame.pack(pady=10)
        
        ModernButton(
            btn_frame,
            text="چاپ",
            style="primary",
            command=lambda: self.actual_print(text_widget)
        ).pack(side="left", padx=5)
        
        ModernButton(
            btn_frame,
            text="ذخیره به فایل",
            style="success",
            command=lambda: self.save_to_file(print_text)
        ).pack(side="left", padx=5)
        
        ModernButton(
            btn_frame,
            text="بستن",
            style="secondary",
            command=print_window.destroy
        ).pack(side="left", padx=5)
    
    def actual_print(self, text_widget):
        """چاپ واقعی"""
        # در نسخه واقعی می‌توان از ماژول‌های چاپ استفاده کرد
        messagebox.showinfo("چاپ", "عملکرد چاپ در این نسخه شبیه‌سازی شده است.")
    
    def save_to_file(self, content):
        """ذخیره به فایل"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                messagebox.showinfo("ذخیره", "فایل با موفقیت ذخیره شد.")
            except Exception as e:
                messagebox.showerror("خطا", f"خطا در ذخیره فایل: {e}")

# ============================================================================
# کلاس اصلی برنامه
# ============================================================================

class GlobalCalendarApp:
    """کلاس اصلی برنامه"""
    
    def __init__(self):
        self.version = "1.0.0"
        self.developer = "Hessamedien"
        self.instagram_url = "https://instagram.com/hessamedien"
        self.config_file = "config.json"
        self.config = self.load_config()
        self.root = None
        self.loading_screen = None
        self.main_window = None
        
    def load_config(self):
        """بارگذاری تنظیمات"""
        default_config = {
            "language": "fa",
            "calendar_type": "persian",
            "theme": "win11_dark",
            "timezone": "Asia/Tehran",
            "show_events": True,
            "show_sunrise_sunset": True,
            "notifications": True,
            "auto_update": True,
            "latitude": 35.6892,
            "longitude": 51.3890,
            "first_run": True,
            "last_update": None
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    for key in default_config:
                        if key not in config:
                            config[key] = default_config[key]
                    return config
        except Exception as e:
            print(f"خطا در خواندن تنظیمات: {e}")
        
        return default_config
    
    def save_config(self):
        """ذخیره تنظیمات"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"خطا در ذخیره تنظیمات: {e}")
    
    def run_wizard(self):
        """اجرای ویزارد"""
        if self.config.get("first_run", True):
            wizard = SetupWizard(self.config)
            wizard.run()
            self.config = wizard.get_config()
            self.save_config()
    
    def show_loading_screen(self):
        """نمایش صفحه لودینگ"""
        self.loading_screen = LoadingScreen()
        self.loading_screen.show()
        
        # شبیه‌سازی لودینگ
        def simulate_loading():
            for i in range(101):
                if self.loading_screen:
                    self.loading_screen.update_progress(i)
                    time.sleep(0.03)
            
            if self.loading_screen:
                self.loading_screen.close()
        
        threading.Thread(target=simulate_loading, daemon=True).start()
        time.sleep(3.5)  # نمایش حداقل 3.5 ثانیه
    
    def show_credits(self):
        """نمایش اطلاعات سازنده"""
        credits_text = f"""
        ========================================
                تقویم جهانی {self.version}
                توسعه‌دهنده: {self.developer}
        ========================================
        
        با تشکر از استفاده شما از این برنامه
        
        ویژگی‌های برنامه:
        • پشتیبانی از ۸ تقویم مختلف
        • نمایش مناسبت‌های ملی و مذهبی
        • نمایش اوقات شرعی و طلوع/غروب
        • رابط کاربری مدرن ویندوز ۱۱
        • قابلیت شخصی‌سازی کامل
        
        برای پشتیبانی و اطلاعات بیشتر:
        صفحه اینستاگرام: {self.instagram_url}
        
        © {datetime.now().year} - تمامی حقوق محفوظ است
        """
        
        print(credits_text)
        
        # ذخیره در فایل
        with open("credits.txt", "w", encoding="utf-8") as f:
            f.write(credits_text)
    
    def open_instagram(self):
        """باز کردن صفحه اینستاگرام"""
        webbrowser.open(self.instagram_url)
    
    def on_closing(self):
        """هنگام بستن برنامه"""
        self.save_config()
        
        if self.main_window:
            response = messagebox.askyesnocancel(
                "خروج",
                "آیا می‌خواهید از برنامه خارج شوید؟\n\nذخیره تنظیمات قبل از خروج؟"
            )
            
            if response is not None:
                if response:  # بله، ذخیره و خروج
                    self.save_config()
                self.main_window.window.destroy()
                sys.exit()
        else:
            sys.exit()
    
    def run(self):
        """اجرای اصلی برنامه"""
        try:
            # نمایش لوگو در کنسول
            print("=" * 50)
            print("تقویم جهانی Hessamedien")
            print("در حال راه‌اندازی...")
            print("=" * 50)
            
            # اجرای ویزارد
            self.run_wizard()
            
            # نمایش صفحه لودینگ
            self.show_loading_screen()
            
            # ایجاد پنجره اصلی
            self.main_window = MainWindow(self.config, self)
            
            # نمایش اعتبارسنجی
            self.show_credits()
            
            # تنظیم هندلر بستن
            self.main_window.window.protocol("WM_DELETE_WINDOW", self.on_closing)
            
            # تنظیم آیکون (اگر موجود باشد)
            try:
                self.main_window.window.iconbitmap("icon.ico")
            except:
                pass
            
            # مرکز کردن پنجره
            self.main_window.window.update_idletasks()
            width = self.main_window.window.winfo_width()
            height = self.main_window.window.winfo_height()
            x = (self.main_window.window.winfo_screenwidth() // 2) - (width // 2)
            y = (self.main_window.window.winfo_screenheight() // 2) - (height // 2)
            self.main_window.window.geometry(f'{width}x{height}+{x}+{y}')
            
            # اجرای حلقه اصلی
            self.main_window.window.mainloop()
            
        except Exception as e:
            messagebox.showerror("خطای سیستمی", f"خطایی رخ داده است:\n{str(e)}")
            sys.exit(1)

# ============================================================================
# تابع اصلی
# ============================================================================

def main():
    """تابع اصلی"""
    app = GlobalCalendarApp()
    app.run()

if __name__ == "__main__":
    main()