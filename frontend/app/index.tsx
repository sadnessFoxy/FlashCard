// Màn hình mở đầu tạm thời của lát F1: trạng thái kết nối tới backend.
// Từ lát F2 sẽ chuyển hướng sang đăng nhập hoặc thư viện.
import { config } from "../src/config";
import { SystemStatusScreen } from "../src/features/system/SystemStatusScreen";

export default function Index() {
  return <SystemStatusScreen apiUrl={config.apiUrl} />;
}
