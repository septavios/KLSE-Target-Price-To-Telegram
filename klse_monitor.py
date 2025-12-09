#!/usr/bin/env python3
"""
KLSE Target Price Monitor
A script to monitor Malaysia Stock Exchange price targets and send updates to Telegram.

Author: cming401
License: MIT
"""

import json
import datetime
import logging
import os
import re
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from zoneinfo import ZoneInfo

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class KLSETargetPriceMonitor:
    def __init__(self, config_file='config.json'):
        """Initialize the monitor with configuration file."""
        self.config = self.load_config(config_file)
        self.telegram_token = self.config['telegram']['bot_token']
        self.telegram_channel = self.config['telegram']['channel_id']
        self.telegram_chat_id = self.config['telegram']['chat_id']
        self.message_cfg = self.config.get('message', {})
        
    def load_config(self, config_file: str) -> dict:
        """Load configuration from JSON file."""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file {config_file} not found!")
            logger.error("Please copy config.json.example to config.json and configure your settings.")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            raise
    
    def get_today_date(self) -> str:
        """Get today's date in YYYY-MM-DD format."""
        return datetime.date.today().strftime('%Y-%m-%d')
    
    def get_sample_data(self) -> List[Dict]:
        """Get sample KLSE target price data."""
        today = self.get_today_date()
        
        # Sample data based on real KLSE targets
        sample_data = [
            {
                'date': today,
                'stock_code': 'ARMADA',
                'stock_name': 'BUMI ARMADA BERHAD',
                'current_price': '0.45',
                'target_price': '0.65',
                'upside_downside': '+0.20 (44.44%)',
                'price_call': 'BUY',
                'analyst': 'RHB-OSK'
            },
            {
                'date': today,
                'stock_code': 'BNASTRA',
                'stock_name': 'BINASTRA CORPORATION BERHAD',
                'current_price': '1.88',
                'target_price': '2.64',
                'upside_downside': '+0.76 (40.43%)',
                'price_call': 'BUY',
                'analyst': 'RHB-OSK'
            },
            {
                'date': today,
                'stock_code': 'GAMUDA',
                'stock_name': 'GAMUDA BHD',
                'current_price': '4.99',
                'target_price': '5.86',
                'upside_downside': '+0.87 (17.43%)',
                'price_call': 'BUY',
                'analyst': 'RHB-OSK'
            },
            {
                'date': today,
                'stock_code': 'GOLDETF',
                'stock_name': 'TRADEPLUS SHARIAH GOLD TRACKER',
                'current_price': '4.34',
                'target_price': '4.78',
                'upside_downside': '+0.44 (10.14%)',
                'price_call': 'HOLD',
                'analyst': 'BIMB'
            },
            {
                'date': today,
                'stock_code': 'IOICORP',
                'stock_name': 'IOI CORPORATION BHD',
                'current_price': '3.76',
                'target_price': '4.05',
                'upside_downside': '+0.29 (7.71%)',
                'price_call': 'HOLD',
                'analyst': 'AmInvest'
            },
            {
                'date': today,
                'stock_code': 'MAYBANK',
                'stock_name': 'MALAYAN BANKING BHD',
                'current_price': '9.71',
                'target_price': '10.90',
                'upside_downside': '+1.19 (12.26%)',
                'price_call': 'BUY',
                'analyst': 'RHB'
            },
            {
                'date': today,
                'stock_code': 'MAYBANK',
                'stock_name': 'MALAYAN BANKING BHD',
                'current_price': '9.71',
                'target_price': '11.40',
                'upside_downside': '+1.69 (17.40%)',
                'price_call': 'BUY',
                'analyst': 'TA'
            },
            {
                'date': today,
                'stock_code': 'MISC',
                'stock_name': 'MISC BHD',
                'current_price': '7.60',
                'target_price': '9.70',
                'upside_downside': '+2.10 (27.63%)',
                'price_call': 'BUY',
                'analyst': 'RHB-OSK'
            },
            {
                'date': today,
                'stock_code': 'MNHLDG',
                'stock_name': 'MN HOLDINGS BERHAD',
                'current_price': '1.40',
                'target_price': '1.69',
                'upside_downside': '+0.29 (20.71%)',
                'price_call': 'BUY',
                'analyst': 'MAYBANK'
            },
            {
                'date': today,
                'stock_code': 'SUNCON',
                'stock_name': 'SUNWAY CONSTRUCTION GROUP BERHAD',
                'current_price': '5.87',
                'target_price': '6.80',
                'upside_downside': '+0.93 (15.84%)',
                'price_call': 'BUY',
                'analyst': 'RHB-OSK'
            },
            {
                'date': today,
                'stock_code': 'WCT',
                'stock_name': 'WCT HOLDINGS BERHAD',
                'current_price': '0.68',
                'target_price': '1.08',
                'upside_downside': '+0.40 (58.82%)',
                'price_call': 'BUY',
                'analyst': 'PUBLIC BANK'
            },
            {
                'date': today,
                'stock_code': 'YINSON',
                'stock_name': 'YINSON HOLDINGS BHD',
                'current_price': '2.41',
                'target_price': '3.69',
                'upside_downside': '+1.28 (53.11%)',
                'price_call': 'BUY',
                'analyst': 'RHB-OSK'
            }
        ]
        
        return sample_data
    
    def fetch_target_prices(self) -> List[Dict]:
        """Fetch KLSE target price data."""
        try:
            logger.info("Fetching KLSE target price data...")

            # Try live web scraping first
            scraped = self.scrape_latest_targets()
            if scraped:
                logger.info(f"Successfully scraped {len(scraped)} target price records")
                return scraped

            # Prefer local JSON file produced by update_data.py if present
            today = self.get_today_date()
            local_file = f"klse_data_{today}.json"
            if os.path.exists(local_file):
                try:
                    with open(local_file, 'r', encoding='utf-8') as f:
                        payload = json.load(f)
                        data_list = payload.get('data', [])
                        if data_list:
                            logger.info(f"Loaded {len(data_list)} records from local file {local_file}")
                            return data_list
                        else:
                            logger.warning(f"Local file {local_file} found but contains no 'data' records; continuing")
                except Exception as e:
                    logger.warning(f"Failed to read local file {local_file}: {e}; continuing")

            # Fallback to sample data when scraping/local file unavailable
            use_sample = True
            try:
                use_sample = bool(self.config.get('data_source', {}).get('fallback_to_sample', True))
            except Exception:
                use_sample = True
            if use_sample:
                logger.info("Using sample data (fallback enabled)...")
                data_list = self.get_sample_data()
                logger.info(f"Successfully fetched {len(data_list)} target price records")
                return data_list
            else:
                logger.warning("No data available: scraping failed, no local file, and fallback disabled")
                return []

        except Exception as e:
            logger.error(f"Failed to fetch data: {e}")
            return []

    def scrape_latest_targets(self) -> List[Dict]:
        """Scrape latest target prices from i3investor using regex on the 'dtdata' JS variable.

        Returns a list of dicts matching the schema used throughout the app.
        On any error, returns an empty list (caller will handle fallback).
        """
        try:
            source_cfg = self.config.get('data_source', {})
            url = source_cfg.get('url') or 'https://klse.i3investor.com/web/pricetarget/latest'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'
            }
            resp = requests.get(url, headers=headers, timeout=15)
            resp.raise_for_status()

            # The data is now inside a JS variable: var dtdata = [[...], ...];
            # We used to parse <table>, now we must parse this JSON-like structure.
            # Example snippet: var dtdata = [["2024-06-19","PBBANK","4.04","4.80","<span ...>...</span>","BUY","TA"], ...];
            
            match = re.search(r'var\s+dtdata\s*=\s*(\[.*?\]);', resp.text, re.DOTALL)
            if not match:
                logger.warning("Could not find 'var dtdata =' in source page")
                return []

            try:
                raw_data = json.loads(match.group(1))
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse 'dtdata' JSON: {e}")
                return []
            
            data_list: List[Dict] = []
            today = self.get_today_date()

            def clean_text(text: str) -> str:
                # Some fields might contain HTML (e.g. Upside with <span>)
                if not text:
                    return ""
                # Simple HTML strip if needed, or use bs4
                if '<' in text and '>' in text:
                    return BeautifulSoup(text, 'lxml').get_text(strip=True)
                return text.strip()

            for item in raw_data:
                # Expected item structure based on inspection:
                # 0: Date (YYYY-MM-DD)
                # 1: Stock Name (e.g. "MAYBANK") - used as Name
                # 2: Current Price (e.g. "9.95")
                # 3: Target Price (e.g. "10.60")
                # 4: Upside/Downside (HTML string)
                # 5: Price Call (e.g. "BUY")
                # 6: Firm (Analyst)
                # Others...
                
                if len(item) < 7:
                    continue

                date_str = str(item[0])
                stock_name = clean_text(str(item[1]))
                current_price = str(item[2])
                target_price = str(item[3])
                upside_downside = clean_text(str(item[4]))
                price_call = clean_text(str(item[5])).upper()
                analyst = clean_text(str(item[6]))

                # Derive stock_code from name (best-effort)
                stock_code = (stock_name.split()[0] if stock_name else 'N/A')

                # Basic validity checks
                if not stock_name or not target_price:
                    continue

                # Normalize prices to plain strings (remove RM if present, though JSON usually clean)
                current_price = current_price.replace('RM', '').strip()
                target_price = target_price.replace('RM', '').strip()

                # If the date_str is not today, we technically just scraped it. 
                # The caller (fetch_target_prices) decides if we use it, 
                # but run_monitor calls filter_today_data later. 
                # So we just return what we found.
                # However, for consistency, we override 'date' with 'today' 
                # strictly if we want to treat it as "fetched today". 
                # But better to keep original date from source if possible?
                # The original code did: 'date': today. 
                # Let's stick to using the scraper's valid date if valid, or today.
                # Actually original code used `today` for all rows. 
                # Let's assume these are "latest" so we can map them to today 
                # OR we respect the date column. The Date column in the table is "Announcement Date" usually.
                # Let's keep using `date_str` from table if it looks like a date,
                # otherwise fallback or just keep it. 
                # The original code Forced `today`. Let's stick to forcing `today` 
                # to ensure `filter_today_data` works if it relies on exact match, 
                # OR, better: `filter_today_data` checks if item['date'] == today.
                # If the table has yesterday's data, we shouldn't report it as today's new target.
                # So we should use the date from the table.
                
                # REVISION: Original code:
                # item = { 'date': today, ... }
                # Then `filter_today_data`: `if item['date'] == self.get_today_date()`
                # This implies original scraper grabbed *everything* and labeled it TODAY.
                # Which means `filter_today_data` was effectively a defined no-op or sanity check.
                # BUT, if the table contains old data, labeling it "today" is wrong.
                # The new table has a date column. We should use it.
                
                item_date = date_str if date_str else today

                item = {
                    'date': item_date,
                    'stock_code': stock_code,
                    'stock_name': stock_name,
                    'current_price': current_price,
                    'target_price': target_price,
                    'upside_downside': upside_downside,
                    'price_call': price_call,
                    'analyst': analyst
                }
                data_list.append(item)

            if not data_list:
                logger.warning("Scraper parsed zero rows from dtdata")
                return []

            return data_list

        except requests.RequestException as e:
            logger.warning(f"Scraping request failed: {e}")
            return []
        except Exception as e:
            logger.warning(f"Scraping parse error: {e}")
            return []
    
    def filter_today_data(self, data_list: List[Dict]) -> List[Dict]:
        """Filter data for today's date."""
        today = self.get_today_date()
        today_data = [item for item in data_list if item['date'] == today]
        logger.info(f"Found {len(today_data)} target price records for today ({today})")
        return today_data
    
    def format_message(self, data_list: List[Dict]) -> str:
        """Format data into Telegram message."""
        if not data_list:
            return f"📊 KLSE Target Price Update\n🗓️ Date: {self.get_today_date()}\n\nNo new target prices available"
        
        today = self.get_today_date()
        message = f"📊 KLSE Target Price Update\n🗓️ Date: {today}\n\n"
        
        # Group by stock code
        stock_groups = {}
        for item in data_list:
            stock_code = item.get('stock_code', 'N/A')
            if stock_code not in stock_groups:
                stock_groups[stock_code] = []
            stock_groups[stock_code].append(item)
        
        # Sort groups by highest upside percentage
        sorted_groups = []
        for stock_code, items in stock_groups.items():
            # Find the highest upside for this stock
            max_upside = 0
            for item in items:
                upside_text = item.get('upside_downside', '0')
                if '(' in upside_text:
                    try:
                        upside_pct = float(upside_text.split('(')[1].split('%')[0])
                        max_upside = max(max_upside, upside_pct)
                    except:
                        pass
            sorted_groups.append((max_upside, stock_code, items))
        
        # Sort by upside percentage (descending)
        sorted_groups.sort(key=lambda x: x[0], reverse=True)
        
        for i, (_, stock_code, items) in enumerate(sorted_groups, 1):
            # Get stock name from first item
            stock_name = items[0].get('stock_name', 'N/A')
            
            # Get recommendation emoji from first item
            price_call = items[0].get('price_call', '').upper()
            call_emoji = {
                'BUY': '🟢',
                'HOLD': '🟡',
                'SELL': '🔴'
            }.get(price_call, '⚪')
            
            message += f"{i}. {call_emoji} {stock_code} - {stock_name}\n"
            
            # Add each target price for this stock
            for item in items:
                current_price = item.get('current_price', 'N/A')
                target_price = item.get('target_price', 'N/A')
                upside_text = item.get('upside_downside', '')
                analyst = item.get('analyst', 'N/A')
                price_call_text = item.get('price_call', 'N/A')
                
                # Determine trend emoji
                if '+' in upside_text:
                    trend_emoji = "📈"
                elif '-' in upside_text:
                    trend_emoji = "📉"
                else:
                    trend_emoji = "➡️"
                
                # Convert recommendation to English
                call_english = {
                    'BUY': 'Buy',
                    'HOLD': 'Hold',
                    'SELL': 'Sell'
                }.get(price_call_text.upper(), price_call_text)
                
                message += f"   💰 Current: RM{current_price} 🎯 Target: RM{target_price} {trend_emoji} Change: {upside_text}\n"
                message += f"   🏢 Analyst: {analyst} ({call_english})\n"
            
            message += "\n"
        
        # Add summary statistics
        buy_count = sum(1 for item in data_list if item.get('price_call', '').upper() == 'BUY')
        hold_count = sum(1 for item in data_list if item.get('price_call', '').upper() == 'HOLD')
        sell_count = sum(1 for item in data_list if item.get('price_call', '').upper() == 'SELL')
        
        message += f"📊 Daily Summary:\n"
        message += f"   🟢 Buy: {buy_count} stocks\n"
        message += f"   🟡 Hold: {hold_count} stocks\n"
        message += f"   🔴 Sell: {sell_count} stocks\n"
        message += f"   📈 Total: {len(data_list)} stocks\n\n"
        message += f"🔗 Source: https://klse.i3investor.com/web/pricetarget/latest"
        
        return message

    def _parse_upside_pct(self, upside_text: str) -> Optional[float]:
        """Extract percentage number from text like '+0.29 (20.71%)'."""
        try:
            if '(' in upside_text and '%' in upside_text:
                return float(upside_text.split('(')[1].split('%')[0])
        except Exception:
            pass
        return None

    def format_message_html(self, data_list: List[Dict]) -> str:
        """Format data into an HTML Telegram message with top movers and filtering."""
        def esc(s: Optional[str]) -> str:
            s = s or ''
            return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

        # Time in MYT for clarity
        now_myt = datetime.datetime.now(ZoneInfo("Asia/Kuala_Lumpur"))
        today_str = now_myt.strftime("%Y-%m-%d")

        if not data_list:
            return f"📊 <b>KLSE Target Price Update</b>\n📅 <i>{today_str}</i>\n\nNo new target prices available."

        # Apply threshold filter
        threshold = float(self.message_cfg.get('upside_threshold_pct', 0) or 0)
        filtered: List[Dict] = []
        for item in data_list:
            pct = self._parse_upside_pct(item.get('upside_downside', ''))
            if pct is None:
                continue
            if pct >= threshold:
                filtered.append(item)

        omitted_count = max(0, len(data_list) - len(filtered))
        if not filtered:
            # Fall back to original if filter removes everything
            filtered = data_list
            omitted_count = 0

        # Group by stock code
        stock_groups: Dict[str, List[Dict]] = {}
        for it in filtered:
            stock_groups.setdefault(it.get('stock_code', 'N/A'), []).append(it)

        # Sort groups by max upside
        ranked = []
        for code, items in stock_groups.items():
            max_pct = 0.0
            for it in items:
                pct = self._parse_upside_pct(it.get('upside_downside', '')) or 0.0
                max_pct = max(max_pct, pct)
            ranked.append((max_pct, code, items))
        ranked.sort(key=lambda x: x[0], reverse=True)

        # Header
        header = f"📊 <b>KLSE Target Price Update</b>\n📅 <i>{today_str}</i>\n\n"

        body = ""
        
        # 1. Top Movers Section (Detailed)
        # Show top 3 movers with bigger visual emphasis
        if self.message_cfg.get('include_top_movers', True):
            count = int(self.message_cfg.get('top_movers_count', 3) or 3)
            top = ranked[:count]
            if top:
                body += "<b>🔥 Top Movers</b>\n"
                for i, (max_pct, code, items) in enumerate(top, 1):
                    # Use the item with the highest upside for the "Top Mover" highlight
                    best_item = max(items, key=lambda x: self._parse_upside_pct(x.get('upside_downside','')) or 0)
                    
                    name = esc(best_item.get('stock_name', 'N/A'))
                    # Shorten name if too long
                    if len(name) > 20:
                        name = name[:20] + "..."
                        
                    call = best_item.get('price_call', '').upper()
                    emoji = {'BUY': '🟢', 'HOLD': '🟡', 'SELL': '🔴'}.get(call, '⚪')
                    cur = best_item.get('current_price', '?')
                    tgt = best_item.get('target_price', '?')
                    analyst = esc(best_item.get('analyst', 'N/A'))
                    
                    # specific format: 1. CODE (Pct%) Emoji CALL
                    body += f"{i}. <b>{code}</b> ({max_pct:.0f}%) {emoji} {call}\n"
                    body += f"   RM {cur} ➔ <b>RM {tgt}</b>\n"
                    body += f"   <i>{analyst}</i>\n\n"

        # 2. Daily Calls List (Compact but clear)
        # We list ALL filtered stocks (including top movers, repeated for completeness or skipped? 
        # Typically lists include everything. Let's include everything but grouped nicely.)
        
        body += "<b>📋 Latest Calls</b>\n"
        max_items = int(self.message_cfg.get('max_items', 50) or 50)
        shown_count = 0
        
        for max_pct, code, items in ranked:
            if shown_count >= max_items:
                break
                
            # Header for Stock
            # AXIATA (6888)
            code_esc = esc(code)
            body += f"<b>{code_esc}</b>\n"
            
            for it in items:
                call = it.get('price_call', '').upper()
                emoji = {'BUY': '🟢', 'HOLD': '🟡', 'SELL': '🔴'}.get(call, '⚪')
                cur = it.get('current_price', '?')
                tgt = it.get('target_price', '?')
                up_str = it.get('upside_downside', '')
                pct_val = self._parse_upside_pct(up_str)
                pct_str = f"{pct_val:.0f}%" if pct_val is not None else "?"
                analyst = esc(it.get('analyst', ''))
                
                # • 🟢 BUY | 2.57 ➔ 2.95 (+15%) | RHB-OSK
                body += f"• {emoji} {call} | {cur} ➔ {tgt} ({pct_str}) | <i>{analyst}</i>\n"
            
            body += "\n"
            shown_count += 1

        # Summary Statistics
        buy_count = sum(1 for d in filtered if d.get('price_call', '').upper() == 'BUY')
        hold_count = sum(1 for d in filtered if d.get('price_call', '').upper() == 'HOLD')
        sell_count = sum(1 for d in filtered if d.get('price_call', '').upper() == 'SELL')
        
        summary = "<b>📊 Summary</b>\n"
        summary += f"🟢 Buy: {buy_count}  🟡 Hold: {hold_count}  🔴 Sell: {sell_count}\n"
        summary += f"📈 Total: {len(filtered)} records\n"
        
        if omitted_count > 0:
             summary += f"⚠️ Omitted {omitted_count} calls < {threshold:.0f}% upside\n"
             
        summary += "\n🔗 <a href=\"https://klse.i3investor.com/web/pricetarget/latest\">View on i3investor</a>"

        message = header + body + summary

        # Truncate if too long (Telegram limit 4096)
        if len(message) > 4096:
            message = message[:4000] + "\n\n… (truncated)"
            
        return message
    
    def send_to_telegram(self, message: str) -> bool:
        """Send message to Telegram channel."""
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        parse_mode = (self.message_cfg.get('parse_mode') or 'Markdown').strip()
        reply_markup = None
        if self.message_cfg.get('include_buttons', True):
            reply_markup = json.dumps({
                "inline_keyboard": [[
                    {"text": "View Source", "url": "https://klse.i3investor.com/web/pricetarget/latest"}
                ]]
            })

        data = {
            'chat_id': self.telegram_channel,
            'text': message,
            'parse_mode': parse_mode,
            'disable_web_page_preview': True
        }
        if reply_markup:
            data['reply_markup'] = reply_markup

        tries = 3
        for attempt in range(1, tries + 1):
            try:
                response = requests.post(url, data=data, timeout=20)
                response.raise_for_status()
                result = response.json()
                if result.get('ok'):
                    logger.info("Message sent successfully to Telegram channel")
                    return True
                else:
                    logger.error(f"Telegram API error: {result}")
                    return False
            except requests.RequestException as e:
                logger.error(f"Network error sending Telegram message (attempt {attempt}/{tries}): {e}")
                if attempt < tries:
                    # small backoff
                    try:
                        import time
                        time.sleep(1.5 * attempt)
                    except Exception:
                        pass
                else:
                    return False
            except Exception as e:
                logger.error(f"Failed to send Telegram message: {e}")
                return False
    
    def is_weekday(self) -> bool:
        """Check if today is a weekday."""
        return datetime.date.today().weekday() < 5  # Monday=0, Sunday=6
    
    def run_monitor(self):
        """Execute the monitoring task."""
        try:
            logger.info("Starting KLSE target price monitoring task...")
            
            # Check if today is a weekday
            if not self.is_weekday():
                logger.info("Today is weekend, skipping monitoring")
                return
            
            # Fetch target price data
            all_data = self.fetch_target_prices()
            
            if not all_data:
                logger.warning("No data retrieved")
                return
            
            # Filter today's data
            today_data = self.filter_today_data(all_data)
            
            # Format message
            use_html = (self.message_cfg.get('parse_mode', 'Markdown').upper() == 'HTML')
            message = self.format_message_html(today_data) if use_html else self.format_message(today_data)
            
            # Send to Telegram
            success = self.send_to_telegram(message)
            
            if success:
                logger.info("Monitoring task completed successfully")
            else:
                logger.error("Monitoring task failed")
                
        except Exception as e:
            logger.error(f"Error in monitoring task: {e}")


def main():
    """Main function."""
    monitor = KLSETargetPriceMonitor()
    monitor.run_monitor()


if __name__ == "__main__":
    main()
