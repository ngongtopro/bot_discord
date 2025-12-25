import discord
from discord.ext import commands, tasks
import aiohttp
import os
import json
from dotenv import load_dotenv
from datetime import datetime, timedelta, time

# Load environment variables từ .env (chỉ dùng khi không có trong system env)
load_dotenv()

# Ưu tiên lấy từ system environment variables
STEAM_DEALS_CHANNEL_ID = int(os.environ.get('STEAM_DEALS_CHANNEL_ID') or os.getenv('STEAM_DEALS_CHANNEL_ID', '0'))
CHECK_TIME_HOUR = 7  # 7 giờ sáng
CHECK_TIME_MINUTE = 0  # 0 phút
LAST_CHECK_FILE = "data/steam_last_check.json"

class SteamDealsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_announced = set()
        self.is_first_run = True  # Đánh dấu lần chạy đầu tiên
        self.check_steam_deals.start()
    
    def load_last_check_date(self):
        """Đọc ngày check cuối cùng từ file (chỉ lấy ngày, không quan tâm giờ)"""
        try:
            if os.path.exists(LAST_CHECK_FILE):
                with open(LAST_CHECK_FILE, 'r') as f:
                    data = json.load(f)
                    last_check_date_str = data.get('last_check_date')
                    if last_check_date_str:
                        return last_check_date_str  # Trả về string dạng "YYYY-MM-DD"
        except Exception as e:
            print(f"[Steam Deals] Lỗi đọc last check date: {e}")
        return None
    
    def save_last_check_date(self):
        """Lưu ngày check hiện tại vào file (chỉ lưu ngày)"""
        try:
            os.makedirs("data", exist_ok=True)
            today = datetime.now().strftime('%Y-%m-%d')
            with open(LAST_CHECK_FILE, 'w') as f:
                json.dump({
                    'last_check_date': today
                }, f)
        except Exception as e:
            print(f"[Steam Deals] Lỗi lưu last check date: {e}")

    def cog_unload(self):
        self.check_steam_deals.cancel()

    @tasks.loop(time=time(hour=CHECK_TIME_HOUR, minute=CHECK_TIME_MINUTE))
    async def check_steam_deals(self):
        print(f"[Steam Deals] Bắt đầu kiểm tra deals lúc {datetime.now().strftime('%H:%M:%S')}...")
        
        channel = await self.bot.fetch_channel(STEAM_DEALS_CHANNEL_ID)
        if not channel:
            print(f"[Steam Deals] Không tìm thấy channel ID: {STEAM_DEALS_CHANNEL_ID}")
            print(f"   Hãy kiểm tra STEAM_DEALS_CHANNEL_ID trong file .env")
            return
        
        print(f"[Steam Deals] Tìm thấy channel: {channel.name} ({channel.id})")
        
        # Nếu không phải lần chạy đầu tiên, kiểm tra ngày check cuối cùng
        if not self.is_first_run:
            last_check_date = self.load_last_check_date()
            today = datetime.now().strftime('%Y-%m-%d')
            
            if last_check_date:
                print(f"[Steam Deals] Ngày check cuối: {last_check_date}")
                print(f"[Steam Deals] Ngày hôm nay: {today}")
                
                # Nếu đã check hôm nay rồi, bỏ qua
                if last_check_date == today:
                    print(f"⏭[Steam Deals] Đã check hôm nay rồi, bỏ qua")
                    return
            else:
                print(f"[Steam Deals] Chưa có lần check nào trước đó")
        else:
            print(f"[Steam Deals] Lần chạy đầu tiên sau khi restart - bỏ qua kiểm tra ngày")
            self.is_first_run = False  # Đánh dấu đã chạy lần đầu
        
        today = datetime.now().strftime('%Y-%m-%d')

        # Thực hiện fetch deals
        try:
            deals = await self.fetch_steam_deals()
            print(f"[Steam Deals] Tìm thấy {len(deals)} deals")

            if not deals:
                print(f"[Steam Deals] Không có deals nào được tìm thấy")
                return
            
            new_deals = 0
            for deal in deals:
                if deal['id'] not in self.last_announced:
                    try:
                        embed = discord.Embed(
                            title=f"🔥 Giảm giá: {deal['name']}",
                            url=deal['url'],
                            description=f"Giá mới: **${deal['price']:.2f}**\nGiá cũ: ~~${deal['old_price']:.2f}~~\nGiảm: **{deal['discount']}%**",
                            color=discord.Color.red(),
                            timestamp=datetime.now()
                        )
                        embed.set_thumbnail(url=deal['image'])
                        
                        await channel.send(embed=embed)
                        self.last_announced.add(deal['id'])
                        new_deals += 1
                        
                        print(f"📢 [Steam Deals] Đã gửi deal: {deal['name']} (-{deal['discount']}%)")
                        
                    except Exception as e:
                        print(f"❌ [Steam Deals] Lỗi gửi tin nhắn cho deal {deal['name']}: {e}")
                        
            if new_deals == 0:
                print("ℹ️  [Steam Deals] Không có deals mới để thông báo")
            else:
                print(f"✅ [Steam Deals] Đã gửi {new_deals} deals mới")
            
            # Lưu ngày check (chỉ lưu ngày, không lưu giờ)
            self.save_last_check_date()
            print(f"💾 [Steam Deals] Đã lưu ngày check: {today}")
                
        except Exception as e:
            print(f"❌ [Steam Deals] Lỗi khi kiểm tra deals: {e}")
            import traceback
            traceback.print_exc()
    
    @check_steam_deals.before_loop
    async def before_check_steam_deals(self):
        """Chờ bot sẵn sàng trước khi bắt đầu loop"""
        await self.bot.wait_until_ready()
        print(f"[Steam Deals] Bot đã sẵn sàng, bắt đầu check ngay lập tức...")
    

    async def fetch_steam_deals(self):
        # Sử dụng API của Steam hoặc third-party (ví dụ: steamdb.info, isthereanydeal.com)
        # Ở đây demo với Steam Store search specials
        url = "https://store.steampowered.com/api/featuredcategories/?cc=us&l=en"
        deals = []
        
        print(f"🌐 [Steam Deals] Đang gọi API Steam: {url}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, ssl=False) as resp:  # Tắt SSL verification nếu gặp lỗi certificate
                    print(f"📡 [Steam Deals] HTTP Status: {resp.status}")
                    
                    if resp.status == 200:
                        try:
                            data = await resp.json()
                            print(f"📋 [Steam Deals] Nhận được dữ liệu từ Steam API")
                            
                            # Kiểm tra xem data có đúng cấu trúc không
                            if not isinstance(data, dict):
                                print(f"⚠️  [Steam Deals] Dữ liệu không đúng định dạng (không phải dict)")
                                return deals
                            
                            specials = data.get('specials', {})
                            if not isinstance(specials, dict):
                                print(f"⚠️  [Steam Deals] 'specials' không đúng định dạng")
                                return deals
                                
                            items = specials.get('items', [])
                            print(f"🎯 [Steam Deals] Số lượng specials từ API: {len(items)}")
                            
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
                                            print(f"   Deal {i+1}: {deal['name']} (-{discount}%)")
                                except (KeyError, TypeError) as e:
                                    print(f"⚠️  [Steam Deals] Bỏ qua item không hợp lệ (index {i}): {e}")
                                    continue
                                    
                        except aiohttp.ContentTypeError as e:
                            print(f"⚠️  [Steam Deals] Lỗi parse JSON từ Steam API: Response không phải JSON")
                        except Exception as e:
                            print(f"⚠️  [Steam Deals] Lỗi xử lý dữ liệu từ Steam API: {e}")
                    else:
                        print(f"❌ [Steam Deals] HTTP Error: {resp.status}")
                        
        except aiohttp.ClientConnectorCertificateError as e:
            print(f"⚠️  [Steam Deals] Lỗi SSL Certificate - Không thể kết nối đến Steam (certificate verification failed)")
        except aiohttp.ClientConnectorError as e:
            print(f"⚠️  [Steam Deals] Lỗi kết nối đến Steam API - Kiểm tra internet hoặc Steam có thể đang down")
        except aiohttp.ClientError as e:
            print(f"⚠️  [Steam Deals] Lỗi client khi gọi Steam API: {type(e).__name__}")
        except Exception as e:
            print(f"❌ [Steam Deals] Lỗi không xác định khi fetch Steam API: {type(e).__name__} - {e}")
            
        print(f"✅ [Steam Deals] Tổng cộng {len(deals)} deals có discount")
        return deals

async def setup(bot):
    await bot.add_cog(SteamDealsCog(bot))

