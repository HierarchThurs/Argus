import React from 'react'
import './App.css'
import LoginPage from './pages/LoginPage.jsx'

/**
 * 应用根组件。
 */
class App extends React.Component {
  /**
   * 渲染应用。
   * @returns {JSX.Element} 页面结构
   */
  render() {
    return <LoginPage />
  }
}

export default App
