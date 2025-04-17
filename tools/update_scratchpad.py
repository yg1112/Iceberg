#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import re
import argparse
import datetime
import subprocess
from pathlib import Path

# 定义颜色编码
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
ENDC = '\033[0m'

def get_git_changes(days=7):
    """获取最近N天的Git提交记录"""
    try:
        # 计算N天前的日期
        date = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime('%Y-%m-%d')
        
        # 执行git命令获取提交记录
        cmd = f'git log --since="{date}" --name-status --pretty=format:"%h|%an|%ad|%s"'
        result = subprocess.check_output(cmd, shell=True).decode('utf-8')
        
        # 解析结果
        commits = []
        current_commit = None
        
        for line in result.split('\n'):
            if line.strip() == '':
                continue
                
            if '|' in line:
                # 这是一个提交记录行
                hash_val, author, date, message = line.split('|', 3)
                current_commit = {
                    'hash': hash_val,
                    'author': author,
                    'date': date,
                    'message': message,
                    'files': []
                }
                commits.append(current_commit)
            elif current_commit and line[0] in ['A', 'M', 'D', 'R']:
                # 这是一个文件变更行
                status, file_path = line[0], line[2:] if line[2:] else line[1:]
                if status == 'A':
                    change_type = '🆕 新增'
                elif status == 'M':
                    change_type = '🔄 更新'
                elif status == 'D':
                    change_type = '🗑️ 删除'
                else:
                    change_type = '📋 重命名'
                
                current_commit['files'].append({
                    'status': status,
                    'path': file_path,
                    'change_type': change_type
                })
                
        return commits
    except Exception as e:
        print(f"{RED}获取Git记录失败：{e}{ENDC}")
        return []

def analyze_changes(commits, task_keywords=None):
    """分析变更记录，按模块分组"""
    modules = {}
    
    # 定义模块匹配规则
    module_patterns = {
        '数据收集': r'src/scrapers/|data/|collectors?/',
        '数据分析': r'analysis|analytics|processor|处理',
        '评分引擎': r'scor(e|ing)|评分|rank',
        '可视化面板': r'dashboard|visualization|chart|图表|展示',
        '市场报告': r'report|报告|market|市场分析'
    }
    
    # 分析所有提交
    for commit in commits:
        commit_date = datetime.datetime.strptime(commit['date'], '%a %b %d %H:%M:%S %Y %z').strftime('%Y-%m-%d')
        
        for file_change in commit['files']:
            file_path = file_change['path']
            change_type = file_change['change_type']
            
            # 确定该文件属于哪个模块
            module_name = None
            for name, pattern in module_patterns.items():
                if re.search(pattern, file_path, re.IGNORECASE):
                    module_name = name
                    break
            
            # 如果没有匹配到任何模块，归为"其他"
            if not module_name:
                module_name = "其他"
            
            # 初始化模块信息
            if module_name not in modules:
                modules[module_name] = {
                    'changes': {},
                    'status': '✅ 可用'  # 默认状态
                }
            
            # 记录变更
            if commit_date not in modules[module_name]['changes']:
                modules[module_name]['changes'][commit_date] = []
            
            # 构建变更描述
            description = f"{change_type}: {os.path.basename(file_path)}"
            if task_keywords and any(kw.lower() in commit['message'].lower() for kw in task_keywords):
                description += f" ({commit['message']})"
            
            modules[module_name]['changes'][commit_date].append({
                'file': file_path,
                'description': description,
                'message': commit['message']
            })
    
    return modules

