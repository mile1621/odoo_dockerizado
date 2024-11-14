/** @odoo-module **/

import { loadJS } from '@web/core/assets';

console.log("qr_scanner.js loaded");

let isScanning = false;  // Variable para controlar el estado del escaneo
let stream = null;
let lastNotificationTime = 0;  // Controla el intervalo entre notificaciones
const notificationInterval = 3000;  // Intervalo mínimo entre notificaciones en milisegundos



function showVisualMessage(message, type = 'info') {
    console.log("Dentro de showVisualMessage:");
    const container = document.querySelector("#qr-message-container");

    // Control de intervalo entre notificaciones
    const currentTime = Date.now();
    if (currentTime - lastNotificationTime < notificationInterval) {
        console.log("Intervalo mínimo no cumplido, omitiendo el mensaje:", message);
        return;
    }

    lastNotificationTime = currentTime;  // Actualiza el tiempo de la última notificación

    if (container) {
        const messageDiv = document.createElement("div");
        messageDiv.textContent = message;
        messageDiv.style.padding = "10px";
        messageDiv.style.marginBottom = "10px";
        messageDiv.style.borderRadius = "5px";
        messageDiv.style.color = "#fff";
        messageDiv.style.backgroundColor = type === 'error' ? "#dc3545" : "#28a745"; // Rojo para errores, verde para éxito

        container.appendChild(messageDiv);

        // Elimina el mensaje después de 3 segundos
        setTimeout(() => {
            messageDiv.remove();
        }, 3000);
    }
}

function initializeQRScanner() {
    const toggleButton = document.querySelector("#toggle-qr-scanner");
    const videoContainer = document.querySelector("#video-container");
    const videoPreview = document.querySelector("#video-preview");
    

    if (toggleButton && videoContainer && videoPreview) {
        
        console.log("Found #toggle-qr-scanner button");

        toggleButton.addEventListener("click", async () => {
            // Selecciona el `span` que contiene el ID del aviso
            console.log("Seleccionando el `span` que contiene el ID del aviso");
            const avisoField = document.querySelector("div[name='aviso_id_display'] span");
                
            // Revisar si el campo existe y tiene un valor, de lo contrario, enviar un mensaje de error
            console.log("Verificando si el campo existe y tiene un valor");
            if (!avisoField || !avisoField.innerText) {
                console.error("ID del Aviso no disponible o no encontrado. Guarda el aviso antes de iniciar el escaneo.");
                showVisualMessage("ID del Aviso no disponible o no encontrado. Guarda el aviso antes de escanear.", "error");
                return;
            }
            
            const aviso_id = avisoField.innerText.trim();  // Obtén el texto del `span` y quita los espacios en blanco
            console.log("Mostrando valor de aviso_id: ", aviso_id);



            isScanning = !isScanning;  // Cambia el estado de escaneo

            if (isScanning) {
                console.log("Starting QR Scanner");
                await loadJS('https://cdn.jsdelivr.net/npm/jsqr/dist/jsQR.min.js');
                console.log("jsQR loaded");

                stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } });
                videoContainer.style.display = "block";  // Muestra el contenedor del video
                videoPreview.srcObject = stream;
                videoPreview.play();

                const canvas = document.createElement("canvas");
                const context = canvas.getContext("2d");

                videoPreview.addEventListener("loadeddata", () => {
                    canvas.width = videoPreview.videoWidth;
                    canvas.height = videoPreview.videoHeight;

                    const scan = async () => {
                        if (!isScanning) return; // Detiene el escaneo si se desactiva

                        context.drawImage(videoPreview, 0, 0, canvas.width, canvas.height);
                        const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
                        const code = jsQR(imageData.data, imageData.width, imageData.height);

                        if (code) {
                            console.log("QR Code detected:", code.data);

                            // Mostrar mensaje visual sin detener el flujo de escaneo
                            // showVisualMessage("Código QR Detectado: " + code.data);
                            console.log("Imprimiendo el ID del aviso desde qr_scanner.js: ", window.aviso_id)

                            // Llamada `fetch` para realizar la validación del QR
                            try {
                                const response = await fetch('/web/dataset/call_kw/agenda.aviso/validate_qr', {
                                    method: 'POST',
                                    headers: {
                                        'Content-Type': 'application/json',
                                        'X-Requested-With': 'XMLHttpRequest'
                                    },
                                    body: JSON.stringify({
                                        jsonrpc: "2.0",
                                        method: "call",
                                        params: {
                                            model: "agenda.aviso",
                                            method: "validate_qr",
                                            args: [code.data, aviso_id],  // Usa aviso_id aquí
                                            kwargs: {}
                                        },
                                        id: Math.floor(Math.random() * 1000)
                                    })
                                });

                                const result = await response.json();
                                if (result.result && result.result.success) {
                                    console.log("Asistencia registrada exitosamente.");
                                    showVisualMessage("Asistencia registrada exitosamente.", "success");
                                } else {
                                    console.error("Error:", result.result ? result.result.error : "Error desconocido");
                                    const error = result.result ? result.result.error : "Error desconocido";
                                    showVisualMessage("Error: " + error, "error");
                                }
                            } catch (error) {
                                console.error("Error en la llamada fetch:", error);
                                showVisualMessage("Ocurrió un error durante la validación.", "error");
                            }
                        }

                        // Sigue escaneando en el siguiente frame sin detener el flujo
                        requestAnimationFrame(scan);
                    };
                    scan();
                });
            } else {
                // Detener el escaneo y la cámara
                if (stream) {
                    stream.getTracks().forEach(track => track.stop());
                    videoPreview.srcObject = null;
                }
                videoContainer.style.display = "none";  // Oculta el contenedor del video
                console.log("QR Scanner stopped");
            }
        });
    } else {
        console.log("No se encontró el botón #toggle-qr-scanner en el DOM, esperando...");

        const intervalId = setInterval(() => {
            const toggleButton = document.querySelector("#toggle-qr-scanner");
            const videoContainer = document.querySelector("#video-container");
            const videoPreview = document.querySelector("#video-preview");

            if (toggleButton && videoContainer && videoPreview) {
                console.log("Button #toggle-qr-scanner found after delay");
                clearInterval(intervalId);
                initializeQRScanner();
            }
        }, 500);
    }
}

document.addEventListener("DOMContentLoaded", function () {
    console.log("DOM fully loaded and parsed");
    initializeQRScanner();
});
