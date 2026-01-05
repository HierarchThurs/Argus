import React from 'react'
import AuthService from '../services/AuthService.js'
import FormValidator from '../utils/FormValidator.js'

/**
 * 登录页面组件。
 */
export default class LoginPage extends React.Component {
  /**
   * @param {object} props 组件属性
   */
  constructor(props) {
    super(props)
    this.state = {
      studentId: '',
      password: '',
      status: 'idle',
      message: '',
    }

    this.authService = AuthService.createDefault()
    this.validator = new FormValidator()

    this.handleInputChange = this.handleInputChange.bind(this)
    this.handleSubmit = this.handleSubmit.bind(this)
  }

  /**
   * 处理输入框变化。
   * @param {React.ChangeEvent<HTMLInputElement>} event 输入事件
   */
  handleInputChange(event) {
    const { name, value } = event.target
    this.setState({ [name]: value, message: '' })
  }

  /**
   * 处理登录提交。
   * @param {React.FormEvent<HTMLFormElement>} event 提交事件
   */
  async handleSubmit(event) {
    event.preventDefault()

    if (this.state.status === 'loading') {
      return
    }

    const validation = this.validator.validateLogin(
      this.state.studentId,
      this.state.password,
    )

    if (!validation.isValid) {
      this.setState({ status: 'error', message: validation.message })
      return
    }

    this.setState({ status: 'loading', message: '正在验证账号信息...' })

    try {
      const response = await this.authService.login(
        this.state.studentId,
        this.state.password,
      )

      if (response.success) {
        this.setState({
          status: 'success',
          message: response.message || '登录成功。',
        })
        return
      }

      this.setState({
        status: 'error',
        message: response.message || '账号或密码错误。',
      })
    } catch (error) {
      this.setState({
        status: 'error',
        message: error?.message || '服务器暂时不可用，请稍后重试。',
      })
    }
  }

  /**
   * 渲染状态提示。
   * @returns {JSX.Element | null} 状态提示节点
   */
  renderStatus() {
    if (!this.state.message) {
      return null
    }

    const statusClass = `status status-${this.state.status}`
    return (
      <div className={statusClass} role="status" aria-live="polite">
        {this.state.message}
      </div>
    )
  }

  /**
   * 渲染组件。
   * @returns {JSX.Element} 页面结构
   */
  render() {
    const isLoading = this.state.status === 'loading'

    return (
      <div className="app">
        <main className="login-shell">
          <section className="brand-panel">
            <span className="brand-badge">校园网智能防护</span>
            <h1>钓鱼邮件智能过滤系统</h1>
            <p>
              基于机器学习的校园网钓鱼邮件识别与过滤，让每一次登录都更安全。
            </p>
            <div className="feature-list">
              <div className="feature-item">
                <span>01</span>
                <div>
                  <h3>实时威胁感知</h3>
                  <p>多维特征融合，快速拦截可疑邮件。</p>
                </div>
              </div>
              <div className="feature-item">
                <span>02</span>
                <div>
                  <h3>行为模型驱动</h3>
                  <p>账号行为画像，识别异常登录。</p>
                </div>
              </div>
              <div className="feature-item">
                <span>03</span>
                <div>
                  <h3>高并发架构</h3>
                  <p>Router-Service-CRUD 分层，支撑高峰访问。</p>
                </div>
              </div>
            </div>
          </section>

          <section className="login-card">
            <header>
              <h2>登录系统</h2>
              <p>请输入学号与密码，进入安全控制台。</p>
            </header>

            <form onSubmit={this.handleSubmit} className="login-form">
              <label className="form-row">
                <span>学号</span>
                <input
                  name="studentId"
                  type="text"
                  autoComplete="username"
                  placeholder="请输入学号"
                  value={this.state.studentId}
                  onChange={this.handleInputChange}
                  disabled={isLoading}
                />
              </label>

              <label className="form-row">
                <span>密码</span>
                <input
                  name="password"
                  type="password"
                  autoComplete="current-password"
                  placeholder="请输入密码"
                  value={this.state.password}
                  onChange={this.handleInputChange}
                  disabled={isLoading}
                />
              </label>

              {this.renderStatus()}

              <button type="submit" disabled={isLoading}>
                {isLoading ? '验证中...' : '登录'}
              </button>
            </form>

            <footer>
              <p>提示：仅支持学号 + 密码登录，无需注册与找回密码。</p>
            </footer>
          </section>
        </main>
      </div>
    )
  }
}
