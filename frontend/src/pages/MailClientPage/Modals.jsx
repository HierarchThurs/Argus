/**
 * 模态框组件集合。
 *
 * 包含添加邮箱和写邮件模态框。
 */

import React, { useState, useCallback } from 'react'
import { useOverlayClose } from '../../hooks/useOverlayClose'

/**
 * 添加邮箱模态框。
 *
 * @param {object} props 组件属性
 * @returns {JSX.Element|null} 模态框结构
 */
export function AddEmailModal({ isOpen, onClose, onSubmit }) {
  const [form, setForm] = useState({
    emailAddress: '',
    emailType: 'QQ',
    authPassword: '',
    imapHost: '',
    imapPort: '',
    smtpHost: '',
    smtpPort: '',
  })
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  
  // 使用自定义 hook 处理遮罩层关闭逻辑
  const { handleMouseDown, handleClick } = useOverlayClose(onClose)

  const handleChange = useCallback((field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }))
    setError('')
  }, [])

  const handleSubmit = useCallback(
    async (e) => {
      e.preventDefault()

      if (!form.emailAddress || !form.authPassword) {
        setError('请填写邮箱地址和授权密码。')
        return
      }

      setIsSubmitting(true)
      setError('')

      try {
        const result = await onSubmit({
          email_address: form.emailAddress,
          email_type: form.emailType,
          auth_password: form.authPassword,
          imap_host: form.imapHost || undefined,
          imap_port: form.imapPort ? parseInt(form.imapPort) : undefined,
          smtp_host: form.smtpHost || undefined,
          smtp_port: form.smtpPort ? parseInt(form.smtpPort) : undefined,
        })

        if (result.success) {
          setForm({
            emailAddress: '',
            emailType: 'QQ',
            authPassword: '',
            imapHost: '',
            imapPort: '',
            smtpHost: '',
            smtpPort: '',
          })
        } else {
          setError(result.message || '添加失败。')
        }
      } catch (err) {
        setError(err.message || '添加失败。')
      } finally {
        setIsSubmitting(false)
      }
    },
    [form, onSubmit]
  )

  if (!isOpen) return null

  const isCustomType = form.emailType === 'CUSTOM'

  return (
    <div className="modal-overlay" onMouseDown={handleMouseDown} onClick={handleClick}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>添加邮箱账户</h3>
          <button className="btn-close" onClick={onClose}>
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className="modal-form">
          <div className="form-group">
            <label>邮箱类型</label>
            <select value={form.emailType} onChange={(e) => handleChange('emailType', e.target.value)}>
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
              value={form.emailAddress}
              onChange={(e) => handleChange('emailAddress', e.target.value)}
            />
          </div>

          <div className="form-group">
            <label>授权密码</label>
            <input
              type="password"
              placeholder="请输入授权密码（非登录密码）"
              value={form.authPassword}
              onChange={(e) => handleChange('authPassword', e.target.value)}
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
                    value={form.imapHost}
                    onChange={(e) => handleChange('imapHost', e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label>IMAP端口</label>
                  <input
                    type="number"
                    placeholder="993"
                    value={form.imapPort}
                    onChange={(e) => handleChange('imapPort', e.target.value)}
                  />
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>SMTP服务器</label>
                  <input
                    type="text"
                    placeholder="smtp.example.com"
                    value={form.smtpHost}
                    onChange={(e) => handleChange('smtpHost', e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label>SMTP端口</label>
                  <input
                    type="number"
                    placeholder="465"
                    value={form.smtpPort}
                    onChange={(e) => handleChange('smtpPort', e.target.value)}
                  />
                </div>
              </div>
            </>
          )}

          {error && <div className="form-error">{error}</div>}

          <div className="form-actions">
            <button type="button" className="btn-secondary" onClick={onClose}>
              取消
            </button>
            <button type="submit" className="btn-primary" disabled={isSubmitting}>
              {isSubmitting ? '添加中...' : '添加邮箱'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

/**
 * 写邮件模态框。
 *
 * @param {object} props 组件属性
 * @returns {JSX.Element|null} 模态框结构
 */
export function ComposeModal({ isOpen, onClose, onSubmit, isSending }) {
  const [form, setForm] = useState({
    toAddresses: '',
    subject: '',
    content: '',
  })
  const [error, setError] = useState('')
  
  // 使用自定义 hook 处理遮罩层关闭逻辑
  const { handleMouseDown, handleClick } = useOverlayClose(onClose)

  const handleChange = useCallback((field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }))
    setError('')
  }, [])

  const handleSubmit = useCallback(
    async (e) => {
      e.preventDefault()

      if (!form.toAddresses || !form.subject || !form.content) {
        setError('请填写完整的邮件信息。')
        return
      }

      try {
        const result = await onSubmit({
          to_addresses: form.toAddresses.split(',').map((s) => s.trim()),
          subject: form.subject,
          content: form.content,
        })

        if (result.success) {
          setForm({ toAddresses: '', subject: '', content: '' })
        } else {
          setError(result.message || '发送失败。')
        }
      } catch (err) {
        setError(err.message || '发送失败。')
      }
    },
    [form, onSubmit]
  )

  if (!isOpen) return null

  return (
    <div className="modal-overlay" onMouseDown={handleMouseDown} onClick={handleClick}>
      <div className="modal-content modal-large" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>写邮件</h3>
          <button className="btn-close" onClick={onClose}>
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className="modal-form">
          <div className="form-group">
            <label>收件人</label>
            <input
              type="text"
              placeholder="多个收件人用逗号分隔"
              value={form.toAddresses}
              onChange={(e) => handleChange('toAddresses', e.target.value)}
            />
          </div>

          <div className="form-group">
            <label>主题</label>
            <input
              type="text"
              placeholder="请输入邮件主题"
              value={form.subject}
              onChange={(e) => handleChange('subject', e.target.value)}
            />
          </div>

          <div className="form-group">
            <label>正文</label>
            <textarea
              rows="10"
              placeholder="请输入邮件内容"
              value={form.content}
              onChange={(e) => handleChange('content', e.target.value)}
            />
          </div>

          {error && <div className="form-error">{error}</div>}

          <div className="form-actions">
            <button type="button" className="btn-secondary" onClick={onClose}>
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
