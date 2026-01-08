/**
 * 管理员页面主组件。
 *
 * 根据用户角色显示不同的管理功能Tab。
 * - 超级管理员：管理员管理 + 学生管理 + URL白名单 + 发件人白名单
 * - 普通管理员：学生管理 + URL白名单 + 发件人白名单
 */

import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext.jsx'
import StudentManagement from './StudentManagement.jsx'
import AdminManagement from './AdminManagement.jsx'
import UrlWhitelist from './UrlWhitelist.jsx'
import SenderWhitelist from './SenderWhitelist.jsx'
import SystemSettings from './SystemSettings.jsx'
import './AdminPage.css'

/**
 * 管理员页面入口组件。
 *
 * @returns {JSX.Element} 管理员页面结构
 */
export default function AdminPage() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const role = user?.role || 'admin'
  const isSuperAdmin = role === 'super_admin'

  // 根据角色确定默认Tab
  const [activeTab, setActiveTab] = useState(isSuperAdmin ? 'admins' : 'students')

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="admin-page">
      <header className="admin-header">
        <div className="admin-header-left">
          <h1>管理控制台</h1>
          <span className="admin-badge">
            {isSuperAdmin ? 'Super Admin' : 'Admin'}
          </span>
        </div>
        <div className="admin-header-right">
          <span className="admin-user-info">
            {user?.displayName || '管理员'}
          </span>
          <button className="btn-logout-admin" onClick={handleLogout}>
            退出登录
          </button>
        </div>
      </header>

      <main className="admin-main">
        <nav className="admin-tabs">
          {/* 超级管理员才能看到管理员管理Tab */}
          {isSuperAdmin && (
            <button
              className={`admin-tab ${activeTab === 'admins' ? 'active' : ''}`}
              onClick={() => setActiveTab('admins')}
            >
              👑 管理员管理
            </button>
          )}
          <button
            className={`admin-tab ${activeTab === 'students' ? 'active' : ''}`}
            onClick={() => setActiveTab('students')}
          >
            👤 学生管理
          </button>
          <button
            className={`admin-tab ${activeTab === 'whitelist' ? 'active' : ''}`}
            onClick={() => setActiveTab('whitelist')}
          >
            🛡️ URL白名单
          </button>
          <button
            className={`admin-tab ${activeTab === 'sender-whitelist' ? 'active' : ''}`}
            onClick={() => setActiveTab('sender-whitelist')}
          >
            ✉️ 发件人白名单
          </button>
          <button
            className={`admin-tab ${activeTab === 'settings' ? 'active' : ''}`}
            onClick={() => setActiveTab('settings')}
          >
            ⚙️ 系统设置
          </button>
        </nav>

        <div className="admin-content">
          {activeTab === 'admins' && isSuperAdmin && <AdminManagement />}
          {activeTab === 'students' && <StudentManagement />}
          {activeTab === 'whitelist' && <UrlWhitelist />}
          {activeTab === 'sender-whitelist' && <SenderWhitelist />}
          {activeTab === 'settings' && <SystemSettings />}
        </div>
      </main>
    </div>
  )
}
