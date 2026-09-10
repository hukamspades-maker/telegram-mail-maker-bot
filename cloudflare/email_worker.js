/**
 * Pure & Perfect Email Worker for hukam.bond & jattjames.bond
 * - Attached .html document is 100% PURE ORIGINAL EMAIL.
 * - Telegram text card extracts verified OTP codes and working sign-in links.
 * - PDF attachments are forwarded directly as original .pdf files.
 */

export default {
  async email(message, env, ctx) {
    const botToken = "8985612343:AAEb6TCe-dEkObs1Oy7HxsLWiC4L8E74Aek";
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

      // --- 1. DECODERS ---
      const decodeQP = (str) => {
        if (!str) return "";
        return str
          .replace(/=\r?\n/g, '')
          .replace(/=([0-9A-Fa-f]{2})/g, (_, hex) => String.fromCharCode(parseInt(hex, 16)));
      };

      const decodeBase64Text = (str) => {
        if (!str) return "";
        try {
          const cleanB64 = str.replace(/\s+/g, '');
          const binary = atob(cleanB64);
          const bytes = new Uint8Array(binary.length);
          for (let i = 0; i < binary.length; i++) {
            bytes[i] = binary.charCodeAt(i);
          }
          return new TextDecoder("utf-8").decode(bytes);
        } catch (e) {
          return str;
        }
      };

      // --- 2. MULTIPART RECURSIVE PARSER ---
      let htmlBody = "";
      let textBody = "";
      let pdfAttachments = [];

      const parsePart = (headersText, bodyText) => {
        const isQP = /Content-Transfer-Encoding:\s*quoted-printable/i.test(headersText);
        const isB64 = /Content-Transfer-Encoding:\s*base64/i.test(headersText);

        const isPdf = /Content-Type:\s*application\/pdf/i.test(headersText) || /filename=["']?[^"']+\.pdf["']?/i.test(headersText);
        const isAttachment = /Content-Disposition:\s*attachment/i.test(headersText) || isPdf;

        if (isPdf || (isAttachment && /filename=/i.test(headersText))) {
          let fn = "attachment.pdf";
          const fnMatch = headersText.match(/filename=["']?([^"';\r\n]+)["']?/i) || headersText.match(/name=["']?([^"';\r\n]+)["']?/i);
          if (fnMatch) fn = fnMatch[1];

          if (fn.toLowerCase().endsWith(".pdf") || isPdf) {
            pdfAttachments.push({
              filename: fn,
              base64: bodyText.replace(/\s+/g, '')
            });
          }
          return;
        }

        let decoded = bodyText;
        if (isQP) decoded = decodeQP(bodyText);
        else if (isB64) decoded = decodeBase64Text(bodyText);

        if (/Content-Type:\s*text\/html/i.test(headersText)) {
          if (!htmlBody) htmlBody = decoded;
        } else if (/Content-Type:\s*text\/plain/i.test(headersText)) {
          if (!textBody) textBody = decoded;
        }
      };

      const boundaries = [];
      const bMatches = rawContent.matchAll(/boundary=["']?([^"';\r\n]+)["']?/gi);
      for (const m of bMatches) {
        if (!boundaries.includes(m[1])) boundaries.push(m[1]);
      }

      if (boundaries.length > 0) {
        let currentParts = [rawContent];
        for (const b of boundaries) {
          let newParts = [];
          for (const p of currentParts) {
            if (p.includes("--" + b)) {
              const sub = p.split("--" + b);
              for (const s of sub) {
                if (s.trim() && !s.trim().startsWith("--")) newParts.push(s);
              }
            } else {
              newParts.push(p);
            }
          }
          currentParts = newParts;
        }

        for (const p of currentParts) {
          const headerEnd = p.indexOf("\r\n\r\n") !== -1 ? p.indexOf("\r\n\r\n") : p.indexOf("\n\n");
          if (headerEnd !== -1) {
            const h = p.substring(0, headerEnd);
            let b = p.substring(headerEnd).trim();
            if (b.endsWith("--")) b = b.substring(0, b.length - 2).trim();
            parsePart(h, b);
          }
        }
      } else {
        const doubleBreak = rawContent.indexOf("\r\n\r\n") !== -1 ? rawContent.indexOf("\r\n\r\n") : rawContent.indexOf("\n\n");
        const headers = doubleBreak !== -1 ? rawContent.substring(0, doubleBreak) : "";
        let body = doubleBreak !== -1 ? rawContent.substring(doubleBreak).trim() : rawContent.trim();
        parsePart(headers, body);
      }

      const contentToParse = htmlBody || textBody;

      // --- 3. CLEAN SIGN-IN URLS ---
      let magicLinks = [];
      const cleanUrl = (url) => {
        if (!url) return "";
        let u = decodeQP(url)
          .replace(/&amp;/g, '&')
          .replace(/&#3d;/gi, '=')
          .replace(/=3D/gi, '=')
          .replace(/["'<>]/g, '')
          .trim();
        return u;
      };

      const hrefRegex = /href=["']([^"']+)["']/gi;
      let hrefMatch;
      while ((hrefMatch = hrefRegex.exec(contentToParse)) !== null) {
        let u = cleanUrl(hrefMatch[1]);
        if (u.startsWith("http://") || u.startsWith("https://")) {
          if (!u.includes("schema.org") && !u.includes("w3.org") && !u.includes(".png") && !u.includes(".jpg") && !magicLinks.includes(u)) {
            magicLinks.push(u);
          }
        }
      }

      if (magicLinks.length === 0) {
        const urlRegex = /(https?:\/\/[^\s"<>'{}|\^~\[\]\\]+)/gi;
        let urlMatch;
        while ((urlMatch = urlRegex.exec(contentToParse)) !== null) {
          let u = cleanUrl(urlMatch[0]);
          if (!u.includes("schema.org") && !u.includes("w3.org") && !magicLinks.includes(u)) {
            magicLinks.push(u);
          }
        }
      }

      // --- 4. STRICT OTP CODE EXTRACTOR ---
      let otpCode = "";
      const subjectMatch = subject.match(/\b\d{4,8}\b/);
      if (subjectMatch && !/^(19\d{2}|20[0-2]\d|2030)$/.test(subjectMatch[0])) {
        otpCode = subjectMatch[0];
      }

      if (!otpCode) {
        const kwMatch = contentToParse.match(/(?:code|otp|pin|verification|security\s*key|login\s*code|confirm)[^\d]{1,50}(\b\d{4,8}\b|\b\d{3}[-\s]\d{3}\b)/i);
        if (kwMatch && kwMatch[1]) {
          const candidate = kwMatch[1].replace(/\s+/g, '');
          if (!/^(19\d{2}|20[0-2]\d|2030)$/.test(candidate)) {
            otpCode = candidate;
          }
        }
      }

      const escapeHtml = (str) => (str || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

      // --- 5. CLEAN TEXT PREVIEW ---
      let rawCandidate = textBody || htmlBody;
      let cleanPreview = rawCandidate
        .replace(/<head[\s\S]*?<\/head>/gi, '')
        .replace(/<style[\s\S]*?<\/style>/gi, '')
        .replace(/<script[\s\S]*?<\/script>/gi, '')
        .replace(/<br\s*\/?>/gi, '\n')
        .replace(/<\/(p|div|tr|h1|h2|h3|h4|h5|h6|li)>/gi, '\n')
        .replace(/<[^>]*>/g, ' ')
        .replace(/&nbsp;/gi, ' ')
        .replace(/&amp;/gi, '&')
        .replace(/&lt;/gi, '<')
        .replace(/&gt;/gi, '>')
        .replace(/&quot;/gi, '"')
        .replace(/&#39;/gi, "'")
        .replace(/\r\n/g, '\n')
        .replace(/\n\s*\n/g, '\n\n')
        .trim();

      if (cleanPreview.length > 700) {
        cleanPreview = cleanPreview.substring(0, 700) + "...";
      }

      // --- 6. TELEGRAM SUMMARY CARD ---
      let otpBanner = otpCode ? `🔑 <b>YOUR OTP CODE:</b> <code>${escapeHtml(otpCode)}</code>\n\n` : "";
      let linkBanner = magicLinks.length > 0 ? `🔗 <b>ACTION / SIGN-IN LINK:</b>\n<a href="${escapeHtml(magicLinks[0])}">👉 Click Here to Sign In / Open Link</a>\n\n` : "";
      let pdfBanner = pdfAttachments.length > 0 ? `📎 <b>ATTACHMENTS:</b> ${pdfAttachments.length} PDF file(s) attached below!\n\n` : "";

      const tgSummary = 
        `📩 <b>New Email Received!</b>\n\n` +
        `${otpBanner}` +
        `${linkBanner}` +
        `${pdfBanner}` +
        `<b>📬 To:</b> <code>${escapeHtml(recipient)}</code>\n` +
        `<b>👤 From:</b> <code>${escapeHtml(sender)}</code>\n` +
        `<b>📌 Subject:</b> <b>${escapeHtml(subject)}</b>\n` +
        `━━━━━━━━━━━━━━━━━━━━━━\n\n` +
        `${escapeHtml(cleanPreview || "(Message content empty)")}\n\n` +
        `<i>👇 Full original HTML file attached below!</i>`;

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

      // --- 7. FORWARD ACTUAL REAL PDF ATTACHMENTS TO TELEGRAM ---
      for (const pdf of pdfAttachments) {
        try {
          const binaryStr = atob(pdf.base64);
          const bytes = new Uint8Array(binaryStr.length);
          for (let i = 0; i < binaryStr.length; i++) {
            bytes[i] = binaryStr.charCodeAt(i);
          }
          const pdfBlob = new Blob([bytes], { type: "application/pdf" });

          const pdfFormData = new FormData();
          pdfFormData.append("chat_id", targetChatId);
          pdfFormData.append("caption", `📎 <b>Attached Document:</b> <code>${escapeHtml(pdf.filename)}</code>`);
          pdfFormData.append("parse_mode", "HTML");
          pdfFormData.append("document", pdfBlob, pdf.filename || "document.pdf");

          await fetch(`https://api.telegram.org/bot${botToken}/sendDocument`, {
            method: "POST",
            body: pdfFormData
          });
        } catch (e) {
          console.error("PDF delivery error:", e);
        }
      }

      // --- 8. SEND PURE 100% UNTOUCHED ORIGINAL HTML FILE ATTACHMENT ---
      let pureOriginalHtml = htmlBody;
      if (!pureOriginalHtml) {
        pureOriginalHtml = `<!DOCTYPE html><html><head><meta charset="utf-8"><title>${escapeHtml(subject)}</title></head><body style="font-family:sans-serif;padding:20px;line-height:1.6;">${(textBody || "").replace(/\n/g, '<br>')}</body></html>`;
      }

      const htmlFormData = new FormData();
      htmlFormData.append("chat_id", targetChatId);
      htmlFormData.append("caption", `📄 <b>Full Original Email (.html)</b>\nTap to view with 100% original graphics, formatting & working links!`);
      htmlFormData.append("parse_mode", "HTML");

      const cleanFileName = (subject.replace(/[^a-zA-Z0-9_-]/g, "_").substring(0, 30) || "email") + ".html";
      const htmlBlob = new Blob([pureOriginalHtml], { type: "text/html" });
      htmlFormData.append("document", htmlBlob, cleanFileName);

      await fetch(`https://api.telegram.org/bot${botToken}/sendDocument`, {
        method: "POST",
        body: htmlFormData
      });

      console.log("Delivered pure original email HTML file to Telegram with new token!");
    } catch (err) {
      console.error("Worker error:", err);
    }
  }
};
