import React from 'react'
import EmailAccountService from '../services/EmailAccountService.js'
import EmailService from '../services/EmailService.js'
import Toast from '../components/Toast.jsx'
import ConfirmDialog from '../components/ConfirmDialog.jsx'
import './MailClientPage.css'

/**
 * 邮件客户端首页组件。
 *
 * 三栏布局：左侧邮箱列表、中间邮件列表、右侧邮件详情。
 */
export default class MailClientPage extends React.Component {
  /**
   * @param {object} props 组件属性
   */
  constructor(props) {
    super(props)
    this.state = {
      // 邮箱账户
      emailAccounts: [],
      selectedAccountId: null,
      // 邮件
      emails: [],
      selectedEmail: null,
      emailDetail: null,
      // 模态框
      showAddEmailModal: false,
      showComposeModal: false,
      // 加载状态
      isLoadingAccounts: true,
      isLoadingEmails: false,
      isLoadingDetail: false,
      isSyncing: false,
      // 添加邮箱表单
      addEmailForm: {
        emailAddress: '',
        emailType: 'QQ',
        authPassword: '',
        imapHost: '',
        imapPort: '',
        smtpHost: '',
        smtpPort: '',
      },
      addEmailError: '',
      isAddingEmail: false,
      // 发送邮件表单
      composeForm: {
        toAddresses: '',
        subject: '',
        content: '',
      },
      isSending: false,
      composeError: '',
    }

    this.emailAccountService = EmailAccountService.createDefault()
    this.emailService = EmailService.createDefault()

    this.handleSelectAccount = this.handleSelectAccount.bind(this)
    this.handleSelectEmail = this.handleSelectEmail.bind(this)
    this.handleSyncEmails = this.handleSyncEmails.bind(this)
    this.handleAddEmail = this.handleAddEmail.bind(this)
    this.handleDeleteAccount = this.handleDeleteAccount.bind(this)
    this.handleSendEmail = this.handleSendEmail.bind(this)
  }

  /**
   * 组件挂载后加载数据。
   */
  async componentDidMount() {
    await this.loadEmailAccounts()
  }

  /**
   * 加载邮箱账户列表。
   */
  async loadEmailAccounts() {
    this.setState({ isLoadingAccounts: true })
    try {
      const accounts = await this.emailAccountService.getAccounts()
      this.setState({ emailAccounts: accounts, isLoadingAccounts: false })

      // 如果有账户，加载邮件列表
      if (accounts.length > 0) {
        await this.loadEmails(null)
      }
    } catch (error) {
      console.error('加载邮箱账户失败:', error)
      Toast.error('加载邮箱账户失败，请刷新页面重试')
      this.setState({ isLoadingAccounts: false })
    }
  }

  /**
   * 加载邮件列表。
   * @param {number | null} accountId 邮箱账户ID，null表示聚合所有邮箱
   */
  async loadEmails(accountId) {
    this.setState({ isLoadingEmails: true, selectedAccountId: accountId })
    try {
      const emails = await this.emailService.getEmails(accountId)
      this.setState({ emails, isLoadingEmails: false })
    } catch (error) {
      console.error('加载邮件列表失败:', error)
      this.setState({ isLoadingEmails: false })
    }
  }

  /**
   * 加载邮件详情。
   * @param {number} emailId 邮件ID
   */
  async loadEmailDetail(emailId) {
    this.setState({ isLoadingDetail: true })
    try {
      const detail = await this.emailService.getEmailDetail(emailId)
      this.setState({ emailDetail: detail, isLoadingDetail: false })
    } catch (error) {
      console.error('加载邮件详情失败:', error)
      this.setState({ isLoadingDetail: false })
    }
  }

  /**
   * 处理选择邮箱账户。
   * @param {number | null} accountId 邮箱账户ID
   */
  handleSelectAccount(accountId) {
    this.setState({ selectedEmail: null, emailDetail: null })
    this.loadEmails(accountId)
  }

