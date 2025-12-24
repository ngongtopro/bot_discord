import discord
from discord import app_commands
from discord.ext import commands
import os
import json
import aiohttp
from datetime import datetime
from dotenv import load_dotenv
from utils.clone_or_pull import clone_or_pull_repo

# Load environment variables
load_dotenv()

WEBHOOK_URL = "https://discord.com/api/webhooks/1453237521583706195/gPrq4zU3OLe61qVVGNka2-ck2aI48aLo0X15PSJgDWInh8NYNBDddrUFJAkgXyuy4rpr"
REPOS_FILE = "data/github_repos.json"
PROJECTS_DIR = "projects"


class GitHubManager(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        self.ensure_data_file()
        self.ensure_projects_dir()

    def ensure_projects_dir(self):
        """Đảm bảo thư mục projects tồn tại"""
        os.makedirs(PROJECTS_DIR, exist_ok=True)

    def ensure_data_file(self):
        """Đảm bảo file JSON tồn tại"""
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(REPOS_FILE):
            with open(REPOS_FILE, 'w', encoding='utf-8') as f:
                json.dump([], f)

    def load_repos(self):
        """Đọc danh sách repos từ file JSON"""
        try:
            with open(REPOS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []

    def save_repos(self, repos):
        """Lưu danh sách repos vào file JSON"""
        with open(REPOS_FILE, 'w', encoding='utf-8') as f:
            json.dump(repos, f, indent=2, ensure_ascii=False)

    async def get_repo_info(self, repo_url):
        """Lấy thông tin repository từ GitHub API"""
        try:
            # Parse URL để lấy owner và repo name
            # Format: https://github.com/owner/repo
            parts = repo_url.rstrip('/').split('/')
            if len(parts) < 2:
                return None
            
            owner = parts[-2]
            repo_name = parts[-1]
            
            # Gọi GitHub API
            api_url = f"https://api.github.com/repos/{owner}/{repo_name}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "name": data.get("name"),
                            "full_name": data.get("full_name"),
                            "owner": data.get("owner", {}).get("login"),
                            "description": data.get("description", "Không có mô tả"),
                            "html_url": data.get("html_url"),
                            "stars": data.get("stargazers_count", 0),
                            "forks": data.get("forks_count", 0),
                            "language": data.get("language", "Unknown"),
                            "created_at": data.get("created_at"),
                            "updated_at": data.get("updated_at"),
                            "open_issues": data.get("open_issues_count", 0),
                            "added_date": datetime.now().isoformat()
                        }
                    else:
                        return None
        except Exception as e:
            print(f"Error getting repo info: {e}")
            return None

    async def send_to_webhook(self, repos):
        """Gửi danh sách repos lên Discord webhook"""
        try:
            # Tạo embed
            embed = {
                "title": "📚 Danh sách GitHub Repositories",
                "color": 0x2ecc71,
                "timestamp": datetime.now().isoformat(),
                "fields": [],
                "footer": {
                    "text": f"Tổng số repos: {len(repos)}"
                }
            }
            
            # Thêm thông tin từng repo
            for i, repo in enumerate(repos[:25], 1):  # Discord giới hạn 25 fields
                desc = repo.get('description') or "Không có mô tả"
                desc_text = f"{desc[:100]}..." if len(desc) > 100 else desc
                
                field = {
                    "name": f"{i}. {repo['full_name']}",
                    "value": (
                        f"⭐ {repo['stars']} | 🍴 {repo['forks']} | 💻 {repo['language']}\n"
                        f"[Xem trên GitHub]({repo['html_url']})\n"
                        f"{desc_text}"
                    ),
                    "inline": False
                }
                embed["fields"].append(field)
            
            # Gửi webhook
            async with aiohttp.ClientSession() as session:
                async with session.post(WEBHOOK_URL, json={"embeds": [embed]}) as response:
                    return response.status == 204
        except Exception as e:
            print(f"Error sending webhook: {e}")
            return False

    @app_commands.command(name="addrepo", description="Thêm link GitHub repository public")
    @app_commands.guilds(int(os.getenv('GUILD_ID')))
    @app_commands.describe(github_url="URL của GitHub repository (ví dụ: https://github.com/owner/repo)")
    async def add_repo(self, interaction: discord.Interaction, github_url: str):
        """Command thêm GitHub repository"""
        await interaction.response.defer()
        
        # Kiểm tra URL có hợp lệ không
        if "github.com" not in github_url:
            await interaction.followup.send("❌ URL không hợp lệ! Vui lòng nhập link GitHub repository.", ephemeral=True)
            return
        
        # Lấy thông tin repo
        repo_info = await self.get_repo_info(github_url)
        
        if not repo_info:
            await interaction.followup.send("❌ Không thể lấy thông tin repository! Kiểm tra lại URL hoặc repo có thể là private.", ephemeral=True)
            return
        
        # Load repos hiện tại
        repos = self.load_repos()
        
        # Kiểm tra repo đã tồn tại chưa
        existing = next((r for r in repos if r['full_name'] == repo_info['full_name']), None)
        
        if existing:
            await interaction.followup.send(f"⚠️ Repository **{repo_info['full_name']}** đã tồn tại trong danh sách!", ephemeral=True)
            return
        
        # Thêm repo mới
        repos.append(repo_info)
        self.save_repos(repos)
        
        # Clone hoặc pull repository
        clone_result = await clone_or_pull_repo(repo_info, PROJECTS_DIR)
        
        # Gửi lên webhook
        webhook_sent = await self.send_to_webhook(repos)
        
        # Tạo embed phản hồi
        embed = discord.Embed(
            title="✅ Đã thêm repository thành công!",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Tên", value=repo_info['full_name'], inline=False)
        embed.add_field(name="Mô tả", value=repo_info.get('description') or "Không có mô tả", inline=False)
        embed.add_field(name="⭐ Stars", value=str(repo_info['stars']), inline=True)
        embed.add_field(name="🍴 Forks", value=str(repo_info['forks']), inline=True)
        embed.add_field(name="💻 Ngôn ngữ", value=repo_info['language'], inline=True)
        embed.add_field(name="🔗 Link", value=f"[Xem trên GitHub]({repo_info['html_url']})", inline=False)
        
        # Thêm thông tin về clone/pull
        if clone_result['success']:
            action_text = "📥 Clone" if clone_result['action'] == 'cloned' else "🔄 Pull"
            embed.add_field(name=f"{action_text} Status", value=clone_result['message'], inline=False)
        else:
            embed.add_field(name="⚠️ Git Status", value=clone_result['message'], inline=False)
        
        if webhook_sent:
            embed.set_footer(text="✅ Đã cập nhật lên webhook")
        else:
            embed.set_footer(text="⚠️ Không thể cập nhật lên webhook")
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="listrepos", description="Hiển thị danh sách các GitHub repositories đã thêm")
    @app_commands.guilds(int(os.getenv('GUILD_ID')))
    async def list_repos(self, interaction: discord.Interaction):
        """Command hiển thị danh sách repos"""
        repos = self.load_repos()
        
        if not repos:
            await interaction.response.send_message("📭 Chưa có repository nào được thêm!", ephemeral=True)
            return
        
        # Tạo embed
        embed = discord.Embed(
            title="📚 Danh sách GitHub Repositories",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        # Thêm từng repo (giới hạn 25 fields)
        for i, repo in enumerate(repos[:25], 1):
            embed.add_field(
                name=f"{i}. {repo['full_name']}",
                value=(
                    f"⭐ {repo['stars']} | 🍴 {repo['forks']} | 💻 {repo['language']}\n"
                    f"[Xem trên GitHub]({repo['html_url']})"
                ),
                inline=False
            )
        
        embed.set_footer(text=f"Tổng số repos: {len(repos)}")
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="updatewebhook", description="Cập nhật danh sách repos lên webhook")
    @app_commands.guilds(int(os.getenv('GUILD_ID')))
    async def update_webhook(self, interaction: discord.Interaction):
        """Command cập nhật webhook"""
        await interaction.response.defer()
        
        repos = self.load_repos()
        
        if not repos:
            await interaction.followup.send("📭 Chưa có repository nào để cập nhật!", ephemeral=True)
            return
        
        # Gửi lên webhook
        webhook_sent = await self.send_to_webhook(repos)
        
        if webhook_sent:
            await interaction.followup.send(f"✅ Đã cập nhật {len(repos)} repositories lên webhook!")
        else:
            await interaction.followup.send("❌ Không thể cập nhật lên webhook!", ephemeral=True)

    @app_commands.command(name="removerepo", description="Xóa một repository khỏi danh sách")
    @app_commands.guilds(int(os.getenv('GUILD_ID')))
    @app_commands.describe(repo_identifier="Tên repo (name), owner/repo (full_name), hoặc URL GitHub")
    async def remove_repo(self, interaction: discord.Interaction, repo_identifier: str):
        """Command xóa repository"""
        repos = self.load_repos()
        
        # Chuẩn hóa input (loại bỏ khoảng trắng, chuyển về lowercase để so sánh)
        search_term = repo_identifier.strip().lower()
        
        # Tìm repo phù hợp (so sánh với name, full_name, và html_url)
        found_repo = None
        for repo in repos:
            repo_name = repo.get('name', '').lower()
            repo_full_name = repo.get('full_name', '').lower()
            repo_url = repo.get('html_url', '').lower()
            
            # Kiểm tra khớp với name, full_name, hoặc url
            if (search_term == repo_name or 
                search_term == repo_full_name or 
                search_term == repo_url or
                search_term in repo_url):  # Cho phép match cả URL đầy đủ
                found_repo = repo
                break
        
        if not found_repo:
            await interaction.response.send_message(
                f"❌ Không tìm thấy repository **{repo_identifier}**!\n"
                f"Hãy thử với: tên repo, owner/repo, hoặc URL GitHub đầy đủ.", 
                ephemeral=True
            )
            return
        
        # Xóa repo tìm được
        repos = [r for r in repos if r.get('full_name') != found_repo.get('full_name')]
        
        # Lưu lại
        self.save_repos(repos)
        
        # Cập nhật webhook
        await self.send_to_webhook(repos)
        
        await interaction.response.send_message(
            f"✅ Đã xóa repository **{found_repo['full_name']}** khỏi danh sách!"
        )


async def setup(bot):
    await bot.add_cog(GitHubManager(bot))
