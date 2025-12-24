import discord
from discord.ext import commands, tasks
import aiohttp
import os
import json
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables từ .env (chỉ dùng khi không có trong system env)
load_dotenv()

# Ưu tiên lấy từ system environment variables
STEAM_DEALS_CHANNEL_ID = int(os.environ.get('STEAM_DEALS_CHANNEL_ID') or os.getenv('STEAM_DEALS_CHANNEL_ID', '0'))
CHECK_INTERVAL_MINUTES = int(os.environ.get('STEAM_DEALS_INTERVAL') or os.getenv('STEAM_DEALS_INTERVAL', '30'))
LAST_CHECK_FILE = "data/steam_last_check.json"

class SteamDealsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_announced = set()
        self.check_steam_deals.start()
    
    def load_last_check_time(self):
        """Đọc thời gian check cuối cùng từ file"""
        try:
            if os.path.exists(LAST_CHECK_FILE):
                with open(LAST_CHECK_FILE, 'r') as f:
                    data = json.load(f)
                    last_check_str = data.get('last_check')
                    if last_check_str:
                        return datetime.fromisoformat(last_check_str)
        except Exception as e:
            print(f"[Steam Deals] Lỗi đọc last check time: {e}")
        return None
    
    def save_last_check_time(self):
        """Lưu thời gian check hiện tại vào file"""
        try:
            os.makedirs("data", exist_ok=True)
            with open(LAST_CHECK_FILE, 'w') as f:
                json.dump({
                    'last_check': datetime.now().isoformat()
                }, f)
        except Exception as e:
            print(f"[Steam Deals] Lỗi lưu last check time: {e}")

    def cog_unload(self):
        self.check_steam_deals.cancel()

    @tasks.loop(minutes=CHECK_INTERVAL_MINUTES)
    async def check_steam_deals(self):
        print(f"[Steam Deals] Bắt đầu kiểm tra deals...")
        
        channel = await self.bot.fetch_channel(STEAM_DEALS_CHANNEL_ID)
        if not channel:
            print(f"[Steam Deals] Không tìm thấy channel ID: {STEAM_DEALS_CHANNEL_ID}")
            print(f"   Hãy kiểm tra STEAM_DEALS_CHANNEL_ID trong file .env")
            return
        
        print(f"[Steam Deals] Tìm thấy channel: {channel.name} ({channel.id})")
        
        # Kiểm tra thời gian check cuối cùng
        last_check = self.load_last_check_time()
        now = datetime.now()
        
        if last_check:
            time_since_last_check = now - last_check
            minutes_since_last_check = time_since_last_check.total_seconds() / 60
            
            print(f"[Steam Deals] Lần check cuối: {last_check.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"[Steam Deals] Đã qua: {minutes_since_last_check:.1f} phút")
            
            # Nếu chưa đủ thời gian interval, bỏ qua và gửi thông báo restart
            if minutes_since_last_check < CHECK_INTERVAL_MINUTES:
                remaining_minutes = CHECK_INTERVAL_MINUTES - minutes_since_last_check
                print(f"⏭[Steam Deals] Bỏ qua check (còn {remaining_minutes:.1f} phút nữa)")
                
                # Gửi thông báo bot restart
                embed = discord.Embed(
                    title="Bot đã được restart",
                    description=f"Steam Deals checker đang hoạt động.\nLần check tiếp theo: sau **{remaining_minutes:.0f} phút**",
                    color=discord.Color.blue(),
                    timestamp=datetime.now()
                )
                embed.set_footer(text=f"Interval: {CHECK_INTERVAL_MINUTES} phút")
                
                try:
                    await channel.send(embed=embed)
                    print(f"[Steam Deals] Đã gửi thông báo restart")
                except Exception as e:
                    print(f"[Steam Deals] Không thể gửi thông báo restart: {e}")
                return
        else:
            print(f"[Steam Deals] Chưa có lần check nào trước đó")

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
            
            # Lưu thời gian check
            self.save_last_check_time()
            print(f"💾 [Steam Deals] Đã lưu thời gian check: {now.strftime('%Y-%m-%d %H:%M:%S')}")
                
        except Exception as e:
            print(f"❌ [Steam Deals] Lỗi khi kiểm tra deals: {e}")
            import traceback
            traceback.print_exc()

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