  /**
   * 处理选择邮件。
   * @param {object} email 邮件对象
   */
  handleSelectEmail(email) {
    this.setState({ selectedEmail: email })
    this.loadEmailDetail(email.id)
  }

  /**
   * 处理同步邮件。
   * @param {number} accountId 邮箱账户ID
   */
  async handleSyncEmails(accountId) {
    this.setState({ isSyncing: true })
    try {
      const result = await this.emailAccountService.syncEmails(accountId)
      await this.loadEmails(this.state.selectedAccountId)
      if (result.synced_count > 0) {
        Toast.success(`同步成功，获取${result.synced_count}封新邮件`)
      } else {
        Toast.info('同步完成，暂无新邮件')
      }
    } catch (error) {
      console.error('同步邮件失败:', error)
      Toast.error('同步邮件失败，请检查邮箱配置')
    } finally {
      this.setState({ isSyncing: false })
    }
  }

  /**
   * 处理添加邮箱。
   * @param {React.FormEvent} event 表单事件
   */
  async handleAddEmail(event) {
    event.preventDefault()
    const { addEmailForm } = this.state

    if (!addEmailForm.emailAddress || !addEmailForm.authPassword) {
      this.setState({ addEmailError: '请填写邮箱地址和授权密码。' })
      return
    }

    this.setState({ isAddingEmail: true, addEmailError: '' })

    try {
      const result = await this.emailAccountService.addAccount({
        email_address: addEmailForm.emailAddress,
        email_type: addEmailForm.emailType,
        auth_password: addEmailForm.authPassword,
        imap_host: addEmailForm.imapHost || undefined,
        imap_port: addEmailForm.imapPort ? parseInt(addEmailForm.imapPort) : undefined,
        smtp_host: addEmailForm.smtpHost || undefined,
        smtp_port: addEmailForm.smtpPort ? parseInt(addEmailForm.smtpPort) : undefined,
      })

      if (result.success) {
        this.setState({
          showAddEmailModal: false,
          addEmailForm: {
            emailAddress: '',
            emailType: 'QQ',
            authPassword: '',
            imapHost: '',
            imapPort: '',
            smtpHost: '',
            smtpPort: '',
          },
        })
        Toast.success('邮箱添加成功')
        await this.loadEmailAccounts()
        // 自动同步新添加的邮箱
        if (result.account_id) {
          await this.handleSyncEmails(result.account_id)
        }
      } else {
        this.setState({ addEmailError: result.message || '添加失败。' })
      }
    } catch (error) {
      this.setState({ addEmailError: error.message || '添加失败。' })
    } finally {
      this.setState({ isAddingEmail: false })
    }
  }

  /**
   * 处理删除邮箱账户。
   * @param {number} accountId 邮箱账户ID
   * @param {string} emailAddress 邮箱地址
   */
  async handleDeleteAccount(accountId, emailAddress) {
    const confirmed = await ConfirmDialog.confirmDelete(emailAddress || '此邮箱账户')
    if (!confirmed) {
      return
    }

    try {
      await this.emailAccountService.deleteAccount(accountId)
      Toast.success('邮箱账户已删除')
      await this.loadEmailAccounts()
    } catch (error) {
      console.error('删除邮箱失败:', error)
      Toast.error('删除邮箱失败，请稍后重试')
    }
  }

  /**
   * 处理发送邮件。
   * @param {React.FormEvent} event 表单事件
   */
  async handleSendEmail(event) {
    event.preventDefault()
    const { composeForm, emailAccounts } = this.state

    if (!composeForm.toAddresses || !composeForm.subject || !composeForm.content) {
      this.setState({ composeError: '请填写完整的邮件信息。' })
      return
    }

    if (emailAccounts.length === 0) {
      this.setState({ composeError: '请先添加邮箱账户。' })
      return
    }

    this.setState({ isSending: true, composeError: '' })

    try {
      const result = await this.emailService.sendEmail({
        email_account_id: emailAccounts[0].id,
        to_addresses: composeForm.toAddresses.split(',').map((s) => s.trim()),
        subject: composeForm.subject,
        content: composeForm.content,
      })

      if (result.success) {
        this.setState({
          showComposeModal: false,
          composeForm: { toAddresses: '', subject: '', content: '' },
        })
        Toast.success('邮件发送成功')
      } else {
        this.setState({ composeError: result.message || '发送失败。' })
      }
    } catch (error) {
      this.setState({ composeError: error.message || '发送失败。' })
    } finally {
      this.setState({ isSending: false })
    }
  }

