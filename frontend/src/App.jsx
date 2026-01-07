/**
 * 应用根组件。
 *
 * 配置路由系统和认证状态管理。
 */

import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './contexts/AuthContext.jsx'
import './App.css'
import LoginPage from './pages/LoginPage.jsx'
import MailClientPage from './pages/MailClientPage/index.jsx'
import Toast from './components/Toast.jsx'
import ConfirmDialog from './components/ConfirmDialog.jsx'

/**
 * 受保护路由组件。
 *
 * @param {object} props 组件属性
 * @param {React.ReactNode} props.children 子组件
 * @returns {JSX.Element} 路由元素
 */
function ProtectedRoute({ children }) {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="loading-screen">
        <div className="loading-spinner"></div>
        <p>加载中...</p>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return children
}

/**
 * 公开路由组件（已登录用户重定向）。
 *
 * @param {object} props 组件属性
 * @param {React.ReactNode} props.children 子组件
 * @returns {JSX.Element} 路由元素
 */
function PublicRoute({ children }) {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="loading-screen">
        <div className="loading-spinner"></div>
        <p>加载中...</p>
      </div>
    )
  }

  if (isAuthenticated) {
    return <Navigate to="/mail" replace />
  }

  return children
}

/**
 * 应用路由配置。
 *
 * @returns {JSX.Element} 路由结构
 */
function AppRoutes() {
  const { isAuthenticated } = useAuth()

  return (
    <Routes>
      <Route
        path="/login"
        element={
          <PublicRoute>
            <LoginPage />
          </PublicRoute>
        }
      />
      <Route
        path="/mail"
        element={
          <ProtectedRoute>
            <MailClientPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/"
        element={<Navigate to={isAuthenticated ? '/mail' : '/login'} replace />}
      />
    </Routes>
  )
}

/**
 * 应用主组件。
 *
 * @returns {JSX.Element} 应用结构
 */
function App() {
  return (
    <AuthProvider>
      <Toast />
      <ConfirmDialog />
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App
