import discord
from discord import app_commands
from discord.ext import commands
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from datetime import datetime

# Load environment variables
load_dotenv()

# MongoDB Configuration
MONGODB_URL = os.getenv('MONGODB_URL', 'mongodb://localhost:27017/')
MONGODB_DB = os.getenv('MONGODB_DB', 'discord_bot')

class MongoDB:
    def __init__(self):
        self.client = MongoClient(MONGODB_URL)
        self.db = self.client[MONGODB_DB]
        self.levels_collection = self.db['levels']
    
    def get_user_level(self, user_id: str):
        """Lấy thông tin level của user"""
        user_data = self.levels_collection.find_one({"user_id": user_id})
        if not user_data:
            return {"xp": 0, "level": 1}
        return {"xp": user_data.get("xp", 0), "level": user_data.get("level", 1)}
    
    def update_user_level(self, user_id: str, xp: int, level: int):
        """Cập nhật level của user"""
        self.levels_collection.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "user_id": user_id,
                    "xp": xp,
                    "level": level,
                    "last_updated": datetime.utcnow()
                }
            },
            upsert=True
        )
    
    def get_leaderboard(self, limit: int = 10):
        """Lấy bảng xếp hạng"""
        return list(self.levels_collection.find().sort([("level", -1), ("xp", -1)]).limit(limit))
    
    def close(self):
        """Đóng kết nối MongoDB"""
        self.client.close()

# Danh sách role tu tiên
ROLE_REWARDS = {
    1: "👶 Phàm Nhân",
    5: "🔥 Luyện Khí",
    10: "🌱 Trúc Cơ",
    20: "💎 Kim Đan",
    30: "🌸 Nguyên Anh",
    40: "⚡ Hóa Thần",
    50: "🌌 Luyện Hư",
    60: "🐉 Hợp Thể",
    70: "🔮 Đại Thừa",
    80: "🕊️ Độ Kiếp",
    90: "🏯 Chân Tiên",
    100: "👑 Tiên Đế"
}