  /**
   * 渲染左侧边栏。
   * @returns {JSX.Element} 侧边栏
   */
  renderSidebar() {
    const { emailAccounts, selectedAccountId, isLoadingAccounts, isSyncing } = this.state
    const { user, onLogout } = this.props

    return (
      <aside className="mail-sidebar">
        <div className="sidebar-header">
          <div className="user-info">
            <div className="user-avatar">{user?.displayName?.[0] || 'U'}</div>
            <div className="user-details">
              <span className="user-name">{user?.displayName || '用户'}</span>
              <span className="user-id">{user?.studentId}</span>
            </div>
          </div>
          <button className="btn-logout" onClick={onLogout} title="退出登录">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9" />
            </svg>
          </button>
        </div>

        <div className="sidebar-actions">
          <button
            className="btn-primary"
            onClick={() => this.setState({ showComposeModal: true })}
          >
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            写邮件
          </button>
        </div>

        <nav className="account-list">
          <div className="account-list-header">
            <span>邮箱账户</span>
            <button
              className="btn-icon"
              onClick={() => this.setState({ showAddEmailModal: true })}
              title="添加邮箱"
            >
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
              </svg>
            </button>
          </div>

          {isLoadingAccounts ? (
            <div className="loading-placeholder">加载中...</div>
          ) : (
            <>
              <button
                className={`account-item ${selectedAccountId === null ? 'active' : ''}`}
                onClick={() => this.handleSelectAccount(null)}
              >
                <span className="account-icon">📥</span>
                <span className="account-name">全部邮件</span>
              </button>

              {emailAccounts.map((account) => (
                <div key={account.id} className="account-item-wrapper">
                  <button
                    className={`account-item ${selectedAccountId === account.id ? 'active' : ''}`}
                    onClick={() => this.handleSelectAccount(account.id)}
                  >
                    <span className="account-icon">
                      {account.email_type === 'QQ' ? '📨' : account.email_type === 'NETEASE' ? '📧' : '✉️'}
                    </span>
                    <span className="account-name">{account.email_address}</span>
                  </button>
                  <div className="account-actions">
                    <button
                      className="btn-icon-sm"
                      onClick={() => this.handleSyncEmails(account.id)}
                      disabled={isSyncing}
                      title="同步邮件"
                    >
                      <svg className={isSyncing ? 'spin' : ''} viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M21 12a9 9 0 11-9-9" />
                      </svg>
                    </button>
                    <button
                      className="btn-icon-sm btn-danger"
                      onClick={() => this.handleDeleteAccount(account.id, account.email_address)}
                      title="删除邮箱"
                    >
                      <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M3 6h18M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2m3 0v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6h14" />
                      </svg>
                    </button>
                  </div>
                </div>
              ))}
            </>
          )}
        </nav>
      </aside>
    )
  }

