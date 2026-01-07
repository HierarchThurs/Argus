/**
 * API 请求客户端。
 */
export default class ApiClient {
  /**
   * @param {string} baseUrl API 基础地址
   */
  constructor(baseUrl) {
    this.baseUrl = (baseUrl || '').replace(/\/$/, '')
  }

  /**
   * 获取用户ID（从localStorage）。
   * @returns {string | null} 用户ID
   */
  _getUserId() {
    const user = localStorage.getItem('user')
    if (user) {
      try {
        return JSON.parse(user).userId || '1'
      } catch {
        return '1'
      }
    }
    return '1'
  }

  /**
   * 构建请求头。
   * @returns {object} 请求头对象
   */
  _buildHeaders() {
    return {
      'Content-Type': 'application/json',
      'X-User-Id': this._getUserId(),
    }
  }

  /**
   * 发送 GET 请求。
   * @param {string} path 请求路径
   * @returns {Promise<object>} 响应数据
   */
  async get(path) {
    const response = await fetch(this._buildUrl(path), {
      method: 'GET',
      headers: this._buildHeaders(),
    })

    if (!response.ok) {
      const errorData = await this._safeJson(response)
      const message = errorData?.message || '请求失败，请稍后重试。'
      throw new Error(message)
    }

    return this._safeJson(response)
  }

  /**
   * 发送 POST 请求。
   * @param {string} path 请求路径
   * @param {object} body 请求体
   * @returns {Promise<object>} 响应数据
   */
  async post(path, body) {
    const response = await fetch(this._buildUrl(path), {
      method: 'POST',
      headers: this._buildHeaders(),
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const errorData = await this._safeJson(response)
      const message = errorData?.message || '请求失败，请稍后重试。'
      throw new Error(message)
    }

    return this._safeJson(response)
  }

  /**
   * 发送 DELETE 请求。
   * @param {string} path 请求路径
   * @returns {Promise<object>} 响应数据
   */
  async delete(path) {
    const response = await fetch(this._buildUrl(path), {
      method: 'DELETE',
      headers: this._buildHeaders(),
    })

    if (!response.ok) {
      const errorData = await this._safeJson(response)
      const message = errorData?.message || '请求失败，请稍后重试。'
      throw new Error(message)
    }

    return this._safeJson(response)
  }

  /**
   * 构建完整请求地址。
   * @param {string} path 请求路径
   * @returns {string} 完整 URL
   */
  _buildUrl(path) {
    const normalizedPath = path.startsWith('/') ? path : `/${path}`
    return `${this.baseUrl}${normalizedPath}`
  }

  /**
   * 安全解析 JSON，避免空响应导致异常。
   * @param {Response} response Fetch 响应对象
   * @returns {Promise<object | null>} 解析结果
   */
  async _safeJson(response) {
    try {
      return await response.json()
    } catch (error) {
      return null
    }
  }
}