class LevelSystemMongo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = MongoDB()

    def cog_unload(self):
        """Đóng kết nối MongoDB khi unload cog"""
        self.db.close()

    def get_level_xp(self, level: int):
        """Tính XP cần để lên level tiếp theo"""
        return 100 * level

    def make_progress_bar(self, current: int, total: int, length: int = 20):
        """Tạo thanh progress bar"""
        filled = int(length * current // total)
        bar = "█" * filled + "─" * (length - filled)
        return f"[{bar}] {current}/{total} XP"

    async def assign_role(self, member: discord.Member, level: int):
        """Gán role tu tiên khi đạt cấp"""
        if level in ROLE_REWARDS:
            role_name = ROLE_REWARDS[level]
            role = discord.utils.get(member.guild.roles, name=role_name)
            if role:
                try:
                    await member.add_roles(role)
                    await member.send(f"🎉 Chúc mừng! Bạn đã đạt **Level {level}** và nhận role mới: **{role_name}**")
                except discord.Forbidden:
                    print(f"Không thể gán role {role_name} cho {member.name}")
                except Exception as e:
                    print(f"Lỗi khi gán role: {e}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Lắng nghe tin nhắn để tăng XP"""
        if message.author.bot:
            return

        user_id = str(message.author.id)
        
        # Lấy thông tin level hiện tại
        user_data = self.db.get_user_level(user_id)
        current_xp = user_data["xp"]
        current_level = user_data["level"]

        # Tăng XP
        new_xp = current_xp + 10
        xp_needed = self.get_level_xp(current_level)

        # Kiểm tra có lên level không
        if new_xp >= xp_needed:
            new_level = current_level + 1
            new_xp = 0  # Reset XP về 0 khi lên level

            # Cập nhật vào database
            self.db.update_user_level(user_id, new_xp, new_level)

            # Thông báo lên level
            await message.channel.send(
                f"🎉 {message.author.mention} đã lên cấp **{new_level}**!"
            )

            # Gán role tu tiên nếu có
            await self.assign_role(message.author, new_level)
        else:
            # Chỉ cập nhật XP
            self.db.update_user_level(user_id, new_xp, current_level)

    @app_commands.command(name="level", description="Xem cấp độ hiện tại của bạn")
    @app_commands.guilds(int(os.getenv("GUILD_ID")))
    async def level(self, interaction: discord.Interaction):
        """Hiển thị level của user"""
        user_id = str(interaction.user.id)
        user_data = self.db.get_user_level(user_id)
        
        level = user_data["level"]
        xp = user_data["xp"]
        xp_needed = self.get_level_xp(level)

        progress_bar = self.make_progress_bar(xp, xp_needed)

        embed = discord.Embed(
            title=f"📊 Level của {interaction.user.name}",
            color=discord.Color.blue()
        )
        embed.add_field(name="Level", value=str(level), inline=True)
        embed.add_field(name="XP", value=f"{xp}/{xp_needed}", inline=True)
        embed.add_field(name="Progress", value=progress_bar, inline=False)
        
        # Thêm thông tin role tiếp theo
        next_role_level = None
        for role_level in sorted(ROLE_REWARDS.keys()):
            if role_level > level:
                next_role_level = role_level
                break
        
        if next_role_level:
            embed.add_field(
                name="Role tiếp theo", 
                value=f"Level {next_role_level}: {ROLE_REWARDS[next_role_level]}", 
                inline=False
            )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leaderboard", description="Xem bảng xếp hạng level trong server")
    @app_commands.guilds(int(os.getenv("GUILD_ID")))
    async def leaderboard(self, interaction: discord.Interaction):
        """Hiển thị bảng xếp hạng level"""
        leaderboard_data = self.db.get_leaderboard(10)
        
        if not leaderboard_data:
            await interaction.response.send_message("Chưa có ai có level cả.", ephemeral=True)
            return

        embed = discord.Embed(
            title="🏆 Bảng xếp hạng Level",
            color=discord.Color.gold()
        )

        for i, user_data in enumerate(leaderboard_data, start=1):
            user_id = user_data["user_id"]
            member = interaction.guild.get_member(int(user_id))
            
            if member:
                name = member.display_name
            else:
                # Fallback: thử lấy từ bot cache
                user = self.bot.get_user(int(user_id))
                name = user.name if user else f"User-{user_id[-4:]}"
            
            level = user_data["level"]
            xp = user_data["xp"]
            
            # Tìm role tu tiên tương ứng với level
            current_role = "👶 Phàm Nhân"  # Default role
            for role_level in sorted(ROLE_REWARDS.keys(), reverse=True):
                if level >= role_level:
                    current_role = ROLE_REWARDS[role_level]
                    break
            
            # Thêm emoji cho top 3
            if i == 1:
                rank_emoji = "🥇"
            elif i == 2:
                rank_emoji = "🥈"
            elif i == 3:
                rank_emoji = "🥉"
            else:
                rank_emoji = f"#{i}"
            
            embed.add_field(
                name=f"{rank_emoji} {name}",
                value=f"Level: {level} | XP: {xp}\n{current_role}",
                inline=False
            )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="reset_level", description="[ADMIN] Reset level của một user")
    @app_commands.guilds(int(os.getenv("GUILD_ID")))
    @app_commands.describe(user="User cần reset level")
    async def reset_level(self, interaction: discord.Interaction, user: discord.Member):
        """Reset level của user (chỉ admin)"""
        # Kiểm tra quyền admin
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Bạn không có quyền sử dụng lệnh này!", ephemeral=True)
            return
        
        user_id = str(user.id)
        
        # Reset level về 1, XP về 0
        self.db.update_user_level(user_id, 0, 1)
        
        embed = discord.Embed(
            title="✅ Đã reset level",
            description=f"Level của {user.mention} đã được reset về Level 1",
            color=discord.Color.green()
        )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(LevelSystemMongo(bot))