  /**
   * 渲染邮件列表。
   * @returns {JSX.Element} 邮件列表
   */
  renderEmailList() {
    const { emails, selectedEmail, isLoadingEmails } = this.state

    return (
      <section className="email-list">
        <div className="email-list-header">
          <h2>收件箱</h2>
          <span className="email-count">{emails.length} 封邮件</span>
        </div>

        <div className="email-list-content">
          {isLoadingEmails ? (
            <div className="loading-placeholder">加载中...</div>
          ) : emails.length === 0 ? (
            <div className="empty-placeholder">
              <svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" strokeWidth="1">
                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                <polyline points="22,6 12,13 2,6"/>
              </svg>
              <p>暂无邮件</p>
            </div>
          ) : (
            emails.map((email) => (
              <div
                key={email.id}
                className={`email-item ${selectedEmail?.id === email.id ? 'active' : ''} ${!email.is_read ? 'unread' : ''} phishing-${email.phishing_level.toLowerCase()}`}
                onClick={() => this.handleSelectEmail(email)}
              >
                <div className="email-item-indicator">
                  {email.phishing_level === 'HIGH_RISK' && (
                    <span className="phishing-badge high-risk" title="高危钓鱼邮件">⚠️</span>
                  )}
                  {email.phishing_level === 'SUSPICIOUS' && (
                    <span className="phishing-badge suspicious" title="疑似钓鱼邮件">⚡</span>
                  )}
                </div>
                <div className="email-item-content">
                  <div className="email-item-header">
                    <span className="email-sender">{email.sender}</span>
                    <span className="email-time">
                      {email.received_at ? new Date(email.received_at).toLocaleDateString() : ''}
                    </span>
                  </div>
                  <div className="email-subject">{email.subject || '(无主题)'}</div>
                  <div className="email-account-tag">{email.email_address}</div>
                </div>
              </div>
            ))
          )}
        </div>
      </section>
    )
  }

  /**
   * 渲染邮件详情。
   * @returns {JSX.Element} 邮件详情
   */
  renderEmailDetail() {
    const { emailDetail, isLoadingDetail, selectedEmail } = this.state

    if (!selectedEmail) {
      return (
        <section className="email-detail">
          <div className="empty-placeholder">
            <svg viewBox="0 0 24 24" width="64" height="64" fill="none" stroke="currentColor" strokeWidth="1">
              <rect x="3" y="5" width="18" height="14" rx="2"/>
              <path d="M3 7l9 6 9-6"/>
            </svg>
            <p>选择邮件查看详情</p>
          </div>
        </section>
      )
    }

    if (isLoadingDetail) {
      return (
        <section className="email-detail">
          <div className="loading-placeholder">加载中...</div>
        </section>
      )
    }

    if (!emailDetail) {
      return (
        <section className="email-detail">
          <div className="empty-placeholder">加载失败</div>
        </section>
      )
    }

    return (
      <section className="email-detail">
        <div className="detail-header">
          {emailDetail.phishing_level !== 'NORMAL' && (
            <div className={`phishing-warning ${emailDetail.phishing_level.toLowerCase()}`}>
              {emailDetail.phishing_level === 'HIGH_RISK' ? (
                <>
                  <span className="warning-icon">🚨</span>
                  <span>高危钓鱼邮件 - 请勿点击任何链接</span>
                </>
              ) : (
                <>
                  <span className="warning-icon">⚠️</span>
                  <span>疑似钓鱼邮件 - 请谨慎对待</span>
                </>
              )}
              <span className="phishing-score">风险评分: {(emailDetail.phishing_score * 100).toFixed(0)}%</span>
            </div>
          )}
          <h1 className="detail-subject">{emailDetail.subject || '(无主题)'}</h1>
          <div className="detail-meta">
            <div className="detail-from">
              <span className="label">发件人:</span>
              <span className="value">{emailDetail.sender}</span>
            </div>
            <div className="detail-to">
              <span className="label">收件人:</span>
              <span className="value">{emailDetail.recipients}</span>
            </div>
            <div className="detail-time">
              <span className="label">时间:</span>
              <span className="value">
                {emailDetail.received_at ? new Date(emailDetail.received_at).toLocaleString() : ''}
              </span>
            </div>
          </div>
        </div>

        <div className="detail-body">
          <PhishingProtectedContent
            content={emailDetail.content_html || emailDetail.content_text}
            phishingLevel={emailDetail.phishing_level}
            isHtml={!!emailDetail.content_html}
          />
        </div>
      </section>
    )
  }

