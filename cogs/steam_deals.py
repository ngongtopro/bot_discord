import discord
from discord.ext import commands, tasks
import aiohttp
import os
from dotenv import load_dotenv
import datetime

# Load environment variables từ .env (chỉ dùng khi không có trong system env)
load_dotenv()

# Ưu tiên lấy từ system environment variables
STEAM_DEALS_CHANNEL_ID = int(os.environ.get('STEAM_DEALS_CHANNEL_ID') or os.getenv('STEAM_DEALS_CHANNEL_ID', '0'))
CHECK_INTERVAL_MINUTES = int(os.environ.get('STEAM_DEALS_INTERVAL') or os.getenv('STEAM_DEALS_INTERVAL', '30'))

class SteamDealsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_announced = set()
        self.check_steam_deals.start()

    def cog_unload(self):
        self.check_steam_deals.cancel()

    @tasks.loop(minutes=CHECK_INTERVAL_MINUTES)
    async def check_steam_deals(self):
        print(f"🔍 [Steam Deals] Bắt đầu kiểm tra deals...")
        
        channel = await self.bot.fetch_channel(STEAM_DEALS_CHANNEL_ID)
        if not channel:
            print(f"❌ [Steam Deals] Không tìm thấy channel ID: {STEAM_DEALS_CHANNEL_ID}")
            print(f"   Hãy kiểm tra STEAM_DEALS_CHANNEL_ID trong file .env")
            return
        
        print(f"✅ [Steam Deals] Tìm thấy channel: {channel.name} ({channel.id})")
        
        try:
            deals = await self.fetch_steam_deals()
            print(f"📊 [Steam Deals] Tìm thấy {len(deals)} deals")
            
            if not deals:
                print("⚠️  [Steam Deals] Không có deals nào được tìm thấy")
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
                            timestamp=datetime.datetime.utcnow()
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

