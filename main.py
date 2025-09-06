import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
from github import GitHubAPI
from ping import PingTester
from host import HostsManager

class GitHubAccelerator:
    def __init__(self, root):
        self.root = root
        self.root.title("GitHub加速工具 Powered by 鼠子Tomoriゞ")
        self.root.geometry("720x600")
        self.root.resizable(False, False)
        
        self.github_api = GitHubAPI()
        self.ping_tester = PingTester()
        self.hosts_manager = HostsManager()
        
        self.domain_vars = {}
        self.domain_ips = {}
        self.selected_ips = {}
        self.testing = False
        
        self.setup_ui()
        self.load_domains()
    
    def setup_ui(self):
        # 顶部标题区域
        title_frame = ttk.Frame(self.root)
        title_frame.pack(fill=tk.X, padx=10, pady=10)
        
        title_label = ttk.Label(title_frame, text="GitHubAcce", font=('Arial', 14, 'bold'))
        title_label.pack(anchor=tk.W)
        
        subtitle_label = ttk.Label(title_frame, text="选择需要加速的GitHub域名", font=('Arial', 9))
        subtitle_label.pack(anchor=tk.W, pady=(2, 0))
        
        # 主内容区域
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 左侧域名列表
        left_frame = ttk.LabelFrame(main_frame, text="域名列表", padding=5)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # 快速操作按钮
        quick_frame = ttk.Frame(left_frame)
        quick_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(quick_frame, text="全选", command=self.select_all, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_frame, text="全不选", command=self.deselect_all, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_frame, text="推荐", command=self.select_recommended, width=8).pack(side=tk.LEFT, padx=2)
        
        # 域名选择区域
        domain_canvas = tk.Canvas(left_frame, height=200)
        domain_scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=domain_canvas.yview)
        self.domain_frame = ttk.Frame(domain_canvas)
        
        self.domain_frame.bind("<Configure>", lambda e: domain_canvas.configure(scrollregion=domain_canvas.bbox("all")))
        
        domain_canvas.create_window((0, 0), window=self.domain_frame, anchor="nw")
        domain_canvas.configure(yscrollcommand=domain_scrollbar.set)
        
        domain_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        domain_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 右侧操作按钮
        right_frame = ttk.LabelFrame(main_frame, text="操作", padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        
        # 操作按钮
        self.get_ips_btn = ttk.Button(right_frame, text="获取IP", command=self.get_ips, width=12)
        self.get_ips_btn.pack(pady=5)
        
        self.test_btn = ttk.Button(right_frame, text="测试延迟", command=self.test_latency, state='disabled', width=12)
        self.test_btn.pack(pady=5)
        
        self.apply_btn = ttk.Button(right_frame, text="应用选中", command=self.apply_selected, state='disabled', width=12)
        self.apply_btn.pack(pady=5)
        
        self.gen_btn = ttk.Button(right_frame, text="生成Hosts", command=self.generate_hosts, state='disabled', width=12)
        self.gen_btn.pack(pady=5)
        
        ttk.Button(right_frame, text="恢复备份", command=self.restore_backup, width=12).pack(pady=5)
        
        # 统计信息
        stats_frame = ttk.Frame(right_frame)
        stats_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.stats_var = tk.StringVar()
        self.stats_var.set("就绪")
        stats_label = ttk.Label(stats_frame, textvariable=self.stats_var, font=('Arial', 8))
        stats_label.pack()
        
        # IP显示区域
        ip_frame = ttk.LabelFrame(self.root, text="IP地址信息", padding=5)
        ip_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 10))
        
        # 创建Treeview
        columns = ("domain", "ip", "latency", "status")
        self.tree = ttk.Treeview(ip_frame, columns=columns, show="headings", height=8)
        
        self.tree.heading("domain", text="域名")
        self.tree.heading("ip", text="IP地址")
        self.tree.heading("latency", text="延迟(ms)")
        self.tree.heading("status", text="状态")
        
        self.tree.column("domain", width=180)
        self.tree.column("ip", width=120)
        self.tree.column("latency", width=80)
        self.tree.column("status", width=80)
        
        # 添加滚动条
        scrollbar_tree_y = ttk.Scrollbar(ip_frame, orient="vertical", command=self.tree.yview)
        scrollbar_tree_x = ttk.Scrollbar(ip_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar_tree_y.set, xscrollcommand=scrollbar_tree_x.set)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar_tree_y.grid(row=0, column=1, sticky=(tk.N, tk.S))
        scrollbar_tree_x.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        ip_frame.columnconfigure(0, weight=1)
        ip_frame.rowconfigure(0, weight=1)
        
        # 底部状态栏
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, padx=10, pady=(0, 5))
        
        self.progress = ttk.Progressbar(status_frame, mode='indeterminate')
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        status_label = ttk.Label(status_frame, textvariable=self.status_var)
        status_label.pack(side=tk.RIGHT)
    
    def select_all(self):
        """全选"""
        for var in self.domain_vars.values():
            var.set(True)
        self._update_stats()
    
    def deselect_all(self):
        """全不选"""
        for var in self.domain_vars.values():
            var.set(False)
        self._update_stats()
    
    def select_recommended(self):
        """选择推荐域名"""
        recommended = self.github_api.get_recommended_domains()
        for domain, var in self.domain_vars.items():
            var.set(domain in recommended)
        self._update_stats()
    
    def _update_stats(self):
        """更新统计信息"""
        selected_count = sum(1 for var in self.domain_vars.values() if var.get())
        total_count = len(self.domain_vars)
        ip_count = sum(len(ips) for ips in self.domain_ips.values())
        self.stats_var.set(f"选中: {selected_count}/{total_count} | IP: {ip_count}")
    
    def load_domains(self):
        """加载域名列表"""
        domains = self.github_api.get_all_domains()
        
        for widget in self.domain_frame.winfo_children():
            widget.destroy()
        
        self.domain_vars = {}
        recommended = self.github_api.get_recommended_domains()
        
        # 创建2列的网格布局
        for i, domain in enumerate(domains):
            var = tk.BooleanVar(value=(domain in recommended))
            chk = ttk.Checkbutton(self.domain_frame, text=domain, variable=var,
                                 command=self._update_stats)
            row = i // 2
            col = i % 2
            chk.grid(row=row, column=col, sticky=tk.W, padx=2, pady=1)
            self.domain_vars[domain] = var
        
        self._update_stats()
    
    def get_ips(self):
        """获取IP地址"""
        if self.testing:
            return
        
        selected_domains = [domain for domain, var in self.domain_vars.items() if var.get()]
        if not selected_domains:
            messagebox.showwarning("提示", "请至少选择一个域名")
            return
        
        self.testing = True
        self.progress.start()
        self.status_var.set("正在获取IP地址...")
        self.get_ips_btn.config(state='disabled')
        
        threading.Thread(target=self._get_ips_thread, args=(selected_domains,), daemon=True).start()
    
    def _get_ips_thread(self, selected_domains):
        """获取IP的线程"""
        self.domain_ips = {}
        total = len(selected_domains)
        
        for i, domain in enumerate(selected_domains):
            self.root.after(0, lambda d=domain, idx=i+1, tot=total: 
                          self.status_var.set(f"正在解析 {d} ({idx}/{tot})"))
            ips = self.github_api.get_domain_ips(domain)
            if ips:
                self.domain_ips[domain] = list(ips)
            time.sleep(0.1)
        
        self.root.after(0, self._update_ip_display)
        self.root.after(0, lambda: self.status_var.set("IP地址获取完成"))
        self.root.after(0, self._reset_ui)
        self.root.after(0, lambda: self.test_btn.config(state='normal'))
        self.root.after(0, self._update_stats)
    
    def _update_ip_display(self):
        """更新IP显示"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for domain, ips in self.domain_ips.items():
            for ip in ips:
                self.tree.insert("", "end", values=(domain, ip, "未测试", "等待"))
    
    def test_latency(self):
        """测试延迟"""
        if not self.domain_ips:
            return
        
        self.testing = True
        self.progress.start()
        self.status_var.set("正在测试延迟...")
        self.test_btn.config(state='disabled')
        
        all_ips = []
        for ips in self.domain_ips.values():
            all_ips.extend(ips)
        
        threading.Thread(target=self._test_latency_thread, args=(all_ips,), daemon=True).start()
    
    def _test_latency_thread(self, ips):
        """测试延迟线程"""
        results = self.ping_tester.test_ips(ips)
        
        self.root.after(0, lambda: self._update_latency_display(results))
        self.root.after(0, lambda: self.status_var.set("延迟测试完成"))
        self.root.after(0, self._reset_ui)
        self.root.after(0, lambda: self.apply_btn.config(state='normal'))
        self.root.after(0, lambda: self.gen_btn.config(state='normal'))
    
    def _update_latency_display(self, results):
        """更新延迟显示"""
        fastest_ips = {}
        
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            domain = values[0]
            ip = values[1]
            
            if ip in results:
                latency = results[ip]
                if latency == float('inf'):
                    latency_str = "超时"
                    status = "失败"
                else:
                    latency_str = f"{latency:.1f}"
                    status = "正常"
                    
                    if domain not in fastest_ips or latency < fastest_ips[domain][1]:
                        fastest_ips[domain] = (ip, latency)
                
                self.tree.set(item, "latency", latency_str)
                self.tree.set(item, "status", status)
        
        # 自动选择每个域名最快的IP
        for domain, (ip, latency) in fastest_ips.items():
            for item in self.tree.get_children():
                values = self.tree.item(item, "values")
                if values[0] == domain and values[1] == ip:
                    self.tree.selection_add(item)
                    break
    
    def apply_selected(self):
        """应用选中"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择要应用的IP地址")
            return
        
        self.selected_ips = {}
        for item in selection:
            values = self.tree.item(item, "values")
            domain = values[0]
            ip = values[1]
            self.selected_ips[domain] = ip
        
        success = self.hosts_manager.update_github_hosts(self.selected_ips)
        if success:
            messagebox.showinfo("成功", "Hosts文件已更新")
            self.status_var.set("Hosts文件更新成功")
        else:
            messagebox.showerror("错误", "更新失败，请以管理员权限运行")
    
    def generate_hosts(self):
        """生成Hosts内容"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择IP地址")
            return
        
        selected_ips = {}
        for item in selection:
            values = self.tree.item(item, "values")
            selected_ips[values[0]] = values[1]
        
        content = self.hosts_manager.generate_hosts_content(selected_ips)
        
        top = tk.Toplevel(self.root)
        top.title("生成的Hosts内容")
        top.geometry("600x400")
        
        text = scrolledtext.ScrolledText(top, wrap=tk.WORD, font=('Consolas', 9))
        text.insert(tk.INSERT, content)
        text.config(state='disabled')
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Button(top, text="关闭", command=top.destroy).pack(pady=5)
    
    def restore_backup(self):
        """恢复备份"""
        if messagebox.askyesno("确认", "确定要恢复Hosts文件备份吗？"):
            success = self.hosts_manager.restore_backup()
            if success:
                messagebox.showinfo("成功", "Hosts文件已恢复")
                self.status_var.set("Hosts文件已恢复备份")
            else:
                messagebox.showerror("错误", "恢复备份失败")
    
    def _reset_ui(self):
        """重置UI状态"""
        self.testing = False
        self.progress.stop()
        self.get_ips_btn.config(state='normal')

if __name__ == "__main__":
    root = tk.Tk()
    app = GitHubAccelerator(root)
    root.mainloop()