  /**
   * 渲染添加邮箱模态框。
   * @returns {JSX.Element | null} 模态框
   */
  renderAddEmailModal() {
    if (!this.state.showAddEmailModal) {
      return null
    }

    const { addEmailForm, addEmailError, isAddingEmail } = this.state
    const isCustomType = addEmailForm.emailType === 'CUSTOM'

    return (
      <div className="modal-overlay" onClick={() => this.setState({ showAddEmailModal: false })}>
        <div className="modal-content" onClick={(e) => e.stopPropagation()}>
          <div className="modal-header">
            <h3>添加邮箱账户</h3>
            <button
              className="btn-close"
              onClick={() => this.setState({ showAddEmailModal: false })}
            >
              ×
            </button>
          </div>

          <form onSubmit={this.handleAddEmail} className="modal-form">
            <div className="form-group">
              <label>邮箱类型</label>
              <select
                value={addEmailForm.emailType}
                onChange={(e) =>
                  this.setState({
                    addEmailForm: { ...addEmailForm, emailType: e.target.value },
                  })
                }
              >
                <option value="QQ">QQ邮箱</option>
                <option value="NETEASE">网易163邮箱</option>
                <option value="DEFAULT">学校邮箱</option>
                <option value="CUSTOM">自定义配置</option>
              </select>
            </div>

            <div className="form-group">
              <label>邮箱地址</label>
              <input
                type="email"
                placeholder="example@qq.com"
                value={addEmailForm.emailAddress}
                onChange={(e) =>
                  this.setState({
                    addEmailForm: { ...addEmailForm, emailAddress: e.target.value },
                  })
                }
              />
            </div>

            <div className="form-group">
              <label>授权密码</label>
              <input
                type="password"
                placeholder="请输入授权密码（非登录密码）"
                value={addEmailForm.authPassword}
                onChange={(e) =>
                  this.setState({
                    addEmailForm: { ...addEmailForm, authPassword: e.target.value },
                  })
                }
              />
              <small>QQ邮箱和163邮箱需要使用授权码，请在邮箱设置中获取。</small>
            </div>

            {isCustomType && (
              <>
                <div className="form-row">
                  <div className="form-group">
                    <label>IMAP服务器</label>
                    <input
                      type="text"
                      placeholder="imap.example.com"
                      value={addEmailForm.imapHost}
                      onChange={(e) =>
                        this.setState({
                          addEmailForm: { ...addEmailForm, imapHost: e.target.value },
                        })
                      }
                    />
                  </div>
                  <div className="form-group">
                    <label>IMAP端口</label>
                    <input
                      type="number"
                      placeholder="993"
                      value={addEmailForm.imapPort}
                      onChange={(e) =>
                        this.setState({
                          addEmailForm: { ...addEmailForm, imapPort: e.target.value },
                        })
                      }
                    />
                  </div>
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label>SMTP服务器</label>
                    <input
                      type="text"
                      placeholder="smtp.example.com"
                      value={addEmailForm.smtpHost}
                      onChange={(e) =>
                        this.setState({
                          addEmailForm: { ...addEmailForm, smtpHost: e.target.value },
                        })
                      }
                    />
                  </div>
                  <div className="form-group">
                    <label>SMTP端口</label>
                    <input
                      type="number"
                      placeholder="465"
                      value={addEmailForm.smtpPort}
                      onChange={(e) =>
                        this.setState({
                          addEmailForm: { ...addEmailForm, smtpPort: e.target.value },
                        })
                      }
                    />
                  </div>
                </div>
              </>
            )}

            {addEmailError && <div className="form-error">{addEmailError}</div>}

            <div className="form-actions">
              <button
                type="button"
                className="btn-secondary"
                onClick={() => this.setState({ showAddEmailModal: false })}
              >
                取消
              </button>
              <button type="submit" className="btn-primary" disabled={isAddingEmail}>
                {isAddingEmail ? '添加中...' : '添加邮箱'}
              </button>
            </div>
          </form>
        </div>
      </div>
    )
  }

