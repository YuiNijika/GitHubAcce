import os
import tempfile
import platform
import shutil
from typing import Dict, List

class HostsManager:
    def __init__(self):
        self.system = platform.system()
        self.hosts_path = self._get_hosts_path()
    
    def _get_hosts_path(self) -> str:
        """获取系统hosts文件路径"""
        if self.system == "Windows":
            return r"C:\Windows\System32\drivers\etc\hosts"
        else:
            return "/etc/hosts"
    
    def read_hosts(self) -> List[str]:
        """读取hosts文件内容"""
        try:
            with open(self.hosts_path, 'r', encoding='utf-8') as f:
                return f.readlines()
        except Exception as e:
            print(f"读取hosts文件失败: {e}")
            return []
    
    def write_hosts(self, lines: List[str]) -> bool:
        """写入hosts文件"""
        try:
            # 创建备份
            self._create_backup()
            
            # 写入新文件
            with open(self.hosts_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            return True
        except Exception as e:
            print(f"写入hosts文件失败: {e}")
            return False
    
    def _create_backup(self):
        """创建hosts文件备份"""
        try:
            backup_path = self.hosts_path + ".backup"
            shutil.copy2(self.hosts_path, backup_path)
        except:
            pass
    
    def update_github_hosts(self, domain_ips: Dict[str, str]) -> bool:
        """更新hosts文件中的GitHub相关条目"""
        lines = self.read_hosts()
        
        # 移除现有的GitHub相关条目
        new_lines = []
        github_domains = set(domain_ips.keys())
        
        for line in lines:
            if line.strip().startswith('#'):
                new_lines.append(line)
                continue
            
            parts = line.split()
            if len(parts) >= 2:
                domain = parts[1]
                if not any(g_domain in domain for g_domain in github_domains):
                    new_lines.append(line)
            else:
                new_lines.append(line)
        
        # 添加新的GitHub条目
        new_lines.append("\n# GitHub加速配置\n")
        for domain, ip in domain_ips.items():
            new_lines.append(f"{ip}\t{domain}\n")
        new_lines.append("# GitHub加速配置结束\n")
        
        return self.write_hosts(new_lines)
    
    def generate_hosts_content(self, domain_ips: Dict[str, str]) -> str:
        """生成hosts文件内容字符串"""
        content = "# GitHub加速配置\n"
        for domain, ip in domain_ips.items():
            content += f"{ip}\t{domain}\n"
        content += "# GitHub加速配置结束\n"
        return content
    
    def restore_backup(self) -> bool:
        """恢复备份"""
        try:
            backup_path = self.hosts_path + ".backup"
            if os.path.exists(backup_path):
                shutil.copy2(backup_path, self.hosts_path)
                return True
            return False
        except:
            return False