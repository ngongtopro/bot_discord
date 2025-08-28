import discord
from discord import app_commands
from discord.ext import commands
import os
from dotenv import load_dotenv
from all_def.mongodb import get_user, add_user_data, get_user_collection, get_user_data
import time
import asyncio
import random
# Load environment variables
load_dotenv()

job = {
    "Bạn đã đi thông cống và kiếm được {money} $",
    "Bạn vô tình nhặt được {money} $",
    "Bạn đã trúng xổ số và nhận được {money} $",
    "Bạn đã giúp bà cụ qua đường và được thưởng {money} $",
    "Bạn đã nhặt được ví tiền và được trả ơn {money} $",
    "Bạn đã bán ve chai và kiếm được {money} $",
    "Bạn đã làm shipper và nhận được {money} $",
    "Bạn đã đi dọn nhà thuê và nhận được {money} $",
    "Bạn đã làm gia sư và được trả {money} $",
    "Bạn đã đi sửa xe và kiếm được {money} $",
    "Bạn đã đi bán hàng rong và kiếm được {money} $",
    "Bạn đã đi làm bảo vệ và nhận được {money} $",
    "Bạn đã đi làm phục vụ quán cà phê và nhận được {money} $",
    "Bạn đã đi làm thợ xây và nhận được {money} $",
    "Bạn đã đi làm vườn và nhận được {money} $",
    "Bạn đã đi bắt cá và bán được {money} $",
    "Bạn đã đi thu gom rác và nhận được {money} $",
    "Bạn đã đi phát tờ rơi và nhận được {money} $",
    "Bạn đã đi làm MC đám cưới và nhận được {money} $",
    "Bạn đã đi làm diễn viên quần chúng và nhận được {money} $",
    "Bạn đã đi trông trẻ và nhận được {money} $",
    "Bạn đã đi làm thợ cắt tóc và nhận được {money} $",
    "Bạn đã đi làm thợ sửa điện và nhận được {money} $",
    "Bạn đã đi làm thợ sơn và nhận được {money} $",
    "Bạn giả làm tượng sống ở công viên và được cho {money} $",
    "Bạn cosplay làm cây chuối, ai đó thương hại cho {money} $",
    "Bạn đi nhảy flashmob giữa chợ và được thưởng {money} $",
    "Bạn đi bán bánh mì bằng loa kéo, bán được {money} $",
    "Bạn đi thi ăn mì cay cấp độ 7, giải thưởng là {money} $",
    "Bạn đi bắt vịt chạy bộ, bắt được nhận {money} $",
    "Bạn đi làm người mẫu bàn tay cho quảng cáo, nhận {money} $",
    "Bạn đi thi hét to nhất phố, giải khuyến khích {money} $",
    "Bạn đi làm thợ... gãi lưng thuê, khách tip {money} $",
    "Bạn đi dọa ma trong nhà ma, bị khách cho {money} $ để đừng dọa nữa",
    "Bạn đi làm người giữ cửa tự động, được trả {money} $",
    "Bạn đi làm thợ... đếm sao trời, đếm xong được {money} $",
    "Bạn đã giả làm tượng sống ngoài công viên và được người ta bỏ {money} $ vào nón",
    "Bạn đã cosplay Pikachu nhảy múa ở đèn đỏ và kiếm được {money} $",
    "Bạn đã đi làm diễn viên đóng thế cho con gà trong quảng cáo mì tôm và nhận {money} $",
    "Bạn đã đi cõng heo cho hội thi kéo co và bất ngờ được thưởng {money} $",
    "Bạn đã đi đóng vai xác sống trong phim ma làng và nhận {money} $",
    "Bạn đã đi giữ dép cho đội bóng phong trào và được trả {money} $",
    "Bạn đã đi thi ăn hết 10 tô phở và thắng {money} $",
    "Bạn đã gãi lưng thuê cho hàng xóm và kiếm được {money} $",
    "Bạn đã đi làm người hô 'dô hò dô hò' cho thuyền và được trả {money} $",
    "Bạn đã giả làm khủng long chạy quanh phố và được tip {money} $",
    "Bạn đã giúp mèo qua đường và nó tặng bạn {money} $ (không hiểu sao mèo có tiền)",
    "Bạn đã đi hát karaoke dạo và được tặng {money} $",
    "Bạn đã đóng vai 'người ngã xuống đường' để test phản xạ tài xế và nhận {money} $",
    "Bạn đã đi dán râu giả cho tượng Hồ Ly và nhận {money} $",
    "Bạn đã giả tiếng vịt kêu ngoài chợ và được tip {money} $",
    "Bạn đã đi bắt muỗi thuê và được thưởng {money} $",
    "Bạn đã đi thử ghế massage 8 tiếng liên tục và được trả {money} $",
    "Bạn đã ngồi làm bù nhìn rơm trong ruộng lúa và được trả {money} $",
    "Bạn đã đi gào thét thay cho loa phường và được trả {money} $",
    "Bạn đã đóng vai zombie trong game thực tế ảo và nhận {money} $",
    "Bạn đã làm 'người gánh nước' cho team cosplay Naruto và được trả {money} $",
    "Bạn đã ngồi ôm cột điện giả làm bảo vệ và được trả {money} $",
    "Bạn đã giả tiếng chó sủa để giữ nhà và nhận {money} $",
    "Bạn đã đi đóng vai ma trong nhà ma hội chợ và kiếm {money} $",
    "Bạn đã làm 'người rung chuông' cho gà chọi và nhận {money} $",
    "Bạn đã cười thuê trong đám cưới và được trả {money} $",
    "Bạn đã làm 'người giữ chỗ xếp hàng' ngoài tiệm trà sữa và nhận {money} $",
    "Bạn đã thử mùi nước hoa trong siêu thị cho khách và kiếm {money} $",
    "Bạn đã được thuê ngồi xe tăng đồ chơi để quảng cáo và được {money} $",
    "Bạn đã đi rao 'ai mua hành tôi' và kiếm được {money} $",
    "Bạn đã giả giọng Siri cho quán net và được trả {money} $",
    "Bạn đã làm 'cái cây biết nhảy' trong MV và nhận {money} $",
    "Bạn đã làm khán giả thuê trong gameshow và được thưởng {money} $",
    "Bạn đã được thuê la hét trong phim kinh dị và kiếm {money} $",
    "Bạn đã đi múa bụng cho hội nghị và nhận {money} $",
    "Bạn đã giả làm ông già Noel giữa mùa hè và kiếm được {money} $",
    "Bạn đã đóng vai 'người té' trong clip quảng cáo bảo hiểm và nhận {money} $",
    "Bạn đã làm người cầm biển 'quán mở cửa' 12 tiếng và được {money} $",
    "Bạn đã giả làm robot đứng siêu thị và nhận {money} $",
    "Bạn đã thi ngủ 24h và được thưởng {money} $",
    "Bạn đã gõ mõ thuê cho chùa và nhận {money} $",
    "Bạn đã đi hù trẻ con trong đêm Trung thu và được trả {money} $",
    "Bạn đã gào tên khách ở bến xe như MC chuyên nghiệp và nhận {money} $",
    "Bạn đã giả làm 'ông địa' múa lân và kiếm {money} $",
    "Bạn đã đi canh vịt chạy đồng và được trả {money} $",
    "Bạn đã làm 'người thử độ cay' của quán ớt địa ngục và nhận {money} $",
    "Bạn đã giả làm loa thông báo ở siêu thị và nhận {money} $",
    "Bạn đã làm 'người giữ micro' cho ca sĩ và kiếm {money} $",
    "Bạn đã thi bơi trong hồ bột giặt và thắng {money} $",
    "Bạn đã giả làm tượng cá chép ngoài hồ và được trả {money} $",
    "Bạn đã hát ru cho... bò sữa ngủ và được thưởng {money} $",
}