  /**
   * 渲染写邮件模态框。
   * @returns {JSX.Element | null} 模态框
   */
  renderComposeModal() {
    if (!this.state.showComposeModal) {
      return null
    }

    const { composeForm, composeError, isSending } = this.state

    return (
      <div className="modal-overlay" onClick={() => this.setState({ showComposeModal: false })}>
        <div className="modal-content modal-large" onClick={(e) => e.stopPropagation()}>
          <div className="modal-header">
            <h3>写邮件</h3>
            <button
              className="btn-close"
              onClick={() => this.setState({ showComposeModal: false })}
            >
              ×
            </button>
          </div>

          <form onSubmit={this.handleSendEmail} className="modal-form">
            <div className="form-group">
              <label>收件人</label>
              <input
                type="text"
                placeholder="多个收件人用逗号分隔"
                value={composeForm.toAddresses}
                onChange={(e) =>
                  this.setState({
                    composeForm: { ...composeForm, toAddresses: e.target.value },
                  })
                }
              />
            </div>

            <div className="form-group">
              <label>主题</label>
              <input
                type="text"
                placeholder="请输入邮件主题"
                value={composeForm.subject}
                onChange={(e) =>
                  this.setState({
                    composeForm: { ...composeForm, subject: e.target.value },
                  })
                }
              />
            </div>

            <div className="form-group">
              <label>正文</label>
              <textarea
                rows="10"
                placeholder="请输入邮件内容"
                value={composeForm.content}
                onChange={(e) =>
                  this.setState({
                    composeForm: { ...composeForm, content: e.target.value },
                  })
                }
              />
            </div>

            {composeError && <div className="form-error">{composeError}</div>}

            <div className="form-actions">
              <button
                type="button"
                className="btn-secondary"
                onClick={() => this.setState({ showComposeModal: false })}
              >
                取消
              </button>
              <button type="submit" className="btn-primary" disabled={isSending}>
                {isSending ? '发送中...' : '发送'}
              </button>
            </div>
          </form>
        </div>
      </div>
    )
  }

  /**
   * 渲染组件。
   * @returns {JSX.Element} 页面结构
   */
  render() {
    return (
      <div className="mail-client">
        {this.renderSidebar()}
        {this.renderEmailList()}
        {this.renderEmailDetail()}
        {this.renderAddEmailModal()}
        {this.renderComposeModal()}
      </div>
    )
  }
}

/**
 * 钓鱼保护内容组件。
 *
 * 根据钓鱼等级处理邮件内容中的链接。
 */
class PhishingProtectedContent extends React.Component {
  /**
   * @param {object} props 组件属性
   */
  constructor(props) {
    super(props)
    this.state = {
      showLinkModal: false,
      pendingLink: '',
      schoolInput: '',
      schoolError: '',
    }
  }

  /**
   * 处理高危链接点击。
   * @param {string} url 链接URL
   */
  handleHighRiskLinkClick(url) {
    this.setState({ showLinkModal: true, pendingLink: url, schoolInput: '', schoolError: '' })
  }

  /**
   * 验证学校并复制链接。
   */
  handleVerifyAndCopy() {
    const { schoolInput, pendingLink } = this.state

    if (!schoolInput.trim()) {
      this.setState({ schoolError: '请输入您的学校名称。' })
      return
    }

    // 复制链接到剪贴板
    navigator.clipboard.writeText(pendingLink).then(() => {
      this.setState({ showLinkModal: false })
      alert('链接已复制到剪贴板。请自行判断是否访问。')
    }).catch(() => {
      this.setState({ schoolError: '复制失败，请手动复制。' })
    })
  }

