# Optional account integrations

Every integration below is **off by default**. JARVIS runs perfectly without them —
these steps add online answers, Gmail checking, WhatsApp messages, SMS and calls.

Run `jarvis --doctor` at any time to see what is currently configured:

```json
"integrations": { "gmail": false, "whatsapp": false, "twilio": false }
```

Two rules that always apply:

1. **Messages and calls need their own confirmation.** JARVIS stages the action and
   waits for *yes*. A thumbs-up gesture can confirm a pending action, but a gesture can
   never *create* one.
2. **Charges are possible** for Twilio SMS and calls.

---

## 1. Online answers, speech and screen analysis

JARVIS uses one key for: general answers, speech transcription, spoken replies and
screen analysis.

| Variable | Required | Purpose |
|---|---|---|
| `OPENAI_API_KEY` | yes (for these features) | answers, transcription, narration, vision |
| `JARVIS_LLM_MODEL` | no | default `gpt-4o-mini` |
| `JARVIS_STT_MODEL` | no | default `whisper-1` |
| `JARVIS_TTS_VOICE` | no | default `alloy` |
| `JARVIS_VISION_MODEL` | no | default `gpt-4o-mini` |
| `JARVIS_LLM_PROVIDER` | no | `openai` or `gemini` |
| `GEMINI_API_KEY` | alternative | used for answers/vision if no OpenAI key |

**Windows (PowerShell)**

```powershell
setx OPENAI_API_KEY "sk-your-key-here"
# open a new terminal, then:
jarvis --doctor
```

**Windows (cmd)**

```bat
setx OPENAI_API_KEY "sk-your-key-here"
```

**Linux / macOS** (`~/.bashrc`, `~/.zshrc` or `~/.profile`)

```bash
export OPENAI_API_KEY="sk-your-key-here"
```

Keys are read at call time, are never written to the audit log, and are only sent to the
provider you configure. To refuse every outbound call, set `JARVIS_OFFLINE=1`.

---

## 2. Gmail — read-only unread check

JARVIS requests exactly one scope: `https://www.googleapis.com/auth/gmail.readonly`.
It **cannot** send, delete or modify mail.

### 2.1 Create OAuth credentials

1. Open <https://console.cloud.google.com/> and create (or select) a project.
2. **APIs & Services → Library → Gmail API → Enable**.
3. **APIs & Services → OAuth consent screen** → *External* → add your own address as a
   **Test user** (this avoids the verification process for personal use).
4. **APIs & Services → Credentials → Create credentials → OAuth client ID**
   → Application type **Desktop app** → Create.
5. Copy the **Client ID** and **Client secret**.

### 2.2 Get a refresh token (once)

```bash
# Windows PowerShell
$env:GMAIL_CLIENT_ID="xxxx.apps.googleusercontent.com"
$env:GMAIL_CLIENT_SECRET="GOCSPX-xxxx"
python -m jarvis.integrations.gmail_auth

# Linux / macOS
export GMAIL_CLIENT_ID="xxxx.apps.googleusercontent.com"
export GMAIL_CLIENT_SECRET="GOCSPX-xxxx"
python -m jarvis.integrations.gmail_auth
```

A browser tab opens for consent; the helper prints the three variables to store. The
loopback redirect is `http://localhost:8765/`.

### 2.3 Store the variables

**Windows (PowerShell)**

```powershell
setx GMAIL_CLIENT_ID "xxxx.apps.googleusercontent.com"
setx GMAIL_CLIENT_SECRET "GOCSPX-xxxx"
setx GMAIL_REFRESH_TOKEN "1//0g..."
```

**Linux / macOS**

```bash
export GMAIL_CLIENT_ID="xxxx.apps.googleusercontent.com"
export GMAIL_CLIENT_SECRET="GOCSPX-xxxx"
export GMAIL_REFRESH_TOKEN="1//0g..."
```

### 2.4 Use it

