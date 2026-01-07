/**
 * 登录页面组件。
 *
 * 提供用户学号密码登录功能。
 */

import React, { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext.jsx'
import AuthService from '../services/AuthService.js'
import FormValidator from '../utils/FormValidator.js'
import Toast from '../components/Toast.jsx'

/**
 * 登录页面。
 *
 * @returns {JSX.Element} 登录页面结构
 */
export default function LoginPage() {
  const [studentId, setStudentId] = useState('')
  const [password, setPassword] = useState('')
  const [status, setStatus] = useState('idle')
  const [message, setMessage] = useState('')

  const { login } = useAuth()
  const navigate = useNavigate()

  const validator = new FormValidator()
  const authService = AuthService.createDefault()

  /**
   * 处理登录提交。
   *
   * @param {React.FormEvent} event 表单事件
   */
  const handleSubmit = useCallback(
    async (event) => {
      event.preventDefault()

      if (status === 'loading') {
        return
      }

      const validation = validator.validateLogin(studentId, password)
      if (!validation.isValid) {
        setStatus('error')
        setMessage(validation.message)
        return
      }

      setStatus('loading')
      setMessage('正在验证账号信息...')

      try {
        const response = await authService.login(studentId, password)

        if (response.success) {
          setStatus('success')
          setMessage('登录成功。')

          // 保存认证状态
          login({
            token: response.token,
            refresh_token: response.refresh_token,
            user_id: response.user_id,
            student_id: response.student_id,
            display_name: response.display_name,
          })

          Toast.success('登录成功，欢迎回来！')
          navigate('/mail', { replace: true })
          return
        }

        setStatus('error')
        setMessage(response.message || '账号或密码错误。')
      } catch (error) {
        let errorMessage = '服务器暂时不可用，请稍后重试。'

        if (error?.message) {
          if (
            error.message.includes('Failed to fetch') ||
            error.message.includes('NetworkError')
          ) {
            errorMessage = '网络连接失败，请检查网络后重试。'
          } else if (error.message.includes('timeout')) {
            errorMessage = '请求超时，服务器响应过慢。'
          } else {
            errorMessage = error.message
          }
        }

        setStatus('error')
        setMessage(errorMessage)
      }
    },
    [studentId, password, status, login, navigate, authService, validator]
  )

  const isLoading = status === 'loading'

  return (
    <div className="app">
      <main className="login-shell">
        <section className="brand-panel">
          <span className="brand-badge">校园网智能防护</span>
          <h1>钓鱼邮件智能过滤系统</h1>
          <p>基于机器学习的校园网钓鱼邮件识别与过滤，让每一次登录都更安全。</p>
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

          <form onSubmit={handleSubmit} className="login-form">
            <label className="form-row">
              <span>学号</span>
              <input
                name="studentId"
                type="text"
                autoComplete="username"
                placeholder="请输入学号"
                value={studentId}
                onChange={(e) => {
                  setStudentId(e.target.value)
                  setMessage('')
                }}
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
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value)
                  setMessage('')
                }}
                disabled={isLoading}
              />
            </label>

            {message && (
              <div className={`status status-${status}`} role="status">
                {message}
              </div>
            )}

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
