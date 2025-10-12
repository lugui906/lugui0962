# 将网站部署到GitHub Pages的完整指南

## 步骤1：安装Git

1. 访问[Git官网](https://git-scm.com/download/win)下载Windows版Git安装程序
2. 运行安装程序，按照默认设置完成安装
3. 安装完成后，打开命令提示符或PowerShell验证安装：
   ```
   git --version
   ```

## 步骤2：在GitHub上创建仓库

1. 访问[GitHub](https://github.com/)并登录您的账号
2. 点击右上角的"+"号，选择"New repository"
3. 输入仓库名称（例如：`c-cleaner-website`）
4. 选择"Public"选项，让所有人都能访问您的GitHub Pages
5. 点击"Create repository"

## 步骤3：将您的网站推送到GitHub

1. 打开命令提示符，导航到您的网站目录：
   ```
   cd d:\desktop\app\webapp\download
   ```
2. 初始化Git仓库：
   ```
   git init
   ```
3. 创建一个`.gitignore`文件（可选但推荐），添加不需要版本控制的文件：
   ```
   echo "node_modules/\ndist/\n.env\n.DS_Store\n*.log" > .gitignore
   ```
4. 添加所有文件到暂存区：
   ```
   git add .
   ```
5. 提交更改：
   ```
   git commit -m "Initial commit"
   ```
6. 连接到GitHub仓库：
   ```
   git remote add origin https://github.com/您的用户名/您的仓库名.git
   ```
7. 推送到GitHub：
   ```
   git push -u origin master
   ```

## 步骤4：启用GitHub Pages

1. 在GitHub上打开您的仓库
2. 点击"Settings"选项卡
3. 在左侧菜单中点击"Pages"
4. 在"Source"部分，从"None"下拉菜单中选择"main"分支
5. 点击"Save"
6. 稍等几分钟，GitHub Pages会为您的网站生成一个URL（格式为：`https://您的用户名.github.io/您的仓库名/`）

## 额外提示

- 您可以通过编辑GitHub仓库中的`CNAME`文件来设置自定义域名
- 如果网站有更新，只需在本地执行`git add .`、`git commit -m "Update"`和`git push`即可更新GitHub Pages
- 如果您遇到任何问题，可以在GitHub Pages的设置页面查看构建日志以进行排查