# 代碼摘要生成器

這個工具可以掃描專案目錄，生成代碼文件的摘要，並將結果保存為樹狀結構的JSON文件。它使用AI模型（如OpenAI的GPT）來分析和總結代碼。

## 功能特點

- 自動掃描專案目錄中的文本文件
- 忽略.gitignore中指定的文件和目錄
- 使用AI模型生成每個文件的摘要
- 將結果保存為樹狀結構的JSON文件
- 支持使用YAML配置文件或環境變數進行設定

## 安裝

1. 克隆此倉庫：

```bash
git clone https://github.com/yourusername/code-summarizer.git
cd code-summarizer
```

2. 安裝依賴：

```bash
pip install -r requirements.txt
```

## 配置

### 重要：必須設置 API 密鑰

您必須設置 OpenAI API 密鑰才能使用此工具。有兩種方式設置：

### 方式一：YAML配置文件

1. 第一次運行程式時，會自動生成 `config.yaml.example` 範例配置檔案
2. 將 `config.yaml.example` 複製為 `config.yaml`：

```bash
cp config.yaml.example config.yaml
```

3. 編輯 `config.yaml` 文件，填入你的API密鑰和其他設定：

```yaml
api_key: "your-api-key-here"  # 必須設置
model: "gpt-3.5-turbo"
api_base: "https://api.openai.com/v1"
# 其他配置項...
```

### 方式二：環境變數

1. 將 `.env.example` 複製為 `.env`：

```bash
cp .env.example .env
```

2. 編輯 `.env` 文件，填入你的API密鑰和其他設定：

```
OPENAI_API_KEY=your-api-key-here  # 必須設置
MODEL_NAME=gpt-3.5-turbo
# 其他配置項...
```

## 配置優先順序

程式按照以下優先順序讀取配置：
1. `config.yaml` 文件（如果存在）
2. 環境變數（`.env` 文件或系統環境變數）
3. 默認值

## 使用方法

設置API密鑰後，運行以下命令開始掃描專案並生成摘要：

```bash
python code_summarizer.py
```

如果遇到配置錯誤，程序會提示您需要進行的操作。

程式將會：
1. 掃描當前目錄中的所有文本文件（排除 .gitignore 中指定的文件）
2. 為每個文件生成摘要
3. 將結果保存到 `code_summary_tree.json` 文件中

## 輸出結果

輸出的JSON文件將包含樹狀結構的代碼摘要，例如：

```json
{
  "src": {
    "main.py": "這個文件包含應用程序的入口點...",
    "utils": {
      "helpers.py": "提供了多種輔助函數，包括..."
    }
  }
}
```

## 可視化樹狀結構

生成JSON摘要後，您可以使用 `tree_visualizer.py` 將JSON文件轉換為更易讀的樹狀結構文本文件：

```bash
python tree_visualizer.py
```

這個腳本會讀取 `code_summary_tree.json` 文件，並生成 `code_summary_tree.txt` 文件，內容如下：

```
代碼摘要樹狀結構
==============

├── code_summarizer.py    這個文件包含代碼摘要生成器的主要實現...
├── README.md    專案說明文檔...
├── requirements.txt    專案依賴項列表...
└── tree_visualizer.py    將JSON樹狀結構轉換為文本格式的工具...
```

樹狀結構文件提供了更清晰的專案結構視圖，特別適合與團隊成員分享或快速瀏覽整個專案的代碼摘要。

## 疑難排解

如果遇到 "API密鑰未設置" 錯誤，請確保：
- 您已經在 `config.yaml` 文件中設置了 `api_key` 值
- 或者在 `.env` 文件中設置了 `OPENAI_API_KEY` 環境變數

如果遇到 YAML 解析錯誤，請檢查您的 `config.yaml` 文件格式是否正確。

## 注意事項

- 配置文件和 .env 文件包含API密鑰，已添加到 .gitignore 中，不會被上傳至版本控制系統
- 確保你有足夠的API使用額度，尤其是處理大型專案時
- 處理大型專案可能需要較長時間，請耐心等待 