  /**
   * 处理邮件内容，根据钓鱼等级处理链接。
   * @returns {JSX.Element} 处理后的内容
   */
  renderContent() {
    const { content, phishingLevel, isHtml } = this.props

    if (!content) {
      return <p className="no-content">（无内容）</p>
    }

    // 正常邮件直接显示
    if (phishingLevel === 'NORMAL') {
      if (isHtml) {
        return <div className="email-html-content" dangerouslySetInnerHTML={{ __html: content }} />
      }
      return <pre className="email-text-content">{content}</pre>
    }

    // 疑似钓鱼：将链接变为纯文本
    if (phishingLevel === 'SUSPICIOUS') {
      let processedContent = content
      if (isHtml) {
        // 移除href属性，保留链接文本
        processedContent = content.replace(
          /<a\s+[^>]*href=["']([^"']*)["'][^>]*>(.*?)<\/a>/gi,
          '<span class="disabled-link" title="链接已禁用: $1">$2 [链接已禁用]</span>',
        )
        return <div className="email-html-content suspicious" dangerouslySetInnerHTML={{ __html: processedContent }} />
      }
      return <pre className="email-text-content">{content}</pre>
    }

    // 高危钓鱼：隐藏链接，添加查看按钮
    if (phishingLevel === 'HIGH_RISK') {
      if (isHtml) {
        // 提取所有链接并替换为按钮
        const linkRegex = /<a\s+[^>]*href=["']([^"']*)["'][^>]*>(.*?)<\/a>/gi
        const links = []
        let match
        while ((match = linkRegex.exec(content)) !== null) {
          links.push({ url: match[1], text: match[2] })
        }

        let processedContent = content.replace(
          linkRegex,
          '<span class="hidden-link">[链接已隐藏]</span>',
        )

        return (
          <div className="high-risk-content">
            <div className="email-html-content high-risk" dangerouslySetInnerHTML={{ __html: processedContent }} />
            {links.length > 0 && (
              <div className="hidden-links-section">
                <p className="warning-text">检测到 {links.length} 个可疑链接：</p>
                {links.map((link, index) => (
                  <button
                    key={index}
                    className="btn-view-link"
                    onClick={() => this.handleHighRiskLinkClick(link.url)}
                  >
                    点击查看疑似钓鱼链接 #{index + 1}
                  </button>
                ))}
              </div>
            )}
          </div>
        )
      }
      return <pre className="email-text-content">{content}</pre>
    }

    return <pre className="email-text-content">{content}</pre>
  }

  /**
   * 渲染链接确认模态框。
   * @returns {JSX.Element | null} 模态框
   */
  renderLinkModal() {
    if (!this.state.showLinkModal) {
      return null
    }

    const { pendingLink, schoolInput, schoolError } = this.state

    return (
      <div className="modal-overlay" onClick={() => this.setState({ showLinkModal: false })}>
        <div className="modal-content modal-small" onClick={(e) => e.stopPropagation()}>
          <div className="modal-header warning">
            <h3>⚠️ 高危链接警告</h3>
            <button
              className="btn-close"
              onClick={() => this.setState({ showLinkModal: false })}
            >
              ×
            </button>
          </div>

          <div className="modal-body">
            <p className="warning-text">这是一个疑似钓鱼链接，请谨慎操作！</p>
            <div className="link-display">
              <code>{pendingLink}</code>
            </div>
            <p>为确认您已了解风险，请输入您的学校名称：</p>
            <input
              type="text"
              placeholder="请输入您的学校名称"
              value={schoolInput}
              onChange={(e) => this.setState({ schoolInput: e.target.value })}
              className="school-input"
            />
            {schoolError && <div className="form-error">{schoolError}</div>}
          </div>

          <div className="modal-footer">
            <button
              className="btn-secondary"
              onClick={() => this.setState({ showLinkModal: false })}
            >
              取消
            </button>
            <button
              className="btn-warning"
              onClick={() => this.handleVerifyAndCopy()}
            >
              确认复制链接
            </button>
          </div>
        </div>
      </div>
    )
  }

  /**
   * 渲染组件。
   * @returns {JSX.Element} 组件结构
   */
  render() {
    return (
      <>
        {this.renderContent()}
        {this.renderLinkModal()}
      </>
    )
  }
}
