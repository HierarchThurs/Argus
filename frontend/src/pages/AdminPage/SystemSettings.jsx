/**
 * 系统设置组件。
 *
 * 提供系统级别的操作功能，如重新检测所有邮件等。
 */

import React, { useEffect, useMemo, useState, useCallback } from 'react'
import AdminService from '../../services/AdminService.js'
import { useOverlayClose } from '../../hooks/useOverlayClose'

export default function SystemSettings() {
  const [isLoading, setIsLoading] = useState(false)
  const [showConfirmModal, setShowConfirmModal] = useState(false)
  const [confirmInput, setConfirmInput] = useState('')
  const [resultMessage, setResultMessage] = useState(null)
  const [errorMessage, setErrorMessage] = useState(null)
  const [settingsLoading, setSettingsLoading] = useState(true)
  const [settingsSaving, setSettingsSaving] = useState(false)
  const [settingsError, setSettingsError] = useState(null)
  const [settingsMessage, setSettingsMessage] = useState(null)
  const [longUrlEnabled, setLongUrlEnabled] = useState(true)

  const adminService = useMemo(() => new AdminService(), [])
  const CONFIRM_KEYWORD = '重新检测'
  
  // 遮罩层关闭回调
  const handleCloseModal = useCallback(() => {
    if (!isLoading) {
      setShowConfirmModal(false)
    }
  }, [isLoading])
  
  // 使用 hook 处理遮罩层关闭逻辑
  const { handleMouseDown, handleClick } = useOverlayClose(handleCloseModal)

  useEffect(() => {
    let isActive = true

    const loadSettings = async () => {
      setSettingsLoading(true)
      setSettingsError(null)
      try {
        const response = await adminService.getSystemSettings()
        if (!isActive) return
        setLongUrlEnabled(Boolean(response.enable_long_url_detection))
      } catch (error) {
        if (!isActive) return
        console.error('加载系统设置失败:', error)
        setSettingsError(error.message || '加载系统设置失败，请稍后重试')
      } finally {
        if (isActive) setSettingsLoading(false)
      }
    }

    loadSettings()
    return () => {
      isActive = false
    }
  }, [adminService])

  const handleToggleLongUrlDetection = async () => {
    if (settingsLoading || settingsSaving) return
    const nextValue = !longUrlEnabled
    const previousValue = longUrlEnabled

    setSettingsSaving(true)
    setSettingsMessage(null)
    setSettingsError(null)
    setLongUrlEnabled(nextValue)

    try {
      const response = await adminService.updateSystemSettings({
        enable_long_url_detection: nextValue,
      })
      setLongUrlEnabled(Boolean(response.enable_long_url_detection))
      setSettingsMessage(nextValue ? '已开启长链接检测' : '已关闭长链接检测')
    } catch (error) {
      console.error('更新系统设置失败:', error)
      setLongUrlEnabled(previousValue)
      setSettingsError(error.message || '更新失败，请重试')
    } finally {
      setSettingsSaving(false)
    }
  }

  const handleRedetectClick = () => {
    setShowConfirmModal(true)
    setConfirmInput('')
    setResultMessage(null)
    setErrorMessage(null)
  }

  const handleConfirmRedetect = async () => {
    if (confirmInput !== CONFIRM_KEYWORD) {
      setErrorMessage(`请输入"${CONFIRM_KEYWORD}"以确认操作`)
      return
    }

    try {
      setIsLoading(true)
      const response = await adminService.redetectAllEmails()
      setResultMessage(response.message || '操作成功，后台已开始重新检测')
      setShowConfirmModal(false)
    } catch (error) {
      console.error('重新检测请求失败:', error)
      setErrorMessage(error.message || '操作失败，请重试')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="admin-card">
      <div className="admin-card-header">
        <h2>⚙️ 系统设置</h2>
      </div>

      <div className="admin-form">
        <div className="setting-item">
          <div className="setting-row">
            <div className="setting-info">
              <h3>🔗 长链接检测</h3>
              <p>
                关闭后仅执行机器学习检测，不影响现有邮件检测结果。
                <br />
                重新检测全部邮件时将按当前开关重新评估，URL白名单依然优先生效。
              </p>
            </div>
            <div className="setting-control">
              <label className={`toggle-switch ${longUrlEnabled ? 'on' : 'off'}`}>
                <input
                  type="checkbox"
                  checked={longUrlEnabled}
                  onChange={handleToggleLongUrlDetection}
                  disabled={settingsLoading || settingsSaving}
                />
                <span className="toggle-track">
                  <span className="toggle-thumb" />
                </span>
                <span className="toggle-label">
                  {longUrlEnabled ? '已开启' : '已关闭'}
                </span>
              </label>
            </div>
          </div>

          {settingsLoading && (
            <div className="setting-hint">正在加载系统设置...</div>
          )}
          {settingsSaving && (
            <div className="setting-hint">正在保存设置...</div>
          )}
          {settingsMessage && (
            <div className="setting-alert success">{settingsMessage}</div>
          )}
          {settingsError && (
            <div className="setting-alert error">{settingsError}</div>
          )}
        </div>

        <div className="setting-item">
          <div className="setting-row">
            <div className="setting-info">
              <h3>🛡️ 全局钓鱼检测</h3>
              <p className="setting-description">
                重新运行钓鱼检测算法，对系统中所有历史邮件进行重新评估。
              </p>
              <p className="setting-warning">
                ⚠️ 注意：此操作可能会显著增加服务器负载，建议在低峰期执行。
              </p>

              {resultMessage && (
                <div style={{ 
                  marginTop: '8px', 
                  padding: '10px 14px', 
                  background: 'var(--color-success-light)', 
                  color: 'var(--color-success)', 
                  borderRadius: '8px',
                  fontSize: '0.9rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}>
                  ✅ {resultMessage}
                </div>
              )}
            </div>
            <div className="setting-control">
              <button 
                className="btn-action danger" 
                style={{ padding: '10px 20px', fontSize: '0.95rem' }}
                onClick={handleRedetectClick}
                disabled={isLoading}
              >
                {isLoading ? '正在触发...' : '重新检测所有邮件'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* 二次确认弹窗 */}
      {showConfirmModal && (
        <div className="modal-overlay admin-modal" onMouseDown={handleMouseDown} onClick={handleClick}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h3>⚠️ 高危操作确认</h3>
              <button 
                className="btn-close" 
                onClick={() => setShowConfirmModal(false)}
                disabled={isLoading}
              >
                ✕
              </button>
            </div>
            
            <div className="modal-body">
              <p style={{ margin: '0 0 16px', color: 'var(--color-ink)' }}>
                您即将触发 <strong>全局邮件重新检测</strong>。
              </p>
              <ul style={{ 
                margin: '0 0 20px', 
                paddingLeft: '20px', 
                color: 'var(--color-ink-secondary)',
                lineHeight: '1.6' 
              }}>
                <li>系统将重新分析数据库中的所有邮件</li>
                <li>历史检测结果可能会被更新</li>
                <li>此过程在后台运行，可能需要较长时间</li>
              </ul>
              
              <div className="admin-form">
                <div className="form-group">
                  <label>
                    请输入 <code>{CONFIRM_KEYWORD}</code> 以确认操作：
                  </label>
                  <input
                    type="text"
                    value={confirmInput}
                    onChange={e => {
                      setConfirmInput(e.target.value)
                      setErrorMessage(null)
                    }}
                    placeholder={CONFIRM_KEYWORD}
                    disabled={isLoading}
                    autoFocus
                  />
                </div>
              </div>

              {errorMessage && (
                <div style={{ color: 'var(--color-danger)', fontSize: '0.9rem', marginTop: '8px' }}>
                  {errorMessage}
                </div>
              )}
              
              <div className="form-actions" style={{ marginTop: '24px' }}>
                <button 
                  className="btn-cancel" 
                  onClick={() => setShowConfirmModal(false)}
                  disabled={isLoading}
                >
                  取消
                </button>
                <button 
                  className="btn-action danger"
                  style={{ padding: '12px 24px', borderRadius: '10px' }}
                  onClick={handleConfirmRedetect}
                  disabled={isLoading || confirmInput !== CONFIRM_KEYWORD}
                >
                  {isLoading ? '正在提交...' : '确认执行'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