class Economy(commands.Cog):
    async def work_cooldown_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.CommandOnCooldown):
            retry_after = int(error.retry_after)
            minutes, seconds = divmod(retry_after, 60)
            msg = f"⏳ Bạn phải chờ {minutes} phút {seconds} giây nữa mới được đi làm tiếp!"
            await interaction.response.send_message(msg, ephemeral=True)
        else:
            raise error
    
    def __init__(self, bot):
        self.bot = bot


    from discord.app_commands import checks
    @checks.cooldown(1, 3600, key=lambda i: i.user.id)
    @app_commands.command(name="work", description="Đi làm kiếm cơm")
    @app_commands.guilds(int(os.getenv('GUILD_ID')))  # Restrict to specific guild
    async def work(self, interaction: discord.Interaction):

        try:
            embed = discord.Embed(title="Thu nhập", description="Bạn đang đi tìm việc...", color=discord.Color.green())
            await interaction.response.send_message(embed=embed)
            # delay random from 1-5 second
            await asyncio.sleep(random.randint(1, 5))
            money = random.randint(1, 100)
            job_message = random.choice(list(job))
            # add money to user
            add_user_data(interaction.user.id,"money", money)
            embed = discord.Embed(title="Thu nhập", description=job_message.format(money=money), color=discord.Color.green())
            # hiện tổng tài sản
            embed.add_field(name="Tổng tài sản", value=f"{get_user_data(interaction.user.id, 'money')[1]} $", inline=True)
            await interaction.followup.send(embed=embed)
        except:
            # remove cooldown
            self.bot.get_command("work").reset_cooldown(interaction)
    # reply when cooldown
    async def work_cooldown_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.CommandOnCooldown):
            retry_after = int(error.retry_after)
            minutes, seconds = divmod(retry_after, 60)
            msg = f"⏳ Bạn phải chờ {minutes} phút {seconds} giây nữa mới được đi làm tiếp!"
            await interaction.response.send_message(msg, ephemeral=True)
        else:
            raise error

async def setup(bot):
    await bot.add_cog(Economy(bot))
