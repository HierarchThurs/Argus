# 校园网钓鱼邮件智能过滤系统 - 实现计划

## 项目概述
基于机器学习的校园网钓鱼邮件智能过滤系统，前后端分离架构（FastAPI +
React+Vite）。
     
## 用户确认的需求
- **注册方式**：管理员批量导入用户数据，无需自主注册
- **前端架构**：从Class组件迁移到Function组件+Hooks
- **高并发策略**：简单方案优先（优化数据库查询和连接池，不引入Redis/Celery）
- **学校邮箱配置**：预留接口，稍后配置
     
---
     
## 阶段一：后端基础设施完善
     
### 1.1 JWT认证中间件实现
**新建文件**：
- `backend/app/middleware/__init__.py`
- `backend/app/middleware/jwt_auth.py` - JWT令牌生成、验证、刷新
     
**修改文件**：
- `backend/app/core/container.py` - 注入JWT中间件
- `backend/app/routers/auth_router.py` - 使用JWT保护API
- `backend/app/routers/email_router.py` - 添加认证依赖
- `backend/app/routers/email_account_router.py` - 添加认证依赖
- `backend/app/services/auth_service.py` - 返回JWT令牌
     
### 1.2 数据库表结构更新
**修改文件**：
- `backend/app/entities/user_entity.py` - 添加last_login_at、status字段
- `backend/scripts/init_db.py` - 更新初始化脚本
     
### 1.3 IMAP同步修复与优化
**修改文件**：
- `backend/app/utils/imap/imap_client.py` - 修复连接问题
- `backend/app/services/email_account_service.py` - 优化同步逻辑（增量20封）
     
---
     
## 阶段二：钓鱼检测接口完善
     
### 2.1 ML接口规范扩展
**修改文件**：
- `backend/app/utils/phishing/phishing_detector_interface.py` -
添加特征提取、模型热加载接口
     
**新建文件**：
- `backend/app/utils/phishing/feature_extractor.py` - 特征提取器（供ML模型使用）
- `backend/app/utils/phishing/ml_phishing_detector.py` - ML检测器模板（预留）
     
### 2.2 高危链接验证接口
**新建文件**：
- `backend/app/routers/phishing_router.py` - 学号验证API
     
**修改文件**：
- `backend/app/core/app_factory.py` - 注册新路由
     
---
     
## 阶段三：前端现代化重构
     
### 3.1 项目结构调整
**新建目录和文件**：
     ```
     frontend/src/
     ├── hooks/
     │   ├── useAuth.js              # 认证状态Hook
     │   ├── useEmails.js            # 邮件数据Hook
     │   └── useAccounts.js          # 邮箱账户Hook
     ├── contexts/
     │   └── AuthContext.jsx         # 认证上下文
     └── styles/
         ├── variables.css           # CSS变量定义
         └── animations.css          # 动画定义
     ```
     
### 3.2 页面组件重构（Class → Function + Hooks）
**重构文件**：
- `frontend/src/App.jsx` - 使用AuthContext
- `frontend/src/pages/LoginPage.jsx` - 重构为函数组件
- `frontend/src/pages/MailClientPage.jsx` - 拆分为多个子组件
     
**新建组件**：
     ```
     frontend/src/pages/MailClientPage/
     ├── index.jsx                   # 主组件
     ├── Sidebar.jsx                 # 侧边栏
     ├── EmailList.jsx               # 邮件列表
     ├── EmailDetail.jsx             # 邮件详情
     ├── ComposeModal.jsx            # 写邮件模态框
     ├── AddEmailModal.jsx           # 添加邮箱模态框
     └── PhishingProtectedContent.jsx # 钓鱼保护内容（修复学号验证）
     ```
     
### 3.3 UI现代化升级
**修改文件**：
- `frontend/src/index.css` - 更新设计令牌
- `frontend/src/pages/MailClientPage.css` - 现代化样式
- `frontend/src/components/Toast.css` - 动画效果
- `frontend/src/components/ConfirmDialog.css` - 动画效果
     
### 3.4 高危链接学号验证修复
**关键修改**：
- `PhishingProtectedContent.jsx` 第942行：将"学校名称"改为"学号"验证
- 调用后端 `/api/phishing/verify-link` 接口验证学号
     
---
     
## 阶段四：邮件功能完善
     
### 4.1 发送邮件功能实现
**修改文件**：
- `backend/app/services/email_service.py` - 实现send_email方法
- `backend/app/routers/email_router.py` - 完善发送接口
     
### 4.2 邮件操作API
**修改文件**：
- `backend/app/crud/email_crud.py` - 添加mark_as_unread、star、delete方法
- `backend/app/services/email_service.py` - 添加对应服务方法
- `backend/app/routers/email_router.py` - 添加API端点
     
---
     
## 阶段五：性能优化
     
### 5.1 数据库查询优化
**修改文件**：
- `backend/app/crud/email_crud.py` - 游标分页替代OFFSET
- `backend/app/entities/` - 添加复合索引
     
