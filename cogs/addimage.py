import discord
from discord import app_commands
from discord.ext import commands
import os
import json
from dotenv import load_dotenv

# Load environment variables từ .env (chỉ dùng khi không có trong system env)
load_dotenv()

# Ưu tiên lấy từ system environment variables
GUILD_ID = int(os.environ.get('GUILD_ID') or os.getenv('GUILD_ID'))
OWNER_ID = int(os.environ.get('OWNER_ID') or os.getenv('OWNER_ID'))

class AddImage(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="add_all_images", description="Add all images from image folder as emojis and create JSON output")
    @app_commands.guilds(GUILD_ID)  # Restrict to specific guild
    async def add_all_images(self, interaction: discord.Interaction):
        # Check if user is owner or admin
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("❌ Chỉ owner mới được dùng lệnh này!", ephemeral=True)
            return
        
        # Defer the response since this might take time
        await interaction.response.defer()
        
        # Path to image folder
        image_folder = './image'
        
        if not os.path.exists(image_folder):
            await interaction.followup.send("❌ Thư mục 'image' không tồn tại!")
            return
        
        # Get all image files
        image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.webp')
        image_files = [f for f in os.listdir(image_folder) if f.lower().endswith(image_extensions)]
        
        if not image_files:
            await interaction.followup.send("❌ Không tìm thấy file ảnh nào trong thư mục 'image'!")
            return
        
        # Prepare JSON data
        emoji_data = []
        
        # Add emojis
        added_count = 0
        failed_count = 0
        
        for image_file in image_files:
            try:
                # Create emoji name from filename (lowercase, remove extension, replace spaces with underscores)
                emoji_name = os.path.splitext(image_file)[0].lower().replace(' ', '_').replace('-', '_')
                
                # Ensure emoji name is valid (alphanumeric + underscores, max 32 chars)
                emoji_name = ''.join(c for c in emoji_name if c.isalnum() or c == '_')[:32]
                
                # Skip if name is empty or starts with number
                if not emoji_name or emoji_name[0].isdigit():
                    emoji_name = f"emoji_{added_count}"
                
                # Full path to image
                image_path = os.path.join(image_folder, image_file)
                
                # Create emoji (for bot application)
                with open(image_path, 'rb') as image:
                    emoji = await self.bot.create_application_emoji(
                        name=emoji_name,
                        image=image.read()
                    )
                
                # Add to JSON data
                emoji_data.append({
                    "filename": image_file,
                    "emoji_name": emoji_name,
                    "emoji_id": str(emoji.id),
                    "emoji_mention": f"<:{emoji_name}:{emoji.id}>"
                })
                
                added_count += 1
                
            except Exception as e:
                failed_count += 1
                print(f"❌ Lỗi khi thêm emoji {image_file}: {e}")
        
        # Create JSON output
        json_output = {
            "total_images": len(image_files),
            "added_emojis": added_count,
            "failed_emojis": failed_count,
            "emojis": emoji_data
        }
        
        # Save JSON to file
        json_filename = "emoji_data.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(json_output, f, indent=2, ensure_ascii=False)
        
        # Send summary
        summary = f"✅ Đã thêm {added_count} emoji thành công!\n"
        if failed_count > 0:
            summary += f"❌ {failed_count} emoji thất bại.\n"
        summary += f"📄 File JSON đã được tạo: {json_filename}"
        
        # Send the JSON file
        try:
            await interaction.followup.send(
                content=summary,
                file=discord.File(json_filename)
            )
        except Exception as e:
            # If file sending fails, send JSON as text
            json_text = json.dumps(json_output, indent=2, ensure_ascii=False)
            if len(json_text) > 2000:
                json_text = json_text[:1997] + "..."
            
            await interaction.followup.send(
                content=f"{summary}\n\n```json\n{json_text}\n```"
            )

async def setup(bot):
    await bot.add_cog(AddImage(bot))
