import discord

from discord import app_commands

from discord.ext import commands

import os

from dotenv import load_dotenv

import json



# Load environment variables

load_dotenv()



LEVEL_FILE = os.path.join(os.path.dirname(__file__), "levels.json")



def load_levels():

    if not os.path.exists(LEVEL_FILE):

        # tạo file rỗng mặc định

        with open(LEVEL_FILE, "w", encoding="utf-8") as f:

            json.dump({}, f, indent=4)

        return {}

    with open(LEVEL_FILE, "r", encoding="utf-8") as f:

        return json.load(f)



def save_levels(data):

    with open(LEVEL_FILE, "w", encoding="utf-8") as f:

        json.dump(data, f, indent=4)



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



class LevelSystem(commands.Cog):

    def __init__(self, bot):

        self.bot = bot

        self.levels = load_levels()



    def get_level_xp(self, level: int):

        return 100 * level



    def make_progress_bar(self, current: int, total: int, length: int = 20):

        filled = int(length * current // total)

        bar = "█" * filled + "─" * (length - filled)

        return f"[{bar}] {current}/{total} XP"



    async def assign_role(self, member: discord.Member, level: int):

        """Gán role tu tiên khi đạt cấp"""

        if level in ROLE_REWARDS:

            role_name = ROLE_REWARDS[level]

            role = discord.utils.get(member.guild.roles, name=role_name)

            if role:

                await member.add_roles(role)

                await member.send(f"🎉 Chúc mừng! Bạn đã đạt **Level {level}** và nhận role mới: **{role_name}**")



    @commands.Cog.listener()

    async def on_message(self, message: discord.Message):

        if message.author.bot:

            return



        user_id = str(message.author.id)



        if user_id not in self.levels:

            self.levels[user_id] = {"xp": 0, "level": 1}



        self.levels[user_id]["xp"] += 10

        xp = self.levels[user_id]["xp"]

        level = self.levels[user_id]["level"]



        if xp >= self.get_level_xp(level):

            self.levels[user_id]["level"] += 1

            self.levels[user_id]["xp"] = 0

            new_level = self.levels[user_id]["level"]



            await message.channel.send(

                f"🎉 {message.author.mention} đã lên cấp **{new_level}**!"

            )



            # Gán role tu tiên nếu có

            await self.assign_role(message.author, new_level)



        save_levels(self.levels)



    @app_commands.command(name="level", description="Xem cấp độ hiện tại của bạn")

    @app_commands.guilds(int(os.getenv("GUILD_ID")))

    async def level(self, interaction: discord.Interaction):

        user_id = str(interaction.user.id)

        if user_id not in self.levels:

            await interaction.response.send_message("Bạn chưa có level nào cả.", ephemeral=True)

            return



        level = self.levels[user_id]["level"]

        xp = self.levels[user_id]["xp"]

        xp_needed = self.get_level_xp(level)



        progress_bar = self.make_progress_bar(xp, xp_needed)



        embed = discord.Embed(

            title=f"📊 Level của {interaction.user.name}",

            color=discord.Color.blue()

        )

        embed.add_field(name="Level", value=str(level), inline=True)

        embed.add_field(name="XP", value=f"{xp}/{xp_needed}", inline=True)

        embed.add_field(name="Progress", value=progress_bar, inline=False)



        await interaction.response.send_message(embed=embed)



    @app_commands.command(name="leaderboard", description="Xem bảng xếp hạng level trong server")

    @app_commands.guilds(int(os.getenv("GUILD_ID")))

    async def leaderboard(self, interaction: discord.Interaction):

        if not self.levels:

            await interaction.response.send_message("Chưa có ai có level cả.", ephemeral=True)

            return



        sorted_users = sorted(

            self.levels.items(),

            key=lambda x: (x[1]["level"], x[1]["xp"]),

            reverse=True

        )



        embed = discord.Embed(

            title="🏆 Bảng xếp hạng Level",

            color=discord.Color.gold()

        )



        for i, (user_id, data) in enumerate(sorted_users[:10], start=1):

            user = self.bot.get_user(int(user_id))

            name = user.name if user else f"Unknown User ({user_id})"

            embed.add_field(

                name=f"#{i} {name}",

                value=f"Level: {data['level']} | XP: {data['xp']}",

                inline=False

            )



        await interaction.response.send_message(embed=embed)



async def setup(bot):

    await bot.add_cog(LevelSystem(bot))

