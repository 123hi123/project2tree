import json
import os
from typing import Dict, Any, TextIO

class TreeVisualizer:
    def __init__(self, json_file: str, output_file: str = "code_summary_tree.txt"):
        """
        初始化樹狀結構可視化工具
        
        Args:
            json_file: JSON文件路徑
            output_file: 輸出文本文件路徑
        """
        self.json_file = json_file
        self.output_file = output_file
        
    def load_json(self) -> Dict[str, Any]:
        """
        加載JSON文件
        
        Returns:
            Dict: 樹狀結構數據
        """
        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"讀取JSON文件失敗: {str(e)}")
            return {}
    
    def _visualize_tree_recursive(self, data: Dict[str, Any], file: TextIO, prefix: str = "", is_last: bool = True) -> None:
        """
        遞歸生成樹狀結構
        
        Args:
            data: 當前節點數據
            file: 輸出文件對象
            prefix: 當前行前綴
            is_last: 是否為當前層級的最後一項
        """
        items = list(data.items())
        
        for i, (key, value) in enumerate(items):
            is_last_item = i == len(items) - 1
            
            # 生成當前行的連接符號
            connector = "└── " if is_last_item else "├── "
            
            # 如果值是字典，只顯示目錄名
            if isinstance(value, dict):
                file.write(f"{prefix}{connector}{key}/\n")
                
                # 為子項生成新的前綴
                new_prefix = prefix + ("    " if is_last_item else "│   ")
                self._visualize_tree_recursive(value, file, new_prefix)
            else:
                # 對於文件，在同一行顯示摘要
                # 將多行摘要合併成一行，保留所有內容
                summary = value.strip().replace('\n', ' | ')
                
                # 顯示文件名和完整摘要在同一行
                file.write(f"{prefix}{connector}{key}    {summary}\n")
    
    def visualize(self) -> None:
        """
        生成並保存樹狀結構可視化
        """
        data = self.load_json()
        if not data:
            print("無數據可視化")
            return
        
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                f.write("代碼摘要樹狀結構\n")
                f.write("==============\n\n")
                self._visualize_tree_recursive(data, f)
            
            print(f"樹狀結構已保存到: {self.output_file}")
        except Exception as e:
            print(f"生成樹狀結構文件失敗: {str(e)}")
    
    def print_tree(self) -> None:
        """
        直接打印樹狀結構到控制台
        """
        data = self.load_json()
        if not data:
            print("無數據可視化")
            return
        
        print("代碼摘要樹狀結構")
        print("==============\n")
        
        # 使用StringIO來捕獲輸出，然後打印到控制台
        from io import StringIO
        output = StringIO()
        self._visualize_tree_recursive(data, output)
        print(output.getvalue())

def main():
    # 默認參數
    json_file = "code_summary_tree.json"
    output_file = "code_summary_tree.txt"
    
    # 創建可視化器
    visualizer = TreeVisualizer(json_file, output_file)
    
    # 生成樹狀結構文件
    visualizer.visualize()
    
    # 也可以直接打印到控制台
    # visualizer.print_tree()

if __name__ == "__main__":
    main() 