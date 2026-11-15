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
            const box = document.getElementById('chatBox');
            const welcome = document.getElementById('welcomeScreen');
            box.innerHTML = '';
            if (!chat || chat.messages.length === 0) {
                box.appendChild(welcome);
                welcome.classList.remove('hidden');
                return;
            }
            welcome.classList.add('hidden');
            chat.messages.forEach(m => appendMessageToDOM(m.sender, m.text, m.thinking));
            box.scrollTop = box.scrollHeight;
        }

        function renderChatList() {
            const container = document.getElementById('chatListContainer');
            container.innerHTML = '';
            chats.forEach(chat => {
                const div = document.createElement('div');
                div.className = `chat-item group flex items-center justify-between px-3 py-2 rounded-xl text-xs cursor-pointer transition ${chat.id === currentChatId ? 'bg-zinc-800 text-white font-semibold' : 'text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200'}`;
                div.onclick = () => switchChat(chat.id);
                div.innerHTML = `
                    <div class="flex items-center gap-2 truncate flex-1">
                        <i class="fa-solid fa-message text-indigo-400 text-[10px]"></i>
                        <span class="truncate">${chat.title}</span>
                    </div>
                    <button onclick="openChatOptions(event, '${chat.id}')" class="chat-options-btn opacity-0 group-hover:opacity-100 text-zinc-500 hover:text-white px-1.5 py-1 transition cursor-pointer">
                        <i class="fa-solid fa-ellipsis"></i>
                    </button>
                `;
                container.appendChild(div);
            });
        }

        let activeMenuChatId = null;
        function openChatOptions(e, chatId) {
            e.stopPropagation();
            activeMenuChatId = chatId;
            const menu = document.getElementById('chatOptionsMenu');
            const rect = e.target.getBoundingClientRect();
            menu.style.top = `${rect.bottom + window.scrollY}px`;
            menu.style.left = `${rect.left - 100}px`;
            menu.classList.remove('hidden');
            const chat = chats.find(c => c.id === chatId);
            const pinBtn = document.getElementById('menuPinBtn');
            if (chat && chat.pinned) {
                pinBtn.innerHTML = '<i class="fa-solid fa-thumbtack-slash text-indigo-400"></i> Sissa';
            } else {
                pinBtn.innerHTML = '<i class="fa-solid fa-thumbtack text-indigo-400"></i> Fissa';
            }
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

        function menuActionRename() {
            document.getElementById('chatOptionsMenu').classList.add('hidden');
            const chat = chats.find(c => c.id === activeMenuChatId);
            if (chat) {
                document.getElementById('renameInput').value = chat.title;
                document.getElementById('renameModal').classList.remove('hidden');
            }
        }

        function closeRenameModal() {
            document.getElementById('renameModal').classList.add('hidden');
        }

        function confirmRenameChat() {
            const newTitle = document.getElementById('renameInput').value.trim();
            if (newTitle && activeMenuChatId) {
                const chat = chats.find(c => c.id === activeMenuChatId);
                if (chat) {
                    chat.title = newTitle;
                    saveChatsToStorage();
                    renderChatList();
                }
            }
            closeRenameModal();
        }

        function menuActionShare() {
            document.getElementById('chatOptionsMenu').classList.add('hidden');
            const chat = chats.find(c => c.id === activeMenuChatId);
            if (chat) {
                const text = chat.messages.map(m => `${m.sender}: ${m.text}`).join('\\n');
                navigator.clipboard.writeText(text);
                showToast("Chat copiata negli appunti!");
            }
        }

        function menuActionDelete() {
            document.getElementById('chatOptionsMenu').classList.add('hidden');
            chats = chats.filter(c => c.id !== activeMenuChatId);
            saveChatsToStorage();
            if (chats.length === 0) {
                createNewChat(true);
            } else {
                switchChat(chats[0].id);
            }
            renderChatList();
        }

        function toggleThinking() {
            isThinkingEnabled = !isThinkingEnabled;
            const status = document.getElementById('thinkingStatus');
            if (isThinkingEnabled) {
                status.textContent = "ON";
                status.className = "text-emerald-400";
            } else {
                status.textContent = "OFF";
                status.className = "text-zinc-500";
            }
        }

        function toggleVoiceInput() {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!SpeechRecognition) {
                alert("Riconoscimento vocale non supportato dal browser.");
                return;
            }
            if (!isRecording) {
                recognition = new SpeechRecognition();
                recognition.lang = 'it-IT';
                recognition.onstart = () => {
                    isRecording = true;
                    document.getElementById('micBtn').classList.add('border-indigo-500', 'text-indigo-400');
                    document.getElementById('micText').textContent = "Ascolto...";
                };
                recognition.onresult = (event) => {
                    const transcript = event.results[0][0].transcript;
                    document.getElementById('promptInput').value = transcript;
                };
                recognition.onerror = () => { stopVoiceInput(); };
                recognition.onend = () => { stopVoiceInput(); };
                recognition.start();
            } else {
                stopVoiceInput();
            }
        }

        function stopVoiceInput() {
            isRecording = false;
            if (recognition) { try { recognition.stop(); } catch(e){} }
            document.getElementById('micBtn').classList.remove('border-indigo-500', 'text-indigo-400');
            document.getElementById('micText').textContent = "Vocale";
        }

        function handleKeyDown(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleAction();
            }
        }

        async function handleAction() {
            const input = document.getElementById('promptInput');
            const text = input.value.trim();
            if (!text || isGenerating) return;

            input.value = '';
            const welcome = document.getElementById('welcomeScreen');
            welcome.classList.add('hidden');

            appendMessageToDOM('User', text);
            const chat = chats.find(c => c.id === currentChatId);
            if (chat) {
                if (chat.messages.length === 0) {
                    chat.title = text.length > 25 ? text.substring(0, 25) + '...' : text;
                    renderChatList();
                }
                chat.messages.push({ sender: 'User', text });
                saveChatsToStorage();
            }

            const apiKey = localStorage.getItem('scorea_api_key');
            if (!apiKey) {
                openApiKeyModal();
                return;
            }

            isGenerating = true;
            const box = document.getElementById('chatBox');
            const aiMsgDiv = document.createElement('div');
            aiMsgDiv.className = 'flex gap-3 my-4 items-start';
            aiMsgDiv.innerHTML = `
                <img src="/icon.jpg" class="w-8 h-8 rounded-xl object-cover shrink-0 mt-1 shadow">
                <div class="bg-zinc-900 border border-zinc-800 rounded-2xl p-4 text-xs text-zinc-200 max-w-2xl leading-relaxed space-y-2 flex-1">
                    <div class="flex items-center gap-2 text-indigo-400 font-semibold">
                        <i class="fa-solid fa-spinner animate-spin"></i> Scorea sta elaborando...
                    </div>
                    <div class="ai-response-text font-normal"></div>
                </div>
            `;
            box.appendChild(aiMsgDiv);
            box.scrollTop = box.scrollHeight;

            const responseTextEl = aiMsgDiv.querySelector('.ai-response-text');

            try {
                currentAbortController = new AbortController();
                const promptToSend = isThinkingEnabled ? `[Pensiero Profondo Attivo] ${text}` : text;
                
                const res = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${apiKey}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        contents: [{ parts: [{ text: promptToSend }] }]
                    }),
                    signal: currentAbortController.signal
                });

                const data = await res.json();
                const reply = data.candidates && data.candidates[0].content.parts[0].text 
                    ? data.candidates[0].content.parts[0].text 
                    : "Risposta non valida dall'API Gemini.";

                aiMsgDiv.querySelector('.text-indigo-400').remove();
                responseTextEl.textContent = reply;

                if (chat) {
                    chat.messages.push({ sender: 'Scorea', text: reply });
                    saveChatsToStorage();
                }
            } catch (err) {
                if (err.name === 'AbortError') {
                    aiMsgDiv.querySelector('.text-indigo-400').textContent = "Generazione interrotta.";
                } else {
                    aiMsgDiv.querySelector('.text-indigo-400').textContent = "Errore di connessione con l'API.";
                }
            } finally {
                isGenerating = false;
                box.scrollTop = box.scrollHeight;
            }
        }

        function appendMessageToDOM(sender, text) {
            const box = document.getElementById('chatBox');
            const div = document.createElement('div');
            div.className = `flex gap-3 my-4 items-start ${sender === 'User' ? 'justify-end' : ''}`;
            if (sender === 'User') {
                div.innerHTML = `
                    <div class="bg-indigo-600 rounded-2xl p-4 text-xs text-white max-w-2xl leading-relaxed">
                        ${escapeHtml(text)}
                    </div>
                    <div class="w-8 h-8 rounded-xl bg-zinc-800 text-indigo-400 flex items-center justify-center font-bold text-xs shrink-0 mt-1">TU</div>
                `;
            } else {
                div.innerHTML = `
                    <img src="/icon.jpg" class="w-8 h-8 rounded-xl object-cover shrink-0 mt-1 shadow">
                    <div class="bg-zinc-900 border border-zinc-800 rounded-2xl p-4 text-xs text-zinc-200 max-w-2xl leading-relaxed">
                        ${escapeHtml(text)}
                    </div>
                `;
            }
            box.appendChild(div);
            box.scrollTop = box.scrollHeight;
        }

        function escapeHtml(string) {
            return string.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
        }

        function showToast(msg) {
            const toast = document.getElementById('phoneToast');
            document.getElementById('toastMessage').textContent = msg;
            toast.classList.remove('hidden');
            setTimeout(() => toast.classList.add('hidden'), 3500);
        }

        function openSettingsModal() { document.getElementById('settingsModal').classList.remove('hidden'); }
        function closeSettingsModal() { document.getElementById('settingsModal').classList.add('hidden'); }
        function openApiKeyModal() { document.getElementById('apiKeyModal').classList.remove('hidden'); }
        function closeApiKeyModal() { document.getElementById('apiKeyModal').classList.add('hidden'); }
        function openPricingPage() { document.getElementById('pricingOverlay').classList.remove('hidden'); }
        function closePricingPage() { document.getElementById('pricingOverlay').classList.add('hidden'); }
        function openWebcamModal() { 
            document.getElementById('ageModal').classList.remove('hidden');
            navigator.mediaDevices.getUserMedia({ video: true }).then(stream => {
                webcamStream = stream;
                document.getElementById('webcamVideo').srcObject = stream;
                document.getElementById('camLoading').classList.add('hidden');
            }).catch(() => {
                document.getElementById('camLoading').textContent = "Webcam non disponibile o permessi negati.";
            });
        }

        function captureAndVerifyAge() {
            if (webcamStream) {
                webcamStream.getTracks().forEach(track => track.stop());
            }
            localStorage.setItem('scorea_age_verified', 'true');
            document.getElementById('ageModal').classList.add('hidden');
            showToast("Verifica età completata (+18)!");
            openEmailModal();
        }

        function openEmailModal() { document.getElementById('emailAuthModal').classList.remove('hidden'); }

        function sendOtpCode() {
            const email = document.getElementById('userEmailInput').value.trim();
            if (!email || !email.includes('@')) {
                alert("Inserisci un'email valida.");
                return;
            }
            fetch('/api/send-otp', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email })
            }).then(res => res.json()).then(data => {
                if (data.success) {
                    document.getElementById('stepEmail').classList.add('hidden');
                    document.getElementById('stepOtp').classList.remove('hidden');
                    document.getElementById('otpSentInfo').textContent = `Codice OTP inviato! (Demo code: ${data.code})`;
                    localStorage.setItem('scorea_pending_email', email);
                }
            });
        }

        function verifyOtpCode() {
            const code = document.getElementById('otpCodeInput').value.trim();
            const email = localStorage.getItem('scorea_pending_email');
            if (code.length === 6) {
                localStorage.setItem('scorea_user_email', email);
                document.getElementById('emailAuthModal').classList.add('hidden');
                updateEmailDisplay();
                showToast("Autenticazione riuscita!");
                if (!localStorage.getItem('scorea_api_key')) {
                    openApiKeyModal();
                }
            } else {
                alert("Inserisci un codice valido a 6 cifre.");
            }
        }

        function updateEmailDisplay() {
            const email = localStorage.getItem('scorea_user_email');
            const disp = document.getElementById('loggedEmailDisplay');
            if (email) {
                disp.textContent = `Autenticato come: ${email}`;
                disp.className = "text-xs text-emerald-400 font-medium";
            }
        }

        function resetAllVerifications() {
            localStorage.removeItem('scorea_age_verified');
            localStorage.removeItem('scorea_user_email');
            closeSettingsModal();
            openWebcamModal();
        }

        function saveApiKey() {
            const key = document.getElementById('apiKeyInput').value.trim();
            if (key) {
                localStorage.setItem('scorea_api_key', key);
                closeApiKeyModal();
                showToast("API Key salvata con successo!");
            } else {
                alert("Inserisci una chiave valida.");
            }
        }

        function changeLanguage(lang) {
            localStorage.setItem('scorea_lang', lang);
            const t = translations[lang] || translations['it'];
            document.querySelectorAll('[data-i18n]').forEach(el => {
                const key = el.getAttribute('data-i18n');
                if (t[key]) el.textContent = t[key];
            });
            const promptInput = document.getElementById('promptInput');
            if (promptInput && t['placeholder']) promptInput.placeholder = t['placeholder'];
        }

        function runSpeedTest() {
            const needle = document.getElementById('gaugeNeedle');
            const text = document.getElementById('speedMbpsText');
            const status = document.getElementById('speedStatusLabel');
            const btn = document.getElementById('speedTestBtn');
            btn.disabled = true;
            status.textContent = "Misurazione in corso...";
            let current = 0;
            const target = Math.floor(Math.random() * 300) + 150;
            const interval = setInterval(() => {
                current += Math.floor(Math.random() * 15) + 5;
                if (current >= target) {
                    current = target;
                    clearInterval(interval);
                    btn.disabled = false;
                    status.textContent = "Test completato con successo!";
                }
                text.textContent = current;
                const deg = -90 + (current / 500) * 180;
                needle.style.transform = `rotate(${deg}deg)`;
            }, 50);
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

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
    if not email:
        return jsonify({"error": "Email mancante"}), 400
    code = str(random.randint(100000, 999999))
    EMAIL_VERIFICATION_CODES[email] = code
    return jsonify({"success": True, "code": code})

if __name__ == '__main__':
    app.run(debug=True)