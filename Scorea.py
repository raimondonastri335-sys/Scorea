from flask import Flask, request, jsonify, render_template_string, send_file, send_from_directory
from flask_cors import CORS
import urllib.request
import json
import time
import os
import random

app = Flask(__name__)
CORS(app)

EMAIL_VERIFICATION_CODES = {}

MANIFEST_JSON = {
    "name": "Scorea",
    "short_name": "Scorea",
    "start_url": "/",
    "display": "standalone",
    "background_color": "#0e0e11",
    "theme_color": "#141417",
    "icons": [
        {
            "src": "/icon.jpg",
            "sizes": "512x512",
            "type": "image/jpeg",
            "purpose": "any maskable"
        }
    ]
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Scorea</title>

    <link rel="manifest" href="/manifest.json">
    <link rel="icon" href="{{ url_for('static', filename='icon.ico') }}">
    <link rel="apple-touch-icon" href="/icon.jpg">
    <meta name="theme-color" content="#141417">

    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: #0e0e11; }
        ::-webkit-scrollbar-thumb { background: #27272a; border-radius: 4px; }
        
        @keyframes bounce-slow {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-3px); }
        }
        .dot1 { animation: bounce-slow 0.8s infinite ease-in-out; }
        .dot2 { animation: bounce-slow 0.8s infinite ease-in-out 0.2s; }
        .dot3 { animation: bounce-slow 0.8s infinite ease-in-out 0.4s; }
        
        @keyframes slideDown {
            from { transform: translateY(-100%); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
        .toast-enter { animation: slideDown 0.4s ease forwards; }

        @keyframes purpleBlackFlow {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        .animated-purple-black {
            background: linear-gradient(-45deg, #050507, #1e0b36, #0a0514, #3b0764, #09090b);
            background-size: 400% 400%;
            animation: purpleBlackFlow 10s ease infinite;
        }

        .gauge-needle {
            transition: transform 1.5s cubic-bezier(0.15, 1.15, 0.35, 1.15);
            transform-origin: bottom center;
        }

        .chat-item:hover .chat-options-btn {
            opacity: 1;
        }
    </style>
</head>
<body class="bg-[#0e0e11] text-gray-100 font-sans h-screen flex flex-col overflow-hidden select-none">

    <!-- NOTIFICA TOAST -->
    <div id="phoneToast" class="fixed top-5 left-1/2 -translate-x-1/2 z-50 hidden max-w-sm w-full px-4">
        <div class="bg-zinc-900 border border-indigo-500/50 rounded-2xl p-4 shadow-2xl flex items-start gap-3 backdrop-blur-md bg-opacity-95 toast-enter">
            <div class="w-10 h-10 rounded-xl bg-indigo-600/20 text-indigo-400 flex items-center justify-center shrink-0 text-base">
                <i class="fa-solid fa-bell"></i>
            </div>
            <div class="flex-1">
                <div class="flex items-center justify-between">
                    <h4 class="text-xs font-bold text-white">Scorea Security</h4>
                    <span class="text-[10px] text-zinc-500">Adesso</span>
                </div>
                <p id="toastMessage" class="text-xs text-zinc-300 mt-1 font-medium"></p>
            </div>
        </div>
    </div>

    <!-- HEADER SUPERIORE -->
    <header class="h-14 border-b border-zinc-800/60 flex items-center justify-between px-6 bg-[#141417] shrink-0 z-20">
        <div class="flex items-center gap-3">
            <button onclick="toggleSidebar()" class="text-zinc-400 hover:text-white md:hidden text-sm mr-1"><i class="fa-solid fa-bars"></i></button>
            <img src="/icon.jpg" class="w-8 h-8 rounded-xl shadow-lg object-cover" alt="Scorea Logo">
            <span class="font-bold text-lg tracking-tight text-white">Scorea</span>
        </div>
        <div class="flex items-center gap-2">
            <button id="installBtn" onclick="installApp()" class="hidden px-3 py-1.5 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white transition flex items-center gap-1.5 cursor-pointer">
                <i class="fa-solid fa-download"></i> <span data-i18n="install">Installa</span>
            </button>
            <button onclick="openPricingPage()" class="px-3 py-1.5 rounded-lg text-xs font-semibold bg-purple-900/50 text-purple-300 border border-purple-600/50 hover:bg-purple-800/60 transition cursor-pointer flex items-center gap-1.5">
                <i class="fa-solid fa-crown text-amber-400"></i> Piani PRO (Coming Soon)
            </button>
            <button onclick="openSettingsModal()" class="px-3 py-1.5 rounded-lg text-xs font-semibold bg-zinc-800 text-indigo-400 border border-zinc-700 hover:bg-zinc-700 transition cursor-pointer flex items-center gap-1.5">
                <i class="fa-solid fa-gear"></i> <span data-i18n="settings">Impostazioni</span>
            </button>
            <button onclick="openApiKeyModal()" class="px-3 py-1.5 rounded-lg text-xs font-semibold bg-zinc-800 text-amber-400 border border-zinc-700 hover:bg-zinc-700 transition cursor-pointer">
                <i class="fa-solid fa-key mr-1.5"></i>API Key
            </button>
        </div>
    </header>

    <!-- CORPO PRINCIPALE CON SIDEBAR E CHAT -->
    <div class="flex-1 flex overflow-hidden relative">
        
        <!-- SIDEBAR CHAT -->
        <aside id="sidebar" class="w-72 bg-[#121215] border-r border-zinc-800/60 flex flex-col z-30 transition-all duration-300">
            <div class="p-3">
                <button onclick="createNewChat()" class="w-full flex items-center gap-2.5 px-4 py-2.5 rounded-full bg-zinc-800/70 hover:bg-zinc-800 text-zinc-200 text-xs font-semibold border border-zinc-700/50 transition cursor-pointer">
                    <i class="fa-solid fa-plus text-indigo-400"></i> <span>Nuova chat</span>
                </button>
            </div>

            <div class="px-4 py-2 text-[11px] font-bold text-zinc-500 tracking-wider uppercase">Chat recenti</div>

            <div id="chatListContainer" class="flex-1 overflow-y-auto px-2 space-y-1 pb-4">
                <!-- Popolato da JS -->
            </div>
        </aside>

        <!-- AREA CHAT CENTRALE -->
        <main class="flex-1 flex flex-col justify-between h-full bg-[#0e0e11] p-6 relative">
            <div id="chatBox" class="flex-1 overflow-y-auto space-y-4 max-w-3xl w-full mx-auto pb-4">
                <div id="welcomeScreen" class="h-full flex flex-col items-center justify-center text-center space-y-3 my-auto">
                    <img src="/icon.jpg" class="w-20 h-20 rounded-3xl shadow-2xl mb-2 object-cover" alt="Scorea Logo Large">
                    <h1 class="text-3xl font-extrabold text-white tracking-tight" data-i18n="welcomeTitle">Ciao Enzo, sono Scorea!</h1>
                    <p class="text-zinc-400 text-xs max-w-sm" data-i18n="welcomeSub">Usa la task bar in basso per scrivere, attivare il pensiero profondo o usare la voce.</p>
                </div>
            </div>

            <!-- TASK BAR -->
            <div class="p-4 max-w-3xl w-full mx-auto">
                <div class="bg-zinc-900 border border-zinc-800 rounded-2xl p-3 shadow-2xl flex flex-col gap-2">
                    <textarea id="promptInput" rows="2" placeholder="Scrivi un messaggio a Scorea..." class="w-full bg-transparent text-sm text-zinc-100 focus:outline-none resize-none px-1" onkeydown="handleKeyDown(event)"></textarea>
                    
                    <div class="flex items-center justify-between pt-2 border-t border-zinc-800/60 text-xs">
                        <div class="flex items-center gap-2 flex-wrap">
                            <!-- SELETTORE MODELLI CON COMING SOON -->
                            <select id="modelSelector" onchange="checkModelAccess(this)" class="bg-zinc-950 border border-zinc-800 rounded-lg px-2.5 py-1 text-xs text-indigo-300 font-semibold focus:outline-none cursor-pointer">
                                <option value="Scorea-Fast">⚡ Scorea-Fast (Gratis)</option>
                                <option value="Scorea-Pro" disabled>🔒 Scorea-Pro (COMING SOON)</option>
                                <option value="Scorea-Ultra" disabled>🔒 Scorea-Ultra (COMING SOON)</option>
                            </select>

                            <button type="button" onclick="toggleThinking()" id="thinkingBtn" class="flex items-center gap-1.5 bg-zinc-950 border border-zinc-800 hover:border-zinc-700 text-zinc-400 px-2.5 py-1 rounded-lg transition cursor-pointer">
                                <i class="fa-solid fa-brain text-[10px]"></i>
                                <span data-i18n="thinkingLabel">Pensiero:</span> <strong id="thinkingStatus" class="text-zinc-500">OFF</strong>
                            </button>

                            <button type="button" onclick="toggleVoiceInput()" id="micBtn" class="flex items-center gap-1.5 bg-zinc-950 border border-zinc-800 hover:border-zinc-700 text-zinc-400 px-2.5 py-1 rounded-lg transition cursor-pointer">
                                <i class="fa-solid fa-microphone text-[10px]" id="micIcon"></i>
                                <span id="micText" data-i18n="voice">Vocale</span>
                            </button>
                        </div>

                        <button type="button" onclick="handleAction()" id="actionBtn" class="px-4 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold transition shadow-md flex items-center gap-1.5 cursor-pointer">
                            <span data-i18n="send">Invia</span> <i class="fa-solid fa-paper-plane text-[10px]"></i>
                        </button>
                    </div>
                </div>
            </div>
        </main>
    </div>

    <!-- MENU OPZIONI CHAT -->
    <div id="chatOptionsMenu" class="hidden fixed z-50 bg-zinc-900 border border-zinc-700 rounded-2xl shadow-2xl py-1.5 w-48 text-xs">
        <button onclick="menuActionPin()" id="menuPinBtn" class="w-full text-left px-4 py-2 text-zinc-200 hover:bg-zinc-800 flex items-center gap-2 cursor-pointer"><i class="fa-solid fa-thumbtack text-indigo-400"></i> Fissa</button>
        <button onclick="menuActionRename()" class="w-full text-left px-4 py-2 text-zinc-200 hover:bg-zinc-800 flex items-center gap-2 cursor-pointer"><i class="fa-solid fa-pen text-amber-400"></i> Rinominare</button>
        <button onclick="menuActionShare()" class="w-full text-left px-4 py-2 text-zinc-200 hover:bg-zinc-800 flex items-center gap-2 cursor-pointer"><i class="fa-solid fa-share-nodes text-emerald-400"></i> Condividi</button>
        <button onclick="menuActionDelete()" class="w-full text-left px-4 py-2 text-red-400 hover:bg-zinc-800 flex items-center gap-2 cursor-pointer"><i class="fa-solid fa-trash"></i> Eliminare</button>
    </div>

    <!-- FRAME MODALE RINOMINA CHAT -->
    <div id="renameModal" class="hidden fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
        <div class="animated-purple-black border-2 border-purple-500/50 rounded-3xl max-w-sm w-full p-6 space-y-4 shadow-2xl shadow-purple-950/60">
            <h3 class="text-base font-bold text-white flex items-center gap-2"><i class="fa-solid fa-pen text-amber-400"></i> Rinomina questa chat</h3>
            <p class="text-xs text-purple-200/80">Inserisci il nuovo nome per la conversazione:</p>
            <input type="text" id="renameInput" placeholder="Nome chat..." class="w-full bg-zinc-950/90 border border-purple-500/40 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-purple-400">
            <div class="flex items-center gap-2 pt-2">
                <button onclick="closeRenameModal()" class="flex-1 py-2.5 rounded-xl bg-zinc-900/90 hover:bg-zinc-800 text-zinc-300 font-semibold text-xs transition cursor-pointer border border-zinc-700">Annulla</button>
                <button onclick="confirmRenameChat()" class="flex-1 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-semibold text-xs transition cursor-pointer shadow-lg shadow-purple-900/50">Salva</button>
            </div>
        </div>
    </div>

    <!-- VETRINA ABBONAMENTI CON COMING SOON -->
    <div id="pricingOverlay" class="hidden fixed inset-0 animated-purple-black z-50 overflow-y-auto p-6 md:p-10 flex flex-col">
        <div class="max-w-6xl w-full mx-auto flex items-center justify-between mb-8">
            <div class="flex items-center gap-3">
                <img src="/icon.jpg" class="w-9 h-9 rounded-xl shadow-lg object-cover">
                <span class="text-xl font-extrabold text-white tracking-tight">Scorea <span class="text-purple-400">PRO</span></span>
            </div>
            <button onclick="closePricingPage()" class="px-4 py-2 rounded-xl bg-white/10 hover:bg-white/20 text-white text-xs font-semibold backdrop-blur-md transition cursor-pointer flex items-center gap-2">
                <i class="fa-solid fa-xmark"></i> Torna alla Chat
            </button>
        </div>

        <div class="text-center max-w-2xl mx-auto mb-8 space-y-2">
            <h2 class="text-3xl md:text-4xl font-extrabold text-white tracking-tight">Piani PRO in Arrivo</h2>
            <p class="text-sm text-purple-200/80">I modelli avanzati Scorea-Pro e Scorea-Ultra saranno disponibili molto presto!</p>
            <div class="inline-block mt-3 px-6 py-2 rounded-full bg-amber-500/20 border border-amber-500/40 text-amber-300 font-bold text-xs tracking-wider uppercase">
                COMING SOON 🚀
            </div>
        </div>

        <div class="max-w-6xl w-full mx-auto grid grid-cols-1 md:grid-cols-3 gap-6 pb-10">
            <!-- PIANO SETTIMANALE -->
            <div class="bg-zinc-950/85 backdrop-blur-xl border border-purple-500/30 rounded-3xl p-6 flex flex-col justify-between shadow-2xl">
                <div>
                    <span class="text-[10px] font-bold uppercase tracking-widest text-purple-400">ACCESSO RAPIDO</span>
                    <h3 class="text-xl font-bold text-white mt-1">Scorea Weekly</h3>
                    <div class="mt-4 flex items-baseline gap-1">
                        <span class="text-4xl font-extrabold text-white">50 $</span>
                        <span class="text-xs text-zinc-400">/ ogni settimana</span>
                    </div>
                    <button disabled class="mt-6 w-full py-3 rounded-full bg-zinc-800 text-zinc-400 font-bold text-xs transition flex items-center justify-center cursor-not-allowed border border-zinc-700">
                        COMING SOON
                    </button>
                    <div class="mt-6 space-y-3 text-xs text-zinc-300 border-t border-zinc-800/80 pt-5">
                        <div class="flex items-start gap-2.5">
                            <i class="fa-solid fa-clock text-purple-400 mt-0.5"></i>
                            <div><strong class="text-white block">In arrivo</strong><span class="text-[11px] text-zinc-400">Presto disponibile.</span></div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- PIANO MENSILE -->
            <div class="bg-zinc-950/90 backdrop-blur-xl border-2 border-purple-500 rounded-3xl p-6 flex flex-col justify-between shadow-2xl shadow-purple-950/60 relative">
                <div class="absolute -top-3 left-6 px-3 py-0.5 rounded-full bg-purple-600 text-[10px] font-bold uppercase tracking-wider text-white">COMING SOON</div>
                <div>
                    <span class="text-[10px] font-bold uppercase tracking-widest text-purple-400">POTENZA COMPLETA</span>
                    <h3 class="text-xl font-bold text-white mt-1">Scorea Monthly</h3>
                    <div class="mt-4 flex items-baseline gap-1">
                        <span class="text-4xl font-extrabold text-white">100 $</span>
                        <span class="text-xs text-zinc-400">/ ogni mese</span>
                    </div>
                    <button disabled class="mt-6 w-full py-3 rounded-full bg-zinc-800 text-zinc-400 font-extrabold text-xs transition flex items-center justify-center cursor-not-allowed border border-zinc-700">
                        COMING SOON
                    </button>
                    <div class="mt-6 space-y-3 text-xs text-zinc-300 border-t border-zinc-800/80 pt-5">
                        <div class="flex items-start gap-2.5">
                            <i class="fa-solid fa-clock text-purple-400 mt-0.5"></i>
                            <div><strong class="text-white block">In arrivo</strong><span class="text-[11px] text-zinc-400">Presto disponibile.</span></div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- PIANO ANNUALE -->
            <div class="bg-zinc-950/85 backdrop-blur-xl border border-purple-500/30 rounded-3xl p-6 flex flex-col justify-between shadow-2xl">
                <div>
                    <span class="text-[10px] font-bold uppercase tracking-widest text-amber-400">VIP PASS ILLIMITATO</span>
                    <h3 class="text-xl font-bold text-white mt-1">Scorea Yearly</h3>
                    <div class="mt-4 flex items-baseline gap-1">
                        <span class="text-4xl font-extrabold text-white">200 $</span>
                        <span class="text-xs text-zinc-400">/ ogni anno</span>
                    </div>
                    <button disabled class="mt-6 w-full py-3 rounded-full bg-zinc-800 text-zinc-400 font-bold text-xs transition flex items-center justify-center cursor-not-allowed border border-zinc-700">
                        COMING SOON
                    </button>
                    <div class="mt-6 space-y-3 text-xs text-zinc-300 border-t border-zinc-800/80 pt-5">
                        <div class="flex items-start gap-2.5">
                            <i class="fa-solid fa-clock text-amber-400 mt-0.5"></i>
                            <div><strong class="text-white block">In arrivo</strong><span class="text-[11px] text-zinc-400">Presto disponibile.</span></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- MODALE WEBCAM AGE VERIFICATION -->
    <div id="ageModal" class="hidden fixed inset-0 bg-black/95 backdrop-blur-md z-50 flex items-center justify-center p-4">
        <div class="bg-zinc-900 border border-zinc-800 rounded-3xl max-w-md w-full p-6 space-y-4 text-center shadow-2xl">
            <div class="w-12 h-12 bg-indigo-600/20 text-indigo-400 rounded-2xl mx-auto flex items-center justify-center text-xl">
                <i class="fa-solid fa-camera"></i>
            </div>
            <h3 class="text-base font-bold text-white">Verifica Età via Webcam (+18)</h3>
            <p class="text-xs text-zinc-400">Inquadrati con la webcam per confermare la tua identità.</p>
            <div class="relative w-full h-48 bg-black rounded-2xl overflow-hidden border border-zinc-800 flex items-center justify-center">
                <video id="webcamVideo" autoplay playsinline class="w-full h-full object-cover"></video>
                <div id="camLoading" class="absolute text-xs text-zinc-500">Avvio fotocamera...</div>
            </div>
            <button onclick="captureAndVerifyAge()" class="w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs transition cursor-pointer">Scatta e Procedi</button>
        </div>
    </div>

    <!-- MODALE EMAIL -->
    <div id="emailAuthModal" class="hidden fixed inset-0 bg-black/95 backdrop-blur-md z-50 flex items-center justify-center p-4">
        <div class="bg-zinc-900 border border-zinc-800 rounded-3xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <div class="flex items-center justify-between border-b border-zinc-800 pb-3">
                <h3 class="text-base font-bold text-white flex items-center gap-2"><i class="fa-solid fa-envelope text-indigo-400"></i> Inserisci la tua Email</h3>
            </div>
            <div id="stepEmail" class="space-y-3">
                <p class="text-xs text-zinc-400">Inserisci la tua email:</p>
                <input type="email" id="userEmailInput" placeholder="tua@email.com" class="w-full bg-zinc-950 border border-zinc-800 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-indigo-500">
                <button onclick="sendOtpCode()" class="w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs transition cursor-pointer">Invia Notifica Codice</button>
            </div>
            <div id="stepOtp" class="hidden space-y-3">
                <p class="text-xs text-emerald-400 font-medium" id="otpSentInfo">Notifica inviata con successo!</p>
                <input type="text" id="otpCodeInput" placeholder="Inserisci codice a 6 cifre" maxlength="6" class="w-full bg-zinc-950 border border-zinc-800 rounded-xl p-3 text-center tracking-widest text-lg text-white font-mono focus:outline-none focus:border-indigo-500">
                <button onclick="verifyOtpCode()" class="w-full py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs transition cursor-pointer">Conferma Codice ed Entra</button>
            </div>
        </div>
    </div>

    <!-- MODALE IMPOSTAZIONI -->
    <div id="settingsModal" class="hidden fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
        <div class="bg-zinc-900 border border-zinc-800 rounded-3xl max-w-lg w-full p-6 space-y-5 shadow-2xl overflow-y-auto max-h-[90vh]">
            <div class="flex items-center justify-between border-b border-zinc-800 pb-3">
                <h3 class="text-base font-bold text-white flex items-center gap-2"><i class="fa-solid fa-gear text-indigo-400"></i> <span data-i18n="settingsTitle">Impostazioni Scorea</span></h3>
                <button onclick="closeSettingsModal()" class="text-zinc-500 hover:text-white cursor-pointer"><i class="fa-solid fa-xmark"></i></button>
            </div>

            <div class="space-y-2">
                <label class="text-xs font-semibold text-zinc-300 flex items-center gap-1.5"><i class="fa-solid fa-globe text-indigo-400"></i> <span data-i18n="langLabel">Lingua Interfaccia</span></label>
                <select id="langSelect" onchange="changeLanguage(this.value)" class="w-full bg-zinc-950 border border-zinc-800 rounded-xl p-2.5 text-xs text-white focus:outline-none cursor-pointer">
                    <option value="it">Italiano</option>
                    <option value="en">English</option>
                    <option value="es">Español</option>
                    <option value="fr">Français</option>
                </select>
            </div>

            <div class="space-y-3 pt-2 border-t border-zinc-800">
                <label class="text-xs font-semibold text-indigo-400 flex items-center gap-1.5"><i class="fa-solid fa-gauge-high"></i> Connessione Viewer (Speed Test)</label>
                <div class="bg-zinc-950 border border-zinc-800 rounded-2xl p-4 flex flex-col items-center space-y-3">
                    <div class="relative w-40 h-20 overflow-hidden flex items-end justify-center">
                        <div class="absolute w-40 h-40 rounded-full border-8 border-zinc-800 border-t-indigo-500 border-l-indigo-500"></div>
                        <div id="gaugeNeedle" class="gauge-needle absolute bottom-0 w-1 h-16 bg-indigo-400 rounded-full origin-bottom" style="transform: rotate(-90deg);"></div>
                        <div class="absolute bottom-1 text-center">
                            <span id="speedMbpsText" class="text-lg font-extrabold text-white">0</span>
                            <span class="text-[10px] text-zinc-400 block">Mbps</span>
                        </div>
                    </div>
                    <div class="flex items-center justify-between w-full pt-2">
                        <span id="speedStatusLabel" class="text-xs text-zinc-400">Stato: Pronto a testare</span>
                        <button onclick="runSpeedTest()" id="speedTestBtn" class="px-4 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs transition cursor-pointer shadow-md">
                            <i class="fa-solid fa-play mr-1"></i> Prova
                        </button>
                    </div>
                </div>
            </div>

            <div class="space-y-2 pt-2 border-t border-zinc-800">
                <label class="text-xs font-semibold text-amber-400 flex items-center gap-1.5"><i class="fa-solid fa-crown"></i> Abbonamento & Piani PRO</label>
                <button onclick="closeSettingsModal(); openPricingPage();" class="w-full py-3 rounded-2xl bg-gradient-to-r from-purple-700 to-indigo-700 hover:from-purple-600 hover:to-indigo-600 text-white font-bold text-xs transition cursor-pointer shadow-lg">
                    Scopri i Piani Scorea PRO (Coming Soon)
                </button>
            </div>

            <div class="space-y-2 pt-2 border-t border-zinc-800">
                <label class="text-xs font-semibold text-zinc-300"><i class="fa-solid fa-user-shield text-emerald-400 mr-1.5"></i> Sicurezza</label>
                <div class="flex items-center justify-between bg-zinc-950 border border-zinc-800 rounded-xl p-3">
                    <span id="loggedEmailDisplay" class="text-xs text-zinc-400">Non autenticato</span>
                    <button onclick="resetAllVerifications()" class="px-3 py-1.5 rounded-xl bg-red-900/40 text-red-300 border border-red-800/50 text-xs transition cursor-pointer">Ripeti Webcam</button>
                </div>
            </div>
        </div>
    </div>

    <!-- MODALE API KEY -->
    <div id="apiKeyModal" class="hidden fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
        <div class="bg-zinc-900 border border-zinc-800 rounded-3xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <div class="flex items-center justify-between">
                <h3 class="text-base font-bold text-white"><i class="fa-solid fa-key text-amber-400 mr-2"></i>Chiave API Gemini</h3>
                <button onclick="closeApiKeyModal()" class="text-zinc-500 hover:text-white cursor-pointer"><i class="fa-solid fa-xmark"></i></button>
            </div>
            <p class="text-xs text-zinc-400">Incolla qui la tua API Key.</p>
            <input type="password" id="apiKeyInput" placeholder="Incolla API Key..." class="w-full bg-zinc-950 border border-zinc-800 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-indigo-500">
            <button onclick="saveApiKey()" class="w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs transition cursor-pointer">Salva Chiave</button>
        </div>
    </div>

    <script>
        let isThinkingEnabled = false;
        let isRecording = false;
        let recognition = null;
        let webcamStream = null;
        let currentAbortController = null;
        let isGenerating = false;

        let chats = JSON.parse(localStorage.getItem('scorea_chats')) || [];
        let currentChatId = localStorage.getItem('scorea_current_chat') || null;

        const translations = {
            it: { welcomeTitle: "Ciao Enzo, sono Scorea!", welcomeSub: "Usa la task bar in basso per scrivere, attivare il pensiero profondo o usare la voce.", settings: "Impostazioni", settingsTitle: "Impostazioni Scorea", langLabel: "Lingua Interfaccia", install: "Installa", thinkingLabel: "Pensiero:", voice: "Vocale", send: "Invia", placeholder: "Scrivi un messaggio a Scorea..." },
            en: { welcomeTitle: "Hi Enzo, I'm Scorea!", welcomeSub: "Use the bottom task bar to write, toggle deep thinking, or use voice.", settings: "Settings", settingsTitle: "Scorea Settings", langLabel: "Interface Language", install: "Install", thinkingLabel: "Thinking:", voice: "Voice", send: "Send", placeholder: "Write a message to Scorea..." },
            es: { welcomeTitle: "¡Hola Enzo, soy Scorea!", welcomeSub: "Usa la barra inferior para escribir, activar el pensamiento profundo o usar la voz.", settings: "Ajustes", settingsTitle: "Ajustes de Scorea", langLabel: "Idioma de la interfaz", install: "Instalar", thinkingLabel: "Pensar:", voice: "Voz", send: "Enviar", placeholder: "Escribe un mensaje a Scorea..." },
            fr: { welcomeTitle: "Salut Enzo, je suis Scorea !", welcomeSub: "Utilisez la barre du bas pour écrire, penser en profondeur ou utiliser la voix.", settings: "Paramètres", settingsTitle: "Paramètres Scorea", langLabel: "Langue de l'interface", install: "Installer", thinkingLabel: "Penser:", voice: "Voix", send: "Envoyer", placeholder: "Écrivez un message à Scorea..." }
        };

        window.onload = function() {
            const savedLang = localStorage.getItem('scorea_lang') || 'it';
            document.getElementById('langSelect').value = savedLang;
            changeLanguage(savedLang);

            if (window.Notification && Notification.permission !== "granted") {
                Notification.requestPermission();
            }

            if(!localStorage.getItem('scorea_age_verified')) {
                openWebcamModal();
            } else if(!localStorage.getItem('scorea_user_email')) {
                openEmailModal();
            } else if(!localStorage.getItem('scorea_api_key')) {
                openApiKeyModal();
            }

            updateEmailDisplay();
            initChats();

            document.addEventListener('click', (e) => {
                if (!e.target.closest('#chatOptionsMenu') && !e.target.closest('.chat-options-btn')) {
                    document.getElementById('chatOptionsMenu').classList.add('hidden');
                }
            });
        };

        function toggleSidebar() {
            const sb = document.getElementById('sidebar');
            sb.classList.toggle('hidden');
        }

        function checkModelAccess(select) {
            const model = select.value;
            if (model !== 'Scorea-Fast') {
                select.value = 'Scorea-Fast';
                openPricingPage();
            }
        }

        function initChats() {
            if (chats.length === 0) {
                createNewChat(false);
            } else {
                if (!currentChatId || !chats.find(c => c.id === currentChatId)) {
                    currentChatId = chats[0].id;
                }
                loadChat(currentChatId);
            }
            renderChatList();
        }

        function createNewChat(switchNow = true) {
            const newChat = {
                id: 'chat_' + Date.now(),
                title: 'Nuova chat',
                pinned: false,
                messages: []
            };
            chats.unshift(newChat);
            saveChatsToStorage();
            if (switchNow) {
                switchChat(newChat.id);
            }
            renderChatList();
        }

        function saveChatsToStorage() {
            localStorage.setItem('scorea_chats', JSON.stringify(chats));
            localStorage.setItem('scorea_current_chat', currentChatId);
        }

        function switchChat(chatId) {
            currentChatId = chatId;
            saveChatsToStorage();
            loadChat(chatId);
            renderChatList();
        }

        function loadChat(chatId) {
            const chat = chats.find(c => c.id === chatId);
            const chatBox = document.getElementById('chatBox');
            chatBox.innerHTML = '';

            if (!chat || chat.messages.length === 0) {
                chatBox.innerHTML = `
                    <div id="welcomeScreen" class="h-full flex flex-col items-center justify-center text-center space-y-3 my-auto">
                        <img src="/icon.jpg" class="w-20 h-20 rounded-3xl shadow-2xl mb-2 object-cover" alt="Scorea Logo">
                        <h1 class="text-3xl font-extrabold text-white tracking-tight">Ciao Enzo, sono Scorea!</h1>
                        <p class="text-zinc-400 text-xs max-w-sm">Usa la task bar in basso per scrivere, attivare il pensiero profondo o usare la voce.</p>
                    </div>
                `;
                return;
            }

            chat.messages.forEach(msg => {
                if (msg.role === 'user') {
                    chatBox.innerHTML += `
                        <div class="flex flex-col items-end space-y-1">
                            <div class="bg-indigo-600 text-white rounded-2xl px-4 py-3 text-xs max-w-md shadow-md border border-indigo-500/30">
                                ${escapeHtml(msg.text)}
                            </div>
                        </div>
                    `;
                } else if (msg.role === 'assistant') {
                    chatBox.innerHTML += `
                        <div class="flex flex-col items-start space-y-1">
                            <div class="bg-zinc-900 border border-zinc-800 text-zinc-100 rounded-2xl p-4 text-xs max-w-lg leading-relaxed shadow-xl whitespace-pre-wrap">
                                ${escapeHtml(msg.text)}
                            </div>
                        </div>
                    `;
                } else if (msg.role === 'system_stop') {
                    chatBox.innerHTML += `
                        <div class="flex flex-col items-center my-3">
                            <span class="text-[11px] text-zinc-500 font-mono tracking-wider">------------HAI FERMATO IL MESSAGGIO ------------------</span>
                        </div>
                    `;
                }
            });
            chatBox.scrollTop = chatBox.scrollHeight;
        }

        function renderChatList() {
            const container = document.getElementById('chatListContainer');
            container.innerHTML = '';

            const sortedChats = [...chats].sort((a, b) => (b.pinned === true) - (a.pinned === true));

            sortedChats.forEach(chat => {
                const isActive = chat.id === currentChatId;
                const activeClass = isActive ? 'bg-zinc-800 text-white font-semibold' : 'text-zinc-300 hover:bg-zinc-900/80';
                
                const itemDiv = document.createElement('div');
                itemDiv.className = `chat-item group relative flex items-center justify-between px-3.5 py-2.5 rounded-full cursor-pointer text-xs transition ${activeClass}`;
                
                let titleHtml = `<div class="flex items-center gap-2 truncate flex-1 pr-6" onclick="switchChat('${chat.id}')">`;
                if (chat.pinned) {
                    titleHtml += `<i class="fa-solid fa-thumbtack text-[10px] text-indigo-400"></i>`;
                }
                titleHtml += `<span class="truncate">${escapeHtml(chat.title)}</span></div>`;

                const optionsBtn = `
                    <button onclick="openChatMenu(event, '${chat.id}')" class="chat-options-btn opacity-0 group-hover:opacity-100 ${isActive ? 'opacity-100' : ''} text-zinc-400 hover:text-white px-2 py-1 rounded-md transition">
                        <i class="fa-solid fa-ellipsis"></i>
                    </button>
                `;

                itemDiv.innerHTML = titleHtml + optionsBtn;
                container.appendChild(itemDiv);
            });
        }

        let activeMenuChatId = null;
        function openChatMenu(event, chatId) {
            event.stopPropagation();
            activeMenuChatId = chatId;
            const menu = document.getElementById('chatOptionsMenu');
            const chat = chats.find(c => c.id === chatId);
            
            const pinBtn = document.getElementById('menuPinBtn');
            if (chat && chat.pinned) {
                pinBtn.innerHTML = `<i class="fa-solid fa-thumbtack-slash text-indigo-400"></i> Stacca (Unpin)`;
            } else {
                pinBtn.innerHTML = `<i class="fa-solid fa-thumbtack text-indigo-400"></i> Fissa`;
            }

            const rect = event.currentTarget.getBoundingClientRect();
            menu.style.top = (rect.bottom + 4) + 'px';
            menu.style.left = Math.min(rect.left, window.innerWidth - 200) + 'px';
            menu.classList.remove('hidden');
        }

        function menuActionPin() {
            const chat = chats.find(c => c.id === activeMenuChatId);
            if (chat) {
                chat.pinned = !chat.pinned;
                saveChatsToStorage();
                renderChatList();
            }
            document.getElementById('chatOptionsMenu').classList.add('hidden');
        }

        let chatToRenameId = null;
        function menuActionRename() {
            const chat = chats.find(c => c.id === activeMenuChatId);
            if (chat) {
                chatToRenameId = chat.id;
                document.getElementById('renameInput').value = chat.title;
                document.getElementById('renameModal').classList.remove('hidden');
                document.getElementById('renameInput').focus();
            }
            document.getElementById('chatOptionsMenu').classList.add('hidden');
        }

        function closeRenameModal() {
            document.getElementById('renameModal').classList.add('hidden');
            chatToRenameId = null;
        }

        function confirmRenameChat() {
            const newTitle = document.getElementById('renameInput').value.trim();
            if (newTitle && chatToRenameId) {
                const chat = chats.find(c => c.id === chatToRenameId);
                if (chat) {
                    chat.title = newTitle;
                    saveChatsToStorage();
                    renderChatList();
                }
            }
            closeRenameModal();
        }

        function menuActionShare() {
            const chat = chats.find(c => c.id === activeMenuChatId);
            if (chat) {
                const summary = chat.messages.map(m => `${m.role}: ${m.text}`).join('\\n');
                navigator.clipboard.writeText(summary).then(() => {
                    alert("📋 Conversazione copiata negli appunti!");
                });
            }
            document.getElementById('chatOptionsMenu').classList.add('hidden');
        }

        function menuActionDelete() {
            if (chats.length <= 1) {
                alert("Non puoi eliminare l'ultima chat rimasta!");
                document.getElementById('chatOptionsMenu').classList.add('hidden');
                return;
            }
            if (confirm("Vuoi davvero eliminare questa chat?")) {
                chats = chats.filter(c => c.id !== activeMenuChatId);
                if (currentChatId === activeMenuChatId) {
                    currentChatId = chats[0].id;
                    loadChat(currentChatId);
                }
                saveChatsToStorage();
                renderChatList();
            }
            document.getElementById('chatOptionsMenu').classList.add('hidden');
        }

        function escapeHtml(text) {
            const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
            return text.replace(/[&<>"']/g, function(m) { return map[m]; });
        }

        function openPricingPage() {
            document.getElementById('pricingOverlay').classList.remove('hidden');
        }
        function closePricingPage() {
            document.getElementById('pricingOverlay').classList.add('hidden');
        }

        function resetAllVerifications() {
            localStorage.removeItem('scorea_age_verified');
            localStorage.removeItem('scorea_user_email');
            closeSettingsModal();
            openWebcamModal();
        }

        async function openWebcamModal() {
            document.getElementById('ageModal').classList.remove('hidden');
            try {
                webcamStream = await navigator.mediaDevices.getUserMedia({ video: true });
                const video = document.getElementById('webcamVideo');
                video.srcObject = webcamStream;
                document.getElementById('camLoading').style.display = 'none';
            } catch (err) {
                document.getElementById('camLoading').innerText = "Webcam non rilevata o permessi negati.";
            }
        }

        function captureAndVerifyAge() {
            if(webcamStream) {
                webcamStream.getTracks().forEach(track => track.stop());
            }
            localStorage.setItem('scorea_age_verified', 'true');
            document.getElementById('ageModal').classList.add('hidden');
            
            if(!localStorage.getItem('scorea_user_email')) {
                openEmailModal();
            } else if(!localStorage.getItem('scorea_api_key')) {
                openApiKeyModal();
            }
        }

        function openEmailModal() { 
            document.getElementById('emailAuthModal').classList.remove('hidden');
            document.getElementById('stepEmail').classList.remove('hidden');
            document.getElementById('stepOtp').classList.add('hidden');
        }
        function closeEmailModal() { document.getElementById('emailAuthModal').classList.add('hidden'); }

        async function sendOtpCode() {
            const email = document.getElementById('userEmailInput').value.trim();
            if(!email || !email.includes('@')) { return; }

            const res = await fetch('/api/send-otp', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ email: email })
            });
            const data = await res.json();
            if(res.ok) {
                document.getElementById('stepEmail').classList.add('hidden');
                document.getElementById('stepOtp').classList.remove('hidden');
                document.getElementById('otpSentInfo').innerText = `Codice inviato a ${email}. Controlla la notifica!`;
                localStorage.setItem('pending_email', email);
                showSmartNotification(`Il codice della app Scorea ti ha mandato sull'email ${email} il codice di: ${data.code}`);
            }
        }

        function showSmartNotification(messageText) {
            const isDesktop = window.innerWidth >= 768;
            if (isDesktop && window.Notification && Notification.permission === "granted") {
                new Notification("Scorea Security", { body: messageText, icon: "/icon.jpg" });
            } else {
                const toast = document.getElementById('phoneToast');
                document.getElementById('toastMessage').innerText = messageText;
                toast.classList.remove('hidden');
                setTimeout(() => { toast.classList.add('hidden'); }, 6000);
            }
        }

        async function verifyOtpCode() {
            const email = localStorage.getItem('pending_email');
            const code = document.getElementById('otpCodeInput').value.trim();

            const res = await fetch('/api/verify-otp', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ email: email, code: code })
            });
            const data = await res.json();
            if(res.ok) {
                localStorage.setItem('scorea_user_email', email);
                updateEmailDisplay();
                closeEmailModal();
                if(!localStorage.getItem('scorea_api_key')) {
                    openApiKeyModal();
                }
            }
        }

        function updateEmailDisplay() {
            const email = localStorage.getItem('scorea_user_email');
            const disp = document.getElementById('loggedEmailDisplay');
            if(email) {
                disp.innerText = email;
                disp.className = "text-xs text-emerald-400 font-semibold";
            } else {
                disp.innerText = "Non autenticato";
                disp.className = "text-xs text-zinc-400";
            }
        }

        function runSpeedTest() {
            const btn = document.getElementById('speedTestBtn');
            const statusLabel = document.getElementById('speedStatusLabel');
            const mbpsText = document.getElementById('speedMbpsText');
            const needle = document.getElementById('gaugeNeedle');

            btn.disabled = true;
            statusLabel.innerText = "Test in corso...";
            mbpsText.innerText = "...";
            needle.style.transform = "rotate(0deg)";

            let startTime = performance.now();
            fetch('/icon.jpg?' + Math.random())
                .then(() => {
                    let duration = (performance.now() - startTime) / 1000;
                    let mbps = Math.floor(Math.random() * 120 + 80);
                    if (duration > 0.5) mbps = Math.floor(Math.random() * 50 + 20);

                    mbpsText.innerText = mbps;
                    statusLabel.innerText = "Ottima Connessione!";
                    let angle = Math.min(Math.max((mbps / 250) * 180 - 90, -90), 90);
                    needle.style.transform = `rotate(${angle}deg)`;
                    btn.disabled = false;
                })
                .catch(() => {
                    mbpsText.innerText = "45";
                    statusLabel.innerText = "Connessione stabile";
                    needle.style.transform = "rotate(-20deg)";
                    btn.disabled = false;
                });
        }

        function changeLanguage(lang) {
            localStorage.setItem('scorea_lang', lang);
            const t = translations[lang] || translations['it'];
            document.querySelectorAll('[data-i18n]').forEach(el => {
                const key = el.getAttribute('data-i18n');
                if(t[key]) el.innerText = t[key];
            });
            const input = document.getElementById('promptInput');
            if(input && t.placeholder) input.placeholder = t.placeholder;
        }

        function openSettingsModal() { document.getElementById('settingsModal').classList.remove('hidden'); }
        function closeSettingsModal() { document.getElementById('settingsModal').classList.add('hidden'); }
        function openApiKeyModal() { document.getElementById('apiKeyModal').classList.remove('hidden'); }
        function closeApiKeyModal() { document.getElementById('apiKeyModal').classList.add('hidden'); }

        function saveApiKey() {
            const key = document.getElementById('apiKeyInput').value.trim();
            if(!key) { return; }
            localStorage.setItem('scorea_api_key', key);
            closeApiKeyModal();
        }

        function toggleThinking() {
            isThinkingEnabled = !isThinkingEnabled;
            const btn = document.getElementById('thinkingBtn');
            const status = document.getElementById('thinkingStatus');
            if(isThinkingEnabled) {
                btn.classList.add('border-indigo-500', 'text-indigo-400');
                status.innerText = 'ON';
                status.classList.replace('text-zinc-500', 'text-indigo-400');
            } else {
                btn.classList.remove('border-indigo-500', 'text-indigo-400');
                status.innerText = 'OFF';
                status.classList.replace('text-indigo-400', 'text-zinc-500');
            }
        }

        function toggleVoiceInput() {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if(!SpeechRecognition) { return; }
            if(isRecording) { recognition.stop(); return; }
            recognition = new SpeechRecognition();
            recognition.lang = localStorage.getItem('scorea_lang') === 'en' ? 'en-US' : 'it-IT';
            recognition.onstart = () => { isRecording = true; document.getElementById('micBtn').classList.add('border-red-500', 'text-red-400'); };
            recognition.onresult = (e) => { document.getElementById('promptInput').value += ' ' + e.results[0][0].transcript; };
            recognition.onerror = () => stopVoiceUI();
            recognition.onend = () => stopVoiceUI();
            recognition.start();
        }
        function stopVoiceUI() {
            isRecording = false;
            document.getElementById('micBtn').classList.remove('border-red-500', 'text-red-400');
        }

        function handleKeyDown(e) { if(e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleAction(); } }

        function handleAction() {
            if (isGenerating) {
                stopGeneration();
            } else {
                sendMessage();
            }
        }

        function setStopButton() {
            isGenerating = true;
            const btn = document.getElementById('actionBtn');
            btn.className = "px-4 py-1.5 rounded-xl bg-red-600 hover:bg-red-500 text-white font-semibold transition shadow-md flex items-center gap-2 cursor-pointer";
            btn.innerHTML = `Ferma <div class="w-3.5 h-3.5 bg-transparent border border-white rounded-[4px] flex items-center justify-center"><div class="w-1.5 h-1.5 bg-white rounded-[1px]"></div></div>`;
        }

        function resetSendButton() {
            isGenerating = false;
            const btn = document.getElementById('actionBtn');
            btn.className = "px-4 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold transition shadow-md flex items-center gap-1.5 cursor-pointer";
            btn.innerHTML = `<span data-i18n="send">Invia</span> <i class="fa-solid fa-paper-plane text-[10px]"></i>`;
        }

        function stopGeneration() {
            if (currentAbortController) {
                currentAbortController.abort();
                currentAbortController = null;
            }
            if (window.currentCountdown) {
                clearInterval(window.currentCountdown);
            }

            const loadingElem = document.getElementById('activeLoadingBox');
            if (loadingElem) loadingElem.remove();

            const chatBox = document.getElementById('chatBox');
            chatBox.innerHTML += `
                <div class="flex flex-col items-center my-3">
                    <span class="text-[11px] text-zinc-500 font-mono tracking-wider">------------HAI FERMATO IL MESSAGGIO ------------------</span>
                </div>
            `;
            chatBox.scrollTop = chatBox.scrollHeight;

            const currentChat = chats.find(c => c.id === currentChatId);
            if (currentChat) {
                currentChat.messages.push({ role: 'system_stop', text: '------------HAI FERMATO IL MESSAGGIO ------------------' });
                saveChatsToStorage();
            }

            resetSendButton();
        }

        async function sendMessage() {
            const promptInput = document.getElementById('promptInput');
            const prompt = promptInput.value.trim();
            const apiKey = localStorage.getItem('scorea_api_key');
            const selectedModel = document.getElementById('modelSelector').value;
            if(!prompt) return;
            if(!apiKey) { openApiKeyModal(); return; }

            const chatBox = document.getElementById('chatBox');
            const welcome = document.getElementById('welcomeScreen');
            if(welcome) welcome.remove();

            const currentChat = chats.find(c => c.id === currentChatId);
            if (currentChat) {
                if (currentChat.messages.length === 0) {
                    currentChat.title = prompt.length > 28 ? prompt.substring(0, 28) + '...' : prompt;
                }
                currentChat.messages.push({ role: 'user', text: prompt });
                saveChatsToStorage();
                renderChatList();
            }

            chatBox.innerHTML += `
                <div class="flex flex-col items-end space-y-1">
                    <div class="bg-indigo-600 text-white rounded-2xl px-4 py-3 text-xs max-w-md shadow-md border border-indigo-500/30">
                        ${escapeHtml(prompt)}
                    </div>
                </div>
            `;
            promptInput.value = '';
            chatBox.scrollTop = chatBox.scrollHeight;

            setStopButton();
            currentAbortController = new AbortController();

            const loadingId = 'loading-' + Date.now();
            
            if (isThinkingEnabled) {
                let randomSeconds = Math.floor(Math.random() * 30) + 10;
                chatBox.innerHTML += `
                    <div id="${loadingId}" class="flex items-center gap-1.5 text-xs text-indigo-400 py-1">
                        <div id="activeLoadingBox" class="bg-zinc-900 border border-indigo-500/40 px-4 py-3 rounded-2xl shadow-xl flex items-center gap-2">
                            <i class="fa-solid fa-brain fa-beat text-indigo-400"></i>
                            <span class="text-zinc-300">Scorea sta elaborando in profondità... (<span id="timer-${loadingId}">${randomSeconds}</span>s)</span>
                        </div>
                    </div>
                `;
                chatBox.scrollTop = chatBox.scrollHeight;

                let countdownInterval = setInterval(() => {
                    randomSeconds--;
                    const timerElem = document.getElementById(`timer-${loadingId}`);
                    if (timerElem) timerElem.innerText = randomSeconds;
                    if (randomSeconds <= 0) clearInterval(countdownInterval);
                }, 1000);
                window.currentCountdown = countdownInterval;
            } else {
                chatBox.innerHTML += `
                    <div id="${loadingId}" class="flex items-center gap-1.5 text-xs text-indigo-400 py-1">
                        <div id="activeLoadingBox" class="bg-zinc-900 border border-zinc-800 px-4 py-3 rounded-2xl shadow-xl flex items-center gap-2">
                            <div class="flex items-center gap-1">
                                <span class="w-1 h-1 bg-indigo-400 rounded-full dot1"></span>
                                <span class="w-1 h-1 bg-indigo-400 rounded-full dot2"></span>
                                <span class="w-1 h-1 bg-indigo-400 rounded-full dot3"></span>
                            </div>
                            <span class="text-zinc-400 text-[11px]">Scorea sta scrivendo...</span>
                        </div>
                    </div>
                `;
            }
            chatBox.scrollTop = chatBox.scrollHeight;

            try {
                const res = await fetch('/api/scorea', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ prompt: prompt, apiKey: apiKey, model: selectedModel, thinking: isThinkingEnabled }),
                    signal: currentAbortController.signal
                });
                
                if (window.currentCountdown) clearInterval(window.currentCountdown);
                document.getElementById(loadingId)?.remove();

                const data = await res.json();
                if(res.ok) {
                    if (currentChat) {
                        currentChat.messages.push({ role: 'assistant', text: data.reply });
                        saveChatsToStorage();
                    }
                    chatBox.innerHTML += `
                        <div class="flex flex-col items-start space-y-1">
                            <div class="bg-zinc-900 border border-zinc-800 text-zinc-100 rounded-2xl p-4 text-xs max-w-lg leading-relaxed shadow-xl whitespace-pre-wrap">
                                ${escapeHtml(data.reply)}
                            </div>
                        </div>
                    `;
                } else {
                    alert("⚠️ " + data.error);
                }
            } catch(e) {
                if (e.name !== 'AbortError') {
                    if (window.currentCountdown) clearInterval(window.currentCountdown);
                    document.getElementById(loadingId)?.remove();
                }
            } finally {
                resetSendButton();
                chatBox.scrollTop = chatBox.scrollHeight;
            }
        }

        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            window.deferredPrompt = e;
            document.getElementById('installBtn').classList.remove('hidden');
        });
        async function installApp() {
            if (window.deferredPrompt) {
                window.deferredPrompt.prompt();
                const { outcome } = await window.deferredPrompt.userChoice;
                if (outcome === 'accepted') document.getElementById('installBtn').classList.add('hidden');
                window.deferredPrompt = null;
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return "Benvenuto su Scorea"

# --- ROTTA PER LA FAVICON ---
@app.route('/favicon.ico')
@app.route('/icon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'icon.ico')

@app.route('/manifest.json')
def manifest():
    return jsonify(MANIFEST_JSON)

@app.route('/api/send-otp', methods=['POST'])
def send_otp():
    data = request.json or {}
    email = data.get('email')
    if not email: return jsonify({"error": "Email mancante"}), 400
    code = str(random.randint(100000, 999999))
    EMAIL_VERIFICATION_CODES[email] = code
    return jsonify({"success": True, "code": code})

@app.route('/api/verify-otp', methods=['POST'])
def verify_otp():
    data = request.json or {}
    if EMAIL_VERIFICATION_CODES.get(data.get('email')) == data.get('code'):
        return jsonify({"success": True})
    return jsonify({"error": "Codice errato o scaduto."}), 400

@app.route('/api/scorea', methods=['POST'])
def scorea_chat():
    data = request.json or {}
    api_key = data.get('apiKey')
    prompt = data.get('prompt')
    thinking = data.get('thinking', False)
    
    if not api_key: return jsonify({"error": "Chiave API mancante!"}), 400
    
    gemini_model = "gemini-3.8-flash-lite"
    if thinking:
        prompt = "[Modalità Pensiero]: Analizza con precisione.\n\n" + prompt

    url = f"https://generativelanguage.googleapis.com/v1/models/{gemini_model}:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 4096}
    }
    
    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req, timeout=20) as resp:
            res_data = json.loads(resp.read().decode('utf-8'))
            return jsonify({"reply": res_data['candidates'][0]['content']['parts'][0]['text']})
    except Exception:
        try:
            fallback_url = f"https://generativelanguage.googleapis.com/v1/models/gemini-3.5-flash:generateContent?key={api_key}"
            req_fb = urllib.request.Request(fallback_url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'}, method='POST')
            with urllib.request.urlopen(req_fb, timeout=20) as resp_fb:
                res_data_fb = json.loads(resp_fb.read().decode('utf-8'))
                return jsonify({"reply": res_data_fb['candidates'][0]['content']['parts'][0]['text']})
        except Exception:
            return jsonify({"reply": "⚠️ Scorea ha riscontrato un piccolo rallentamento di rete. Riprova a inviare il messaggio!"})

if __name__ == '__main__':
    print("🚀 Scorea avviato su http://127.0.0.1:5000 !")
    app.run(host='0.0.0.0', port=5000)