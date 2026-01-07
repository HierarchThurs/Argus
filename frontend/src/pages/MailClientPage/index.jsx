/**
 * 邮件客户端主页组件。
 *
 * 三栏布局：左侧邮箱列表、中间邮件列表、右侧邮件详情。
 */

import React, { useEffect, useState, useCallback } from 'react'
import { useAuth } from '../../contexts/AuthContext.jsx'
import { useAccounts } from '../../hooks/useAccounts.js'
import { useEmails } from '../../hooks/useEmails.js'
import Toast from '../../components/Toast.jsx'
import ConfirmDialog from '../../components/ConfirmDialog.jsx'
import Sidebar from './Sidebar.jsx'
import EmailList from './EmailList.jsx'
import EmailDetail from './EmailDetail.jsx'
import { AddEmailModal, ComposeModal } from './Modals.jsx'
import '../MailClientPage.css'

/**
 * 邮件客户端主页。
 *
 * @returns {JSX.Element} 页面结构
 */
export default function MailClientPage() {
  const { user, token, logout } = useAuth()
  const accounts = useAccounts()
  const emails = useEmails()
  const { applyPhishingUpdate } = emails

  const [selectedAccountId, setSelectedAccountId] = useState(null)
  const [showAddEmailModal, setShowAddEmailModal] = useState(false)
  const [showComposeModal, setShowComposeModal] = useState(false)

  /**
   * 初始化加载邮箱账户和邮件。
   */
  useEffect(() => {
    const init = async () => {
      try {
        const accountList = await accounts.loadAccounts()
        if (accountList.length > 0) {
          await emails.loadEmails(null)
        }
      } catch (error) {
        Toast.error('加载数据失败，请刷新页面重试')
      }
    }
    init()
  }, [])

  /**
   * 订阅钓鱼检测结果的SSE事件流。
   * 后台检测完成后推送增量更新，避免轮询刷新导致滚动位置丢失。
   */
  useEffect(() => {
    if (!token) return

    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:10003/api'
    const streamUrl = `${baseUrl}/phishing/stream?token=${encodeURIComponent(token)}`
    const eventSource = new EventSource(streamUrl)

    const handleUpdate = (event) => {
      try {
        const payload = JSON.parse(event.data)
        applyPhishingUpdate(payload)
      } catch (error) {
        console.debug('解析钓鱼检测事件失败:', error)
      }
    }

    eventSource.addEventListener('phishing_update', handleUpdate)

    eventSource.onerror = (error) => {
      console.debug('钓鱼检测事件流异常:', error)
    }

    return () => {
      eventSource.removeEventListener('phishing_update', handleUpdate)
      eventSource.close()
    }
  }, [token, applyPhishingUpdate])

  /**
   * 选择邮箱账户。
   */
  const handleSelectAccount = useCallback(
    async (accountId) => {
      setSelectedAccountId(accountId)
      emails.clearSelection()
      try {
        await emails.loadEmails(accountId)
      } catch (error) {
        Toast.error('加载邮件失败')
      }
    },
    [emails]
  )

  /**
   * 选择邮件。
   */
  const handleSelectEmail = useCallback(
    async (email) => {
      await emails.selectEmail(email)
      // 标记已读
      if (!email.is_read) {
        try {
          await emails.markAsRead(email.id)
        } catch (error) {
          console.error('标记已读失败:', error)
        }
      }
    },
    [emails]
  )

  /**
   * 同步邮件。
   */
  const handleSyncEmails = useCallback(
    async (accountId) => {
      try {
        const result = await accounts.syncEmails(accountId)
        await emails.loadEmails(selectedAccountId)
        if (result.synced_count > 0) {
          Toast.success(`同步成功，获取${result.synced_count}封新邮件`)
        } else {
          Toast.info('同步完成，暂无新邮件')
        }
      } catch (error) {
        Toast.error('同步邮件失败')
      }
    },
    [accounts, emails, selectedAccountId]
  )

  /**
   * 添加邮箱账户。
   */
  const handleAddAccount = useCallback(
    async (formData) => {
      try {
        const result = await accounts.addAccount(formData)
        if (result.success) {
          setShowAddEmailModal(false)
          Toast.success('邮箱添加成功')
          // 自动同步
          if (result.account_id) {
            await handleSyncEmails(result.account_id)
          }
          return { success: true }
        }
        return { success: false, message: result.message }
      } catch (error) {
        return { success: false, message: error.message }
      }
    },
    [accounts, handleSyncEmails]
  )

  /**
   * 删除邮箱账户。
   */
  const handleDeleteAccount = useCallback(
    async (accountId, emailAddress) => {
      const confirmed = await ConfirmDialog.confirmDelete(emailAddress || '此邮箱账户')
      if (!confirmed) return

      try {
        await accounts.deleteAccount(accountId)
        Toast.success('邮箱账户已删除')
        if (selectedAccountId === accountId) {
          setSelectedAccountId(null)
          await emails.loadEmails(null)
        }
      } catch (error) {
        Toast.error('删除邮箱失败')
      }
    },
    [accounts, emails, selectedAccountId]
  )

  /**
   * 发送邮件。
   */
  const handleSendEmail = useCallback(
    async (formData) => {
      if (accounts.accounts.length === 0) {
        return { success: false, message: '请先添加邮箱账户' }
      }

      try {
        const result = await emails.sendEmail({
          email_account_id: accounts.accounts[0].id,
          ...formData,
        })
        if (result.success) {
          setShowComposeModal(false)
          Toast.success('邮件发送成功')
          return { success: true }
        }
        return { success: false, message: result.message }
      } catch (error) {
        return { success: false, message: error.message }
      }
    },
    [accounts.accounts, emails]
  )

  /**
   * 登出处理。
   */
  const handleLogout = useCallback(() => {
    logout()
    Toast.info('已安全退出登录')
  }, [logout])

  return (
    <div className="mail-client">
      <Sidebar
        user={user}
        accounts={accounts.accounts}
        selectedAccountId={selectedAccountId}
        isLoading={accounts.isLoading}
        isSyncing={accounts.isSyncing}
        onSelectAccount={handleSelectAccount}
        onSyncEmails={handleSyncEmails}
        onDeleteAccount={handleDeleteAccount}
        onAddEmail={() => setShowAddEmailModal(true)}
        onCompose={() => setShowComposeModal(true)}
        onLogout={handleLogout}
      />

      <EmailList
        emails={emails.emails}
        selectedEmail={emails.selectedEmail}
        isLoading={emails.isLoading}
        onSelectEmail={handleSelectEmail}
      />

      <EmailDetail
        emailDetail={emails.emailDetail}
        isLoading={emails.isLoadingDetail}
        selectedEmail={emails.selectedEmail}
        user={user}
      />

      <AddEmailModal
        isOpen={showAddEmailModal}
        onClose={() => setShowAddEmailModal(false)}
        onSubmit={handleAddAccount}
      />

      <ComposeModal
        isOpen={showComposeModal}
        onClose={() => setShowComposeModal(false)}
        onSubmit={handleSendEmail}
        isSending={emails.isSending}
      />
    </div>
  )
}