def update_scratchpad(modules):
    """更新.cursorscratchpad文件"""
    scratchpad_path = Path('.cursorscratchpad')
    
    # 如果文件不存在，创建基本结构
    if not scratchpad_path.exists():
        create_new_scratchpad(modules)
        return
    
    # 读取现有内容
    content = scratchpad_path.read_text(encoding='utf-8')
    
    # 更新模块状态
    modules_section = "## 📊 模块状态概览\n\n| 模块名称 | 状态 | 主文件路径 | 最后更新 |\n|---------|------|-----------|---------|"
    
    # 找到所有现有模块
    existing_modules = {}
    module_pattern = r'\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|'
    for match in re.finditer(module_pattern, content):
        module_name = match.group(1).strip()
        status = match.group(2).strip()
        path = match.group(3).strip()
        last_update = match.group(4).strip()
        
        existing_modules[module_name] = {
            'status': status,
            'path': path,
            'last_update': last_update
        }
    
    # 更新模块状态
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    for module_name, info in modules.items():
        # 如果模块已存在，更新最后更新时间
        if module_name in existing_modules:
            existing_modules[module_name]['last_update'] = today
        else:
            # 新模块
            main_path = determine_module_path(module_name)
            existing_modules[module_name] = {
                'status': '✅ 可用',
                'path': main_path,
                'last_update': today
            }
    
    # 重建模块状态部分
    new_module_section = modules_section + "\n"
    for name, info in sorted(existing_modules.items()):
        new_module_section += f"| {name} | {info['status']} | {info['path']} | {info['last_update']} |\n"
    
    # 替换模块状态部分
    pattern = r'## 📊 模块状态概览\n\n\|[^#]*'
    content = re.sub(pattern, new_module_section + "\n", content)
    
    # 更新最近变更部分
    changes_section = "## 🔄 最近变更\n\n"
    for date, changes in get_recent_changes(modules).items():
        changes_section += f"### {date}\n"
        for change in changes:
            changes_section += f"- {change}\n"
        changes_section += "\n"
    
    # 替换最近变更部分
    pattern = r'## 🔄 最近变更\n\n(?:###[^#]*)*?(?=\n## |$)'
    if re.search(pattern, content):
        content = re.sub(pattern, changes_section, content)
    else:
        # 如果没有找到最近变更部分，添加到文件末尾
        content += "\n" + changes_section
    
    # 写回文件
    scratchpad_path.write_text(content, encoding='utf-8')
    print(f"{GREEN}成功更新 .cursorscratchpad 文件{ENDC}")

def create_new_scratchpad(modules):
    """创建新的.cursorscratchpad文件"""
    scratchpad_path = Path('.cursorscratchpad')
    
    # 构建基本结构
    content = "# 市场需求分析项目追踪\n\n"
    
    # 模块状态
    content += "## 📊 模块状态概览\n\n"
    content += "| 模块名称 | 状态 | 主文件路径 | 最后更新 |\n"
    content += "|---------|------|-----------|---------|n"
    
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    for module_name, info in sorted(modules.items()):
        main_path = determine_module_path(module_name)
        content += f"| {module_name} | ✅ 可用 | {main_path} | {today} |\n"
    
    # 最近变更
    content += "\n## 🔄 最近变更\n\n"
    for date, changes in get_recent_changes(modules).items():
        content += f"### {date}\n"
        for change in changes:
            content += f"- {change}\n"
        content += "\n"
    
    # 已知问题
    content += "## ⚠️ 已知问题\n\n"
    content += "1. 请添加项目中的已知问题\n\n"
    
    # 待办事项
    content += "## 📋 待办事项\n\n"
    content += "- [ ] 请添加项目待办事项\n\n"
    
    # 文件结构
    content += "## 📁 文件结构\n\n"
    content += "```\n"
    content += get_file_structure()
    content += "```\n"
    
    # 写入文件
    scratchpad_path.write_text(content, encoding='utf-8')
    print(f"{GREEN}成功创建 .cursorscratchpad 文件{ENDC}")

def determine_module_path(module_name):
    """根据模块名称确定主要文件路径"""
    module_paths = {
        '数据收集': 'src/scrapers/',
        '数据分析': 'analysis.py',
        '评分引擎': 'scoring_engine.py',
        '可视化面板': 'dashboard.py',
        '市场报告': 'reports/',
        '其他': 'misc/'
    }
    
    return module_paths.get(module_name, f"{module_name.lower().replace(' ', '_')}/")

