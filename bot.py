import discord
from discord import app_commands
from discord.ext import commands
import os
import asyncio
import aiohttp
import ast
import json
import shutil
from datetime import datetime
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)

class DiscordBot(commands.Bot):
    def __init__(self):
        # Bot intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        
        # Initialize bot
        super().__init__(
            command_prefix='!',
            intents=intents,
            application_id=int(os.getenv('APPLICATION_ID'))
        )
        
        self.guild_id = int(os.getenv('GUILD_ID'))
        self.owner_id = int(os.getenv('OWNER_ID'))
        self.admin_role_id = int(os.getenv('ADMIN_ROLE_ID'))
        self._commands_added = False
        
    async def setup_hook(self):
        """Called when the bot is starting up"""
        print(f'{self.user} đã đăng nhập!')
        
        # Load cogs
        await self.load_cogs()
        
        # Create and add slash commands manually to guild
        guild_obj = discord.Object(id=self.guild_id)
        
        hello_cmd = app_commands.Command(
            name="hello",
            description="Test slash command - chào hỏi",
            callback=self._hello_callback
        )
        
        botinfo_cmd = app_commands.Command(
            name="botinfo", 
            description="Thông tin về bot",
            callback=self._botinfo_callback
        )
        
        upload_cog_cmd = app_commands.Command(
            name="upload_cog",
            description="Upload file .py để tạo cog mới",
            callback=self._upload_cog_callback
        )
        
        check_pending_cmd = app_commands.Command(
            name="check_pending",
            description="[OWNER] Kiểm tra các cog đang chờ duyệt",
            callback=self._check_pending_callback
        )
        
        approve_cog_cmd = app_commands.Command(
            name="approve_cog", 
            description="[OWNER] Duyệt cog theo index",
            callback=self._approve_cog_callback
        )
        
        delete_pending_cmd = app_commands.Command(
            name="delete_pending",
            description="[ADMIN] Xóa file trong waiting_cogs theo index",
            callback=self._delete_pending_callback
        )
        
        # Add commands to guild tree specifically
        self.tree.add_command(hello_cmd, guild=guild_obj)
        self.tree.add_command(botinfo_cmd, guild=guild_obj)
        self.tree.add_command(upload_cog_cmd, guild=guild_obj)
        self.tree.add_command(check_pending_cmd, guild=guild_obj)
        self.tree.add_command(approve_cog_cmd, guild=guild_obj)
        self.tree.add_command(delete_pending_cmd, guild=guild_obj)
    
    async def load_cogs(self):
        """Load all cogs from cogs folder"""
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py') and not filename.startswith('__'):
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    print(f'✅ Đã load cog: {filename}')
                except Exception as e:
                    print(f'❌ Lỗi load cog {filename}: {e}')
    
    async def on_ready(self):
        """Called when bot is ready"""
        print(f'Bot {self.user} đã sẵn sàng!')
        print(f'Bot ID: {self.user.id}')
        print(f'Guild ID: {self.guild_id}')
        
        # Change bot status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="slash commands!"
            )
        )
        
        # Sync slash commands to guild for faster testing (chỉ sync một lần)
        if not self._commands_added:
            try:
                # Clear global commands trước (để tránh conflict)
                self.tree.clear_commands(guild=None)
                await self.tree.sync()  # Sync empty global commands
                print("Đã xóa global commands")
                
                # Debug: kiểm tra số lượng commands trong tree
                guild_obj = discord.Object(id=self.guild_id)
                all_commands = self.tree.get_commands(guild=guild_obj)
                global_commands = self.tree.get_commands()
                
                print(f"Debug: {len(all_commands)} commands trong guild tree")
                print(f"Debug: {len(global_commands)} commands trong global tree")
                
                # List commands trong tree
                for cmd in all_commands:
                    print(f"Guild command trong tree: {cmd.name}")
                for cmd in global_commands:
                    print(f"Global command trong tree: {cmd.name}")
                
                # Sync guild commands
                synced_guild = await self.tree.sync(guild=guild_obj)
                
                print(f"Đã sync {len(synced_guild)} guild commands tới guild {self.guild_id}")
                
                # List all guild commands
                for cmd in synced_guild:
                    print(f"  - /{cmd.name}: {cmd.description}")
                    
                self._commands_added = True
            except Exception as e:
                print(f"Lỗi khi sync guild commands: {e}")
    
    # Built-in slash command callbacks
    async def _hello_callback(self, interaction: discord.Interaction):
        """Built-in test slash command"""
        user = interaction.user
        embed = discord.Embed(
            title="👋 Xin chào!",
            description=f"Chào {user.mention}! Bot đang hoạt động tốt!",
            color=discord.Color.green()
        )
        embed.add_field(name="User ID", value=user.id, inline=True)
        embed.add_field(name="Guild", value=interaction.guild.name, inline=True)
        embed.set_footer(text="Test slash command")
        
        await interaction.response.send_message(embed=embed)
    
    async def _botinfo_callback(self, interaction: discord.Interaction):
        """Bot information slash command"""
        embed = discord.Embed(
            title="🤖 Thông tin Bot",
            color=discord.Color.blue()
        )
        embed.add_field(name="Bot Name", value=self.user.name, inline=True)
        embed.add_field(name="Bot ID", value=self.user.id, inline=True)
        embed.add_field(name="Guild Count", value=len(self.guilds), inline=True)
        embed.add_field(name="User Count", value=len(self.users), inline=True)
        embed.add_field(name="Discord.py Version", value=discord.__version__, inline=True)
        embed.set_thumbnail(url=self.user.display_avatar.url)
        
        await interaction.response.send_message(embed=embed)
    
    async def _upload_cog_callback(self, interaction: discord.Interaction, file: discord.Attachment):
        """Upload file .py để tạo cog mới"""
        
        # Defer response vì process có thể mất thời gian
        await interaction.response.defer()
        
        try:
            # Validate file type
            if not file.filename.endswith('.py'):
                await interaction.followup.send("❌ File phải có extension .py!")
                return
            
            # Check file size (max 1MB)
            if file.size > 1024 * 1024:
                await interaction.followup.send("❌ File quá lớn! Tối đa 1MB.")
                return
            
            # Download file content
            async with aiohttp.ClientSession() as session:
                async with session.get(file.url) as response:
                    if response.status != 200:
                        await interaction.followup.send("❌ Không thể download file!")
                        return
                    
                    file_content = await response.text()
            
            # Validate Python syntax
            try:
                ast.parse(file_content)
            except SyntaxError as e:
                await interaction.followup.send(f"❌ Lỗi syntax Python: {e}")
                return
            
            # Check if file contains required setup function
            if 'async def setup(bot):' not in file_content:
                await interaction.followup.send("❌ File phải chứa function `async def setup(bot):`!")
                return
            
            # Get filename without extension for cog name
            cog_name = file.filename[:-3]  # Remove .py
            
            # Check if user is owner
            if interaction.user.id == self.owner_id:
                # Owner: Load trực tiếp
                file_path = f"./cogs/{file.filename}"
                
                # Check if cog already exists
                cog_exists = os.path.exists(file_path)
                
                if cog_exists:
                    # Unload existing cog first
                    try:
                        await self.unload_extension(f'cogs.{cog_name}')
                        await interaction.followup.send(f"🔄 Đã unload cog cũ: {cog_name}")
                    except Exception as e:
                        await interaction.followup.send(f"⚠️ Lỗi unload cog cũ: {e}")
                    
                    # Remove old file
                    os.remove(file_path)
                    await interaction.followup.send(f"🗑️ Đã xóa file cũ: {file.filename}")
                
                # Save new file
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(file_content)
                
                # Try to load the new cog
                try:
                    await self.load_extension(f'cogs.{cog_name}')
                    
                    # Sync commands để update slash commands
                    guild = discord.Object(id=self.guild_id)
                    synced = await self.tree.sync(guild=guild)
                    
                    # Create success embed
                    embed = discord.Embed(
                        title="✅ [OWNER] Cog đã được load thành công!",
                        color=discord.Color.green()
                    )
                    embed.add_field(name="File", value=file.filename, inline=True)
                    embed.add_field(name="Cog Name", value=cog_name, inline=True)
                    embed.add_field(name="Status", value="Mới" if not cog_exists else "Cập nhật", inline=True)
                    embed.add_field(name="Commands Synced", value=len(synced), inline=True)
                    embed.add_field(name="File Size", value=f"{file.size} bytes", inline=True)
                    embed.set_footer(text=f"Owner: {interaction.user.display_name}")
                    
                    await interaction.followup.send(embed=embed)
                    
                    # List new commands if any
                    if len(synced) > 0:
                        cmd_list = "\n".join([f"• /{cmd.name}: {cmd.description}" for cmd in synced])
                        await interaction.followup.send(f"🎮 **Slash Commands mới:**\n```\n{cmd_list}\n```")
                    
                except Exception as e:
                    # If loading fails, remove the file
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    
                    error_embed = discord.Embed(
                        title="❌ Lỗi load cog!",
                        description=f"```python\n{str(e)}\n```",
                        color=discord.Color.red()
                    )
                    error_embed.add_field(name="File", value=file.filename, inline=True)
                    error_embed.add_field(name="Action", value="File đã được xóa", inline=True)
                    
                    await interaction.followup.send(embed=error_embed)
            
            else:
                # Regular user: Lưu vào waiting_cogs
                waiting_path = f"./waiting_cogs/{file.filename}"
                
                # Save file to waiting folder
                with open(waiting_path, 'w', encoding='utf-8') as f:
                    f.write(file_content)
                
                # Save metadata
                metadata = {
                    "filename": file.filename,
                    "cog_name": cog_name,
                    "uploader_id": interaction.user.id,
                    "uploader_name": interaction.user.display_name,
                    "upload_time": datetime.now().isoformat(),
                    "file_size": file.size,
                    "guild_id": interaction.guild.id,
                    "guild_name": interaction.guild.name
                }
                
                metadata_path = f"./waiting_cogs/{cog_name}.json"
                with open(metadata_path, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2)
                
                # Create pending embed
                embed = discord.Embed(
                    title="⏳ Cog đã được gửi để chờ duyệt!",
                    color=discord.Color.orange()
                )
                embed.add_field(name="File", value=file.filename, inline=True)
                embed.add_field(name="Cog Name", value=cog_name, inline=True)
                embed.add_field(name="Status", value="Chờ duyệt", inline=True)
                embed.add_field(name="File Size", value=f"{file.size} bytes", inline=True)
                embed.add_field(name="Uploader", value=interaction.user.display_name, inline=True)
                embed.set_footer(text="Owner sẽ xem xét và duyệt cog của bạn")
                
                await interaction.followup.send(embed=embed)
                
                # Notify owner (if owner is in the guild)
                try:
                    owner = self.get_user(self.owner_id)
                    if owner:
                        owner_embed = discord.Embed(
                            title="🔔 Cog mới chờ duyệt!",
                            color=discord.Color.blue()
                        )
                        owner_embed.add_field(name="File", value=file.filename, inline=True)
                        owner_embed.add_field(name="From", value=f"{interaction.user.display_name} ({interaction.user.id})", inline=True)
                        owner_embed.add_field(name="Guild", value=interaction.guild.name, inline=True)
                        owner_embed.set_footer(text="Sử dụng /check_pending để xem và /approve_cog để duyệt")
                        
                        await owner.send(embed=owner_embed)
                except:
                    pass  # If can't DM owner, that's okay
        
        except Exception as e:
            await interaction.followup.send(f"❌ Lỗi không xác định: {str(e)}")
    
    async def _check_pending_callback(self, interaction: discord.Interaction):
        """[OWNER] Kiểm tra các cog đang chờ duyệt"""
        
        # Check if user is owner
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("❌ Chỉ owner mới có thể sử dụng command này!", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        try:
            # Get all pending files
            waiting_files = []
            if os.path.exists('./waiting_cogs'):
                for filename in os.listdir('./waiting_cogs'):
                    if filename.endswith('.json'):
                        try:
                            with open(f'./waiting_cogs/{filename}', 'r', encoding='utf-8') as f:
                                metadata = json.load(f)
                                waiting_files.append(metadata)
                        except:
                            continue
            
            if not waiting_files:
                embed = discord.Embed(
                    title="📋 Không có cog nào chờ duyệt",
                    description="Tất cả cog đã được xử lý!",
                    color=discord.Color.green()
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Sort by upload time
            waiting_files.sort(key=lambda x: x.get('upload_time', ''))
            
            # Create embed with pending cogs
            embed = discord.Embed(
                title="📋 Cogs đang chờ duyệt",
                description=f"Có **{len(waiting_files)}** cog chờ duyệt:",
                color=discord.Color.orange()
            )
            
            for i, metadata in enumerate(waiting_files):
                upload_time = metadata.get('upload_time', 'Unknown')
                if upload_time != 'Unknown':
                    try:
                        dt = datetime.fromisoformat(upload_time)
                        upload_time = dt.strftime('%d/%m/%Y %H:%M')
                    except:
                        pass
                
                embed.add_field(
                    name=f"[{i}] {metadata.get('filename', 'Unknown')}",
                    value=f"**Uploader:** {metadata.get('uploader_name', 'Unknown')} (ID: {metadata.get('uploader_id', 'Unknown')})\n"
                          f"**Size:** {metadata.get('file_size', 0)} bytes\n"
                          f"**Time:** {upload_time}\n"
                          f"**Guild:** {metadata.get('guild_name', 'Unknown')}",
                    inline=False
                )
            
            embed.set_footer(text="Sử dụng /approve_cog <index> để duyệt cog")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Lỗi kiểm tra pending: {str(e)}")
    
    # Placeholder for approve_cog command
    @app_commands.describe(index="Số thứ tự của cog cần duyệt (bắt đầu từ 0)")
    async def _approve_cog_callback(self, interaction: discord.Interaction, index: int):
        """[OWNER] Duyệt cog theo index"""
        
        # Check if user is owner
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("❌ Chỉ owner mới có thể sử dụng command này!", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        try:
            # Get all pending files
            waiting_files = []
            metadata_files = []
            
            if os.path.exists('./waiting_cogs'):
                for filename in os.listdir('./waiting_cogs'):
                    if filename.endswith('.json'):
                        try:
                            with open(f'./waiting_cogs/{filename}', 'r', encoding='utf-8') as f:
                                metadata = json.load(f)
                                waiting_files.append(metadata)
                                metadata_files.append(filename)
                        except:
                            continue
            
            if not waiting_files:
                await interaction.followup.send("❌ Không có cog nào chờ duyệt!")
                return
            
            # Sort by upload time
            combined = list(zip(waiting_files, metadata_files))
            combined.sort(key=lambda x: x[0].get('upload_time', ''))
            waiting_files, metadata_files = zip(*combined)
            waiting_files = list(waiting_files)
            metadata_files = list(metadata_files)
            
            # Check index
            if index < 0 or index >= len(waiting_files):
                await interaction.followup.send(f"❌ Index không hợp lệ! Chọn từ 0 đến {len(waiting_files)-1}")
                return
            
            # Get selected cog
            selected_metadata = waiting_files[index]
            filename = selected_metadata.get('filename')
            cog_name = selected_metadata.get('cog_name')
            
            waiting_py_path = f"./waiting_cogs/{filename}"
            waiting_json_path = f"./waiting_cogs/{metadata_files[index]}"
            final_py_path = f"./cogs/{filename}"
            
            # Check if files exist
            if not os.path.exists(waiting_py_path):
                await interaction.followup.send(f"❌ File {filename} không tồn tại trong waiting_cogs!")
                return
            
            # Check if cog already exists in cogs folder
            cog_exists = os.path.exists(final_py_path)
            
            if cog_exists:
                # Unload existing cog first
                try:
                    await self.unload_extension(f'cogs.{cog_name}')
                    await interaction.followup.send(f"🔄 Đã unload cog cũ: {cog_name}")
                except Exception as e:
                    await interaction.followup.send(f"⚠️ Lỗi unload cog cũ: {e}")
                
                # Remove old file
                os.remove(final_py_path)
                await interaction.followup.send(f"🗑️ Đã xóa file cũ: {filename}")
            
            # Move file from waiting to cogs
            shutil.move(waiting_py_path, final_py_path)
            
            # Remove metadata file
            if os.path.exists(waiting_json_path):
                os.remove(waiting_json_path)
            
            # Try to load the new cog
            try:
                await self.load_extension(f'cogs.{cog_name}')
                
                # Sync commands để update slash commands
                guild = discord.Object(id=self.guild_id)
                synced = await self.tree.sync(guild=guild)
                
                # Create success embed
                embed = discord.Embed(
                    title="✅ Cog đã được duyệt và load thành công!",
                    color=discord.Color.green()
                )
                embed.add_field(name="File", value=filename, inline=True)
                embed.add_field(name="Cog Name", value=cog_name, inline=True)
                embed.add_field(name="Original Uploader", value=selected_metadata.get('uploader_name', 'Unknown'), inline=True)
                embed.add_field(name="Status", value="Mới" if not cog_exists else "Cập nhật", inline=True)
                embed.add_field(name="Commands Synced", value=len(synced), inline=True)
                embed.add_field(name="File Size", value=f"{selected_metadata.get('file_size', 0)} bytes", inline=True)
                embed.set_footer(text=f"Approved by {interaction.user.display_name}")
                
                await interaction.followup.send(embed=embed)
                
                # List new commands if any
                if len(synced) > 0:
                    cmd_list = "\n".join([f"• /{cmd.name}: {cmd.description}" for cmd in synced])
                    await interaction.followup.send(f"🎮 **Slash Commands mới:**\n```\n{cmd_list}\n```")
                
                # Notify original uploader if possible
                try:
                    uploader_id = selected_metadata.get('uploader_id')
                    if uploader_id:
                        uploader = self.get_user(uploader_id)
                        if uploader:
                            notify_embed = discord.Embed(
                                title="🎉 Cog của bạn đã được duyệt!",
                                color=discord.Color.green()
                            )
                            notify_embed.add_field(name="File", value=filename, inline=True)
                            notify_embed.add_field(name="Cog Name", value=cog_name, inline=True)
                            notify_embed.add_field(name="Status", value="Đã load thành công", inline=True)
                            notify_embed.set_footer(text="Cog của bạn đã được thêm vào bot!")
                            
                            await uploader.send(embed=notify_embed)
                except:
                    pass  # If can't notify, that's okay
                
            except Exception as e:
                # If loading fails, move file back to waiting and recreate metadata
                if os.path.exists(final_py_path):
                    shutil.move(final_py_path, waiting_py_path)
                    
                    # Recreate metadata
                    with open(waiting_json_path, 'w', encoding='utf-8') as f:
                        json.dump(selected_metadata, f, indent=2)
                
                error_embed = discord.Embed(
                    title="❌ Lỗi load cog sau khi duyệt!",
                    description=f"```python\n{str(e)}\n```",
                    color=discord.Color.red()
                )
                error_embed.add_field(name="File", value=filename, inline=True)
                error_embed.add_field(name="Action", value="File đã được chuyển lại waiting_cogs", inline=True)
                
                await interaction.followup.send(embed=error_embed)
        
        except Exception as e:
            await interaction.followup.send(f"❌ Lỗi approve cog: {str(e)}")
    
    @app_commands.describe(index="Số thứ tự của cog cần xóa (bắt đầu từ 0)")
    async def _delete_pending_callback(self, interaction: discord.Interaction, index: int):
        """[ADMIN] Xóa file trong waiting_cogs theo index"""
        
        # Check if user is owner or has admin role
        is_owner = interaction.user.id == self.owner_id
        has_admin_role = False
        
        if hasattr(interaction.user, 'roles'):
            has_admin_role = any(role.id == self.admin_role_id for role in interaction.user.roles)
        
        if not (is_owner or has_admin_role):
            await interaction.response.send_message("❌ Chỉ owner hoặc admin mới có thể sử dụng command này!", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        try:
            # Get all pending files
            waiting_files = []
            metadata_files = []
            
            if os.path.exists('./waiting_cogs'):
                for filename in os.listdir('./waiting_cogs'):
                    if filename.endswith('.json'):
                        try:
                            with open(f'./waiting_cogs/{filename}', 'r', encoding='utf-8') as f:
                                metadata = json.load(f)
                                waiting_files.append(metadata)
                                metadata_files.append(filename)
                        except:
                            continue
            
            if not waiting_files:
                await interaction.followup.send("❌ Không có cog nào chờ duyệt!")
                return
            
            # Sort by upload time
            combined = list(zip(waiting_files, metadata_files))
            combined.sort(key=lambda x: x[0].get('upload_time', ''))
            waiting_files, metadata_files = zip(*combined)
            waiting_files = list(waiting_files)
            metadata_files = list(metadata_files)
            
            # Check index
            if index < 0 or index >= len(waiting_files):
                await interaction.followup.send(f"❌ Index không hợp lệ! Chọn từ 0 đến {len(waiting_files)-1}")
                return
            
            # Get selected cog info
            selected_metadata = waiting_files[index]
            filename = selected_metadata.get('filename')
            cog_name = selected_metadata.get('cog_name')
            uploader_name = selected_metadata.get('uploader_name', 'Unknown')
            
            waiting_py_path = f"./waiting_cogs/{filename}"
            waiting_json_path = f"./waiting_cogs/{metadata_files[index]}"
            
            # Delete files
            files_deleted = []
            
            if os.path.exists(waiting_py_path):
                os.remove(waiting_py_path)
                files_deleted.append(f"{filename}")
            
            if os.path.exists(waiting_json_path):
                os.remove(waiting_json_path)
                files_deleted.append(f"{metadata_files[index]}")
            
            if not files_deleted:
                await interaction.followup.send(f"❌ Không tìm thấy file để xóa!")
                return
            
            # Create delete confirmation embed
            embed = discord.Embed(
                title="🗑️ Đã xóa cog khỏi waiting list",
                color=discord.Color.orange()
            )
            embed.add_field(name="File đã xóa", value=filename, inline=True)
            embed.add_field(name="Cog Name", value=cog_name, inline=True)
            embed.add_field(name="Original Uploader", value=uploader_name, inline=True)
            embed.add_field(name="Deleted by", value=interaction.user.display_name, inline=True)
            embed.add_field(name="Files removed", value=f"{len(files_deleted)} files", inline=True)
            embed.add_field(name="Reason", value="Rejected by admin", inline=True)
            embed.set_footer(text="Cog đã bị từ chối và xóa khỏi waiting list")
            
            await interaction.followup.send(embed=embed)
            
            # Try to notify original uploader
            try:
                uploader_id = selected_metadata.get('uploader_id')
                if uploader_id:
                    uploader = self.get_user(uploader_id)
                    if uploader:
                        notify_embed = discord.Embed(
                            title="❌ Cog của bạn đã bị từ chối",
                            color=discord.Color.red()
                        )
                        notify_embed.add_field(name="File", value=filename, inline=True)
                        notify_embed.add_field(name="Cog Name", value=cog_name, inline=True)
                        notify_embed.add_field(name="Status", value="Đã bị xóa khỏi waiting list", inline=True)
                        notify_embed.add_field(name="Reviewed by", value=interaction.user.display_name, inline=True)
                        notify_embed.set_footer(text="Bạn có thể upload lại sau khi sửa đổi cog")
                        
                        await uploader.send(embed=notify_embed)
            except:
                pass  # If can't notify, that's okay
                
        except Exception as e:
            await interaction.followup.send(f"❌ Lỗi xóa cog: {str(e)}")

async def main():
    """Main function to run the bot"""
    # Check environment variables
    token = os.getenv('TOKEN')
    if not token:
        print("❌ Không tìm thấy TOKEN trong file .env!")
        return
    
    application_id = os.getenv('APPLICATION_ID')
    if not application_id:
        print("❌ Không tìm thấy APPLICATION_ID trong file .env!")
        return
        
    guild_id = os.getenv('GUILD_ID')
    if not guild_id:
        print("❌ Không tìm thấy GUILD_ID trong file .env!")
        return
    
    # Create and run bot
    bot = DiscordBot()
    
    try:
        await bot.start(token)
    except KeyboardInterrupt:
        print("\n🛑 Bot đã được dừng bởi người dùng")
    except Exception as e:
        print(f"❌ Lỗi khi chạy bot: {e}")
    finally:
        await bot.close()

if __name__ == "__main__":
    # Run the bot
    asyncio.run(main())