```bash
jarvis --command "check my gmail"
```

```text
jarvis> You have 2 unread Gmail message(s):
        • Alice: Lunch on Friday?
        • GitHub: [repo] new pull request
```

Access tokens are refreshed automatically and cached in memory only. Revoke access any
time at <https://myaccount.google.com/permissions>.

| Variable | Purpose |
|---|---|
| `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET` | OAuth desktop client |
| `GMAIL_REFRESH_TOKEN` | long-lived token from the helper |
| `GMAIL_ACCESS_TOKEN` | optional short-lived override, handy for testing |

---

## 3. WhatsApp — Cloud API (outbound)

Uses Meta's official **WhatsApp Cloud API**. Outbound messages only.

> **Receiving** incoming messages requires a Meta webhook pointing at a publicly
> reachable **HTTPS** endpoint. JARVIS does not host that for you; this build sends only.

### 3.1 Set up on Meta

1. Go to <https://developers.facebook.com/apps/> → **Create app** → type **Business**.
2. Add the **WhatsApp** product.
3. From **WhatsApp → API Setup**, note:
   * the **temporary access token** (valid ~24 h; create a **System User** token in
     Business Settings for something permanent),
   * the **Phone number ID** (not the phone number itself).
4. Add your own number as a **recipient** while the app is in test mode.

### 3.2 Store the variables

```powershell
# Windows PowerShell
setx WHATSAPP_TOKEN "EAAG..."
setx WHATSAPP_PHONE_NUMBER_ID "123456789012345"
# optional
setx WHATSAPP_API_VERSION "v21.0"
setx JARVIS_DEFAULT_COUNTRY_CODE "254"
```

```bash
# Linux / macOS
export WHATSAPP_TOKEN="EAAG..."
export WHATSAPP_PHONE_NUMBER_ID="123456789012345"
export WHATSAPP_API_VERSION="v21.0"
export JARVIS_DEFAULT_COUNTRY_CODE="254"      # lets you say "0700 000 000"
```

| Variable | Required | Purpose |
|---|---|---|
| `WHATSAPP_TOKEN` | yes | Meta access token |
| `WHATSAPP_PHONE_NUMBER_ID` | yes | sender phone number ID |
| `WHATSAPP_API_VERSION` | no | default `v21.0` |
| `JARVIS_DEFAULT_COUNTRY_CODE` | no | prefix for local-format numbers |

### 3.3 Use it

```bash
jarvis --command "send a whatsapp message to +254700000000 saying I am on my way"
```

```text
jarvis> Confirm and I will send a WhatsApp message to +254700000000 saying: I am on my way.
        Say yes or no.
you> yes
jarvis> WhatsApp message sent to +254700000000 (id wamid.HBgM...).
```

Numbers are normalised to E.164 (spaces, dashes and brackets are stripped; `00` and a
leading national `0` are handled). Messages are limited to 4096 characters — replies
outside Meta's 24-hour customer-service window need an approved template, which this
build does not send.

---

## 4. Twilio — SMS and outbound calls

These actions **may incur charges** on your Twilio account.

### 4.1 Set up on Twilio

1. Create an account at <https://www.twilio.com/>.
2. **Console → Account Info**: copy the **Account SID** and **Auth Token**.
3. Buy or verify a **Twilio phone number** (SMS-capable; voice-capable for calls).
4. For trial accounts, verify each destination number under **Phone Numbers → Verified
   Caller IDs**.

### 4.2 Store the variables

```powershell
# Windows PowerShell
setx TWILIO_ACCOUNT_SID "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
setx TWILIO_AUTH_TOKEN "your-auth-token"
setx TWILIO_FROM_NUMBER "+15550001111"
setx TWILIO_TO_NUMBER "+254700000000"                 # optional default recipient
setx TWILIO_CALL_MESSAGE "Hello from JARVIS. Goodbye."  # optional spoken call text
```

