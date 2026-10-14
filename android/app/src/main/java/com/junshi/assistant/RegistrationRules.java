package com.junshi.assistant;

final class RegistrationRules {
 static final String ACCOUNT_HINT = "账号：3–64 个字符，仅支持英文字母、数字、点（.）、下划线（_）和短横线（-），不区分大小写，不支持中文或空格。例如：xiaoming_01。";
 static final String PASSWORD_HINT = "注册密码：12–256 个字符，区分大小写；无需强制包含数字、大写字母或特殊符号。建议使用不易猜测的长密码，不要与其他网站重复。";
 static String error(String username, String password) {
  if (!username.matches("[A-Za-z0-9._-]{3,64}")) return "账号须为 3–64 个字符，仅允许英文字母、数字、点、下划线和短横线";
  int length = password.codePointCount(0, password.length());
  if (length < 12 || length > 256) return "注册密码须为 12–256 个字符，无需强制包含特殊符号";
  return null;
 }
 private RegistrationRules() {}
}