def get_recent_changes(modules):
    """获取最近变更记录，按日期分组"""
    all_changes = {}
    
    # 收集所有变更
    for module_name, info in modules.items():
        for date, changes in info['changes'].items():
            if date not in all_changes:
                all_changes[date] = []
            
            for change in changes:
                description = f"{change['description']} ({module_name})"
                if description not in all_changes[date]:
                    all_changes[date].append(description)
    
    # 按日期排序
    return dict(sorted(all_changes.items(), key=lambda x: x[0], reverse=True))

def get_file_structure():
    """获取项目文件结构"""
    # 递归地列出所有文件和目录
    result = ""
    
    def list_files(path, prefix="", is_last=True):
        nonlocal result
        current_path = Path(path)
        
        # 跳过某些目录和文件
        if current_path.name.startswith('.') or current_path.name in ['__pycache__', 'node_modules']:
            return
        
        # 添加当前路径
        if prefix:
            result += f"{prefix}{'└── ' if is_last else '├── '}{current_path.name}"
            if current_path.is_dir():
                result += "/\n"
            else:
                result += "\n"
        else:
            result += f"{current_path.name}/\n"
        
        # 如果是目录，递归处理
        if current_path.is_dir():
            items = list(current_path.iterdir())
            items = [item for item in items if not item.name.startswith('.') and item.name not in ['__pycache__', 'node_modules']]
            
            for i, item in enumerate(sorted(items, key=lambda x: (x.is_file(), x.name))):
                new_prefix = prefix + ('    ' if is_last else '│   ')
                list_files(item, new_prefix, i == len(items) - 1)
    
    list_files('.')
    return result

