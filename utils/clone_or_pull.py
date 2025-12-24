import os
import asyncio


async def clone_or_pull_repo(repo_info, projects_dir="projects"):
    """Clone repository nếu chưa có hoặc pull nếu đã có
    
    Args:
        repo_info (dict): Thông tin repository từ GitHub API
        projects_dir (str): Đường dẫn thư mục chứa các projects
        
    Returns:
        dict: Kết quả của thao tác clone/pull với các keys:
            - success (bool): Thành công hay không
            - action (str): 'cloned', 'pulled', 'clone_failed', 'pull_failed', hoặc 'error'
            - message (str): Thông báo chi tiết
    """
    try:
        repo_name = repo_info['name']
        repo_url = repo_info['html_url']
        repo_path = os.path.join(projects_dir, repo_name)
        
        # Kiểm tra xem repo đã tồn tại chưa
        if os.path.exists(repo_path):
            # Nếu đã tồn tại, thực hiện git pull
            print(f"Repository {repo_name} đã tồn tại, đang pull...")
            
            # Chạy git pull
            process = await asyncio.create_subprocess_exec(
                'git', '-C', repo_path, 'pull',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return {
                    'success': True,
                    'action': 'pulled',
                    'message': f"✅ Đã pull repository **{repo_name}** thành công!"
                }
            else:
                error_msg = stderr.decode('utf-8', errors='ignore')
                return {
                    'success': False,
                    'action': 'pull_failed',
                    'message': f"⚠️ Không thể pull repository **{repo_name}**: {error_msg[:100]}"
                }
        else:
            # Nếu chưa tồn tại, thực hiện git clone
            print(f"Repository {repo_name} chưa tồn tại, đang clone...")
            
            # Chạy git clone
            process = await asyncio.create_subprocess_exec(
                'git', 'clone', repo_url, repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return {
                    'success': True,
                    'action': 'cloned',
                    'message': f"✅ Đã clone repository **{repo_name}** thành công!"
                }
            else:
                error_msg = stderr.decode('utf-8', errors='ignore')
                return {
                    'success': False,
                    'action': 'clone_failed',
                    'message': f"⚠️ Không thể clone repository **{repo_name}**: {error_msg[:100]}"
                }
                
    except Exception as e:
        return {
            'success': False,
            'action': 'error',
            'message': f"❌ Lỗi khi xử lý repository: {str(e)[:100]}"
        }
