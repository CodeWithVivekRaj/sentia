"""WhatsApp notifier — CallMeBot (default) or Twilio."""
import logging
import urllib.parse
import httpx

log = logging.getLogger("sentia.social.whatsapp")


class WhatsAppNotifier:
    def __init__(
        self,
        provider: str = "callmebot",
        # CallMeBot
        phone: str = "",
        api_key: str = "",
        # Twilio
        account_sid: str = "",
        auth_token: str = "",
        from_number: str = "whatsapp:+14155238886",
        to_number: str = "",
    ) -> None:
        self._provider = provider
        self._phone = phone
        self._api_key = api_key
        self._account_sid = account_sid
        self._auth_token = auth_token
        self._from_number = from_number
        self._to_number = to_number
        self._client = httpx.AsyncClient(timeout=15.0)

    @property
    def enabled(self) -> bool:
        if self._provider == "callmebot":
            return bool(self._phone and self._api_key)
        if self._provider == "twilio":
            return bool(self._account_sid and self._auth_token and self._to_number)
        return False

    @property
    def provider(self) -> str:
        return self._provider

    async def send(self, message: str) -> bool:
        if not self.enabled:
            log.debug("WhatsApp not configured — skipping")
            return False
        try:
            if self._provider == "callmebot":
                return await self._callmebot(message)
            if self._provider == "twilio":
                return await self._twilio(message)
            return False
        except Exception:
            log.exception("WhatsApp send failed")
            return False

    async def _callmebot(self, message: str) -> bool:
        encoded = urllib.parse.quote(message)
        url = (
            f"https://api.callmebot.com/whatsapp.php"
            f"?phone={self._phone}&text={encoded}&apikey={self._api_key}"
        )
        r = await self._client.get(url)
        ok = r.status_code == 200
        if ok:
            log.info("WhatsApp sent via CallMeBot to %s", self._phone)
        else:
            log.warning("CallMeBot failed: %d — %s", r.status_code, r.text[:120])
        return ok

    async def _twilio(self, message: str) -> bool:
        url = f"https://api.twilio.com/2010-04-01/Accounts/{self._account_sid}/Messages.json"
        r = await self._client.post(
            url,
            data={"From": self._from_number, "To": self._to_number, "Body": message},
            auth=(self._account_sid, self._auth_token),
        )
        ok = r.status_code in (200, 201)
        if ok:
            log.info("WhatsApp sent via Twilio to %s", self._to_number)
        else:
            log.warning("Twilio failed: %d — %s", r.status_code, r.text[:120])
        return ok

    async def close(self) -> None:
        await self._client.aclose()