def generate_prompt_header(task_description=None, task_modules=None):
    """生成PROMPT_HEADER.md文件"""
    scratchpad_path = Path('.cursorscratchpad')
    
    if not scratchpad_path.exists():
        print(f"{YELLOW}警告: .cursorscratchpad文件不存在，无法生成PROMPT_HEADER.md{ENDC}")
        return
    
    # 读取现有内容
    content = scratchpad_path.read_text(encoding='utf-8')
    
    # 提取模块状态
    modules_pattern = r'## 📊 模块状态概览\n\n\|[^#]*'
    modules_match = re.search(modules_pattern, content)
    modules_text = modules_match.group(0) if modules_match else ""
    
    # 提取最近变更
    changes_pattern = r'## 🔄 最近变更\n\n(?:###[^#]*)*?(?=\n## |$)'
    changes_match = re.search(changes_pattern, content)
    changes_text = changes_match.group(0) if changes_match else ""
    
    # 提取已知问题
    issues_pattern = r'## ⚠️ 已知问题\n\n[^#]*'
    issues_match = re.search(issues_pattern, content)
    issues_text = issues_match.group(0) if issues_match else ""
    
    # 统计模块状态
    available_modules = []
    partial_modules = []
    unavailable_modules = []
    
    module_pattern = r'\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|'
    for match in re.finditer(module_pattern, content):
        module_name = match.group(1).strip()
        status = match.group(2).strip()
        
        if '✅' in status:
            available_modules.append(module_name)
        elif '🟡' in status:
            partial_modules.append(module_name)
        elif '🔴' in status:
            unavailable_modules.append(module_name)
    
    # 提取最近7天变更
    recent_changes = []
    date_pattern = r'### (\d{4}-\d{2}-\d{2})\n((?:-[^\n]*\n)+)'
    for match in re.finditer(date_pattern, content):
        date = match.group(1)
        changes = match.group(2).strip().split('\n')
        for change in changes:
            if change.strip():
                recent_changes.append(f"{date}: {change.strip()}")
    
    # 限制为最近7天
    recent_changes = recent_changes[:7]
    
    # 提取关键问题
    key_issues = []
    issues_text_clean = issues_text.replace('## ⚠️ 已知问题\n\n', '')
    for line in issues_text_clean.split('\n'):
        if line.strip() and re.match(r'\d+\.', line.strip()):
            key_issues.append(line.strip())
    
    # 构建PROMPT_HEADER.md内容
    header_content = "# 市场需求分析项目 - Prompt Header\n\n"
    header_content += "## 🔄 项目状态概览 (来自.cursorscratchpad)\n\n"
    
    header_content += "### 📊 模块状态\n"
    if available_modules:
        header_content += f"- ✅ 可用模块: {', '.join(available_modules)}\n"
    if partial_modules:
        header_content += f"- 🟡 部分可用: {', '.join(partial_modules)}\n"
    if unavailable_modules:
        header_content += f"- 🔴 待修复: {', '.join(unavailable_modules)}\n"
    
    header_content += "\n### 🔍 最近变更 (7天内)\n"
    for change in recent_changes:
        parts = change.split(': - ')
        if len(parts) == 2:
            date, desc = parts
            header_content += f"- {desc}\n"
    
    header_content += "\n### ⚠️ 关键问题\n"
    for i, issue in enumerate(key_issues[:3]):  # 限制为前3个问题
        header_content += f"{issue}\n"
    
    header_content += "\n## 🎯 当前任务\n\n"
    header_content += "**任务描述**:\n"
    if task_description:
        header_content += f"<!-- {task_description} -->\n"
    else:
        header_content += "<!-- 在此处简要描述本次开发任务 -->\n"
    
    header_content += "\n**涉及模块**:\n"
    if task_modules:
        header_content += f"<!-- {', '.join(task_modules)} -->\n"
    else:
        header_content += "<!-- 列出本次任务涉及的模块 -->\n"
    
    header_content += "\n**预期成果**:\n"
    header_content += "<!-- 描述任务完成后的预期结果 -->\n\n"
    
    header_content += "---\n\n"
    header_content += "请在开始实现前先查阅完整的 `.cursorscratchpad` 获取详细模块信息，并确认任务所涉及模块的当前状态。任务完成后，记得更新 `.cursorscratchpad` 文件。"
    
    # 写入文件
    prompt_header_path = Path('PROMPT_HEADER.md')
    prompt_header_path.write_text(header_content, encoding='utf-8')
    print(f"{GREEN}成功生成 PROMPT_HEADER.md 文件{ENDC}")

def main():
    parser = argparse.ArgumentParser(description='自动更新项目状态跟踪文件')
    parser.add_argument('--days', type=int, default=7, help='获取最近几天的Git提交记录（默认7天）')
    parser.add_argument('--task', type=str, help='当前任务描述，用于生成任务相关的PROMPT_HEADER')
    
    args = parser.parse_args()
    
    print(f"{GREEN}正在获取最近{args.days}天的Git提交记录...{ENDC}")
    commits = get_git_changes(args.days)
    
    if not commits:
        print(f"{YELLOW}未找到符合条件的Git提交记录{ENDC}")
        # 仍然继续，因为可能只是需要生成头文件
    
    task_keywords = [args.task] if args.task else None
    modules = analyze_changes(commits, task_keywords)
    
    print(f"{GREEN}正在更新 .cursorscratchpad 文件...{ENDC}")
    update_scratchpad(modules)
    
    print(f"{GREEN}正在生成 PROMPT_HEADER.md 文件...{ENDC}")
    task_modules = [m for m, info in modules.items() if args.task and any(
        args.task.lower() in change['message'].lower() 
        for date_changes in info['changes'].values() 
        for change in date_changes
    )]
    generate_prompt_header(args.task, task_modules)
    
    print(f"{GREEN}任务完成{ENDC}")

if __name__ == "__main__":
    main() 