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
DISCORD_TOKEN = "YOUR_DISCORD_BOT_TOKEN"  # Token Discord Bot
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
        
        Hỗ trợ các domain: .ec, .se, .is, .sk, ...
        Pattern: https://z-library.{domain}/book/{id}/{hash}
                 https://z-library.{domain}/dl/{id}/{hash}
        
        Supported URL formats:
        ✅ /book/1269938/e536b6
        ✅ /book/1269938/e536b6/filename.html
        ✅ /book/1269938/e536b6?ts=1651
        ✅ /book/1269938/e536b6?dsource=recommend
        ✅ /book/1269938/e536b6/title.html?utm_source=google&utm_campaign=xyz
        ✅ /book/1269938/e536b6#section
        ✅ /dl/1269938/b88232 (direct download)
        """
        # Remove ALL query params (?xxx) and fragments (#xxx)
        # This handles: ?ts=, ?dsource=, ?utm_source=, ?ref=, etc.
        clean_url = url.split('?')[0].split('#')[0]
        
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
            response = requests.get(book_page_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Method 1: Find by class "addDownloadedBook" (most reliable)
            download_link = soup.find('a', class_='addDownloadedBook')
            
            if not download_link:
                # Method 2: Find any <a> with href matching /dl/{id}/{hash}
                download_link = soup.find('a', href=re.compile(r'/dl/\d+/[a-z0-9]+', re.IGNORECASE))
            
            if download_link:
                href = download_link.get('href')
                logger.info(f"Found download link: {href}")
                
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
            
            # Lấy domain từ URL gốc
            domain = book_info.get('domain', 'z-library.ec')
            
            # Nếu là direct download link
            if book_info['type'] == 'direct_download':
                download_url = url
                title = f"Book_{book_info['id']}"
            else:
                # Nếu là book page, cần parse HTML để lấy hash thật
                logger.info(f"Book page detected, fetching real download hash...")
                real_hash = await self._get_download_hash_from_page(url)
                
                if real_hash:
                    # Dùng hash thật từ download button
                    download_url = f"https://{domain}/dl/{book_info['id']}/{real_hash}"
                    title = f"Book_{book_info['id']}"
                    logger.info(f"Using real download hash: {download_url}")
                else:
                    # Fallback: thử dùng hash từ URL (có thể không work)
                    download_url = f"https://{domain}/dl/{book_info['id']}/{book_info['hash']}"
                    title = f"Book_{book_info['id']}"
                    logger.warning(f"Could not get real hash, using URL hash (may fail): {download_url}")
            
            # Chuẩn bị book_info cho service
            book_data = {
                'zlibrary_id': book_info['id'],
                'title': title,
                'authors': 'Unknown',
                'download_url': download_url,
                'extension': 'pdf',  # Default, sẽ được update từ response
                'url': url
            }
            
            # Download file
            logger.info(f"Downloading từ: {download_url}")
            file_path = self.zlibrary_service.download_book(book_data, DOWNLOAD_DIR)
            
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

async def process_download_request(interaction_or_ctx, url: str, is_slash: bool = False):
    """
    Helper function xử lý download request
    Dùng chung cho cả slash command và prefix command
    
    Args:
        interaction_or_ctx: discord.Interaction (slash) hoặc commands.Context (prefix)
        url: Z-Library URL
        is_slash: True nếu là slash command, False nếu là prefix command
    """
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
        # Bước 1: Download
        if is_slash:
            await interaction_or_ctx.followup.send(f"📥 **[1/4]** Đang download sách từ Z-Library...\n⏳ Request từ {author.mention}")
        else:
            await status_msg.edit(content="📥 **[1/4]** Đang download sách từ Z-Library...")
        
        logger.info(f"User {author} yêu cầu download: {url}")
        
        download_result = await downloader.download_book(url)
        
        if not download_result['success']:
            error_msg = f"❌ **Download thất bại:**\n```{download_result['error']}```"
            if is_slash:
                await interaction_or_ctx.followup.send(error_msg)
            else:
                await status_msg.edit(content=error_msg)
            return
        
        file_path = download_result['file_path']
        file_name = download_result['file_name']
        file_size_mb = download_result['file_size'] / (1024 * 1024)
        
        # Bước 2: Upload lên Google Drive
        upload_msg = f"☁️ **[2/4]** Đang upload `{file_name}` ({file_size_mb:.2f} MB) lên Google Drive..."
        if is_slash:
            await interaction_or_ctx.followup.send(upload_msg)
        else:
            await status_msg.edit(content=upload_msg)
        
        upload_result = await uploader.upload_file(file_path)
        
        if not upload_result['success']:
            error_msg = f"❌ **Upload thất bại:**\n```{upload_result['error']}```"
            if is_slash:
                await interaction_or_ctx.followup.send(error_msg)
            else:
                await status_msg.edit(content=error_msg)
            return
        
        # Bước 3: Tạo message kết quả
        if is_slash:
            await interaction_or_ctx.followup.send("📋 **[3/4]** Đang tạo thông tin chia sẻ...")
        else:
            await status_msg.edit(content="📋 **[3/4]** Đang tạo thông tin chia sẻ...")
        
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
        
        if is_slash:
            await interaction_or_ctx.followup.send(embed=embed)
        else:
            await status_msg.edit(content=None, embed=embed)
        
        # Bước 4: Cleanup (xóa file local nếu được bật)
        if AUTO_DELETE_AFTER_UPLOAD:
            await asyncio.sleep(2)
            try:
                os.remove(file_path)
                logger.info(f"Đã xóa file local: {file_path}")
                cleanup_msg = f"🗑️ **[4/4]** Đã xóa file tạm trên VPS"
                if is_slash:
                    await interaction_or_ctx.followup.send(cleanup_msg)
                else:
                    await interaction_or_ctx.send(cleanup_msg)
            except Exception as e:
                logger.warning(f"Không thể xóa file: {e}")
        
        logger.info(f"Hoàn thành request cho user {author}: {file_name}")
        
    except Exception as e:
        logger.error(f"Lỗi khi xử lý command: {e}")
        error_msg = f"❌ **Lỗi không mong muốn:**\n```{str(e)}```"
        if is_slash:
            await interaction_or_ctx.followup.send(error_msg)
        else:
            await status_msg.edit(content=error_msg)


# ===== SLASH COMMANDS =====

@bot.tree.command(name="download", description="📥 Download sách từ Z-Library và upload lên Google Drive")
async def slash_download(interaction: discord.Interaction, url: str):
    """
    Slash command: /download <url>
    
    Parameters:
        url: URL của sách trên Z-Library (.ec, .se, .is, .sk)
    """
    await process_download_request(interaction, url, is_slash=True)


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
        name="🔗 Supported URLs",
        value=(
            "**Hỗ trợ domain:** .ec, .se, .is, .sk\n"
            "**Ví dụ:**\n"
            "• `https://z-library.ec/book/11948830/2c2f55`\n"
            "• `https://z-library.ec/dl/11948830/b88232` (direct)"
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
