require('dotenv').config();
const { Client, LocalAuth, MessageMedia } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const axios = require('axios');
const fs = require('fs');
const path = require('path');
const FormData = require('form-data');

// --- Configuración Inicial ---
const ALLOWED_PHONE = (process.env.ALLOW_PHONE_NUMBER || '').trim();
const API_URL = process.env.API_BACKEND_URL || 'http://localhost:8000/api/chat';
const API_TRANSCRIBE_URL = process.env.API_TRANSCRIBE_URL || 'http://localhost:8000/api/transcribe';

if (!ALLOWED_PHONE) {
    console.error('❌ ERROR CRÍTICO: ALLOW_PHONE_NUMBER no está definido en el .env');
    process.exit(1);
}

console.log(`🔒 El bot sólo responderá al número: ${ALLOWED_PHONE}`);

// Inicializamos el cliente guardando la sesion localmente
const client = new Client({
    authStrategy: new LocalAuth(),
    puppeteer: {
        args: ['--no-sandbox', '--disable-setuid-sandbox'],
        // En Windows, descomenta y ajusta si es necesario:
        // executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
    }
});

// ─── Eventos del cliente ────────────────────────────────────────────────────

client.on('qr', (qr) => {
    console.log('\n📱 Escanea este código QR con el WhatsApp del bot:');
    qrcode.generate(qr, { small: true });
});

client.on('ready', () => {
    console.log('✅ Cliente de WhatsApp listo e integrado.');
});

client.on('auth_failure', (msg) => {
    console.error('❌ Fallo de autenticación:', msg);
});

client.on('disconnected', (reason) => {
    console.warn('⚠️ Cliente desconectado:', reason);
    console.warn('🔄 Reinicia el bot manualmente con: npm start');
    process.exit(0);
});

// ─── Procesamiento de mensajes ───────────────────────────────────────────────

client.on('message_create', async (msg) => {
    try {
        let senderNumber = msg.from.split('@')[0];

        // 🚨 MÁGIA: Si WhatsApp nos oculta tu número detrás de un @lid, forzamos a revelar tu número real
        if (msg.from.includes('@lid')) {
            try {
                const contact = await msg.getContact();
                if (contact && contact.number) {
                    senderNumber = contact.number;
                }
            } catch (e) {
                console.log("[DEBUG] Fallo al revelar contacto LID");
            }
        }

        // DEBUG: Mostrar TODOS los mensajes que llegan (quitar cuando ya funcione)
        console.log(`[DEBUG] Evento mensaje: RealSender=${senderNumber} \tfrom=${msg.from} \tto=${msg.to || 'N/A'} \tfromMe=${msg.fromMe} \tbody="${(msg.body||'').substring(0,30)}"`);

        // Evitar bucle infinito: Si el mensaje empieza con "🩺" (la firma del bot), ignorarlo
        if (msg.body && msg.body.startsWith('🩺')) return;

        // Ignorar grupos, estados y numeros de sistema de WhatsApp/Meta silenciosamente
        if (
            msg.from === 'status@broadcast' ||
            msg.from.includes('@g.us') ||
            msg.isStatus ||
            senderNumber.length > 14
        ) return;

        // Whitelist: el numero que envia O el numero que recibe debe ser el autorizado
        const toNumber = (msg.to || '').split('@')[0].trim();
        const isFromAllowed = senderNumber.trim() === ALLOWED_PHONE;
        const isToAllowed = toNumber === ALLOWED_PHONE;

        if (!isFromAllowed && !isToAllowed) {
            console.log(`[BLOQUEADO] Mensaje de: ${senderNumber}`);
            return;
        }

        const chat = await msg.getChat();
        await chat.sendStateTyping();

        let messageText = msg.body;

        // ── Manejo de mensajes de voz/audio ──────────────────────────────
        if (msg.hasMedia && (msg.type === 'audio' || msg.type === 'ptt')) {
            console.log(`\n🎙️ Nota de voz recibida de ${senderNumber}. Transcribiendo...`);
            try {
                const media = await msg.downloadMedia();
                const audioBuffer = Buffer.from(media.data, 'base64');
                const tmpPath = path.join(__dirname, `tmp_audio_${Date.now()}.ogg`);
                fs.writeFileSync(tmpPath, audioBuffer);

                const form = new FormData();
                form.append('audio', fs.createReadStream(tmpPath));

                const transcribeResponse = await axios.post(API_TRANSCRIBE_URL, form, {
                    headers: form.getHeaders(),
                    timeout: 60000
                });

                fs.unlinkSync(tmpPath); // Limpiamos el archivo temporal
                messageText = transcribeResponse.data.text;
                console.log(`   -> Transcripción: "${messageText}"`);

                if (!messageText || messageText.trim() === '') {
                    await chat.clearState();
                    await msg.reply('No pude entender tu nota de voz, mamá ❤️ ¿Puedes repetirlo con texto o hablar más despacio?');
                    return;
                }
            } catch (audioErr) {
                console.error('❌ Error transcribiendo audio:', audioErr.message);
                await chat.clearState();
                await msg.reply('No pude escuchar bien tu mensaje de voz, mi amor 😊 ¿Puedes escribirme la pregunta?');
                return;
            }
        }

        // ── Manejo de mensajes de texto normales ─────────────────────────
        if (!messageText || messageText.trim() === '') return;

        console.log(`\n💬 Mensaje de ${senderNumber}: ${messageText}`);

        const response = await axios.post(API_URL, {
            message: messageText,
            user_id: senderNumber
        }, { timeout: 120000 });

        const reply = response.data.reply;
        const source = response.data.source;

        console.log(`🤖 Respuesta (vía ${source}): ${reply}`);

        // Quitamos estado 'escribiendo' y enviamos (añadiendo prefijo 🩺)
        await chat.clearState();
        await msg.reply(`🩺 ${reply}`);

    } catch (error) {
        console.error('❌ Error general procesando el mensaje:', error.message);

        // Mensaje de emergencia empático
        try {
            const chat = await msg.getChat();
            await chat.clearState();
            await msg.reply('🩺 Hola mamá amor, dame un momentito que mi sistema se quedó pensando... Ahorita te respondo bonito ❤️🌿');
        } catch (e) {
            console.error('Error enviando mensaje de emergencia:', e.message);
        }
    }
});

// ─── Arranque ────────────────────────────────────────────────────────────────
console.log('🚀 Iniciando IADESALUD WhatsApp Bot...');
client.initialize();
