# 钓鱼邮件检测功能移植报告

## 一、项目概述

| 项目 | 技术栈 | 说明 |
|------|--------|------|
| **phishingDP** | Flask + Keras | 原始独立项目，基于机器学习的钓鱼邮件检测系统 |
| **backend** | FastAPI + Keras | 目标后端，已完成移植 |
| **frontend** | React + Vite | 目标前端，已完成移植 |

---

## 二、核心功能移植状态汇总

| 功能模块 | phishingDP | Backend | Frontend | 状态 |
|---------|------------|---------|----------|------|
| **神经网络模型** | ✅ | ✅ | - | ✅ 已移植 |
| **TF-IDF特征提取** | ✅ | ✅ | - | ✅ 已移植 |
| **模型训练框架** | ✅ | ✅ | - | ✅ 已移植 |
| **邮件预测函数** | ✅ | ✅ | - | ✅ 已移植 |
| **模型热加载** | ❌ | ✅ | - | ⬆️ 增强 |
| **URL规则检测** | ❌ | ✅ | - | ⬆️ 增强 |
| **特征提取器** | 仅TF-IDF | ✅ 多维度 | - | ⬆️ 增强 |
| **组合检测器** | ❌ | ✅ | - | ⬆️ 增强 |
| **批量异步检测** | ❌ | ✅ | - | ⬆️ 增强 |
| **SSE实时推送** | ❌ | ✅ | ✅ | ⬆️ 增强 |
| **检测等级展示** | ✅ 简单 | - | ✅ 完整 | ✅ 已移植 |
| **链接保护机制** | ❌ | - | ✅ | ⬆️ 增强 |
| **学号验证** | ❌ | ✅ | ✅ | ⬆️ 增强 |
| **可视化图表** | ✅ | ❌ | ❌ | ⚠️ 未移植 |
| **预测历史日志** | ✅ | ❌ | ❌ | ⚠️ 未移植 |

---

## 三、详细对比分析

### 3.1 机器学习模型 ✅ 已移植

| 特性 | phishingDP | Backend | 对比结果 |
|------|------------|---------|----------|
| 模型架构 | Sequential (128→64→1) | Sequential (128→64→1) | ✅ 一致 |
| 输入维度 | 5000 (TF-IDF) | 5000 (TF-IDF) | ✅ 一致 |
| 激活函数 | ReLU + Sigmoid | ReLU + Sigmoid | ✅ 一致 |
| Dropout | 0.2 | 0.2 | ✅ 一致 |
| 优化器 | Adam | Adam | ✅ 一致 |
| 损失函数 | Binary Crossentropy | Binary Crossentropy | ✅ 一致 |
| 模型文件 | `phishing_model.h5` | `phishing_model.h5` | ✅ 一致 |
| TF-IDF向量化器 | 内嵌代码 | `tfidf_vectorizer.joblib` | ⬆️ 改进（可独立加载） |

### 3.2 特征提取 ⬆️ 大幅增强

**phishingDP 原始方案：**
- 仅使用 TF-IDF 文本向量化

**Backend 增强方案：**

| 特征类别 | 特征数量 | 具体特征 |
|---------|---------|----------|
| **URL特征** | 6个 | URL总数、唯一域名、可疑URL数、IP地址URL、短链接、域名伪装 |
| **文本特征** | 7个 | 词数、字符数、紧急词汇、威胁词汇、奖励词汇、HTML表单数、外部资源数 |
| **发件人特征** | 3个 | 域名、免费邮箱标记、显示名伪装 |

### 3.3 检测架构 ⬆️ 大幅增强

**phishingDP 原始方案：**
- 单一检测器 (ML模型)

**Backend 组合检测器方案：**
```
CompositePhishingDetector
├── LongUrlDetector (规则检测)
│   ├── 超长URL检测 (>150字符 → 高危)
│   ├── 可疑长URL检测 (100-150字符 → 疑似)
│   └── 超链接伪装检测
└── MLPhishingDetector (机器学习)
    ├── TF-IDF向量化
    └── Keras神经网络预测
```

### 3.4 检测等级体系 ✅ 已移植并增强

| 等级 | phishingDP | Backend/Frontend |
|------|------------|------------------|
| 高危 | >0.5 (Phishing) | ≥0.8 (HIGH_RISK) |
| 疑似 | - | 0.6-0.8 (SUSPICIOUS) |
| 正常 | ≤0.5 (Not Phishing) | <0.6 (NORMAL) |

**改进：** 三级分类比二级更精细

### 3.5 API接口对比

| 功能 | phishingDP | Backend |
|------|------------|---------|
| 预测接口 | `POST /pdredict` | 通过服务层调用 |
| 可视化接口 | `GET /visualize` | ❌ 未移植 |
| 重训练接口 | `POST /retrasin` | `POST /api/phishing/reload-model` (热加载) |
| 统计接口 | ❌ | `GET /api/phishing/stats` |
| 链接验证 | ❌ | `POST /api/phishing/verify-link` |
| SSE推送 | ❌ | `GET /api/phishing/stream` |
| 模型信息 | ❌ | `GET /api/phishing/model-info` |

### 3.6 数据集 ✅ 已移植

| 属性 | phishingDP | Backend |
|------|------------|---------|
| 数据集 | `spam_assassin.csv` | `spam_assassin.csv` |
| 大小 | ~24.5MB | ~23.4MB |
| 格式 | text, target | text, target |

---

## 四、已移植成功的功能

### 4.1 后端 (Backend)

