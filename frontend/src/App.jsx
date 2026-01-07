import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import './App.css'
import LoginPage from './pages/LoginPage.jsx'
import MailClientPage from './pages/MailClientPage.jsx'
import Toast from './components/Toast.jsx'
import ConfirmDialog from './components/ConfirmDialog.jsx'

/**
 * 应用根组件。
 *
 * 配置路由系统，管理登录状态和页面导航。
 */
class App extends React.Component {
  /**
   * @param {object} props 组件属性
   */
  constructor(props) {
    super(props)
    this.state = {
      isLoggedIn: this._checkLoginStatus(),
      user: this._getStoredUser(),
    }

    this.handleLoginSuccess = this.handleLoginSuccess.bind(this)
    this.handleLogout = this.handleLogout.bind(this)
  }

  /**
   * 检查登录状态。
   * @returns {boolean} 是否已登录
   */
  _checkLoginStatus() {
    const token = localStorage.getItem('token')
    return !!token
  }

  /**
   * 获取存储的用户信息。
   * @returns {object | null} 用户信息
   */
  _getStoredUser() {
    const userJson = localStorage.getItem('user')
    if (userJson) {
      try {
        return JSON.parse(userJson)
      } catch {
        return null
      }
    }
    return null
  }

  /**
   * 处理登录成功。
   * @param {object} data 登录响应数据
   */
  handleLoginSuccess(data) {
    localStorage.setItem('token', data.token)
    localStorage.setItem(
      'user',
      JSON.stringify({
        studentId: data.studentId,
        displayName: data.displayName,
        userId: data.userId,
      }),
    )
    this.setState({
      isLoggedIn: true,
      user: {
        studentId: data.studentId,
        displayName: data.displayName,
        userId: data.userId,
      },
    })
    // 显示登录成功提示
    Toast.success('登录成功，欢迎回来！')
  }

  /**
   * 处理登出。
   */
  handleLogout() {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    this.setState({ isLoggedIn: false, user: null })
    Toast.info('已安全退出登录')
  }

  /**
   * 渲染应用。
   * @returns {JSX.Element} 页面结构
   */
  render() {
    return (
      <>
        <Toast />
        <ConfirmDialog />
        <BrowserRouter>
          <Routes>
            <Route
              path="/login"
              element={
                this.state.isLoggedIn ? (
                  <Navigate to="/mail" replace />
                ) : (
                  <LoginPage onLoginSuccess={this.handleLoginSuccess} />
                )
              }
            />
            <Route
              path="/mail"
              element={
                this.state.isLoggedIn ? (
                  <MailClientPage
                    user={this.state.user}
                    onLogout={this.handleLogout}
                  />
                ) : (
                  <Navigate to="/login" replace />
                )
              }
            />
            <Route
              path="/"
              element={
                <Navigate to={this.state.isLoggedIn ? '/mail' : '/login'} replace />
              }
            />
          </Routes>
        </BrowserRouter>
      </>
    )
  }
}

export default App

