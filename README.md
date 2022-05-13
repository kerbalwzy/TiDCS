## TiDCS

关于 www.ti.com.cn 的分布式数据抓取与自动控制系统

### 项目组成
```text
.
├── backend
├── chromeExt
├── docs
└── frontend
```

- backend/ 后端代码(Python,Flask,SocketIo)
- chromeExt/ Chrome浏览器插件代码(Javascript,ChromeExtensionApi)
- docs/ 部署与业务分析的相关文档
- frontend/ 管理后台的前端代码(Webpack,Vue)

#### backend

- 环境安装: pip install -r env.txt
- 数据库脚本: ./backend/db.sql  
- 启动脚本: ./backend/run.sh
- 启动命令: bash run.sh [start, stop]
- 项目结构:
    ```text
    .
    ├── __init__.py
    ├── config.py   # 配置文件
    ├── consts.py   # 全局变量
    ├── core.py     # 核心交互代码
    ├── db.sql      # 数据库脚本
    ├── env.txt     # 虚拟环境配置文件
    ├── http_apis   # 管理后台相关API
    ├── logs        # 日志
    ├── main.py     # 程序入口
    ├── models      # 数据模型
    ├── run.sh      # 启动脚本
    ├── test.py     # 开发时的临时功能测试脚本
    └── utils       # 工具函数
    ```

#### chromeExt

- 项目代码: chromeExt/tidcs-ext
- 已打包程序: chromeExt/tidcs-ext.crx
- 打包密钥: chromeExt/tidcs-ext.pem
- 插件安装教程: docs/chrome.adm安装使用教程.png
- 项目结构:
  ``` 
  tidcs-ext
  ├── auto-login.js   # 自动登录注入的JS代码
  ├── background.html # 插件后台页面
  ├── background.js   # 插件后台代码
  ├── libs            # 依赖包
  └── manifest.json   # 配置文件
  ```
