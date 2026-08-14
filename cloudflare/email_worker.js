export default {
  async email(message, env, ctx) {
    const botToken = "8985612343:AAGqO-hTyhoSfWKrWQOFqlOWZ4r4yTiB-44";
    const chatId = "8603872187";

    try {
      const to = message.to || "hukam.bond";
      const from = message.from || "Unknown Sender";
      const subject = message.headers.get("subject") || "(No Subject)";

      let body = "";
      try {
        body = await new Response(message.raw).text();
      } catch (e) {
        body = "";
      }

      // Extract 4 to 8 digit OTP code
      let otp = "";
      const match = (subject + " " + body).match(/\b\d{4,8}\b/);
      if (match) {
        otp = match[0];
      }

      // Clean body text
      let cleanText = body.replace(/<[^>]*>/g, ' ').replace(/\r\n/g, '\n').trim();
      if (cleanText.length > 1000) cleanText = cleanText.substring(0, 1000) + "...";

      const otpText = otp ? `\n🔑 OTP CODE: ${otp}\n` : "";

      const msgText = 
        `📩 NEW EMAIL RECEIVED!\n${otpText}\n` +
        `📬 To: ${to}\n` +
        `👤 From: ${from}\n` +
        `📌 Subject: ${subject}\n` +
        `----------------------------------------\n\n` +
        `${cleanText || "(Content preview unavailable)"}`;

      await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          chat_id: chatId,
          text: msgText
        })
      });
    } catch (err) {
      // Emergency fallback send if any error happens
      await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          chat_id: chatId,
          text: `📩 Email received for ${message.to || 'hukam.bond'} from ${message.from || 'Sender'}`
        })
      });
    }
  }
};
