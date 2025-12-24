import discord
from discord import app_commands
from discord.ext import commands
import os
import json
from datetime import datetime
from typing import Dict, List, Optional

class CurrencyJSON:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.currency_file = os.path.join(data_dir, "currency.json")
        self.transactions_file = os.path.join(data_dir, "transactions.json")
        
        # Tạo thư mục data nếu chưa tồn tại
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        
        # Khởi tạo file nếu chưa tồn tại
        if not os.path.exists(self.currency_file):
            self._save_currency_data({})
        
        if not os.path.exists(self.transactions_file):
            self._save_transactions_data([])
    
    def _load_currency_data(self) -> Dict:
        """Load dữ liệu currency từ file JSON"""
        try:
            with open(self.currency_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_currency_data(self, data: Dict):
        """Lưu dữ liệu currency vào file JSON"""
        with open(self.currency_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _load_transactions_data(self) -> List:
        """Load dữ liệu transactions từ file JSON"""
        try:
            with open(self.transactions_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _save_transactions_data(self, data: List):
        """Lưu dữ liệu transactions vào file JSON"""
        with open(self.transactions_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def get_user_balance(self, user_id: str) -> int:
        """Lấy số dư của user"""
        data = self._load_currency_data()
        user_data = data.get(user_id, {})
        return user_data.get("balance", 0)
    
    def update_user_balance(self, user_id: str, balance: int):
        """Cập nhật số dư của user"""
        data = self._load_currency_data()
        data[user_id] = {
            "user_id": user_id,
            "balance": balance,
            "last_updated": datetime.utcnow().isoformat()
        }
        self._save_currency_data(data)
    
    def transfer_money(self, from_user_id: str, to_user_id: str, amount: int):
        """Chuyển tiền giữa 2 users"""
        data = self._load_currency_data()
        
        # Kiểm tra số dư người gửi
        from_user_data = data.get(from_user_id, {})
        from_balance = from_user_data.get("balance", 0)
        
        if from_balance < amount:
            return False, "Không đủ tiền để chuyển"
        
        # Trừ tiền người gửi
        data[from_user_id] = {
            "user_id": from_user_id,
            "balance": from_balance - amount,
            "last_updated": datetime.utcnow().isoformat()
        }
        
        # Cộng tiền người nhận
        to_user_data = data.get(to_user_id, {})
        to_balance = to_user_data.get("balance", 0)
        data[to_user_id] = {
            "user_id": to_user_id,
            "balance": to_balance + amount,
            "last_updated": datetime.utcnow().isoformat()
        }
        
        # Lưu dữ liệu
        self._save_currency_data(data)
        
        # Log transaction
        self.log_transaction(from_user_id, to_user_id, amount, "transfer")
        
        return True, "Chuyển tiền thành công"
    
    def log_transaction(self, from_user_id: str, to_user_id: str, amount: int, transaction_type: str):
        """Log giao dịch"""
        transactions = self._load_transactions_data()
        transaction_data = {
            "from_user_id": from_user_id,
            "to_user_id": to_user_id,
            "amount": amount,
            "type": transaction_type,
            "timestamp": datetime.utcnow().isoformat()
        }
        transactions.append(transaction_data)
        self._save_transactions_data(transactions)
    
    def get_richest_users(self, limit: int = 10) -> List[Dict]:
        """Lấy top users giàu nhất"""
        data = self._load_currency_data()
        users_list = [
            {"user_id": user_id, "balance": user_data["balance"]}
            for user_id, user_data in data.items()
        ]
        users_list.sort(key=lambda x: x["balance"], reverse=True)
        return users_list[:limit]
    
    def get_all_users_with_money(self) -> List[Dict]:
        """Lấy tất cả users có tiền (để hiển thị bảng xếp hạng)"""
        data = self._load_currency_data()
        users_list = [
            {"user_id": user_id, "balance": user_data["balance"]}
            for user_id, user_data in data.items()
            if user_data.get("balance", 0) > 0
        ]
        users_list.sort(key=lambda x: x["balance"], reverse=True)
        return users_list
    
    def create_leaderboard_embed(self, guild):
        """Tạo embed cho bảng xếp hạng"""
        all_users = self.get_all_users_with_money()
        
        if not all_users:
            embed = discord.Embed(
                title="💰 Bảng xếp hạng tiền tệ",
                description="Chưa có ai có tiền trong server này.",
                color=discord.Color.gold()
            )
            embed.set_footer(text=f"Cập nhật lúc: {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}")
            return embed

        embed = discord.Embed(
            title="💰 Bảng xếp hạng tiền tệ",
            color=discord.Color.gold()
        )
        
        description_lines = []
        for i, user_data in enumerate(all_users[:20], start=1):  # Giới hạn 20 người
            user_id = user_data["user_id"]
            member = guild.get_member(int(user_id))
            
            if member:
                name = member.display_name
                # Truncate tên nếu quá dài
                if len(name) > 20:
                    name = name[:17] + "..."
            else:
                name = f"User-{user_id[-4:]}"  # Hiển thị 4 chữ số cuối của ID
            
            balance = user_data["balance"]
            
            # Thêm emoji cho top 3
            if i == 1:
                rank_emoji = "🥇"
            elif i == 2:
                rank_emoji = "🥈" 
            elif i == 3:
                rank_emoji = "🥉"
            else:
                rank_emoji = f"#{i:02d}"
            
            description_lines.append(f"{rank_emoji} {name}: **{balance:,} VNĐ**")
        
        embed.description = "\n".join(description_lines)
        embed.set_footer(text=f"Tổng {len(all_users)} người có tiền • Cập nhật: {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}")
        
        return embed
    
    def initialize_all_members(self, guild, initial_amount: int = 10000):
        """Khởi tạo tiền cho tất cả members hiện tại"""
        data = self._load_currency_data()
        initialized_count = 0
        
        for member in guild.members:
            if not member.bot:  # Không tính bot
                user_id = str(member.id)
                if user_id not in data or data[user_id].get("balance", 0) == 0:
                    data[user_id] = {
                        "user_id": user_id,
                        "balance": initial_amount,
                        "last_updated": datetime.utcnow().isoformat()
                    }
                    initialized_count += 1
        
        self._save_currency_data(data)
        return initialized_count
    
    def add_money_to_all_members(self, guild, amount: int):
        """Thêm tiền cho tất cả members (kể cả đã có tiền)"""
        data = self._load_currency_data()
        updated_count = 0
        
        for member in guild.members:
            if not member.bot:  # Không tính bot
                user_id = str(member.id)
                current_balance = data.get(user_id, {}).get("balance", 0)
                data[user_id] = {
                    "user_id": user_id,
                    "balance": current_balance + amount,
                    "last_updated": datetime.utcnow().isoformat()
                }
                updated_count += 1
        
        self._save_currency_data(data)
        return updated_count
    
    def get_user_transactions(self, user_id: str, limit: int = 5) -> List[Dict]:
        """Lấy lịch sử giao dịch của user"""
        transactions = self._load_transactions_data()
        user_transactions = [
            tx for tx in transactions
            if tx.get("from_user_id") == user_id or tx.get("to_user_id") == user_id
        ]
        # Sắp xếp theo thời gian mới nhất
        user_transactions.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return user_transactions[:limit]

class CurrencySystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = CurrencyJSON()
        self.initial_amount = 10000  # Số tiền khởi tạo
        self.leaderboard_channel_id = 1410120603167494214  # Channel ID để cập nhật bảng xếp hạng
        
        # Cấu hình role permissions (có thể thay đổi theo server)
        self.admin_roles = ["Admin", "Moderator", "Owner"]  # Roles có quyền admin
        self.vip_roles = ["VIP", "Premium", "Supporter"]   # Roles có quyền đặc biệt
    
    def has_admin_permission(self, member: discord.Member) -> bool:
        """Kiểm tra xem user có quyền admin không"""
        # Kiểm tra permission admin
        if member.guild_permissions.administrator:
            return True
        
        # Kiểm tra role admin
        user_roles = [role.name for role in member.roles]
        return any(role in self.admin_roles for role in user_roles)
    
    def has_vip_permission(self, member: discord.Member) -> bool:
        """Kiểm tra xem user có quyền VIP không"""
        user_roles = [role.name for role in member.roles]
        return any(role in self.vip_roles for role in user_roles)

    # Không cần cog_unload nữa vì JSON không cần đóng kết nối

    async def update_leaderboard_channel(self, guild):
        """Cập nhật bảng xếp hạng trong channel chỉ định"""
        try:
            channel = guild.get_channel(self.leaderboard_channel_id)
            if not channel:
                return
            
            # Tạo embed mới
            embed = self.db.create_leaderboard_embed(guild)
            
            # Tìm message cũ để edit hoặc gửi message mới
            async for message in channel.history(limit=10):
                if message.author == self.bot.user and message.embeds:
                    if message.embeds[0].title == "💰 Bảng xếp hạng tiền tệ":
                        await message.edit(embed=embed)
                        return
            
            # Nếu không tìm thấy message cũ, gửi message mới
            await channel.send(embed=embed)
            
        except Exception as e:
            print(f"Lỗi cập nhật leaderboard: {e}")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Tự động tặng tiền khi user join server"""
        if not member.bot:  # Không tính bot
            self.db.update_user_balance(str(member.id), self.initial_amount)
            try:
                embed = discord.Embed(
                    title="🎉 Chào mừng đến server!",
                    description=f"Bạn đã nhận được **{self.initial_amount:,} VNĐ** để bắt đầu!",
                    color=discord.Color.green()
                )
                embed.add_field(name="Server", value=member.guild.name, inline=True)
                embed.add_field(name="Số dư hiện tại", value=f"{self.initial_amount:,} VNĐ", inline=True)
                embed.set_footer(text="Sử dụng /balance để xem số dư")
                
                await member.send(embed=embed)
            except discord.Forbidden:
                pass  # Không thể gửi DM
            
            # Cập nhật bảng xếp hạng khi có user mới join
            await self.update_leaderboard_channel(member.guild)

    @app_commands.command(name="balance", description="Xem số dư hiện tại của bạn hoặc user khác")
    @app_commands.guilds(int(os.getenv("GUILD_ID")))
    @app_commands.describe(user="User muốn xem số dư (để trống để xem số dư của bản thân)")
    async def balance(self, interaction: discord.Interaction, user: discord.Member = None):
        """Hiển thị số dư của user"""
        target_user = user if user else interaction.user
        user_id = str(target_user.id)
        balance = self.db.get_user_balance(user_id)
        
        embed = discord.Embed(
            title=f"💰 Số dư của {target_user.display_name}",
            color=discord.Color.gold()
        )
        embed.add_field(name="Số dư hiện tại", value=f"{balance:,} VNĐ", inline=False)
        embed.set_thumbnail(url=target_user.display_avatar.url)
        embed.set_footer(text="Sử dụng /transfer để chuyển tiền cho người khác")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="transfer", description="Chuyển tiền cho user khác")
    @app_commands.guilds(int(os.getenv("GUILD_ID")))
    @app_commands.describe(
        recipient="User nhận tiền",
        amount="Số tiền muốn chuyển"
    )
    async def transfer(self, interaction: discord.Interaction, recipient: discord.Member, amount: int):
        """Chuyển tiền cho user khác"""
        sender_id = str(interaction.user.id)
        recipient_id = str(recipient.id)
        
        # Kiểm tra điều kiện
        if recipient.bot:
            await interaction.response.send_message("❌ Không thể chuyển tiền cho bot!", ephemeral=True)
            return
        
        if sender_id == recipient_id:
            await interaction.response.send_message("❌ Không thể chuyển tiền cho chính mình!", ephemeral=True)
            return
        
        if amount <= 0:
            await interaction.response.send_message("❌ Số tiền phải lớn hơn 0!", ephemeral=True)
            return
        
        if amount > 1000000:  # Giới hạn 1 triệu VNĐ mỗi lần chuyển
            await interaction.response.send_message("❌ Không thể chuyển quá 1,000,000 VNĐ mỗi lần!", ephemeral=True)
            return
        
        # Thực hiện chuyển tiền
        success, message = self.db.transfer_money(sender_id, recipient_id, amount)
        
        if success:
            # Lấy số dư mới
            sender_balance = self.db.get_user_balance(sender_id)
            recipient_balance = self.db.get_user_balance(recipient_id)
            
            embed = discord.Embed(
                title="✅ Chuyển tiền thành công!",
                color=discord.Color.green()
            )
            embed.add_field(name="Người gửi", value=interaction.user.mention, inline=True)
            embed.add_field(name="Người nhận", value=recipient.mention, inline=True)
            embed.add_field(name="Số tiền", value=f"{amount:,} VNĐ", inline=True)
            embed.add_field(name="Số dư còn lại", value=f"{sender_balance:,} VNĐ", inline=True)
            embed.add_field(name="Số dư người nhận", value=f"{recipient_balance:,} VNĐ", inline=True)
            embed.set_footer(text=f"Giao dịch lúc {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}")
            
            await interaction.response.send_message(embed=embed)
            
            # Cập nhật bảng xếp hạng trong channel
            await self.update_leaderboard_channel(interaction.guild)
            
            # Thông báo cho người nhận
            try:
                notify_embed = discord.Embed(
                    title="💰 Bạn đã nhận được tiền!",
                    description=f"{interaction.user.display_name} đã chuyển cho bạn **{amount:,} VNĐ**",
                    color=discord.Color.green()
                )
                notify_embed.add_field(name="Số dư mới", value=f"{recipient_balance:,} VNĐ", inline=True)
                notify_embed.add_field(name="Server", value=interaction.guild.name, inline=True)
                
                await recipient.send(embed=notify_embed)
            except discord.Forbidden:
                pass  # Không thể gửi DM
        else:
            embed = discord.Embed(
                title="❌ Chuyển tiền thất bại!",
                description=message,
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="richest", description="Xem bảng xếp hạng người giàu nhất")
    @app_commands.guilds(int(os.getenv("GUILD_ID")))
    async def richest(self, interaction: discord.Interaction):
        """Hiển thị bảng xếp hạng người giàu nhất"""
        richest_data = self.db.get_richest_users(10)
        
        if not richest_data:
            await interaction.response.send_message("Chưa có ai có tiền cả.", ephemeral=True)
            return

        embed = discord.Embed(
            title="💎 Bảng xếp hạng người giàu nhất",
            color=discord.Color.gold()
        )

        for i, user_data in enumerate(richest_data, start=1):
            user_id = user_data["user_id"]
            user = self.bot.get_user(int(user_id))
            name = user.name if user else f"Unknown User ({user_id})"
            
            balance = user_data["balance"]
            
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
                value=f"💰 {balance:,} VNĐ",
                inline=False
            )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="init_currency", description="[ADMIN] Khởi tạo tiền cho tất cả members hiện tại")
    @app_commands.guilds(int(os.getenv("GUILD_ID")))
    async def init_currency(self, interaction: discord.Interaction):
        """Khởi tạo tiền cho tất cả members hiện tại (chỉ admin)"""
        # Kiểm tra quyền admin
        if not self.has_admin_permission(interaction.user):
            await interaction.response.send_message("❌ Bạn không có quyền sử dụng lệnh này!", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        # Khởi tạo tiền cho tất cả members
        initialized_count = self.db.initialize_all_members(interaction.guild, self.initial_amount)
        
        embed = discord.Embed(
            title="✅ Khởi tạo tiền tệ thành công!",
            color=discord.Color.green()
        )
        embed.add_field(name="Số người được khởi tạo", value=f"{initialized_count} users", inline=True)
        embed.add_field(name="Số tiền mỗi người", value=f"{self.initial_amount:,} VNĐ", inline=True)
        embed.add_field(name="Tổng tiền phát ra", value=f"{initialized_count * self.initial_amount:,} VNĐ", inline=True)
        embed.set_footer(text="Chỉ khởi tạo cho users chưa có tiền")
        
        await interaction.followup.send(embed=embed)
        
        # Cập nhật bảng xếp hạng
        await self.update_leaderboard_channel(interaction.guild)

    @app_commands.command(name="add_money", description="[ADMIN] Thêm tiền cho user")
    @app_commands.guilds(int(os.getenv("GUILD_ID")))
    @app_commands.describe(
        user="User nhận tiền",
        amount="Số tiền muốn thêm"
    )
    async def add_money(self, interaction: discord.Interaction, user: discord.Member, amount: int):
        """Thêm tiền cho user (chỉ admin)"""
        # Kiểm tra quyền admin
        if not self.has_admin_permission(interaction.user):
            await interaction.response.send_message("❌ Bạn không có quyền sử dụng lệnh này!", ephemeral=True)
            return
        
        if amount <= 0:
            await interaction.response.send_message("❌ Số tiền phải lớn hơn 0!", ephemeral=True)
            return
        
        user_id = str(user.id)
        current_balance = self.db.get_user_balance(user_id)
        new_balance = current_balance + amount
        
        self.db.update_user_balance(user_id, new_balance)
        
        embed = discord.Embed(
            title="✅ Đã thêm tiền thành công!",
            color=discord.Color.green()
        )
        embed.add_field(name="User", value=user.mention, inline=True)
        embed.add_field(name="Số tiền thêm", value=f"+{amount:,} VNĐ", inline=True)
        embed.add_field(name="Số dư mới", value=f"{new_balance:,} VNĐ", inline=True)
        embed.set_footer(text=f"Admin: {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)
        
        # Cập nhật bảng xếp hạng trong channel
        await self.update_leaderboard_channel(interaction.guild)

    @app_commands.command(name="update_leaderboard", description="[ADMIN] Cập nhật bảng xếp hạng trong channel")
    @app_commands.guilds(int(os.getenv("GUILD_ID")))
    async def update_leaderboard(self, interaction: discord.Interaction):
        """Cập nhật bảng xếp hạng thủ công (chỉ admin)"""
        # Kiểm tra quyền admin
        if not self.has_admin_permission(interaction.user):
            await interaction.response.send_message("❌ Bạn không có quyền sử dụng lệnh này!", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        # Cập nhật bảng xếp hạng
        await self.update_leaderboard_channel(interaction.guild)
        
        embed = discord.Embed(
            title="✅ Đã cập nhật bảng xếp hạng!",
            description=f"Bảng xếp hạng đã được cập nhật trong <#{self.leaderboard_channel_id}>",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Admin: {interaction.user.display_name}")
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="add_money_all", description="[ADMIN] Thêm tiền cho tất cả members")
    @app_commands.guilds(int(os.getenv("GUILD_ID")))
    @app_commands.describe(amount="Số tiền muốn thêm cho mỗi người")
    async def add_money_all(self, interaction: discord.Interaction, amount: int):
        """Thêm tiền cho tất cả members (chỉ admin)"""
        # Kiểm tra quyền admin
        if not self.has_admin_permission(interaction.user):
            await interaction.response.send_message("❌ Bạn không có quyền sử dụng lệnh này!", ephemeral=True)
            return
        
        if amount <= 0:
            await interaction.response.send_message("❌ Số tiền phải lớn hơn 0!", ephemeral=True)
            return
        
        if amount > 100000:  # Giới hạn 100k VNĐ mỗi lần để tránh abuse
            await interaction.response.send_message("❌ Không thể thêm quá 100,000 VNĐ mỗi lần cho tất cả!", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        # Thêm tiền cho tất cả members
        updated_count = self.db.add_money_to_all_members(interaction.guild, amount)
        total_money = updated_count * amount
        
        embed = discord.Embed(
            title="✅ Đã thêm tiền cho tất cả thành công!",
            color=discord.Color.green()
        )
        embed.add_field(name="Số người nhận tiền", value=f"{updated_count} users", inline=True)
        embed.add_field(name="Số tiền mỗi người", value=f"+{amount:,} VNĐ", inline=True)
        embed.add_field(name="Tổng tiền phát ra", value=f"{total_money:,} VNĐ", inline=True)
        embed.add_field(name="Lý do", value="Phát tiền cho tất cả members", inline=False)
        embed.set_footer(text=f"Admin: {interaction.user.display_name}")
        
        await interaction.followup.send(embed=embed)
        
        # Cập nhật bảng xếp hạng
        await self.update_leaderboard_channel(interaction.guild)

    @app_commands.command(name="vip_balance", description="[VIP] Xem số dư với thông tin chi tiết")
    @app_commands.guilds(int(os.getenv("GUILD_ID")))
    @app_commands.describe(user="User muốn xem số dư (để trống để xem số dư của bản thân)")
    async def vip_balance(self, interaction: discord.Interaction, user: discord.Member = None):
        """Hiển thị số dư với thông tin chi tiết cho VIP"""
        # Kiểm tra quyền VIP hoặc Admin
        if not (self.has_vip_permission(interaction.user) or self.has_admin_permission(interaction.user)):
            await interaction.response.send_message("❌ Lệnh này chỉ dành cho VIP và Admin!", ephemeral=True)
            return
        
        target_user = user if user else interaction.user
        user_id = str(target_user.id)
        balance = self.db.get_user_balance(user_id)
        
        # Lấy thêm thông tin giao dịch
        transactions = self.db.get_user_transactions(user_id, limit=5)
        
        embed = discord.Embed(
            title=f"💎 Số dư VIP của {target_user.display_name}",
            color=discord.Color.purple()
        )
        embed.add_field(name="💰 Số dư hiện tại", value=f"{balance:,} VNĐ", inline=True)
        embed.add_field(name="📊 Xếp hạng", value="🔍 Đang tính...", inline=True)
        embed.add_field(name="🎯 Trạng thái", value="VIP Member", inline=True)
        
        # Hiển thị giao dịch gần đây
        if transactions:
            recent_transactions = []
            for tx in transactions[:3]:
                if tx["from_user_id"] == user_id:
                    recent_transactions.append(f"📤 -{tx['amount']:,} VNĐ")
                else:
                    recent_transactions.append(f"📥 +{tx['amount']:,} VNĐ")
            
            embed.add_field(
                name="📈 Giao dịch gần đây",
                value="\n".join(recent_transactions),
                inline=False
            )
        
        embed.set_thumbnail(url=target_user.display_avatar.url)
        embed.set_footer(text="✨ VIP Feature • Sử dụng /transfer để chuyển tiền")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="config_roles", description="[ADMIN] Cấu hình roles cho hệ thống")
    @app_commands.guilds(int(os.getenv("GUILD_ID")))
    @app_commands.describe(
        role_type="Loại role muốn cấu hình",
        action="Thêm hoặc xóa role",
        role_name="Tên role"
    )
    @app_commands.choices(
        role_type=[
            app_commands.Choice(name="Admin Roles", value="admin"),
            app_commands.Choice(name="VIP Roles", value="vip")
        ],
        action=[
            app_commands.Choice(name="Thêm", value="add"),
            app_commands.Choice(name="Xóa", value="remove"),
            app_commands.Choice(name="Xem danh sách", value="list")
        ]
    )
    async def config_roles(self, interaction: discord.Interaction, role_type: str, action: str, role_name: str = None):
        """Cấu hình roles cho hệ thống (chỉ admin)"""
        # Kiểm tra quyền admin
        if not self.has_admin_permission(interaction.user):
            await interaction.response.send_message("❌ Bạn không có quyền sử dụng lệnh này!", ephemeral=True)
            return
        
        role_list = self.admin_roles if role_type == "admin" else self.vip_roles
        role_name_display = "Admin" if role_type == "admin" else "VIP"
        
        embed = discord.Embed(
            title=f"⚙️ Cấu hình {role_name_display} Roles",
            color=discord.Color.blue()
        )
        
        if action == "list":
            if role_list:
                embed.add_field(
                    name=f"📋 Danh sách {role_name_display} Roles",
                    value="\n".join([f"• {role}" for role in role_list]),
                    inline=False
                )
            else:
                embed.add_field(
                    name=f"📋 Danh sách {role_name_display} Roles",
                    value="Chưa có role nào được cấu hình",
                    inline=False
                )
        
        elif action == "add":
            if not role_name:
                await interaction.response.send_message("❌ Vui lòng nhập tên role để thêm!", ephemeral=True)
                return
            
            if role_name not in role_list:
                role_list.append(role_name)
                embed.add_field(
                    name="✅ Thêm thành công",
                    value=f"Đã thêm role `{role_name}` vào danh sách {role_name_display}",
                    inline=False
                )
            else:
                embed.add_field(
                    name="⚠️ Role đã tồn tại",
                    value=f"Role `{role_name}` đã có trong danh sách {role_name_display}",
                    inline=False
                )
        
        elif action == "remove":
            if not role_name:
                await interaction.response.send_message("❌ Vui lòng nhập tên role để xóa!", ephemeral=True)
                return
            
            if role_name in role_list:
                role_list.remove(role_name)
                embed.add_field(
                    name="✅ Xóa thành công",
                    value=f"Đã xóa role `{role_name}` khỏi danh sách {role_name_display}",
                    inline=False
                )
            else:
                embed.add_field(
                    name="❌ Role không tồn tại",
                    value=f"Role `{role_name}` không có trong danh sách {role_name_display}",
                    inline=False
                )
        
        embed.set_footer(text=f"Admin: {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(CurrencySystem(bot))
