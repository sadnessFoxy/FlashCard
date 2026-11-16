import * as Google from "expo-auth-session/providers/google";
import * as WebBrowser from "expo-web-browser";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { Button } from "../../components/ui/Button";
import { config } from "../../config";
import { signInWithGoogle, type User } from "./api";
import { authErrorMessage } from "./errorMessage";
import { googleClientIdFor } from "./googleClient";

// Closes the Google pop-up on web once it redirects back.
WebBrowser.maybeCompleteAuthSession();

interface Props {
  onSignedIn: (user: User) => void;
  onError: (message: string) => void;
}

/** Shown only when this platform has a Google OAuth client configured. */
export function GoogleSignInButton(props: Props) {
  return googleClientIdFor() ? <GoogleButton {...props} /> : null;
}

function GoogleButton({ onSignedIn, onError }: Props) {
  const { t, i18n } = useTranslation();
  const [busy, setBusy] = useState(false);
  const [request, response, prompt] = Google.useIdTokenAuthRequest({
    webClientId: config.google.webClientId || undefined,
    androidClientId: config.google.androidClientId || undefined,
    iosClientId: config.google.iosClientId || undefined,
  });

  useEffect(() => {
    if (response?.type === "error") onError(t("auth.google.errors.invalid"));
    if (response?.type !== "success") return;
    const idToken = response.params.id_token;
    if (!idToken) {
      onError(t("auth.google.errors.invalid"));
      return;
    }
    setBusy(true);
    signInWithGoogle(idToken, i18n.language === "en" ? "en" : "vi")
      .then(onSignedIn)
      .catch((error: unknown) => onError(authErrorMessage(error, t)))
      .finally(() => setBusy(false));
    // Run once per Google response only.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [response]);

  return (
    <Button
      label={t("auth.google.button")}
      variant="secondary"
      onPress={() => void prompt()}
      disabled={!request}
      loading={busy}
      testID="auth-google"
    />
  );
}
