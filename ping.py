from ping3 import ping
from typing import Dict, List, Tuple
import concurrent.futures
import time

class PingTester:
    def __init__(self, timeout=3, count=2):
        self.timeout = timeout
        self.count = count
        self.results: Dict[str, float] = {}
    
    def ping_ip(self, ip: str) -> Tuple[str, float]:
        """Ping单个IP并返回平均延迟"""
        delays = []
        for _ in range(self.count):
            try:
                delay = ping(ip, timeout=self.timeout, unit='ms')
                if delay is not None and delay is not False:
                    delays.append(delay)
                time.sleep(0.1)  # 短暂间隔
            except:
                continue
        
        if delays:
            avg_delay = sum(delays) / len(delays)
            return (ip, avg_delay)
        else:
            return (ip, float('inf'))
    
    def test_ips(self, ips: List[str], max_workers=15) -> Dict[str, float]:
        """并发测试多个IP的延迟"""
        self.results = {}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_ip = {executor.submit(self.ping_ip, ip): ip for ip in ips}
            
            for future in concurrent.futures.as_completed(future_to_ip):
                ip, delay = future.result()
                self.results[ip] = delay
        
        return self.results
    
    def get_fastest_ip(self, ips: List[str] = None) -> Tuple[str, float]:
        """获取最快的IP"""
        if ips:
            self.test_ips(ips)
        
        if not self.results:
            return ("", float('inf'))
        
        valid_ips = {ip: delay for ip, delay in self.results.items() if delay != float('inf')}
        
        if not valid_ips:
            return ("", float('inf'))
        
        fastest_ip = min(valid_ips, key=valid_ips.get)
        return (fastest_ip, valid_ips[fastest_ip])
    
    def get_sorted_ips(self, ips: List[str] = None) -> List[Tuple[str, float]]:
        """获取排序后的IP列表 按延迟从低到高"""
        if ips:
            self.test_ips(ips)
        
        valid_ips = [(ip, delay) for ip, delay in self.results.items() if delay != float('inf')]
        return sorted(valid_ips, key=lambda x: x[1])