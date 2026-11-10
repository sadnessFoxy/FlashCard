// F1 system status, reachable without signing in.
import { config } from "../src/config";
import { SystemStatusScreen } from "../src/features/system/SystemStatusScreen";

export default function System() {
  return <SystemStatusScreen apiUrl={config.apiUrl} />;
}
