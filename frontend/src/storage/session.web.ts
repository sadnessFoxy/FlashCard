/**
 * Lưu trữ session trên web: dùng cookie httpOnly do backend set.
 * Tuân thủ R12: không lưu token vào localStorage hay sessionStorage.
 *
 * Trên web, backend sẽ set cookie httpOnly khi đăng nhập thành công.
 * Frontend không tự đặt cookie và không đọc giá trị token.
 * Mỗi request chỉ cần credentials: "include" để trình duyệt tự gửi cookie.
 */

// Web không lưu token trong JS - backend set httpOnly cookie
export async function saveAccessToken(_token: string): Promise<void> {
  // No-op: access token được set bởi backend qua Set-Cookie httpOnly
  // Frontend không cần và không được lưu token trên web
}

export async function getAccessToken(): Promise<string | null> {
  // Không thể đọc httpOnly cookie từ JS - đây là thiết kế bảo mật
  // API client trên web dùng credentials: "include" thay vì Bearer token
  return null;
}

export async function saveRefreshToken(_token: string): Promise<void> {
  // No-op: refresh token được set bởi backend qua Set-Cookie httpOnly
}

export async function getRefreshToken(): Promise<string | null> {
  // Không đọc được - trình duyệt tự gửi cookie khi refresh
  return null;
}

export async function clearTokens(): Promise<void> {
  // Logout bằng cách gọi API /auth/logout - backend sẽ clear cookie
  // Không cần làm gì ở phía frontend
}