```bash
# Linux / macOS
export TWILIO_ACCOUNT_SID="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export TWILIO_AUTH_TOKEN="your-auth-token"
export TWILIO_FROM_NUMBER="+15550001111"
export TWILIO_TO_NUMBER="+254700000000"
export TWILIO_CALL_MESSAGE="Hello from JARVIS. Goodbye."
```

| Variable | Required | Purpose |
|---|---|---|
| `TWILIO_ACCOUNT_SID` | yes | account identifier |
| `TWILIO_AUTH_TOKEN` | yes | API secret |
| `TWILIO_FROM_NUMBER` | yes | your Twilio number (E.164) |
| `TWILIO_TO_NUMBER` | no | default recipient when you do not name one |
| `TWILIO_CALL_MESSAGE` | no | text spoken on outbound calls (TwiML-escaped) |

### 4.3 Use it

```bash
jarvis --command "send sms to +254700000000 saying the meeting moved to 3pm"
# → staged → confirm → "SMS sent to +254700000000 (SID SM...). Charges may apply."

jarvis --command "call +254700000000"
# → staged → confirm → "Outbound call placed to +254700000000 (SID CA...)."
```

Everything changing state is staged first. Example of the full flow:

```text
you> send sms to +254700000000 saying hello
jarvis> Confirm and I will send an SMS to +254700000000 saying: hello. Say yes or no.
you> yes
jarvis> SMS sent to +254700000000 (SID SM1234...). Charges may apply.
```

Say `no` at any point and nothing is sent.

---

## 5. Gestures and confirmations

The dwell-gated gestures interact with these integrations like this:

| Gesture | Effect on a pending message/call |
|---|---|
| Thumbs-up (held 1.2 s) | confirms and sends/calls |
| Fist (held 1.2 s) | cancels, nothing is sent |
| Open palm (held 1.2 s) | pauses gesture recognition |

A gesture with nothing pending does **nothing** — it can never originate a message or a
call. Say the request first, then confirm by voice or gesture.

---

## 6. Security checklist

- [ ] Keys live in environment variables (or `setx`), never in `config.json`.
- [ ] `config.json`, `.env` and the data folder are already in `.gitignore`.
- [ ] Gmail stays read-only — JARVIS cannot send or delete mail.
- [ ] Revoke Gmail access when you stop using it: <https://myaccount.google.com/permissions>.
- [ ] Rotate the WhatsApp temporary token, or create a permanent System User token.
- [ ] Set spending limits/alerts in Twilio if you are worried about charges.
- [ ] Set `JARVIS_OFFLINE=1` for a hard no-network mode.
- [ ] Check `logs/audit.jsonl` — every request and action outcome is recorded, with
      credentials redacted.

---

## 7. Troubleshooting

| Message | Meaning | Fix |
|---|---|---|
| `Gmail is not connected yet…` | no usable credentials | complete §2, then `jarvis --doctor` |
| `Google rejected the Gmail credentials (HTTP 400/401)` | refresh token revoked or wrong client | re-run `python -m jarvis.integrations.gmail_auth` |
| `No refresh token was returned` | consent reused | revoke at myaccount.google.com/permissions and authorise again |
| `WhatsApp is not configured…` | token or phone ID missing | complete §3 |
| `Meta rejected the WhatsApp token` | expired temporary token | create a System User token |
| `WhatsApp returned HTTP 400` | recipient not verified / bad number | verify the number in the Meta test setup |
| `Twilio rejected the account credentials` | wrong SID/token | re-copy from the Twilio Console |
| `Twilio returned HTTP 400` | unverified destination on a trial account | verify the number in Twilio |
| `I need a destination number…` | no number given and `TWILIO_TO_NUMBER` unset | say the number, or set the variable |
| `The online service is rate limiting requests` | 429 from the provider | wait a moment and retry |
| `I could not reach…` | offline / DNS / proxy | check connectivity; local skills still work |
