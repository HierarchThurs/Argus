import ApiClient from './ApiClient.js'

/**
 * 邮件服务类。
 *
 * 提供邮件管理相关的API调用。
 */
export default class EmailService {
  /**
   * @param {ApiClient} apiClient API客户端
   */
  constructor(apiClient) {
    this.apiClient = apiClient
  }

  /**
   * 创建默认服务实例。
   * @returns {EmailService} 服务实例
   */
  static createDefault() {
    const baseUrl =
      import.meta.env.VITE_API_BASE_URL || 'http://localhost:10003/api'
    return new EmailService(new ApiClient(baseUrl))
  }

  /**
   * 使用指定令牌创建服务实例。
   * @param {string} token JWT访问令牌
   * @returns {EmailService} 服务实例
   */
  static createWithToken(token) {
    const baseUrl =
      import.meta.env.VITE_API_BASE_URL || 'http://localhost:10003/api'
    return new EmailService(new ApiClient(baseUrl, token))
  }

  /**
   * 获取邮件列表。
   * @param {number | null} accountId 邮箱账户ID（可选）
   * @param {number} limit 返回数量
   * @param {number} offset 偏移量
   * @returns {Promise<Array>} 邮件列表
   */
  async getEmails(accountId = null, limit = 50, offset = 0) {
    let path = `/emails?limit=${limit}&offset=${offset}`
    if (accountId) {
      path += `&account_id=${accountId}`
    }
    const response = await this.apiClient.get(path)
    if (response?.success) {
      return response.emails || []
    }
    return []
  }

  /**
   * 获取邮件详情。
   * @param {number} emailId 邮件ID
   * @returns {Promise<object | null>} 邮件详情
   */
  async getEmailDetail(emailId) {
    const response = await this.apiClient.get(`/emails/${emailId}`)
    if (response?.success) {
      return response.email
    }
    return null
  }

  /**
   * 发送邮件。
   * @param {object} data 邮件数据
   * @returns {Promise<object>} 发送结果
   */
  async sendEmail(data) {
    return await this.apiClient.post('/emails/send', data)
  }

  /**
   * 标记邮件为已读。
   * @param {number} emailId 邮件ID
   * @returns {Promise<object>} 标记结果
   */
  async markAsRead(emailId) {
    return await this.apiClient.post(`/emails/${emailId}/read`, {})
  }
}
