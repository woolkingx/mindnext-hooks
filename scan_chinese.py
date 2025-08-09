#!/usr/bin/env python3
"""
掃描中文字符並Generate翻譯對照表
"""

import os
import re
import glob
from collections import Counter

def scan_chinese_words():
    """掃描所有PythonFile中的中文詞彙"""
    chinese_words = set()
    files_processed = 0
    
    # 掃描所有PythonFile（排除cleanupDirectory）
    for file_path in glob.glob('/root/Dev/mindnext/hooks/**/*.py', recursive=True):
        if 'cleanup' in file_path:
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            continue
            
        # 查找中文字符
        chinese_matches = re.findall(r'[\u4e00-\u9fff]+', content)
        for match in chinese_matches:
            chinese_words.add(match)
        
        files_processed += 1
    
    print(f"掃描了 {files_processed} files")
    print(f"發現 {len(chinese_words)} 個不重複的中文詞彙")
    
    # 按長度排序，長詞在前
    sorted_words = sorted(chinese_words, key=len, reverse=True)
    
    # Generate翻譯對照表
    translation_map = {}
    
    for word in sorted_words:
        english = get_english_translation(word)
        if english:
            translation_map[word] = english
    
    # 輸出對照表
    print("\n=== 中英翻譯對照表 ===")
    for chinese, english in translation_map.items():
        print(f'"{chinese}": "{english}",')
    
    # Save到File
    with open('chinese_words.txt', 'w', encoding='utf-8') as f:
        for word in sorted_words:
            f.write(word + '\n')
    
    with open('translation_map.txt', 'w', encoding='utf-8') as f:
        for chinese, english in translation_map.items():
            f.write(f'"{chinese}": "{english}",\n')
    
    print(f"\nResultSave到 chinese_words.txt 和 translation_map.txt")

