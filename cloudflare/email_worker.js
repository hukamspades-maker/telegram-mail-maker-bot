export default {
  async email(message, env, ctx) {
    const botToken = "8985612343:AAGqO-hTyhoSfWKrWQOFqlOWZ4r4yTiB-44";
    const targetChatId = "8603872187";

    try {
      const recipient = message.to || "hukam.bond";
      const sender = message.from || "Unknown Sender";
      const subject = message.headers.get("subject") || "(No Subject)";

      let rawContent = "";
      try {
        if (message.raw) {
          rawContent = await new Response(message.raw).text();
        }
      } catch (e) {
        rawContent = "";
      }

      // 1. Extract HTML and Text Body
      let htmlBody = "";
      let textBody = "";

      if (rawContent.includes("Content-Type: text/html")) {
        const parts = rawContent.split(/Content-Type:\s*text\/html/i);
        if (parts.length > 1) {
          const bodyPart = parts[1].split(/--[a-zA-Z0-9_-]{10,}/)[0];
          const headerEnd = bodyPart.indexOf("\r\n\r\n") !== -1 ? bodyPart.indexOf("\r\n\r\n") : bodyPart.indexOf("\n\n");
          htmlBody = headerEnd !== -1 ? bodyPart.substring(headerEnd).trim() : bodyPart.trim();
        }
      }

      if (!htmlBody && rawContent.includes("Content-Type: text/plain")) {
        const parts = rawContent.split(/Content-Type:\s*text\/plain/i);
        if (parts.length > 1) {
          const bodyPart = parts[1].split(/--[a-zA-Z0-9_-]{10,}/)[0];
          const headerEnd = bodyPart.indexOf("\r\n\r\n") !== -1 ? bodyPart.indexOf("\r\n\r\n") : bodyPart.indexOf("\n\n");
          textBody = headerEnd !== -1 ? bodyPart.substring(headerEnd).trim() : bodyPart.trim();
        }
      }

      if (!htmlBody && !textBody) {
        const doubleBreak = rawContent.indexOf("\r\n\r\n") !== -1 ? rawContent.indexOf("\r\n\r\n") : rawContent.indexOf("\n\n");
        textBody = doubleBreak !== -1 ? rawContent.substring(doubleBreak).trim() : rawContent.trim();
      }

      // Quoted-printable decoder
      const decodeQP = (str) => {
        return str
          .replace(/=\r?\n/g, '')
          .replace(/=([37][0-9A-F])/gi, (m, hex) => String.fromCharCode(parseInt(hex, 16)))
          .replace(/=20/g, ' ')
          .replace(/=3D/gi, '=');
      };

      if (htmlBody) htmlBody = decodeQP(htmlBody);
      if (textBody) textBody = decodeQP(textBody);

      const contentToParse = htmlBody || textBody;

      // 2. Extract Action / Magic Links
      let magicLinks = [];
      const urlRegex = /(https?:\/\/[^\s"<>'{}|\^~\[\]\\]+)/gi;
      let urlMatch;
      while ((urlMatch = urlRegex.exec(contentToParse)) !== null) {
        const url = urlMatch[0];
        if (!url.includes("schema.org") && !url.includes("w3.org") && !url.includes(".png") && !url.includes(".jpg")) {
          if (!magicLinks.includes(url)) {
            magicLinks.push(url);
          }
        }
      }

      // 3. Extract OTP Code
      let otpCode = "";
      const subjectMatch = subject.match(/\b\d{3,4}[-\s]?\d{3,4}\b/);
      if (subjectMatch) {
        otpCode = subjectMatch[0];
      } else {
        const bodyMatch = contentToParse.match(/(?:code|otp|pin|verification|login|confirm)[^\d]*(\b\d{3,4}[-\s]?\d{3,4}\b|\b\d{4,8}\b)/i);
        if (bodyMatch && bodyMatch[1]) {
          otpCode = bodyMatch[1];
        } else {
          const allDigits = contentToParse.match(/\b\d{4,8}\b/g);
          if (allDigits) {
            const valid = allDigits.find(d => !/^(202[4-9]|203[0-9])$/.test(d));
            if (valid) otpCode = valid;
          }
        }
      }

      const escapeHtml = (str) => (str || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

      // Format Telegram summary card
      let otpBanner = otpCode ? `🔑 <b>YOUR OTP / CODE:</b> <code>${escapeHtml(otpCode)}</code>\n\n` : "";
      let linkBanner = magicLinks.length > 0 ? `🔗 <b>ACTION / SIGN-IN LINK:</b>\n<a href="${magicLinks[0]}">👉 Click Here to Sign In / Open Link</a>\n\n` : "";

      let previewText = (textBody || htmlBody.replace(/<[^>]*>/g, ' '))
        .replace(/\r\n/g, '\n')
        .replace(/\n\s*\n/g, '\n\n')
        .trim();

      if (previewText.length > 800) {
        previewText = previewText.substring(0, 800) + "...";
      }

      const tgSummary = 
        `📩 <b>New Email Received!</b>\n\n` +
        `${otpBanner}` +
        `${linkBanner}` +
        `<b>📬 To:</b> <code>${escapeHtml(recipient)}</code>\n` +
        `<b>👤 From:</b> <code>${escapeHtml(sender)}</code>\n` +
        `<b>📌 Subject:</b> <b>${escapeHtml(subject)}</b>\n` +
        `━━━━━━━━━━━━━━━━━━━━━━\n\n` +
        `${escapeHtml(previewText || "(Message body empty)")}\n\n` +
        `<i>👇 Full interactive HTML file attached below!</i>`;

      // A. Send Telegram Text Summary Card
      await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          chat_id: targetChatId,
          text: tgSummary,
          parse_mode: "HTML",
          disable_web_page_preview: false
        })
      });

      // B. Create Full .HTML Document File Attachment with Interactive Styles & Links
      const fullHtmlDoc = `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${escapeHtml(subject)}</title>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #f4f6f9; margin: 0; padding: 20px; color: #222; }
  .email-container { max-width: 680px; margin: 0 auto; background: #ffffff; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); padding: 30px; border: 1px solid #e1e4e8; }
  .header { border-bottom: 2px solid #f0f2f5; padding-bottom: 15px; margin-bottom: 20px; }
  .header h1 { font-size: 20px; margin: 0 0 10px 0; color: #0969da; }
  .meta-row { font-size: 14px; color: #57606a; margin: 4px 0; }
  .otp-box { background: #f6feef; border: 1px solid #2da44e; border-radius: 8px; padding: 15px; margin: 20px 0; text-align: center; }
  .otp-code { font-size: 28px; font-weight: bold; letter-spacing: 4px; color: #1a7f37; font-family: monospace; }
  .content { font-size: 15px; line-height: 1.6; color: #1f2328; margin-top: 20px; }
  a { color: #0969da; text-decoration: underline; word-break: break-all; }
  .btn-action { display: inline-block; padding: 12px 24px; background: #0969da; color: #ffffff !important; text-decoration: none; border-radius: 6px; font-weight: bold; margin: 15px 0; text-align: center; }
</style>
</head>
<body>
  <div class="email-container">
    <div class="header">
      <h1>${escapeHtml(subject)}</h1>
      <div class="meta-row"><b>From:</b> ${escapeHtml(sender)}</div>
      <div class="meta-row"><b>To:</b> ${escapeHtml(recipient)}</div>
    </div>
    ${otpCode ? `<div class="otp-box"><div style="font-size:12px;color:#2da44e;font-weight:bold;margin-bottom:5px;">VERIFICATION CODE</div><div class="otp-code">${escapeHtml(otpCode)}</div></div>` : ''}
    ${magicLinks.length > 0 ? `<div style="text-align:center;"><a href="${magicLinks[0]}" class="btn-action" target="_blank">👉 Open Action Link / Sign In</a></div>` : ''}
    <div class="content">
      ${htmlBody || (textBody || "").replace(/\n/g, '<br>')}
    </div>
  </div>
</body>
</html>`;

      // Send .HTML File Document to Telegram
      const formData = new FormData();
      formData.append("chat_id", targetChatId);
      formData.append("caption", `📄 <b>Full Original Email (.html)</b>\nTap to view with 100% graphics, full formatting & working links!`);
      formData.append("parse_mode", "HTML");

      const cleanFileName = (subject.replace(/[^a-zA-Z0-9_-]/g, "_").substring(0, 30) || "email") + ".html";
      const fileBlob = new Blob([fullHtmlDoc], { type: "text/html" });
      formData.append("document", fileBlob, cleanFileName);

      await fetch(`https://api.telegram.org/bot${botToken}/sendDocument`, {
        method: "POST",
        body: formData
      });

      console.log("Delivered summary + full HTML document file to Telegram!");
    } catch (err) {
      console.error("Worker error:", err);
    }
  }
};
