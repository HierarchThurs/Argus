/**
 * 登录请求模型。
 */
export class LoginRequest {
  /**
   * @param {string} studentId 学号
   * @param {string} password 密码
   */
  constructor(studentId, password) {
    this.studentId = studentId
    this.password = password
  }

  /**
   * 将模型转换为后端所需的请求体。
   * @returns {{student_id: string, password: string}} 请求体
   */
  toJson() {
    return {
      student_id: this.studentId,
      password: this.password,
    }
  }
}

/**
 * 登录响应模型。
 */
export class LoginResponse {
  /**
   * @param {object} data 后端响应数据
   * @param {boolean} data.success 是否成功
   * @param {string} data.message 提示信息
   * @param {string | null} data.token 登录令牌
   * @param {string | null} data.studentId 学号
   * @param {string | null} data.displayName 显示名称
   */
  constructor({ success, message, token, studentId, displayName }) {
    this.success = success
    this.message = message
    this.token = token
    this.studentId = studentId
    this.displayName = displayName
  }

  /**
   * 从后端 JSON 构建响应模型。
   * @param {object} data 后端响应 JSON
   * @returns {LoginResponse} 响应模型
   */
  static fromJson(data) {
    return new LoginResponse({
      success: Boolean(data?.success),
      message: data?.message || '',
      token: data?.token || null,
      studentId: data?.student_id || null,
      displayName: data?.display_name || null,
    })
  }
}