def get_english_translation(chinese_word):
    """獲取中文詞的英文翻譯"""
    translations = {
        # 基本Action
        "Execute": "Execute",
        "Process": "Process", 
        "Generate": "Generate",
        "Create": "Create",
        "Create": "Create",
        "Record": "Record",
        "Query": "Query",
        "Update": "Update",
        "Delete": "Delete",
        "Save": "Save",
        "Load": "Load",
        "Check": "Check",
        "Validate": "Validate",
        "Analyze": "Analyze",
        "Evaluate": "Evaluate",
        "Optimize": "Optimize",
        
        # System相關
        "System": "System",
        "Configuration": "Configuration",
        "Settings": "Settings",
        "Options": "Options",
        "Parameters": "Parameters",
        "Result": "Result",
        "Data": "Data",
        "Data": "Data",
        "Information": "Information",
        "Message": "Message",
        "Event": "Event",
        "Status": "Status",
        "Type": "Type",
        
        # Action相關
        "Action": "Action",
        "Operation": "Operation",
        "Function": "Function",
        "Method": "Method",
        "Tool": "Tool",
        "Module": "Module",
        "Component": "Component",
        "Component": "Component",
        "Service": "Service",
        "Interface": "Interface",
        "Interface": "Interface",
        
        # File相關
        "File": "File",
        "File": "File",
        "Directory": "Directory",
        "Path": "Path",
        "Format": "Format",
        "Content": "Content",
        "Size": "Size",
        "Time": "Time",
        "Date": "Date",
        
        # ErrorProcess
        "Error": "Error",
        "Exception": "Exception", 
        "Failed": "Failed",
        "Success": "Success",
        "Complete": "Complete",
        "Interrupted": "Interrupted",
        "Pause": "Pause",
        "Continue": "Continue",
        
        # Quality相關
        "Quality": "Quality",
        "Quality": "Quality",
        "Detection": "Detection",
        "Test": "Test",
        "Validate": "Validation",
        "Score": "Score",
        "Level": "Level",
        
        # Notification相關
        "Notification": "Notification",
        "Reminder": "Reminder",
        "Warning": "Warning",
        "Message": "Message",
        "Email": "Email",
        "Send": "Send",
        "Receive": "Receive",
        
        # Memory相關
        "Memory": "Memory",
        "Cache": "Cache",
        "Storage": "Storage",
        "Storage": "Storage",
        "Temporary": "Temporary",
        "Permanent": "Permanent",
        "Session": "Session",
        "Conversation": "Conversation",
        
        # User相關
        "User": "User",
        "User": "User",
        "Client": "Client",
        "Administrator": "Administrator",
        "Permission": "Permission",
        "Authentication": "Authentication",
        "Authorization": "Authorization",
        
        # Network相關
        "Network": "Network",
        "Network": "Network",
        "Connection": "Connection",
        "Connection": "Connection",
        "Request": "Request",
        "Response": "Response",
        "Response": "Response",
        "Server": "Server",
        "Server": "Server",
        "Client": "Client",
        
        # Status描述
        "Start": "Start",
        "Stop": "Stop",
        "Running": "Running",
        "Executing": "Executing",
        "Waiting": "Waiting",
        "Ready": "Ready",
        "Initialize": "Initialize",
        "In progress": "In progress",
        
        # 特定詞組
        "Event type": "Event Type",
        "Tool name": "Tool Name",
        "File path": "File Path",
        "User prompt": "User Prompt",
        "Execute tool": "Execute Tool",
        "Prepare to execute": "Prepare to execute",
        "Involved files": "Involved files",
        "files": " files",
        "No file operations": "No file operations",
        "Unknown operation": "Unknown operation",
        "Unsupported": "Unsupported",
        "Unsupported": "Unsupported",
        "Default": "Default",
        "Default": "Default",
        "Console notification": "Console notification",
        "System notification": "System notification",
        "Email notification": "Email notification",
        "Security scan": "Security scan",
        "Dependency check": "Dependency check",
        "Similarity check": "Similarity check",
        "Code formatting": "Code formatting",
        "Static check": "Static check",
        "Rate limit": "Rate limit",
        "Circuit breaker": "Circuit breaker",
        "Conditional control": "Conditional control",
        "Loop control": "Loop control",
        "Basic analysis": "Basic analysis",
        "Trend analysis": "Trend analysis",
        "Pattern analysis": "Pattern analysis",
        "Performance analysis": "Performance analysis",
        "Usage analysis": "Usage analysis",
        "Impact analysis": "Impact analysis",
        "Prompt processing": "Prompt processing",
        "Code review": "Code review",
        "Effort estimation": "Effort estimation",
        "Pattern detection": "Pattern detection",
        "Suggestion generation": "Suggestion generation",
        
        # 複合詞
        "Action Executor": "Action Executor",
        "Quality Check Action Executor": "Quality Check Action Executor",
        "Memory Record Action Executor": "Memory Record Action Executor",
        "Notification Action Executor": "Notification Action Executor",
        "Analysis Action Executor": "Analysis Action Executor",
        "Prompt Processing Action Executor": "Prompt Processing Action Executor",
        "Conditional Control Action Executor": "Conditional Control Action Executor",
        "Utility Action Executor": "Utility Action Executor",
        "AI Action Executor": "AI Action Executor",
        "Knowledge Graph": "Knowledge Graph",
        "Three-layer Flow Engine": "Three-layer Flow Engine",
        "Rule Engine": "Rule Engine",
        "Event Processor": "Event Processor",
        "Flow Coordinator": "Flow Coordinator",
        
        # 註解詞
        "負責": "responsible for",
        "包含": "contains", 
        "提供": "provides",
        "支持": "supports",
        "實現": "implements",
        "基於": "based on",
        "用於": "used for",
        "負責Process": "handles",
        "負責Execute": "executes",
        "負責管理": "manages",
        "負責協調": "coordinates",
    }
    
    return translations.get(chinese_word, "")

if __name__ == "__main__":
    scan_chinese_words()