import requests
import json
from typing import Dict, List, Set
import ipaddress
import socket
from concurrent.futures import ThreadPoolExecutor

class GitHubAPI:
    def __init__(self):
        self.api_url = "https://api.github.com/meta"
        self.domain_ips: Dict[str, Set[str]] = {}
        
        # GitHub域名
        self.static_domains = [
            "github.com",
            "github.global.ssl.fastly.net",
            "gist.github.com",
            "help.github.com",
            "status.github.com",
            "training.github.com",
            "github.io",
            "github.community",
            "github.dev",
            "api.github.com",
            "collector.github.com",
            "pipelines.actions.githubusercontent.com",
            "media.githubusercontent.com",
            "codeload.github.com",
            "cloud.githubusercontent.com",
            "objects.githubusercontent.com",
            "raw.githubusercontent.com",
            "user-images.githubusercontent.com",
            "favicons.githubusercontent.com",
            "avatars.githubusercontent.com",
            "avatars0.githubusercontent.com",
            "avatars1.githubusercontent.com",
            "avatars2.githubusercontent.com",
            "avatars3.githubusercontent.com",
            "github.githubassets.com",
            "alive.github.com",
            "central.github.com",
            "live.github.com",
            "githubapp.com",
            "githubstatus.com"
        ]
    
    def get_github_ips(self) -> Dict[str, List[str]]:
        """从GitHub API获取所有IP地址"""
        try:
            response = requests.get(self.api_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            result = {}
            for key, values in data.items():
                if key == "verifiable_password_authentication":
                    continue
                
                ipv4_list = []
                for item in values:
                    try:
                        network = ipaddress.ip_network(item, strict=False)
                        if network.version == 4:
                            ipv4_list.append(str(network.network_address))
                    except ValueError:
                        try:
                            ip = ipaddress.ip_address(item)
                            if ip.version == 4:
                                ipv4_list.append(item)
                        except ValueError:
                            continue
                
                result[key] = ipv4_list
            
            return result
        except Exception as e:
            print(f"获取GitHub IP失败: {e}")
            return {}
    
    def get_domain_ips(self, domain: str) -> Set[str]:
        """获取指定域名的IP地址"""
        if domain in self.domain_ips:
            return self.domain_ips[domain]
        
        try:
            ips = set()
            # 使用多线程DNS解析
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = []
                for record_type in [socket.AF_INET]:  # 只获取IPv4
                    future = executor.submit(self._resolve_dns, domain, record_type)
                    futures.append(future)
                
                for future in futures:
                    try:
                        result = future.result(timeout=5)
                        if result:
                            ips.update(result)
                    except:
                        continue
            
            self.domain_ips[domain] = ips
            return ips
        except Exception as e:
            print(f"获取域名 {domain} 的IP失败: {e}")
            return set()
    
    def _resolve_dns(self, domain: str, record_type: int) -> Set[str]:
        """DNS解析"""
        try:
            ips = set()
            for info in socket.getaddrinfo(domain, 0, record_type):
                ips.add(info[4][0])
            return ips
        except:
            return set()
    
    def get_all_domains(self) -> List[str]:
        """获取所有支持的域名列表"""
        return self.static_domains
    
    def get_recommended_domains(self) -> List[str]:
        """获取推荐加速的域名"""
        return [
            "github.com",
            "github.global.ssl.fastly.net",
            "raw.githubusercontent.com",
            "objects.githubusercontent.com",
            "avatars.githubusercontent.com",
            "github.githubassets.com"
        ]