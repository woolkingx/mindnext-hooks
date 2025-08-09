#!/usr/bin/env python3
"""
掃描連續中文詞組並Generate翻譯對照表
"""

import os
import re
import glob
from collections import Counter

def scan_chinese_phrases():
    """掃描所有PythonFile中的連續中文詞組"""
    chinese_phrases = Counter()
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
            
        # 查找連續的中文字符組成的詞組
        # 使用更精確的正則表達式，匹配2個或更多連續中文字符
        chinese_matches = re.findall(r'[\u4e00-\u9fff]{2,}', content)
        
        for match in chinese_matches:
            # 過濾掉一些不需要翻譯的Content
            if len(match) >= 2:  # 至少2個字符
                chinese_phrases[match] += 1
        
        files_processed += 1
    
    print(f"掃描了 {files_processed} files")
    print(f"發現 {len(chinese_phrases)} 個不重複的中文詞組")
    
    # 按使用頻率排序，常用詞在前
    sorted_phrases = sorted(chinese_phrases.items(), key=lambda x: (-x[1], -len(x[0])))
    
    print("\n=== 高頻中文詞組（出現次數 >= 3）===")
    high_freq_phrases = []
    for phrase, count in sorted_phrases:
        if count >= 3:
            print(f"{phrase}: {count}次")
            high_freq_phrases.append(phrase)
    
    print("\n=== 所有中文詞組（按頻率排序）===")
    for phrase, count in sorted_phrases[:50]:  # 只顯示前50個
        print(f"{phrase}: {count}次")
    
    # Generate翻譯對照表（優先Process高頻詞組）
    translation_map = {}
    
    for phrase, count in sorted_phrases:
        english = get_english_translation(phrase)
        if english:
            translation_map[phrase] = english
    
    # 輸出翻譯對照表
    print("\n=== 中英翻譯對照表 ===")
    for chinese in sorted(translation_map.keys(), key=len, reverse=True):  # 按長度排序，長詞在前
        english = translation_map[chinese]
        print(f'    "{chinese}": "{english}",')
    
    # SaveResult
    with open('/root/Dev/mindnext/hooks/chinese_phrases.txt', 'w', encoding='utf-8') as f:
        for phrase, count in sorted_phrases:
            f.write(f"{phrase}: {count}\n")
    
    with open('/root/Dev/mindnext/hooks/translation_map.txt', 'w', encoding='utf-8') as f:
        for chinese in sorted(translation_map.keys(), key=len, reverse=True):
            english = translation_map[chinese]
            f.write(f'    "{chinese}": "{english}",\n')
    
    print(f"\nResultSave到 chinese_phrases.txt 和 translation_map.txt")
    return translation_map

