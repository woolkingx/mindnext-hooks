"""
基礎品質檢查器
定義所有品質檢查器的共同介面和數據結構
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from pathlib import Path
import os
import hashlib
import json

@dataclass
class QualityIssue:
    """品質問題數據結構"""
    severity: str  # 'info', 'warning', 'error'
    message: str
    line: Optional[int] = None
    column: Optional[int] = None
    rule: Optional[str] = None
    fixable: bool = False
    file_path: Optional[str] = None

@dataclass 
class CheckResult:
    """檢查結果數據結構"""
    file_path: str
    file_type: str
    issues: List[QualityIssue]
    fixed_issues: List[str] = None
    execution_time: float = 0.0
    cache_hit: bool = False
    
    @property
    def has_errors(self) -> bool:
        return any(issue.severity == "error" for issue in self.issues)
    
    @property
    def has_warnings(self) -> bool:
        return any(issue.severity == "warning" for issue in self.issues)
    
    @property
    def error_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "error")
    
    @property
    def warning_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "warning")
    
    @property
    def info_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "info")

class BaseQualityChecker(ABC):
    """品質檢查器基礎類別"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.cache_enabled = self.config.get("cache_enabled", True)
        self.debug = self.config.get("debug", False)
        
        # 設定快取目錄
        hooks_dir = Path(__file__).parent.parent
        self.cache_dir = hooks_dir / ".cache" / self.get_checker_name()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    @abstractmethod
    def get_checker_name(self) -> str:
        """返回檢查器名稱"""
        pass
    
    @abstractmethod
    def get_supported_extensions(self) -> List[str]:
        """返回支援的檔案副檔名列表"""
        pass
    
    @abstractmethod
    def check_file(self, file_path: str) -> CheckResult:
        """檢查檔案品質"""
        pass
    
    def can_handle(self, file_path: str) -> bool:
        """檢查是否可以處理此檔案"""
        ext = Path(file_path).suffix.lower()
        return ext in self.get_supported_extensions()
    
    def _get_cache_key(self, file_path: str) -> str:
        """生成快取鍵值"""
        return hashlib.md5(file_path.encode()).hexdigest()
    
    def _load_cache(self, file_path: str) -> Optional[CheckResult]:
        """載入快取結果"""
        if not self.cache_enabled:
            return None
            
        cache_file = self.cache_dir / f"{self._get_cache_key(file_path)}.json"
        
        if not cache_file.exists():
            return None
        
        try:
            # 檢查檔案修改時間
            file_mtime = os.path.getmtime(file_path)
            cache_mtime = os.path.getmtime(cache_file)
            
            if file_mtime > cache_mtime:
                return None  # 檔案已修改，快取失效
            
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # 重建 CheckResult 對象
            issues = [QualityIssue(**issue) for issue in cache_data["issues"]]
            result = CheckResult(
                file_path=cache_data["file_path"],
                file_type=cache_data["file_type"],
                issues=issues,
                fixed_issues=cache_data.get("fixed_issues", []),
                execution_time=cache_data.get("execution_time", 0.0),
                cache_hit=True
            )
            
            if self.debug:
                print(f"🗄️ {self.get_checker_name()}: 快取命中 {Path(file_path).name}")
            
            return result
            
        except Exception as e:
            if self.debug:
                print(f"⚠️ {self.get_checker_name()}: 快取讀取失敗 {e}")
            return None
    
    def _save_cache(self, result: CheckResult):
        """儲存結果到快取"""
        if not self.cache_enabled:
            return
        
        cache_file = self.cache_dir / f"{self._get_cache_key(result.file_path)}.json"
        
        try:
            cache_data = {
                "file_path": result.file_path,
                "file_type": result.file_type,
                "issues": [issue.__dict__ for issue in result.issues],
                "fixed_issues": result.fixed_issues or [],
                "execution_time": result.execution_time
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
                
            if self.debug:
                print(f"💾 {self.get_checker_name()}: 快取已儲存")
                
        except Exception as e:
            if self.debug:
                print(f"⚠️ {self.get_checker_name()}: 快取儲存失敗 {e}")
    
    def _read_file_content(self, file_path: str) -> tuple[str, List[str]]:
        """讀取檔案內容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()
            return content, lines
        except UnicodeDecodeError:
            # 嘗試其他編碼
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    content = f.read()
                    lines = content.splitlines()
                return content, lines
            except:
                raise Exception("無法讀取檔案，編碼問題")
        except Exception as e:
            raise Exception(f"檔案讀取失敗: {e}")
    
    def format_result(self, result: CheckResult, show_details: bool = True) -> str:
        """格式化檢查結果"""
        if not result.issues:
            cache_info = " (快取)" if result.cache_hit else ""
            return f"✅ {self.get_checker_name()}: {Path(result.file_path).name} 品質檢查通過{cache_info}"
        
        output = [f"📋 {self.get_checker_name()}: {Path(result.file_path).name}"]
        
        if result.cache_hit:
            output[0] += " (快取結果)"
        
        # 統計資訊
        stats = []
        if result.error_count > 0:
            stats.append(f"❌ {result.error_count} 錯誤")
        if result.warning_count > 0:
            stats.append(f"⚠️ {result.warning_count} 警告")
        if result.info_count > 0:
            stats.append(f"💡 {result.info_count} 建議")
            
        if stats:
            output.append("   " + " | ".join(stats))
        
        if not show_details:
            return "\n".join(output)
        
        # 詳細錯誤資訊
        errors = [i for i in result.issues if i.severity == "error"]
        warnings = [i for i in result.issues if i.severity == "warning"]
        infos = [i for i in result.issues if i.severity == "info"]
        
        if errors:
            output.append("   ❌ 錯誤:")
            for issue in errors:
                line_info = f":{issue.line}" if issue.line else ""
                rule_info = f" [{issue.rule}]" if issue.rule else ""
                output.append(f"      • {issue.message}{line_info}{rule_info}")
        
        if warnings:
            output.append("   ⚠️ 警告:")
            for issue in warnings:
                line_info = f":{issue.line}" if issue.line else ""
                rule_info = f" [{issue.rule}]" if issue.rule else ""
                output.append(f"      • {issue.message}{line_info}{rule_info}")
        
        if infos:
            output.append("   💡 建議:")
            for issue in infos:
                line_info = f":{issue.line}" if issue.line else ""
                rule_info = f" [{issue.rule}]" if issue.rule else ""
                output.append(f"      • {issue.message}{line_info}{rule_info}")
        
        if result.fixed_issues:
            output.append("   🔧 自動修復:")
            for fix in result.fixed_issues:
                output.append(f"      • {fix}")
        
        return "\n".join(output)