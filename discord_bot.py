#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Discord Bot để tải sách từ Z-Library và upload lên Google Drive
Workflow: Discord Input → Z-Library Download → Rclone Upload → Share Link → Cleanup

Cách dùng:
1. Invite bot vào server Discord
2. Dùng command: !download <z-library-url>
3. Bot sẽ tải sách và trả về Google Drive link
"""

import asyncio
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

import discord
from discord.ext import commands
import yaml

# Import các module từ project
from config.config_manager import ConfigManager
from services.zlibrary_service import ZLibraryService
from utils.logger import setup_logger, get_logger
import logging

# ===== CẤU HÌNH =====
# Load config first to get Discord token
try:
    config_manager = ConfigManager("config.yaml")
    discord_config = config_manager.config.get('discord', {})
    DISCORD_TOKEN = discord_config.get('token', 'YOUR_DISCORD_BOT_TOKEN')
    TEMP_DIR = discord_config.get('temp_dir', 'data/temp')
except Exception as e:
    print(f"⚠️ Error loading config: {e}")
    DISCORD_TOKEN = "YOUR_DISCORD_BOT_TOKEN"
    TEMP_DIR = "data/temp"

RCLONE_REMOTE = "discord"  # ← SỬA: Tên remote trong rclone config
RCLONE_FOLDER = "ZLibrary-Books"  # Folder trên Google Drive
DOWNLOAD_DIR = "data/downloads/discord"  # Thư mục download tạm
AUTO_DELETE_AFTER_UPLOAD = True  # Tự động xóa file sau khi upload

# ===== SETUP =====
setup_logger(logging.INFO, "logs/discord_bot.log")
logger = get_logger("discord_bot")

# Discord Bot intents
intents = discord.Intents.default()
intents.message_content = True  # Vẫn giữ cho backward compatibility

# Sử dụng commands.Bot để hỗ trợ cả slash commands và prefix commands
bot = commands.Bot(
    command_prefix='!',  # Prefix commands (legacy)
    intents=intents,
    help_command=None  # Disable default help để dùng custom
)


class BookDownloader:
    """
    Class xử lý download sách từ Z-Library
    
    Tương tự logic trong test_download_single_book.py
    Hỗ trợ:
    - Direct download link (/dl/)
    - Book page link (/book/)
    - Tự động parse domain (.ec, .se, .is, ...)
    """
    
    def __init__(self):
        self.config_manager = ConfigManager("config.yaml")
        zlib_config = self.config_manager.get_zlibrary_config()
        
        self.zlibrary_service = ZLibraryService(
            email=zlib_config.get('username'),
            password=zlib_config.get('password'),
            proxy_list=zlib_config.get('proxy_list'),
            format_priority=zlib_config.get('format_priority', ['pdf', 'epub', 'mobi']),
            download_dir=DOWNLOAD_DIR
        )
        
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        logger.info("BookDownloader initialized")
    
    def reload_credentials(self, username: str, password: str):
        """
        Reload Z-Library credentials without restarting bot
        
        Args:
            username: Z-Library email
            password: Z-Library password
        """
        try:
            # Update config file
            import yaml
            config_path = "config.yaml"
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            # Update zlibrary section
            if 'zlibrary' not in config_data:
                config_data['zlibrary'] = {}
            
            config_data['zlibrary']['username'] = username
            config_data['zlibrary']['password'] = password
            
            # Write back to file
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
            
            # Reload ConfigManager
            self.config_manager = ConfigManager(config_path)
            zlib_config = self.config_manager.get_zlibrary_config()
            
            # Recreate ZLibraryService with new credentials
            self.zlibrary_service = ZLibraryService(
                email=username,
                password=password,
                proxy_list=zlib_config.get('proxy_list'),
                format_priority=zlib_config.get('format_priority', ['pdf', 'epub', 'mobi']),
                download_dir=DOWNLOAD_DIR
            )
            
            logger.info(f"Credentials reloaded for user: {username}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reload credentials: {e}")
            return False
    
    def extract_book_info_from_url(self, url: str) -> Optional[dict]:
        """
        Trích xuất thông tin từ URL Z-Library
        
        Hỗ trợ các domain: .ec, .se, .is, .sk, reader.z-library.ec, ...
        Pattern: https://z-library.{domain}/book/{id}/{hash}
                 https://z-library.{domain}/dl/{id}/{hash}
                 https://reader.z-library.ec/read/{hash}/{id}/{hash2}/...
        
        Supported URL formats:
        ✅ /book/1269938/e536b6
        ✅ /book/1269938/e536b6/filename.html
        ✅ /book/1269938/e536b6?ts=1651
        ✅ /book/1269938/e536b6?dsource=recommend
        ✅ /book/1269938/e536b6/title.html?utm_source=google&utm_campaign=xyz
        ✅ /book/1269938/e536b6#section
        ✅ /dl/1269938/b88232 (direct download)
        ✅ reader.z-library.ec/read/{hash}/{id}/{hash2}/... (online reader)
        """
        # Remove ALL query params (?xxx) and fragments (#xxx)
        # This handles: ?ts=, ?dsource=, ?utm_source=, ?ref=, etc.
        clean_url = url.split('?')[0].split('#')[0]
        
        # Pattern 0: reader.z-library.ec/read/{long_hash}/{id}/{hash2}/...
        # Example: https://reader.z-library.ec/read/3b932703.../115995718/b827db/...
        if 'reader.z-library' in url:
            match = re.search(r'/read/[a-z0-9]+/(\d+)/([a-z0-9]+)', url, re.IGNORECASE)
            if match:
                book_id = match.group(1)
                book_hash = match.group(2)
                # Convert reader URL to book page URL
                book_url = f"https://z-library.ec/book/{book_id}/{book_hash}"
                logger.info(f"Converted reader URL to book URL: {book_url}")
                return {
                    'id': book_id,
                    'hash': book_hash,
                    'url': book_url,  # Use converted URL
                    'type': 'book_page',
                    'domain': 'z-library.ec'
                }
        
        # Pattern 1: /book/{id}/{hash}[/optional-filename.ext] (book page)
        # Regex: /book/(\d+)/([a-z0-9]+)(?:/[^/]+)?
        #   - (\d+): book ID (digits)
        #   - ([a-z0-9]+): hash (alphanumeric, case-insensitive)
        #   - (?:/[^/]+)?: optional non-capturing group for filename
        match = re.search(r'/book/(\d+)/([a-z0-9]+)(?:/[^/]+)?', clean_url, re.IGNORECASE)
        if match:
            return {
                'id': match.group(1),
                'hash': match.group(2),
                'url': url,
                'type': 'book_page',
                'domain': self._extract_domain(url)
            }
        
        # Pattern 2: /dl/{id}/{hash} (direct download)
        # Note: Some hashes may contain letters beyond a-f (not strictly hex)
        match = re.search(r'/dl/(\d+)/([a-z0-9]+)', clean_url)
        if match:
            return {
                'id': match.group(1),
                'hash': match.group(2),
                'url': url,
                'type': 'direct_download',
                'domain': self._extract_domain(url)
            }
        
        return None
    
    def _extract_domain(self, url: str) -> str:
        """Trích xuất domain từ URL"""
        import re
        match = re.search(r'https?://([^/]+)', url)
        if match:
            return match.group(1)
        return 'z-library.ec'  # Default
    
    async def _get_download_hash_from_page(self, book_page_url: str) -> Optional[str]:
        """
        Parse book page HTML để lấy download hash thật từ download button
        
        HTML structure:
        <a class="btn btn-default addDownloadedBook" href="/dl/1269938/f07321">
            <span>pdf</span>, 19.30 MB
        </a>
        
        Returns:
            str: Download hash (e.g., 'f07321') hoặc None nếu không tìm thấy
        """
        try:
            import requests
            from bs4 import BeautifulSoup
            
            logger.info(f"Fetching book page: {book_page_url}")
            
            # Add proper headers to mimic browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            response = requests.get(book_page_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Debug: Save HTML to file for inspection
            debug_html_path = "data/temp/debug_page.html"
            os.makedirs(os.path.dirname(debug_html_path), exist_ok=True)
            with open(debug_html_path, 'w', encoding='utf-8') as f:
                f.write(response.text)
            logger.info(f"Saved HTML to {debug_html_path} for debugging")
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Method 1: Find by class "addDownloadedBook" (most reliable)
            # Priority: Look for primary download button (usually PDF, first format)
            download_links = soup.find_all('a', class_='addDownloadedBook')
            
            download_link = None
            if download_links:
                logger.info(f"Found {len(download_links)} download button(s)")
                # Debug: Log all found links
                for i, link in enumerate(download_links):
                    href = link.get('href')
                    format_span = link.find('span', class_='book-property__extension')
                    fmt = format_span.text.strip() if format_span else 'unknown'
                    logger.info(f"  Button {i+1}: {href} (format: {fmt})")
                
                # Take the first one (primary format)
                download_link = download_links[0]
                logger.info(f"Using first button")
            
            if not download_link:
                # Method 2: Find any <a> with href matching /dl/{id}/{hash}
                download_link = soup.find('a', href=re.compile(r'/dl/\d+/[a-z0-9]+', re.IGNORECASE))
                logger.info("Using fallback method to find download link")
            
            if download_link:
                href = download_link.get('href')
                # Try to get format from button text
                format_span = download_link.find('span', class_='book-property__extension')
                file_format = format_span.text.strip() if format_span else 'unknown'
                logger.info(f"Found download link: {href} (format: {file_format})")
                
                # Extract hash from /dl/{id}/{hash}
                match = re.search(r'/dl/\d+/([a-z0-9]+)', href, re.IGNORECASE)
                if match:
                    download_hash = match.group(1)
                    logger.info(f"Found download hash: {download_hash}")
                    return download_hash
            
            logger.warning("Could not find download link in book page")
            return None
            
        except Exception as e:
            logger.error(f"Error parsing book page: {e}")
            return None
    
    async def download_by_isbn(self, isbn: str) -> Optional[dict]:
        """
        Download sách bằng ISBN
        
        Args:
            isbn: ISBN-10 hoặc ISBN-13 (chỉ số, không có dấu gạch ngang)
        
        Returns:
            dict: {
                'success': bool,
                'file_path': str,
                'file_name': str,
                'file_size': int,
                'title': str,
                'error': str (if failed)
            }
        """
        try:
            logger.info(f"Searching by ISBN: {isbn}")
            
            # Search by ISBN using zlibrary API
            try:
                search_results = self.zlibrary_service.search_books(isbn=isbn)
            except Exception as e:
                logger.warning(f"ISBN search failed: {e}")
                search_results = None
            
            if not search_results:
                return {
                    'success': False,
                    'error': f'❌ Không tìm thấy sách với ISBN: {isbn}'
                }
            
            logger.info(f"Found {len(search_results)} book(s) for ISBN {isbn}")
            
            # Get format priority from config
            zlib_config = self.config_manager.get_zlibrary_config()
            format_priority = zlib_config.get('format_priority', ['pdf', 'epub', 'mobi', 'azw3'])
            
            # Choose best format
            best_result = None
            best_score = -1
            
            for i, result in enumerate(search_results[:5]):  # Check first 5
                score = 0
                extension = result.get('extension', '').lower()
                
                # Score by format priority
                for priority_idx, fmt in enumerate(format_priority):
                    if fmt in extension:
                        score = 100 - priority_idx * 10
                        break
                
                logger.info(f"  Result {i+1}: {result.get('title', 'N/A')[:50]} ({extension}) - Score: {score}")
                
                if score > best_score:
                    best_score = score
                    best_result = result
            
            if not best_result:
                return {
                    'success': False,
                    'error': '❌ Không tìm thấy định dạng phù hợp'
                }
            
            # Extract info
            book_id = best_result.get('zlibrary_id')
            title = best_result.get('title', f'Book_{isbn}')
            authors = best_result.get('authors', 'Unknown')
            extension = best_result.get('extension', 'pdf')
            download_url = best_result.get('download_url')
            
            if not download_url:
                return {
                    'success': False,
                    'error': '❌ Không có download URL'
                }
            
            logger.info(f"✅ Selected: {title} ({extension}) - {download_url}")
            
            # Prepare book_data and download
            book_data = {
                'zlibrary_id': book_id,
                'title': title,
                'authors': authors,
                'download_url': download_url,
                'extension': extension,
                'url': download_url  # Use download_url as source
            }
            
            logger.info(f"Downloading book ID: {book_id} via zlibrary service")
            
            # Run download in executor to avoid blocking
            loop = asyncio.get_event_loop()
            file_path = await loop.run_in_executor(
                None,
                self.zlibrary_service.download_book,
                book_data,
                DOWNLOAD_DIR
            )
            
            if not file_path or not os.path.exists(file_path):
                return {
                    'success': False,
                    'error': 'Download thất bại. File không tồn tại sau khi download.'
                }
            
            # Get file info
            file_size = os.path.getsize(file_path)
            file_name = os.path.basename(file_path)
            
            logger.info(f"Download thành công: {file_name} ({file_size} bytes)")
            
            return {
                'success': True,
                'file_path': file_path,
                'file_name': file_name,
                'file_size': file_size,
                'title': title
            }
            
        except Exception as e:
            logger.error(f"Lỗi khi download by ISBN: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': f'Lỗi: {str(e)}'
            }
    
    async def download_book(self, url: str) -> Optional[dict]:
        """
        Download sách từ Z-Library
        
        Returns:
            dict: {
                'success': bool,
                'file_path': str,
                'file_name': str,
                'file_size': int,
                'title': str,
                'error': str (if failed)
            }
        """
        try:
            logger.info(f"Bắt đầu download từ URL: {url}")
            
            # Parse URL
            book_info = self.extract_book_info_from_url(url)
            if not book_info:
                return {
                    'success': False,
                    'error': 'URL không hợp lệ. Vui lòng cung cấp URL từ Z-Library'
                }
            
            # Get book ID (works for both /book/ and /dl/ URLs)
            book_id = book_info['id']
            
            # IMPORTANT: Hash in URL expires! We must search to get fresh download_url
            # Strategy: Extract title from URL filename -> search by title -> match by ID
            logger.info(f"Book ID: {book_id}")
            
            try:
                import requests
                from bs4 import BeautifulSoup
                
                # Step 1: Fetch book page to extract ISBN
                # ISBN is unique identifier - perfect for exact search!
                book_page_url = url.split('?')[0].split('#')[0]
                if '/dl/' in book_page_url:
                    # Convert /dl/ to /book/ to access book page
                    book_page_url = book_page_url.replace('/dl/', '/book/')
                    # Remove hash part: /book/ID/hash → /book/ID
                    parts = book_page_url.split('/')
                    if len(parts) >= 6:  # https://domain/book/ID/hash
                        book_page_url = '/'.join(parts[:5])  # Keep only up to ID
                
                logger.info(f"Fetching book page to extract ISBN: {book_page_url}")
                
                # Get authenticated cookies from zlibrary service
                lib = self.zlibrary_service.search_service.lib
                cookies_dict = {}
                if hasattr(lib, 'cookies') and lib.cookies:
                    cookies_dict = lib.cookies
                    logger.info(f"Using {len(cookies_dict)} authenticated cookies")
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                }
                
                # Add cookies to headers if available
                if cookies_dict:
                    headers['Cookie'] = "; ".join([f"{k}={v}" for k, v in cookies_dict.items()])
                
                try:
                    response = requests.get(book_page_url, headers=headers, timeout=10)
                    response.raise_for_status()
                except Exception as e:
                    logger.error(f"Failed to fetch book page: {e}")
                    return {
                        'success': False,
                        'error': f'❌ Không thể truy cập trang sách: {str(e)}'
                    }
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Step 2: Extract ISBN from meta description or page content
                # Example: <meta name="description" content="...ISBN: 9780194420884...">
                isbn = None
                
                # Method 1: Check meta description
                meta_desc = soup.find('meta', attrs={'name': 'description'})
                if meta_desc and meta_desc.get('content'):
                    desc_content = meta_desc.get('content')
                    # Look for ISBN pattern: ISBN: XXXXXXXXXX or ISBN-10/13
                    isbn_match = re.search(r'ISBN[:\s-]*(\d{10,13})', desc_content, re.IGNORECASE)
                    if isbn_match:
                        isbn = isbn_match.group(1)
                        logger.info(f"Found ISBN in meta description: {isbn}")
                
                # Method 2: Look in page content for ISBN
                if not isbn:
                    # Find all text containing "ISBN"
                    isbn_elements = soup.find_all(string=re.compile(r'ISBN', re.IGNORECASE))
                    for elem in isbn_elements:
                        isbn_match = re.search(r'ISBN[:\s-]*(\d{10,13})', elem, re.IGNORECASE)
                        if isbn_match:
                            isbn = isbn_match.group(1)
                            logger.info(f"Found ISBN in page content: {isbn}")
                            break
                
                # Method 3: Look for data attributes or structured data
                if not isbn:
                    # Sometimes ISBN is in structured data (JSON-LD)
                    script_tags = soup.find_all('script', type='application/ld+json')
                    for script in script_tags:
                        try:
                            import json
                            data = json.loads(script.string)
                            if 'isbn' in data:
                                isbn = str(data['isbn'])
                                logger.info(f"Found ISBN in structured data: {isbn}")
                                break
                        except:
                            pass
                
                # Step 3: Search by ISBN (most accurate!) or fallback to get_by_id
                if not isbn:
                    logger.warning("No ISBN found in page, trying get_by_id API...")
                    
                    # Try using zlibrary's get_by_id (may fail on some domains)
                    lib = self.zlibrary_service.search_service.lib
                    
                    async def get_book_by_id():
                        try:
                            # Try to get book directly by ID
                            book = await lib.get_by_id(str(book_id))
                            return book
                        except Exception as e:
                            logger.error(f"get_by_id failed: {e}")
                            return None
                    
                    book_details = asyncio.run(get_book_by_id())
                    
                    if not book_details:
                        return {
                            'success': False,
                            'error': '❌ URL không có tên sách và không thể tìm theo ID\n\n' +
                                    '💡 Vui lòng dùng URL có tên sách, ví dụ:\n' +
                                    '✅ https://z-library.xx/book/123/abc/book-title.html\n' +
                                    '❌ https://z-library.xx/book/123/abc'
                        }
                    
                    # Got book details directly, extract info
                    download_url = book_details.get('download_url')
                    if not download_url:
                        return {
                            'success': False,
                            'error': '❌ Sách không có link download'
                        }
                    
                    title = book_details.get('name', f'Book_{book_id}')
                    authors = book_details.get('authors', 'Unknown')
                    extension = book_details.get('extension', 'pdf')
                    
                    logger.info(f"Got book via get_by_id: {title}")
                    
                    # Skip search, go directly to download
                    book_data = {
                        'zlibrary_id': book_id,
                        'title': title,
                        'authors': authors,
                        'download_url': download_url,
                        'extension': extension,
                        'url': url
                    }
                    
                    logger.info(f"Downloading book ID: {book_id} (using zlibrary service authenticated session)")
                    file_path = self.zlibrary_service.download_book(book_data, DOWNLOAD_DIR)
                    
                    if not file_path or not os.path.exists(file_path):
                        return {
                            'success': False,
                            'error': 'Download thất bại. File không tồn tại sau khi download.'
                        }
                    
                    # Continue to upload...
                    file_size = os.path.getsize(file_path)
                    file_name = os.path.basename(file_path)
                    
                    logger.info(f"Download thành công: {file_name} ({file_size} bytes)")
                    
                    # Upload to Google Drive
                    logger.info(f"Uploading {file_name} lên {RCLONE_REMOTE}:{RCLONE_FOLDER}/{file_name}")
                    uploader = RcloneUploader(RCLONE_REMOTE, RCLONE_FOLDER)
                    
                    upload_result = uploader.upload_file(file_path)
                    if not upload_result['success']:
                        return {
                            'success': False,
                            'error': f"Upload thất bại: {upload_result.get('error', 'Unknown error')}"
                        }
                    
                    logger.info(f"Upload thành công: {upload_result['remote_path']}")
                    
                    # Get public link
                    link_result = uploader.get_public_link(file_name)
                    public_link = link_result.get('link', 'Không thể tạo public link')
                    
                    logger.info(f"Public link created: {public_link}")
                    
                    # Cleanup
                    if AUTO_DELETE_AFTER_UPLOAD:
                        try:
                            os.remove(file_path)
                            logger.info(f"Đã xóa file local: {file_path}")
                        except Exception as e:
                            logger.warning(f"Không thể xóa file: {e}")
                    
                    logger.info(f"Hoàn thành download qua get_by_id: {file_name}")
                    
                    return {
                        'success': True,
                        'file_name': file_name,
                        'file_size': file_size,
                        'public_link': public_link,
                        'remote_path': upload_result['remote_path']
                    }
                
                # Step 4: Search by ISBN using zlibrary API (proper way!)
                # Use zlibrary_service.search_books(isbn=...) instead of web crawling
                logger.info(f"Searching Z-Library API for ISBN: {isbn}")
                
                search_results = None
                try:
                    # Use authenticated zlibrary API (handles session automatically)
                    # search_books returns List[Dict] with authenticated download_url
                    search_results = self.zlibrary_service.search_books(isbn=isbn)
                    
                except Exception as isbn_search_error:
                    # ISBN search failed - fallback to get_by_id
                    logger.warning(f"ISBN search failed: {isbn_search_error}")
                    logger.info(f"Falling back to get_by_id({book_id})...")
                    search_results = None
                
                if not search_results:
                    # Fallback to get_by_id if ISBN search failed
                    logger.warning(f"No results from ISBN search, trying get_by_id({book_id})...")
                    
                    lib = self.zlibrary_service.search_service.lib
                    
                    async def get_book_by_id():
                        try:
                            book = await lib.get_by_id(str(book_id))
                            return book
                        except Exception as e:
                            logger.error(f"get_by_id failed: {e}")
                            return None
                    
                    book_details = asyncio.run(get_book_by_id())
                    
                    if not book_details:
                        return {
                            'success': False,
                            'error': '❌ Không tìm thấy sách với ISBN và get_by_id cũng thất bại'
                        }
                    
                    # Got book via get_by_id
                    download_url = book_details.get('download_url')
                    if not download_url:
                        return {
                            'success': False,
                            'error': '❌ Sách không có link download'
                        }
                    
                    title = book_details.get('name', f'Book_{book_id}')
                    authors = book_details.get('authors', 'Unknown')
                    extension = book_details.get('extension', 'pdf')
                    
                    logger.info(f"✅ Got book via get_by_id: {title}")
                    
                else:
                    # ISBN search succeeded - choose best match
                    logger.info(f"Found {len(search_results)} book(s) from Z-Library API")
                    
                    # Step 4.5: Choose the best match from API results
                    from difflib import SequenceMatcher
                    
                    def similarity(a, b):
                        """Calculate text similarity (0-1)"""
                        return SequenceMatcher(None, a.lower(), b.lower()).ratio()
                    
                    best_match = None
                    best_score = 0
                    
                    # Get format priority from config
                    zlib_config = self.config_manager.get_zlibrary_config()
                    format_priority = zlib_config.get('format_priority', ['pdf', 'epub', 'mobi', 'azw3'])
                    
                    for i, result in enumerate(search_results[:10]):  # Check first 10 results
                        # Extract from API result (Dict format)
                        candidate_id = result.get('zlibrary_id')
                        candidate_title = result.get('title', '')
                        candidate_format = result.get('extension', 'unknown')
                        candidate_isbn = result.get('isbn', '')
                        candidate_download_url = result.get('download_url', '')  # Authenticated URL!
                        candidate_author = result.get('authors', '')
                        
                        if not candidate_id:
                            continue
                        
                        # Calculate match score
                        score = 0
                        
                        # 1. ISBN match = +50 points (most important!)
                        if candidate_isbn and candidate_isbn == isbn:
                            score += 50
                            logger.info(f"  Result {i+1}: ISBN exact match! +50")
                        
                        # 2. Format priority = +30 points for PDF, +20 for epub, etc.
                        for priority_idx, fmt in enumerate(format_priority):
                            if fmt in candidate_format:
                                score += (30 - priority_idx * 5)
                                logger.info(f"  Result {i+1}: Format {fmt} = +{30 - priority_idx * 5}")
                                break
                        
                        # 3. Title similarity (if we extracted title from URL) = up to +20 points
                        if book_info.get('title'):
                            title_sim = similarity(book_info['title'], candidate_title)
                            title_score = int(title_sim * 20)
                            score += title_score
                            if title_score > 0:
                                logger.info(f"  Result {i+1}: Title similarity {title_sim:.2f} = +{title_score}")
                        
                        logger.info(f"  Result {i+1}: ID={candidate_id}, Title='{candidate_title[:50]}', Format={candidate_format}, Score={score}")
                        
                        if score > best_score:
                            best_score = score
                            best_match = {
                                'id': candidate_id,
                                'title': candidate_title,
                                'format': candidate_format,
                                'download_url': candidate_download_url,  # Already authenticated!
                                'author': candidate_author,
                                'result': result  # Keep full result dict
                            }
                    
                    if not best_match:
                        logger.error("No suitable match found after scoring")
                        return {
                            'success': False,
                            'error': '❌ Không tìm thấy sách phù hợp'
                        }
                    
                    logger.info(f"✅ BEST MATCH: ID={best_match['id']}, Title='{best_match['title'][:50]}', Format={best_match['format']}, Score={best_score}")
                    
                    # Extract from best_match
                    title = best_match.get('title', f'Book_{book_id}')
                    authors = best_match.get('author', 'Unknown')
                    extension = best_match.get('format', 'pdf')
                    download_url = best_match.get('download_url')
                    
                    if not download_url:
                        logger.error("No download_url in API result!")
                        return {
                            'success': False,
                            'error': '❌ API không trả về download URL'
                        }
                    
                    logger.info(f"Using authenticated download URL from API: {download_url}")
            
            except Exception as e:
                logger.error(f"Error in ISBN search workflow: {e}")
                import traceback
                traceback.print_exc()
                return {
                    'success': False,
                    'error': f'❌ Lỗi: {str(e)}'
                }
            
            # Prepare book_data for download service
            book_data = {
                'zlibrary_id': book_id,
                'title': title,
                'authors': authors,
                'download_url': download_url,  # Already authenticated from API!
                'extension': extension,
                'url': url
            }
            logger.info(f"Downloading book ID: {book_id} via zlibrary service (API download_url)")
            
            # Run download in executor to avoid blocking Discord event loop (266MB file!)
            loop = asyncio.get_event_loop()
            file_path = await loop.run_in_executor(
                None,  # Use default ThreadPoolExecutor
                self.zlibrary_service.download_book,
                book_data,
                DOWNLOAD_DIR
            )
            
            if not file_path or not os.path.exists(file_path):
                return {
                    'success': False,
                    'error': 'Download thất bại. File không tồn tại sau khi download.'
                }
            
            # Lấy thông tin file
            file_size = os.path.getsize(file_path)
            file_name = os.path.basename(file_path)
            
            logger.info(f"Download thành công: {file_name} ({file_size} bytes)")
            
            return {
                'success': True,
                'file_path': file_path,
                'file_name': file_name,
                'file_size': file_size,
                'title': title
            }
            
        except Exception as e:
            logger.error(f"Lỗi khi download: {str(e)}")
            return {
                'success': False,
                'error': f'Lỗi: {str(e)}'
            }


class RcloneUploader:
    """Class xử lý upload lên Google Drive bằng Rclone"""
    
    def __init__(self, remote: str, folder: str):
        self.remote = remote
        self.folder = folder
        logger.info(f"RcloneUploader initialized: {remote}:{folder}")
    
    def check_rclone_installed(self) -> bool:
        """Kiểm tra xem rclone đã được cài đặt chưa"""
        try:
            result = subprocess.run(['rclone', 'version'], 
                                   capture_output=True, 
                                   text=True, 
                                   timeout=5)
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Rclone không được cài đặt: {e}")
            return False
    
    async def upload_file(self, file_path: str) -> Optional[dict]:
        """
        Upload file lên Google Drive
        
        Returns:
            dict: {
                'success': bool,
                'remote_path': str,
                'share_link': str (if available),
                'error': str (if failed)
            }
        """
        try:
            if not self.check_rclone_installed():
                return {
                    'success': False,
                    'error': 'Rclone chưa được cài đặt trên VPS'
                }
            
            file_name = os.path.basename(file_path)
            remote_path = f"{self.remote}:{self.folder}/{file_name}"
            
            logger.info(f"Uploading {file_name} lên {remote_path}")
            
            # Upload với progress
            cmd = [
                'rclone', 'copy',
                file_path,
                f"{self.remote}:{self.folder}",
                '--progress',
                '--stats', '1s'
            ]
            
            # Chạy rclone
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode('utf-8')
                logger.error(f"Upload thất bại: {error_msg}")
                return {
                    'success': False,
                    'error': f'Rclone error: {error_msg}'
                }
            
            logger.info(f"Upload thành công: {remote_path}")
            
            # Tạo public link (nếu có thể)
            share_link = await self.create_public_link(file_name)
            
            return {
                'success': True,
                'remote_path': remote_path,
                'file_name': file_name,
                'share_link': share_link
            }
            
        except Exception as e:
            logger.error(f"Lỗi khi upload: {str(e)}")
            return {
                'success': False,
                'error': f'Lỗi: {str(e)}'
            }
    
    async def create_public_link(self, file_name: str) -> Optional[str]:
        """
        Tạo public link cho file (nếu Google Drive hỗ trợ)
        
        Note: Cần cấu hình rclone với Google Drive API
        """
        try:
            # Lấy link từ rclone link
            cmd = [
                'rclone', 'link',
                f"{self.remote}:{self.folder}/{file_name}"
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                link = stdout.decode('utf-8').strip()
                logger.info(f"Public link created: {link}")
                return link
            else:
                logger.warning("Không thể tạo public link, có thể cần cấu hình thêm")
                return None
                
        except Exception as e:
            logger.warning(f"Không thể tạo public link: {e}")
            return None


# ===== DISCORD BOT COMMANDS =====

downloader = BookDownloader()
uploader = RcloneUploader(RCLONE_REMOTE, RCLONE_FOLDER)


@bot.event
async def on_ready():
    logger.info(f'Bot đã đăng nhập: {bot.user.name}')
    print(f'✅ Bot đã sẵn sàng: {bot.user.name}')
    print(f'📚 Slash commands: /download, /quota, /ping, /help')
    print(f'📚 Prefix commands: !download, !quota, !ping, !help_bot')
    
    # Sync slash commands với Discord
    try:
        synced = await bot.tree.sync()
        logger.info(f"Đã sync {len(synced)} slash command(s)")
        print(f"✅ Đã sync {len(synced)} slash command(s)")
    except Exception as e:
        logger.error(f"Lỗi khi sync commands: {e}")
        print(f"⚠️  Lỗi sync commands: {e}")


# ===== HELPER FUNCTION =====

async def process_download_request(interaction_or_ctx, query: str, is_slash: bool = False):
    """
    Helper function xử lý download request - hỗ trợ cả URL và ISBN
    Dùng chung cho cả slash command và prefix command
    
    Args:
        interaction_or_ctx: discord.Interaction (slash) hoặc commands.Context (prefix)
        query: Z-Library URL HOẶC ISBN (10-13 số)
        is_slash: True nếu là slash command, False nếu là prefix command
    """
    # Detect if query is ISBN or URL
    is_isbn = re.match(r'^\d{10,13}$', query.strip())
    
    # Get author info and initialize status_msg
    status_msg = None
    if is_slash:
        author = interaction_or_ctx.user
        # Defer để có thời gian xử lý (15 phút thay vì 3 giây)
        await interaction_or_ctx.response.defer()
    else:
        author = interaction_or_ctx.author
        status_msg = await interaction_or_ctx.send(f"⏳ Đang xử lý request của {author.mention}...")
    
    try:
        # Send initial status message (will be edited throughout)
        if is_slash:
            if is_isbn:
                initial_msg = f"📚 **[1/4]** Đang tìm sách với ISBN: `{query}`...\n⏳ Request từ {author.mention}"
            else:
                initial_msg = f"📥 **[1/4]** Đang download sách từ Z-Library...\n⏳ Request từ {author.mention}"
            
            status_msg = await interaction_or_ctx.followup.send(
                initial_msg,
                wait=True  # Wait to get message object for editing
            )
        else:
            if is_isbn:
                await status_msg.edit(content=f"📚 **[1/4]** Đang tìm sách với ISBN: `{query}`...\n⏳ Request từ {author.mention}")
            else:
                await status_msg.edit(content=f"📥 **[1/4]** Đang download sách từ Z-Library...\n⏳ Request từ {author.mention}")
        
        logger.info(f"User {author} yêu cầu download: {query}")
        
        # If ISBN, search and download first result
        if is_isbn:
            download_result = await downloader.download_by_isbn(query.strip())
        else:
            download_result = await downloader.download_book(query)
        
        if not download_result['success']:
            error_msg = f"❌ **Download thất bại:**\n```{download_result['error']}```"
            await status_msg.edit(content=error_msg)
            return
        
        file_path = download_result['file_path']
        file_name = download_result['file_name']
        file_size_mb = download_result['file_size'] / (1024 * 1024)
        
        # Bước 2: Upload lên Google Drive (edit same message)
        upload_msg = f"☁️ **[2/4]** Đang upload `{file_name}` ({file_size_mb:.2f} MB) lên Google Drive...\n⏳ Request từ {author.mention}"
        await status_msg.edit(content=upload_msg)
        
        upload_result = await uploader.upload_file(file_path)
        
        if not upload_result['success']:
            error_msg = f"❌ **Upload thất bại:**\n```{upload_result['error']}```"
            await status_msg.edit(content=error_msg)
            return
        
        # Bước 3: Tạo public link (edit same message)
        link_msg = f"� **[3/4]** Đang tạo public link...\n⏳ Request từ {author.mention}"
        await status_msg.edit(content=link_msg)
        
        embed = discord.Embed(
            title="✅ Download & Upload Thành Công!",
            color=discord.Color.green(),
            description=f"Sách đã được tải và upload lên Google Drive"
        )
        
        embed.add_field(name="📖 File Name", value=f"`{file_name}`", inline=False)
        embed.add_field(name="📊 File Size", value=f"{file_size_mb:.2f} MB", inline=True)
        embed.add_field(name="☁️ Remote Path", value=f"`{upload_result['remote_path']}`", inline=False)
        
        if upload_result.get('share_link'):
            embed.add_field(name="🔗 Public Link", value=upload_result['share_link'], inline=False)
        else:
            embed.add_field(
                name="📁 Access", 
                value=f"File đã được upload vào folder `{RCLONE_FOLDER}` trên Google Drive\n"
                      f"Dùng lệnh `rclone link {RCLONE_REMOTE}:{RCLONE_FOLDER}/{file_name}` để lấy link",
                inline=False
            )
        
        embed.set_footer(text=f"Requested by {author.name}", icon_url=author.avatar.url if author.avatar else None)
        
        # Bước 4: Cleanup (xóa file local nếu được bật) - edit status message
        if AUTO_DELETE_AFTER_UPLOAD:
            cleanup_msg = f"🗑️ **[4/4]** Đang xóa file tạm trên VPS...\n⏳ Request từ {author.mention}"
            await status_msg.edit(content=cleanup_msg)
            await asyncio.sleep(1)
            try:
                os.remove(file_path)
                logger.info(f"Đã xóa file local: {file_path}")
            except Exception as e:
                logger.warning(f"Không thể xóa file: {e}")
        
        # Final result - edit same message with embed
        await status_msg.edit(content=None, embed=embed)
        
        logger.info(f"Hoàn thành request cho user {author}: {file_name}")
        
    except Exception as e:
        logger.error(f"Lỗi khi xử lý command: {e}", exc_info=True)
        error_msg = f"❌ **Lỗi không mong muốn:**\n```{str(e)}```"
        await status_msg.edit(content=error_msg)


# ===== SLASH COMMANDS =====

@bot.tree.command(name="download", description="📥 Download sách từ Z-Library và upload lên Google Drive")
async def slash_download(interaction: discord.Interaction, query: str):
    """
    Slash command: /download <url hoặc ISBN>
    
    Parameters:
        query: URL sách trên Z-Library HOẶC ISBN (10 hoặc 13 số)
    
    Examples:
        /download https://z-library.ec/book/11948830/2c2f55
        /download 9780194420884
        /download 0194420884
    """
    await process_download_request(interaction, query, is_slash=True)


@bot.tree.command(name="quota", description="📊 Kiểm tra quota Z-Library còn lại")
async def slash_quota(interaction: discord.Interaction):
    """Slash command: /quota"""
    await interaction.response.defer()
    
    try:
        limits = downloader.zlibrary_service.get_download_limits()
        
        embed = discord.Embed(
            title="📊 Z-Library Download Quota",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Daily Limit", value=limits.get('daily_amount', 'N/A'), inline=True)
        embed.add_field(name="Remaining", value=limits.get('daily_remaining', 'N/A'), inline=True)
        embed.add_field(name="Next Reset", value=limits.get('daily_reset', 'N/A'), inline=False)
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        await interaction.followup.send(f"❌ Không thể lấy thông tin quota: {str(e)}")


@bot.tree.command(name="set_credentials", description="🔑 Thay đổi Z-Library credentials (khi hết quota)")
async def slash_set_credentials(interaction: discord.Interaction, email: str, password: str):
    """
    Slash command: /set_credentials <email> <password>
    
    Thay đổi Z-Library account credentials
    Hữu ích khi account hiện tại hết quota
    
    Parameters:
        email: Z-Library email/username
        password: Z-Library password
    """
    # Check if user has permission (optional - có thể thêm role check)
    # if not interaction.user.guild_permissions.administrator:
    #     await interaction.response.send_message("❌ Chỉ admin mới có thể thay đổi credentials!", ephemeral=True)
    #     return
    
    await interaction.response.defer(ephemeral=True)  # Response riêng tư (chỉ user thấy)
    
    try:
        # Reload credentials
        success = downloader.reload_credentials(email, password)
        
        if success:
            # Get new quota info
            try:
                limits = downloader.zlibrary_service.get_download_limits()
                quota_info = (
                    f"\n\n📊 **New Account Quota:**\n"
                    f"• Daily Limit: {limits.get('daily_amount', 'N/A')}\n"
                    f"• Remaining: {limits.get('daily_remaining', 'N/A')}\n"
                    f"• Next Reset: {limits.get('daily_reset', 'N/A')}"
                )
            except:
                quota_info = ""
            
            await interaction.followup.send(
                f"✅ **Credentials Updated Successfully!**\n"
                f"📧 New account: `{email}`\n"
                f"🔐 Password: `{'*' * len(password)}`"
                f"{quota_info}",
                ephemeral=True
            )
            
            logger.info(f"Credentials changed by {interaction.user.name} to {email}")
            
        else:
            await interaction.followup.send(
                f"❌ **Failed to update credentials!**\n"
                f"Check logs for details.",
                ephemeral=True
            )
    
    except Exception as e:
        logger.error(f"Error changing credentials: {e}")
        await interaction.followup.send(
            f"❌ **Error:**\n```{str(e)}```",
            ephemeral=True
        )


@bot.tree.command(name="version", description="📦 Kiểm tra version code bot")
async def slash_version(interaction: discord.Interaction):
    """Slash command: /version - Check bot version"""
    try:
        import subprocess
        # Get git commit hash
        commit = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode('ascii').strip()
        # Get git commit date
        commit_date = subprocess.check_output(['git', 'log', '-1', '--format=%cd', '--date=short']).decode('ascii').strip()
        
        embed = discord.Embed(
            title="📦 Bot Version Info",
            color=discord.Color.blue()
        )
        embed.add_field(name="Git Commit", value=f"`{commit}`", inline=True)
        embed.add_field(name="Commit Date", value=commit_date, inline=True)
        embed.add_field(name="Status", value="✅ Running with HTML parsing fix", inline=False)
        
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"⚠️ Cannot get version: {str(e)}")


@bot.tree.command(name="ping", description="🏓 Kiểm tra bot có hoạt động không")
async def slash_ping(interaction: discord.Interaction):
    """Slash command: /ping"""
    latency_ms = round(bot.latency * 1000)
    await interaction.response.send_message(f'🏓 Pong! Latency: {latency_ms}ms')


@bot.tree.command(name="help", description="📚 Hiển thị hướng dẫn sử dụng bot")
async def slash_help(interaction: discord.Interaction):
    """Slash command: /help"""
    embed = discord.Embed(
        title="📚 Z-Library Discord Bot - Hướng Dẫn",
        description="Bot tự động download sách từ Z-Library và upload lên Google Drive",
        color=discord.Color.purple()
    )
    
    embed.add_field(
        name="⚡ Slash Commands (Modern)",
        value=(
            "`/download <url>` - Download và upload sách\n"
            "`/quota` - Kiểm tra quota còn lại\n"
            "`/set_credentials <email> <password>` - Đổi Z-Library account\n"
            "`/ping` - Test bot\n"
            "`/help` - Xem hướng dẫn này"
        ),
        inline=False
    )
    
    embed.add_field(
        name="📝 Prefix Commands (Legacy)",
        value=(
            "`!download <url>` - Download và upload sách\n"
            "`!quota` - Kiểm tra quota\n"
            "`!ping` - Test bot\n"
            "`!help_bot` - Xem hướng dẫn"
        ),
        inline=False
    )
    
    embed.add_field(
        name="🔗 Supported URL Types",
        value=(
            "Bot tự động tìm và download với URL mới nhất!\n\n"
            "✅ **Book page:** `https://z-library.xx/book/123456/abc123`\n"
            "✅ **Direct link:** `https://z-library.xx/dl/123456/abc123`\n\n"
            "💡 **Tip:** Copy bất kỳ link nào từ Z-Library đều được!"
        ),
        inline=False
    )
    
    embed.set_footer(text="Powered by Z-Library + Rclone")
    
    await interaction.response.send_message(embed=embed)


# ===== PREFIX COMMANDS (Backward Compatible) =====

@bot.command(name='download', help='Download sách từ Z-Library và upload lên Google Drive')
async def download_command(ctx, url: str = None):
    """
    Prefix command: !download <z-library-url>
    """
    if not url:
        await ctx.send(
            "❌ Vui lòng cung cấp URL Z-Library!\n"
            "**Ví dụ:**\n"
            "• `!download https://z-library.ec/book/12345/abcdef`\n"
            "• `!download https://z-library.ec/dl/12345/abcdef` (direct link)\n\n"
            "💡 **Tip:** Dùng slash command `/download` cho trải nghiệm tốt hơn!"
        )
        return
    
    await process_download_request(ctx, url, is_slash=False)


@bot.command(name='ping', help='Kiểm tra bot có hoạt động không')
async def ping_command(ctx):
    """Prefix command: !ping"""
    latency_ms = round(bot.latency * 1000)
    await ctx.send(
        f'🏓 Pong! Latency: {latency_ms}ms\n'
        f'💡 **Tip:** Dùng `/ping` cho trải nghiệm tốt hơn!'
    )


@bot.command(name='quota', help='Kiểm tra quota Z-Library còn lại')
async def quota_command(ctx):
    """Prefix command: !quota"""
    try:
        limits = downloader.zlibrary_service.get_download_limits()
        
        embed = discord.Embed(
            title="📊 Z-Library Download Quota",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Daily Limit", value=limits.get('daily_amount', 'N/A'), inline=True)
        embed.add_field(name="Remaining", value=limits.get('daily_remaining', 'N/A'), inline=True)
        embed.add_field(name="Next Reset", value=limits.get('daily_reset', 'N/A'), inline=False)
        
        embed.set_footer(text="💡 Tip: Dùng /quota cho trải nghiệm tốt hơn!")
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Không thể lấy thông tin quota: {str(e)}")


@bot.command(name='help_bot', help='Hiển thị hướng dẫn sử dụng')
async def help_bot_command(ctx):
    """Prefix command: !help_bot (redirects to /help)"""
    await ctx.send(
        "� **Bot đã chuyển sang dùng Slash Commands!**\n"
        "Gõ `/help` để xem hướng dẫn đầy đủ\n\n"
        "**Quick commands:**\n"
        "• `/download <url>` - Download sách\n"
        "• `/quota` - Check quota\n"
        "• `/ping` - Test bot\n"
        "• `/help` - Xem hướng dẫn chi tiết"
    )


# ===== MAIN =====

def main():
    """Khởi động Discord Bot"""
    
    if DISCORD_TOKEN == "YOUR_DISCORD_BOT_TOKEN":
        print("❌ Lỗi: Chưa cấu hình DISCORD_TOKEN")
        print("Vui lòng sửa DISCORD_TOKEN trong file discord_bot.py")
        return
    
    print("=" * 80)
    print("🤖 DISCORD BOT - Z-LIBRARY DOWNLOADER")
    print("=" * 80)
    print()
    print("✅ Đang khởi động bot...")
    print(f"📁 Download directory: {DOWNLOAD_DIR}")
    print(f"☁️  Rclone remote: {RCLONE_REMOTE}:{RCLONE_FOLDER}")
    print(f"🗑️  Auto delete: {AUTO_DELETE_AFTER_UPLOAD}")
    print()
    
    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        logger.error(f"Lỗi khi chạy bot: {e}")
        print(f"❌ Lỗi: {e}")


if __name__ == "__main__":
    main()