### 5.2 连接池优化
**修改文件**：
- `backend/app/core/database.py` - 优化连接池参数
- `backend/app/core/config.py` - 添加连接池配置项
     
---
     
## 关键文件清单
     
### 后端核心文件
| 文件路径 | 操作 | 说明 |
|---------|------|------|
| `backend/app/middleware/jwt_auth.py` | 新建 | JWT认证中间件 |
| `backend/app/services/auth_service.py` | 修改 | JWT令牌生成 |
| `backend/app/services/email_account_service.py` | 修改 | IMAP同步修复 |
| `backend/app/services/email_service.py` | 修改 | 发送邮件实现 |
| `backend/app/utils/phishing/phishing_detector_interface.py` | 修改 | ML接口扩展 |
| `backend/app/utils/phishing/feature_extractor.py` | 新建 | 特征提取器 |
| `backend/app/routers/phishing_router.py` | 新建 | 学号验证API |
| `backend/app/core/container.py` | 修改 | 依赖注入更新 |
     
### 前端核心文件
| 文件路径 | 操作 | 说明 |
|---------|------|------|
| `frontend/src/contexts/AuthContext.jsx` | 新建 | 认证上下文 |
| `frontend/src/hooks/useAuth.js` | 新建 | 认证Hook |
| `frontend/src/hooks/useEmails.js` | 新建 | 邮件Hook |
| `frontend/src/hooks/useAccounts.js` | 新建 | 账户Hook |
| `frontend/src/App.jsx` | 修改 | 使用Context |
| `frontend/src/pages/LoginPage.jsx` | 重构 | 函数组件 |
| `frontend/src/pages/MailClientPage/` | 新建目录 | 拆分子组件 |
| `frontend/src/services/PhishingService.js` | 新建 | 学号验证服务 |
     
---
     
## API端点设计
     
### 认证模块
```
     POST /api/auth/login           # 登录（返回JWT）
     POST /api/auth/refresh         # 刷新令牌
     POST /api/auth/logout          # 登出
     GET  /api/auth/me              # 获取当前用户
     ```
     
### 邮箱账户模块
     ```
     GET    /api/accounts           # 获取账户列表
     POST   /api/accounts           # 添加账户
     DELETE /api/accounts/{id}      # 删除账户
     POST   /api/accounts/{id}/sync # 同步邮件
     POST   /api/accounts/test      # 测试连接
     ```
     
### 邮件模块
```
     GET    /api/emails             # 邮件列表（支持聚合/筛选）
     GET    /api/emails/{id}        # 邮件详情
     POST   /api/emails/send        # 发送邮件
     POST   /api/emails/{id}/read   # 标记已读
     POST   /api/emails/{id}/unread # 标记未读
     POST   /api/emails/{id}/star   # 标星
     DELETE /api/emails/{id}        # 删除
     ```
     
### 钓鱼检测模块
```
     POST /api/phishing/verify-link # 学号验证后获取链接
     GET  /api/phishing/stats       # 检测统计
```
     
---
     
## 钓鱼检测ML接口规范
     
```python
     class PhishingDetectorInterface(ABC):
         """钓鱼检测器接口。"""
     
         @abstractmethod
         async def detect(
             self,
             subject: Optional[str],
             sender: str,
             content_text: Optional[str],
             content_html: Optional[str],
             headers: Optional[Dict[str, str]] = None,  # 新增
         ) -> PhishingResult:
             """单封邮件检测。"""
             pass
     
         @abstractmethod
         async def batch_detect(self, emails: List[Dict]) -> List[PhishingResult]:
             """批量检测。"""
             pass
     
         @abstractmethod
         def get_model_info(self) -> Dict[str, Any]:
             """获取模型信息。"""
             pass
     
         @abstractmethod
         async def reload_model(self) -> bool:
             """热加载模型（无需重启服务）。"""
             pass
     ```
     
---
     
## 实施顺序
     
1. **第一步**：后端JWT认证 + 路由保护
2. **第二步**：IMAP同步修复
3. **第三步**：前端AuthContext + Hooks基础设施
4. **第四步**：MailClientPage组件拆分重构
5. **第五步**：高危链接学号验证修复
6. **第六步**：发送邮件功能
7. **第七步**：UI现代化 + 动画效果
8. **第八步**：ML接口规范完善
9. **第九步**：性能优化
10. **第十步**：测试验证
     
---
     
## 测试计划
     
1. **后端API测试**：使用pytest + httpx
2. **IMAP同步测试**：使用现有test_email_sync.py框架
3. **前端组件测试**：确保页面正常加载和交互
4. **端到端测试**：手动测试完整流程
     
---
     
## 注意事项
     
1. 每个代码文件不超过500行
2. 使用谷歌风格中文注释
3. 遵循FastAPI CRUD标准
4. 可复用代码封装为工具类
5. 代码质量参考Gmail网页版