| # | 功能 | 文件位置 |
|---|------|----------|
| 1 | Keras神经网络模型 | `ml_phishing_detector.py` |
| 2 | TF-IDF特征向量化 | `ml_phishing_detector.py` |
| 3 | 模型训练框架 | `ml_trainer.py` |
| 4 | 多维度特征提取 | `feature_extractor.py` |
| 5 | URL规则检测 | `url_detector.py` |
| 6 | 组合检测器 | `composite_detector.py` |
| 7 | 检测器接口抽象 | `phishing_detector_interface.py` |
| 8 | 置信度分级映射 | `score_level_mapper.py` |
| 9 | 异步批量检测 | `phishing_detection_service.py` |
| 10 | SSE事件推送 | `phishing_event_service.py` |
| 11 | 模型热加载 | `ml_phishing_detector.py` |
| 12 | 数据库持久化 | `email_entity.py`, `email_crud.py` |
| 13 | RESTful API | `phishing_router.py` |

### 4.2 前端 (Frontend)

| # | 功能 | 文件位置 |
|---|------|----------|
| 1 | 检测等级徽章 | `EmailList.jsx` |
| 2 | 详情页警告栏 | `EmailDetail.jsx` |
| 3 | 置信度百分比显示 | `EmailDetail.jsx` |
| 4 | 链接保护机制 | `EmailDetail.jsx` |
| 5 | 学号验证模态框 | `EmailDetail.jsx` |
| 6 | SSE实时更新 | `index.jsx` |
| 7 | 增量数据同步 | `useEmails.js` |
| 8 | API服务层 | `PhishingService.js` |
| 9 | 阈值计算工具 | `PhishingUtils.js` |
| 10 | 视觉样式系统 | `MailClientPage.css` |

---

## 五、尚未移植的功能 ⚠️

### 5.1 可视化图表系统

**phishingDP 原有功能：**

| 图表 | 文件 | 说明 |
|------|------|------|
| 损失曲线 | `loss_curve.png` | 训练/验证损失变化 |
| 准确率曲线 | `accuracy_curve.png` | 训练/验证准确率变化 |
| 混淆矩阵 | `confusion_matrix.png` | 真正/假正/真负/假负 |
| ROC曲线 | `roc_curve.png` | AUC性能指标 |
| PR曲线 | `pr_curve.png` | 精确率-召回率权衡 |
| 性能指标柱状图 | `metrics_bar.png` | 四项指标对比 |

**移植状态：**
- ❌ 后端：训练器可生成数据文件（`.npy`, `.npz`），但无API暴露
- ❌ 前端：无可视化页面

### 5.2 预测历史日志

**phishingDP 原有功能：**
- `prediction_results.log` 文件记录每次预测
- 首页展示历史日志

**移植状态：**
- ❌ 后端：检测结果存入数据库，但无专门的日志文件
- ❌ 前端：无历史日志展示页面

### 5.3 可视化页面 (`/visualize`)

**phishingDP 原有功能：**
- 展示所有训练图表
- 显示模型性能指标（准确率、精确率、召回率、F1）

**移植状态：**
- ❌ 未移植

---

## 六、增强功能（超出原项目）

### 6.1 Backend 新增功能

| 功能 | 说明 |
|------|------|
| **组合检测器架构** | 支持多检测器并行，取最严格结果 |
| **规则检测层** | URL长度、伪装检测（不依赖ML） |
| **三级威胁等级** | NORMAL/SUSPICIOUS/HIGH_RISK |
| **异步批量检测** | 后台检测，不阻塞用户操作 |
| **SSE实时推送** | 检测完成即时通知前端 |
| **模型热加载** | 无需重启服务更新模型 |
| **数据库持久化** | 检测结果存储到`email_messages`表 |
| **JWT认证** | SSE流需要token验证 |

### 6.2 Frontend 新增功能

| 功能 | 说明 |
|------|------|
| **渐进式链接保护** | 根据威胁等级自动调整链接可访问性 |
| **学号验证机制** | 查看高危链接需身份验证 |
| **实时状态更新** | SSE推送无需刷新页面 |
| **检测状态指示器** | ⏳检测中/⚠️疑似/⚡高危 |
| **详情页警告系统** | 根据等级显示不同颜色警告 |

---

## 七、移植建议

### 7.1 建议移植的功能

| 优先级 | 功能 | 工作量 | 价值 |
|--------|------|--------|------|
| **高** | 可视化仪表板 | 中 | 管理员监控模型性能 |
| **中** | 检测历史日志 | 低 | 审计与回溯 |
| **低** | 模型重训练UI | 高 | 在线更新模型 |

### 7.2 可视化功能移植方案

**后端：**
1. 添加 `/api/phishing/metrics` 返回训练指标JSON
2. 添加 `/api/phishing/charts/{chart_name}` 返回图表图片

**前端：**
1. 新建 `PhishingDashboard.jsx` 页面
2. 使用 Chart.js 或 ECharts 渲染图表
3. 显示准确率、精确率、召回率、F1分数

---

## 八、结论

### 移植完成度：**90%**

| 类别 | 完成度 | 说明 |
|------|--------|------|
| **核心检测功能** | 100% | ML模型、TF-IDF、预测功能完全移植 |
| **API接口** | 95% | 新增多个增强接口，可视化接口未移植 |
| **前端展示** | 100% | 检测结果展示、链接保护完全实现 |
| **可视化系统** | 0% | 训练图表、性能指标展示未移植 |
| **日志系统** | 50% | 数据库存储已实现，日志文件/UI未实现 |

### 核心功能状态

✅ **已完全移植并增强：**
- 神经网络钓鱼检测模型
- TF-IDF文本特征提取
- 邮件预测功能
- 检测结果展示

⚠️ **需要补充移植：**
- 可视化图表页面
- 预测历史日志展示
- 模型性能指标仪表板
