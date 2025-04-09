import os
import json
import yaml
from typing import List, Dict, Optional, Set
import openai
from pathlib import Path
import time
import logging
import fnmatch
from dotenv import load_dotenv

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CodeSummarizer:
    def __init__(
        self,
        config_path: str = "config.yaml",
        root_dir: str = ".",
        output_file: str = "code_summary_tree.json"
    ):
        """
        初始化代碼摘要生成器
        
        Args:
            config_path: YAML配置文件路徑
            root_dir: 要處理的根目錄
            output_file: 輸出文件路徑
        """
        # 讀取配置
        self.config = self._load_config(config_path)
        
        # 設置API參數
        self.api_key = self.config.get("api_key")
        self.model = self.config.get("model", "gpt-3.5-turbo")
        self.api_base = self.config.get("api_base", "https://api.openai.com/v1")
        self.max_retries = self.config.get("max_retries", 3)
        self.retry_delay = self.config.get("retry_delay", 5)
        self.max_tokens = self.config.get("max_tokens", 500)
        self.temperature = self.config.get("temperature", 0.3)
        
        self.root_dir = root_dir
        self.output_file = output_file
        
        # 檢查API密鑰
        if not self.api_key:
            raise ValueError("API密鑰未設置。請在config.yaml或.env文件中設置api_key或OPENAI_API_KEY。")
            
        # 創建OpenAI客戶端
        self.client = openai.OpenAI(
            api_key=self.api_key,
            base_url=self.api_base
        )
        
        # 初始化結果存儲
        self.summaries: Dict[str, str] = {}
        
        # 加載.gitignore規則
        self.ignore_patterns = self._load_gitignore()
        
    def _load_config(self, config_path: str) -> Dict:
        """
        加載YAML配置文件
        
        Args:
            config_path: 配置文件路徑
            
        Returns:
            Dict: 配置字典
        """
        # 首先嘗試從環境變量加載
        load_dotenv()
        
        config = {
            "api_key": os.environ.get("OPENAI_API_KEY"),
            "model": os.environ.get("MODEL_NAME", "gpt-3.5-turbo"),
            "api_base": os.environ.get("API_BASE", "https://api.openai.com/v1"),
            "max_retries": int(os.environ.get("MAX_RETRIES", "3")),
            "retry_delay": int(os.environ.get("RETRY_DELAY", "5")),
            "max_tokens": int(os.environ.get("MAX_TOKENS", "500")),
            "temperature": float(os.environ.get("TEMPERATURE", "0.3"))
        }
        
        # 如果有配置文件，則覆蓋環境變量配置
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    yaml_config = yaml.safe_load(f)
                    if yaml_config:
                        config.update(yaml_config)
            except Exception as e:
                logger.error(f"讀取配置文件失敗: {str(e)}")
                logger.info(f"請確保{config_path}格式正確，或使用環境變量設置配置。")
                
                # 如果配置文件存在但讀取失敗，可能是格式問題，提供範例配置
                if not os.path.exists(f"{config_path}.example"):
                    try:
                        self._create_example_config(f"{config_path}.example")
                        logger.info(f"已創建範例配置文件: {config_path}.example")
                    except Exception as ex:
                        logger.error(f"創建範例配置文件失敗: {str(ex)}")
        else:
            logger.warning(f"配置文件 {config_path} 不存在。使用環境變量或默認值。")
            # 創建示例配置文件
            try:
                self._create_example_config(f"{config_path}.example")
                logger.info(f"已創建範例配置文件: {config_path}.example")
            except Exception as ex:
                logger.error(f"創建範例配置文件失敗: {str(ex)}")
        
        return config
    
    def _create_example_config(self, file_path: str) -> None:
        """
        創建範例配置文件
        
        Args:
            file_path: 文件路徑
        """
        example_config = """# OpenAI API 配置
api_key: "your-api-key-here"
model: "gpt-3.5-turbo"
api_base: "https://api.openai.com/v1"

# 請求配置
max_retries: 3
retry_delay: 5
max_tokens: 500
temperature: 0.3

# 示例說明：將此文件複製為 config.yaml 並填入你的 API 密鑰
"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(example_config)
    
    def _load_gitignore(self) -> Set[str]:
        """
        加載.gitignore文件中的忽略規則
        
        Returns:
            Set[str]: 忽略模式集合
        """
        ignore_patterns = set()
        gitignore_path = os.path.join(self.root_dir, '.gitignore')
        
        if os.path.exists(gitignore_path):
            try:
                with open(gitignore_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            ignore_patterns.add(line)
            except Exception as e:
                logger.error(f"讀取.gitignore失敗: {str(e)}")
        
        return ignore_patterns
    
    def _should_ignore(self, path: str) -> bool:
        """
        判斷文件/目錄是否應該被忽略
        
        Args:
            path: 文件/目錄路徑
            
        Returns:
            bool: 是否應該忽略
        """
        relative_path = os.path.relpath(path, self.root_dir)
        
        # 檢查是否匹配任何忽略模式
        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(relative_path, pattern):
                return True
            if pattern.endswith('/') and relative_path.startswith(pattern[:-1]):
                return True
        
        return False
    
    def is_text_file(self, file_path: str) -> bool:
        """
        判斷文件是否為文本文件
        
        Args:
            file_path: 文件路徑
            
        Returns:
            bool: 是否為文本文件
        """
        text_extensions = {
            '.py', '.js', '.ts', '.java', '.cpp', '.h', '.cs', '.go',
            '.rb', '.php', '.swift', '.kt', '.rs', '.md', '.txt', '.json',
            '.xml', '.yaml', '.yml', '.html', '.css', '.scss', '.less'
        }
        return Path(file_path).suffix.lower() in text_extensions
    
    def read_file_content(self, file_path: str) -> Optional[str]:
        """
        讀取文件內容
        
        Args:
            file_path: 文件路徑
            
        Returns:
            str: 文件內容
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"讀取文件失敗 {file_path}: {str(e)}")
            return None
    
    def get_code_summary(self, content: str, file_path: str) -> Optional[str]:
        """
        使用OpenAI API獲取代碼摘要
        
        Args:
            content: 代碼內容
            file_path: 文件路徑
            
        Returns:
            str: 代碼摘要
        """
        prompt = f"""
        請為以下代碼文件生成簡潔的摘要。摘要應包含:
        1. 文件的主要功能
        2. 核心類和函數
        3. 重要功能點
        
        文件路徑: {file_path}
        代碼內容:
        {content}
        """
        
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "你是一個專業的代碼分析師,擅長生成簡潔的代碼摘要。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
                
                summary = response.choices[0].message.content.strip()
                if summary:  # 確保摘要不為空
                    return summary
                
                logger.warning(f"獲取到空摘要,重試中... (嘗試 {attempt + 1}/{self.max_retries})")
                time.sleep(self.retry_delay)
                
            except Exception as e:
                logger.error(f"API請求失敗: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    return None
        
        return None
    
    def process_directory(self) -> None:
        """
        處理目錄中的所有文件
        """
        for root, dirs, files in os.walk(self.root_dir):
            # 過濾目錄
            dirs[:] = [d for d in dirs if not self._should_ignore(os.path.join(root, d))]
            
            for file in files:
                file_path = os.path.join(root, file)
                if not self._should_ignore(file_path) and self.is_text_file(file_path):
                    logger.info(f"處理文件: {file_path}")
                    
                    content = self.read_file_content(file_path)
                    if content:
                        summary = self.get_code_summary(content, file_path)
                        if summary:
                            relative_path = os.path.relpath(file_path, self.root_dir)
                            self.summaries[relative_path] = summary
    
    def generate_tree_structure(self) -> Dict:
        """
        生成樹狀結構
        
        Returns:
            Dict: 樹狀結構數據
        """
        tree = {}
        
        for file_path, summary in self.summaries.items():
            parts = file_path.split(os.sep)
            current = tree
            
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            
            current[parts[-1]] = summary
        
        return tree
    
    def save_tree_to_file(self) -> None:
        """
        將樹狀結構保存到文件
        """
        tree = self.generate_tree_structure()
        
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(tree, f, ensure_ascii=False, indent=2)
        
        logger.info(f"樹狀結構已保存到: {self.output_file}")

def main():
    try:
        # 從YAML配置文件創建摘要生成器
        summarizer = CodeSummarizer(
            config_path="config.yaml",
            root_dir=".",
            output_file="code_summary_tree.json"
        )
        
        # 處理目錄
        summarizer.process_directory()
        
        # 保存結果
        summarizer.save_tree_to_file()
        
    except ValueError as e:
        logger.error(str(e))
        logger.info("請檢查您的配置文件或環境變量，確保API密鑰已正確設置。")
        logger.info("您可以：")
        logger.info("1. 創建config.yaml文件並設置您的API密鑰")
        logger.info("2. 或在.env文件中設置OPENAI_API_KEY環境變量")
        
    except Exception as e:
        logger.error(f"程序執行出錯: {str(e)}")

if __name__ == "__main__":
    main() 