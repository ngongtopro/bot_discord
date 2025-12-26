import discord
from discord.ext import commands, tasks
import aiohttp
import os
import json
import logging
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Setup logging
logger = logging.getLogger('steam_deals')

# Load environment variables từ .env (chỉ dùng khi không có trong system env)
load_dotenv()

# Ưu tiên lấy từ system environment variables
STEAM_DEALS_CHANNEL_ID = int(os.environ.get('STEAM_DEALS_CHANNEL_ID') or os.getenv('STEAM_DEALS_CHANNEL_ID', '0'))
CHECK_INTERVAL_HOURS = int(os.environ.get('STEAM_DEALS_INTERVAL_HOURS') or os.getenv('STEAM_DEALS_INTERVAL_HOURS', '1'))
DEALS_DATA_FILE = "data/steam_deals_data.json"

class SteamDealsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.has_sent_restart_notification = False  # Flag để chỉ gửi 1 lần thông báo restart
        self.check_steam_deals.start()
    
    def load_deals_data(self):
        """Đọc dữ liệu deals từ file JSON"""
        try:
            if os.path.exists(DEALS_DATA_FILE):
                with open(DEALS_DATA_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data
        except Exception as e:
            logger.error(f"Lỗi đọc deals data: {e}")
        return {
            'last_check_date': None,
            'deals': {}
        }
    
    def save_deals_data(self, deals_list):
        """Lưu dữ liệu deals vào file JSON theo ngày"""
        try:
            os.makedirs("data", exist_ok=True)
            
            # Lấy ngày hiện tại
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Tạo dict deals với key là deal_id
            deals_dict = {str(deal['id']): deal for deal in deals_list}
            
            data = {
                'last_check_date': today,
                'deals': deals_dict
            }
            
            with open(DEALS_DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            logger.info(f"💾 Đã lưu {len(deals_dict)} deals cho ngày {today}")
        except Exception as e:
            logger.error(f"Lỗi lưu deals data: {e}")
    
    def get_new_deals(self, current_deals, old_deals_dict):
        """So sánh và lấy danh sách deals mới"""
        new_deals = []
        for deal in current_deals:
            deal_id = str(deal['id'])
            if deal_id not in old_deals_dict:
                new_deals.append(deal)
        return new_deals

    def cog_unload(self):
        self.check_steam_deals.cancel()

    @tasks.loop(hours=CHECK_INTERVAL_HOURS)
    async def check_steam_deals(self):
        logger.info("Bắt đầu kiểm tra deals...")
        
        channel = await self.bot.fetch_channel(STEAM_DEALS_CHANNEL_ID)
        if not channel:
            logger.error(f"Không tìm thấy channel ID: {STEAM_DEALS_CHANNEL_ID}")
            logger.error("   Hãy kiểm tra STEAM_DEALS_CHANNEL_ID trong file .env")
            return
        
        logger.info(f"Tìm thấy channel: {channel.name} ({channel.id})")
        
        # Load dữ liệu deals cũ
        deals_data = self.load_deals_data()
        last_check_date = deals_data.get('last_check_date')
        old_deals_dict = deals_data.get('deals', {})
        
        today = datetime.now().strftime('%Y-%m-%d')
        now = datetime.now()
        
        # Kiểm tra xem đã check hôm nay chưa
        if last_check_date == today:
            logger.info(f"✅ Đã check deals hôm nay ({today})")
            
            # Tính toán thời gian đến 1h sáng ngày mai
            tomorrow = now + timedelta(days=1)
            next_check_time = tomorrow.replace(hour=1, minute=0, second=0, microsecond=0)
            time_until_next = next_check_time - now
            hours_until_next = time_until_next.total_seconds() / 3600
            
            logger.info(f"⏭  Hẹn check lại lúc 1h sáng ngày mai ({hours_until_next:.1f} giờ nữa)")
            
            # Chỉ gửi thông báo restart 1 lần duy nhất khi bot khởi động
            if not self.has_sent_restart_notification:
                embed = discord.Embed(
                    title="🤖 Bot đã được restart",
                    description=f"Steam Deals checker đang hoạt động.\n\n"
                               f"📅 Đã check deals hôm nay: **{today}**\n"
                               f"🕐 Lần check tiếp theo: **1h sáng ngày mai** (~{hours_until_next:.0f}h nữa)\n"
                               f"📊 Số deals hiện tại: **{len(old_deals_dict)}** deals",
                    color=discord.Color.blue(),
                    timestamp=datetime.now()
                )
                embed.set_footer(text=f"Check mỗi {CHECK_INTERVAL_HOURS}h cho đến 1h sáng")
                
                try:
                    await channel.send(embed=embed)
                    self.has_sent_restart_notification = True
                    logger.info("Đã gửi thông báo restart")
                except Exception as e:
                    logger.error(f"Không thể gửi thông báo restart: {e}")
            
            return
        
        logger.info(f"📅 Ngày mới! Last check: {last_check_date or 'Chưa có'} -> Today: {today}")
        logger.info("🔍 Bắt đầu fetch deals từ Steam...")
        
        # Thực hiện fetch deals
        try:
            current_deals = await self.fetch_steam_deals()
            logger.info(f"Tìm thấy {len(current_deals)} deals từ Steam API")

            if not current_deals:
                logger.warning("⚠️  Không có deals nào được tìm thấy từ API")
                return
            
            # So sánh với deals cũ để tìm deals mới
            new_deals = self.get_new_deals(current_deals, old_deals_dict)
            logger.info(f"🆕 Tìm thấy {len(new_deals)} deals mới so với lần check trước")
            
            # Gửi thông báo deals mới
            if new_deals:
                for deal in new_deals:
                    try:
                        embed = discord.Embed(
                            title=f"🔥 Giảm giá: {deal['name']}",
                            url=deal['url'],
                            description=f"💰 Giá mới: **${deal['price']:.2f}**\n"
                                       f"~~Giá cũ: ${deal['old_price']:.2f}~~\n"
                                       f"📉 Giảm: **{deal['discount']}%**",
                            color=discord.Color.red(),
                            timestamp=datetime.now()
                        )
                        embed.set_thumbnail(url=deal['image'])
                        embed.set_footer(text=f"Steam Deal • {today}")
                        
                        await channel.send(embed=embed)
                        logger.info(f"📢 Đã gửi deal: {deal['name']} (-{deal['discount']}%)")
                        
                    except Exception as e:
                        logger.error(f"❌ Lỗi gửi tin nhắn cho deal {deal['name']}: {e}")
                
                logger.info(f"✅ Đã gửi {len(new_deals)} deals mới")
            else:
                logger.info("ℹ️  Không có deals mới để thông báo")
                
                # Gửi thông báo không có deals mới
                embed = discord.Embed(
                    title="📊 Steam Deals - Cập nhật hàng ngày",
                    description=f"Không có deals mới hôm nay.\n\n"
                               f"📅 Ngày check: **{today}**\n"
                               f"📦 Tổng số deals: **{len(current_deals)}** deals",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
                embed.set_footer(text="Steam Deal Checker")
                
                try:
                    await channel.send(embed=embed)
                except Exception as e:
                    logger.error(f"Không thể gửi thông báo: {e}")
            
            # Lưu deals hiện tại vào file
            self.save_deals_data(current_deals)
                
        except Exception as e:
            logger.error(f"❌ Lỗi khi kiểm tra deals: {e}")
            logger.exception(e)

    async def fetch_steam_deals(self):
        # Sử dụng API của Steam hoặc third-party (ví dụ: steamdb.info, isthereanydeal.com)
        # Ở đây demo với Steam Store search specials
        url = "https://store.steampowered.com/api/featuredcategories/?cc=us&l=en"
        deals = []
        
        logger.info(f"🌐 Đang gọi API Steam: {url}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, ssl=False) as resp:  # Tắt SSL verification nếu gặp lỗi certificate
                    logger.info(f"📡 HTTP Status: {resp.status}")
                    
                    if resp.status == 200:
                        try:
                            data = await resp.json()
                            logger.info("📋 Nhận được dữ liệu từ Steam API")
                            
                            # Kiểm tra xem data có đúng cấu trúc không
                            if not isinstance(data, dict):
                                logger.warning("⚠️  Dữ liệu không đúng định dạng (không phải dict)")
                                return deals
                            
                            specials = data.get('specials', {})
                            if not isinstance(specials, dict):
                                logger.warning("⚠️  'specials' không đúng định dạng")
                                return deals
                                
                            items = specials.get('items', [])
                            logger.info(f"🎯 Số lượng specials từ API: {len(items)}")
                            
                            for i, item in enumerate(items):
                                try:
                                    discount = item.get('discount_percent', 0)
                                    if discount > 0:
                                        deal = {
                                            'id': item['id'],
                                            'name': item['name'],
                                            'url': f"https://store.steampowered.com/app/{item['id']}/",
                                            'price': item.get('final_price', 0) / 100,
                                            'old_price': item.get('original_price', 0) / 100,
                                            'discount': discount,
                                            'image': item.get('small_capsule_image', '')
                                        }
                                        deals.append(deal)
                                        
                                        if i < 3:  # Log first 3 deals for debugging
                                            logger.debug(f"   Deal {i+1}: {deal['name']} (-{discount}%)")
                                except (KeyError, TypeError) as e:
                                    logger.warning(f"⚠️  Bỏ qua item không hợp lệ (index {i}): {e}")
                                    continue
                                    
                        except aiohttp.ContentTypeError as e:
                            logger.warning("⚠️  Lỗi parse JSON từ Steam API: Response không phải JSON")
                        except Exception as e:
                            logger.warning(f"⚠️  Lỗi xử lý dữ liệu từ Steam API: {e}")
                    else:
                        logger.error(f"❌ HTTP Error: {resp.status}")
                        
        except aiohttp.ClientConnectorCertificateError as e:
            logger.error("⚠️  Lỗi SSL Certificate - Không thể kết nối đến Steam (certificate verification failed)")
        except aiohttp.ClientConnectorError as e:
            logger.error("⚠️  Lỗi kết nối đến Steam API - Kiểm tra internet hoặc Steam có thể đang down")
        except aiohttp.ClientError as e:
            logger.error(f"⚠️  Lỗi client khi gọi Steam API: {type(e).__name__}")
        except Exception as e:
            logger.error(f"❌ Lỗi không xác định khi fetch Steam API: {type(e).__name__} - {e}")
            
        logger.info(f"✅ Tổng cộng {len(deals)} deals có discount")
        return deals

async def setup(bot):
    await bot.add_cog(SteamDealsCog(bot))

