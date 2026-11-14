/**
 * Small JSON values kept on the device between visits (e.g. an unfinished quiz).
 * Never for secrets: tokens live in secure storage or httpOnly cookies (R12).
 */
import AsyncStorage from "@react-native-async-storage/async-storage";

const PREFIX = "flashcard.draft.";

export async function loadDraft<T>(key: string): Promise<T | null> {
  try {
    const raw = await AsyncStorage.getItem(PREFIX + key);
    return raw ? (JSON.parse(raw) as T) : null;
  } catch {
    return null;
  }
}

export async function saveDraft(key: string, value: unknown): Promise<void> {
  await AsyncStorage.setItem(PREFIX + key, JSON.stringify(value));
}

export async function removeDraft(key: string): Promise<void> {
  await AsyncStorage.removeItem(PREFIX + key);
}
