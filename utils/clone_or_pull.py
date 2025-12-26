import os
import asyncio


async def run_docker_compose(repo_path, repo_name):
    """Chạy docker compose để build và deploy container
    
    Args:
        repo_path (str): Đường dẫn đến repository
        repo_name (str): Tên repository
        
    Returns:
        dict: Kết quả của thao tác docker compose với các keys:
            - success (bool): Thành công hay không
            - message (str): Thông báo chi tiết
    """
    try:
        # Kiểm tra xem có file docker-compose.yml không
        docker_compose_file = None
        for filename in ['docker-compose.yml']:
            file_path = os.path.join(repo_path, filename)
            if os.path.exists(file_path):
                docker_compose_file = filename
                break
        
        if not docker_compose_file:
            return {
                'success': False,
                'message': f"⚠️ Không tìm thấy file docker-compose trong **{repo_name}**"
            }
        
        print(f"Tìm thấy {docker_compose_file}, đang chạy docker compose...")
        
        # Dừng và xóa containers cũ (nếu có)
        print(f"Dừng containers cũ của {repo_name}...")
        stop_process = await asyncio.create_subprocess_exec(
            'docker', 'compose', '-f', docker_compose_file, 'down',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=repo_path
        )
        await stop_process.communicate()
        
        # Build và chạy containers mới
        print(f"Build và deploy containers cho {repo_name}...")
        up_process = await asyncio.create_subprocess_exec(
            'docker', 'compose', '-f', docker_compose_file, 
            'up', '-d', '--build',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=repo_path
        )
        stdout, stderr = await up_process.communicate()
        
        if up_process.returncode == 0:
            return {
                'success': True,
                'message': f"🐳 Đã deploy **{repo_name}** lên Docker thành công!"
            }
        else:
            error_msg = stderr.decode('utf-8', errors='ignore')
            return {
                'success': False,
                'message': f"⚠️ Lỗi khi deploy Docker cho **{repo_name}**: {error_msg[:150]}"
            }
            
    except FileNotFoundError:
        return {
            'success': False,
            'message': f"❌ Docker hoặc Docker Compose chưa được cài đặt hoặc không có trong PATH"
        }
    except Exception as e:
        return {
            'success': False,
            'message': f"❌ Lỗi khi chạy Docker Compose: {str(e)[:150]}"
        }


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
                # Sau khi pull thành công, chạy docker compose
                docker_result = await run_docker_compose(repo_path, repo_name)
                
                # Kết hợp thông báo
                message = f"✅ Đã pull repository **{repo_name}** thành công!"
                if docker_result['success']:
                    message += f"\n{docker_result['message']}"
                elif docker_result['message']:
                    message += f"\n{docker_result['message']}"
                
                return {
                    'success': True,
                    'action': 'pulled',
                    'message': message,
                    'docker_deployed': docker_result['success']
                }
            else:
                error_msg = stderr.decode('utf-8', errors='ignore')
                return {
                    'success': False,
                    'action': 'pull_failed',
                    'message': f"⚠️ Không thể pull repository **{repo_name}**: {error_msg[:100]}",
                    'docker_deployed': False
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
                # Sau khi clone thành công, chạy docker compose
                docker_result = await run_docker_compose(repo_path, repo_name)
                
                # Kết hợp thông báo
                message = f"✅ Đã clone repository **{repo_name}** thành công!"
                if docker_result['success']:
                    message += f"\n{docker_result['message']}"
                elif docker_result['message']:
                    message += f"\n{docker_result['message']}"
                
                return {
                    'success': True,
                    'action': 'cloned',
                    'message': message,
                    'docker_deployed': docker_result['success']
                }
            else:
                error_msg = stderr.decode('utf-8', errors='ignore')
                return {
                    'success': False,
                    'action': 'clone_failed',
                    'message': f"⚠️ Không thể clone repository **{repo_name}**: {error_msg[:100]}",
                    'docker_deployed': False
                }
                
    except Exception as e:
        return {
            'success': False,
            'action': 'error',
            'message': f"❌ Lỗi khi xử lý repository: {str(e)[:100]}",
            'docker_deployed': False
        }