def get_english_translation(chinese_phrase):
    """獲取中文詞組的英文翻譯"""
    translations = {
        # 完整的Execute器類名
        "Quality Check Action Executor": "Quality Check Action Executor",
        "Memory Record Action Executor": "Memory Record Action Executor", 
        "Notification Action Executor": "Notification Action Executor",
        "Analysis Action Executor": "Analysis Action Executor",
        "Prompt Processing Action Executor": "Prompt Processing Action Executor",
        "Conditional Control Action Executor": "Conditional Control Action Executor",
        "Utility Action Executor": "Utility Action Executor",
        "AI Action Executor": "AI Action Executor",
        
        # SystemComponent
        "Three-layer Flow Engine": "Three-layer Flow Engine",
        "Flow Coordinator": "Flow Coordinator",
        "Event Processor": "Event Processor", 
        "Rule Engine": "Rule Engine",
        "Action Executor": "Action Executor",
        "Knowledge Graph": "Knowledge Graph",
        
        # Operation相關
        "Execute action": "Execute action",
        "Process action": "Process action",
        "Record action": "Record action",
        "Notification action": "Notification action",
        "Analysis action": "Analysis action",
        "Quality check": "Quality check",
        "Memory record": "Memory record",
        "Prompt processing": "Prompt processing",
        "Conditional control": "Conditional control",
        "Loop control": "Loop control",
        
        # Event相關
        "Event type": "Event type",
        "Tool name": "Tool name", 
        "File path": "File path",
        "User prompt": "User prompt",
        "Execute tool": "Execute tool",
        "Prepare to execute": "Prepare to execute",
        "Record event": "Record event",
        "Process event": "Process event",
        
        # NotificationType
        "Console notification": "Console notification",
        "System notification": "System notification",
        "Email notification": "Email notification", 
        "Simulate email": "Simulate email",
        "In actual implementation": "In actual implementation",
        
        # CheckType
        "Security scan": "Security scan",
        "Dependency check": "Dependency check", 
        "Similarity check": "Similarity check",
        "Code formatting": "Code formatting",
        "Static check": "Static check",
        "Health check": "Health check",
        
        # AnalyzeType
        "Basic analysis": "Basic analysis",
        "Trend analysis": "Trend analysis",
        "Pattern analysis": "Pattern analysis", 
        "Performance analysis": "Performance analysis",
        "Usage analysis": "Usage analysis",
        "Impact analysis": "Impact analysis",
        "Code analysis": "Code analysis",
        
        # 控制邏輯
        "Rate limit": "Rate limit",
        "Circuit breaker": "Circuit breaker",
        "Conditional logic": "Conditional logic",
        "Loop logic": "Loop logic",
        "Evaluate condition": "Evaluate condition",
        
        # 常見Action
        "Generate summary": "Generate summary",
        "Extract keywords": "Extract keywords", 
        "Classify text": "Classify text",
        "Sentiment analysis": "Sentiment analysis",
        "Generate text": "Generate text",
        "Translate text": "Translate text",
        "Effort estimation": "Effort estimation",
        "Pattern detection": "Pattern detection",
        "Suggestion generation": "Suggestion generation",
        "Code review": "Code review",
        
        # Status描述
        "Unknown operation": "Unknown operation",
        "No file operations": "No file operations", 
        "Involved files": "Involved files",
        "files": " files",
        "Unsupported": "Unsupported",
        "Unsupported": "Unsupported", 
        "Execution time": "Execution time",
        "Processing time": "Processing time",
        "Start time": "Start time",
        
        # 基本詞彙
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
        "Test": "Test",
        "Initialize": "Initialize",
        "Configuration": "Configuration",
        "Settings": "Settings",
        "Parameters": "Parameters",
        "Options": "Options",
        "Result": "Result",
        "Data": "Data",
        "Data": "Data",
        "Information": "Information",
        "Message": "Message",
        "Event": "Event",
        "Status": "Status",
        "Type": "Type",
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
        "File": "File",
        "File": "File",
        "Directory": "Directory", 
        "Path": "Path",
        "Format": "Format",
        "Content": "Content",
        "Size": "Size",
        "Time": "Time",
        "Date": "Date",
        "Error": "Error",
        "Exception": "Exception",
        "Failed": "Failed",
        "Success": "Success",
        "Complete": "Complete", 
        "Interrupted": "Interrupted",
        "Pause": "Pause",
        "Continue": "Continue",
        "Quality": "Quality",
        "Quality": "Quality",
        "Detection": "Detection",
        "Score": "Score",
        "Level": "Level",
        "Notification": "Notification",
        "Reminder": "Reminder",
        "Warning": "Warning",
        "Message": "Message",
        "Email": "Email",
        "Send": "Send",
        "Receive": "Receive",
        "Memory": "Memory",
        "Cache": "Cache",
        "Storage": "Storage",
        "Storage": "Storage",
        "Temporary": "Temporary",
        "Permanent": "Permanent",
        "Session": "Session", 
        "Conversation": "Conversation",
        "User": "User",
        "User": "User",
        "Client": "Client",
        "Administrator": "Administrator",
        "Permission": "Permission",
        "Authentication": "Authentication",
        "Authorization": "Authorization",
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
        "Start": "Start",
        "Stop": "Stop",
        "Running": "Running",
        "Executing": "Executing", 
        "Waiting": "Waiting",
        "Ready": "Ready",
        "In progress": "In progress",
        "System": "System",
        "Default": "Default",
        "Default": "Default"
    }
    
    return translations.get(chinese_phrase, "")

if __name__ == "__main__":
    scan_chinese_phrases()