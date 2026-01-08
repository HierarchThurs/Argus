/**
 * 校验结果模型。
 */
class ValidationResult {
  /**
   * @param {boolean} isValid 是否通过
   * @param {string} message 提示信息
   */
  constructor(isValid, message) {
    this.isValid = isValid
    this.message = message
  }

  /**
   * 创建通过状态的结果。
   * @returns {ValidationResult} 校验结果
   */
  static ok() {
    return new ValidationResult(true, '')
  }

  /**
   * 创建失败状态的结果。
   * @param {string} message 提示信息
   * @returns {ValidationResult} 校验结果
   */
  static fail(message) {
    return new ValidationResult(false, message)
  }
}

/**
 * 登录表单校验器。
 */
export default class FormValidator {
  /**
   * 校验登录表单。
   * @param {string} studentId 学号
   * @param {string} password 密码
   * @returns {ValidationResult} 校验结果
   */
  validateLogin(studentId, password) {
    if (!studentId || !password) {
      return ValidationResult.fail('请输入学号和密码。')
    }

    if (!/^[a-zA-Z0-9]{3,20}$/.test(studentId)) {
      return ValidationResult.fail('账号应为 3-20 位字母或数字。')
    }

    if (password.length < 6) {
      return ValidationResult.fail('密码长度至少为 6 位。')
    }

    return ValidationResult.ok()
  }
}
