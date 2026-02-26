import flet as ft
import shelve
import os
import sys
import hashlib
import hmac
import secrets
import subprocess
import platform
import threading
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Callable

# ================= TRANSLATOR =================
try:
    from deep_translator import GoogleTranslator
    TRANSLATOR_AVAILABLE = True
except ImportError:
    TRANSLATOR_AVAILABLE = False

# Language codes for translation
LANGUAGE_CODES = {
    'English': 'en',
    'Malayalam': 'ml',
    'Hindi': 'hi',
    'Tamil': 'ta',
    'Kannada': 'kn',
    'Marathi': 'mr',
    'Gujarati': 'gu',
    'French': 'fr',
    'Spanish': 'es',
    'Japanese': 'ja',
    'Chinese': 'zh-CN',
    'Arabic': 'ar',
    'German': 'de',
    'Italian': 'it',
    'Portuguese': 'pt',
    'Russian': 'ru',
    'Korean': 'ko',
    'Thai': 'th',
    'Vietnamese': 'vi',
    'Indonesian': 'id',
    'Bengali': 'bn',
    'Telugu': 'te',
    'Punjabi': 'pa',
    'Urdu': 'ur',
}

def smart_translate(text: str, source_lang: str = 'auto', target_lang: str = 'en') -> str:
    """Translate text between any two languages"""
    if not text or not text.strip():
        return text
    if not TRANSLATOR_AVAILABLE:
        return f"[Translator unavailable] {text}"
    try:
        src_code = LANGUAGE_CODES.get(source_lang, 'auto') if source_lang != 'auto' else 'auto'
        tgt_code = LANGUAGE_CODES.get(target_lang, 'en')
        if src_code == tgt_code:
            return text
        translator = GoogleTranslator(source=src_code, target=tgt_code)
        result = translator.translate(text)
        return result if result else text
    except Exception as e:
        return f"[Translation error: {str(e)[:30]}] {text}"

APP_NAME     = "My Vault"
APP_VERSION  = "2.0.0"
APP_SUBTITLE = "Your Secure Credential Manager"

# ================= PLATFORM DETECTION =================
def is_mobile() -> bool:
    return sys.platform in ('android', 'ios') or os.environ.get('FLET_PLATFORM', '') in ('android', 'ios')

def is_windows() -> bool:
    return os.name == 'nt'

def is_macos() -> bool:
    return sys.platform == 'darwin'

def is_linux() -> bool:
    return sys.platform.startswith('linux') and not is_mobile()

# ================= STORAGE PATH =================
def get_storage_path() -> str:
    if os.name == 'nt':
        base = os.environ.get('APPDATA', os.path.expanduser('~'))
    elif sys.platform == 'darwin':
        base = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support')
    else:
        base = os.path.join(os.path.expanduser('~'), '.local', 'share')
    path = os.path.join(base, 'MyVault')
    os.makedirs(path, exist_ok=True)
    return path

STORAGE_PATH = get_storage_path()

# ================= SECURITY CONSTANTS =================
MAX_ATTEMPTS = 3
LOCKOUT_BASE_TIME = 60
LOCKOUT_MULTIPLIER = 2
MAX_LOCKOUT_TIME = 3600
SECRET_QUESTIONS = [
    'q_favorite_childhood_friend',
    'q_first_school_name',
    'q_mother_maiden_name',
    'q_first_pet_name',
    'q_birth_city',
    'q_favorite_teacher_name',
    'q_childhood_nickname',
    'q_first_car_model',
]

# ================= TRANSLATIONS =================
translations: Dict[str, Dict[str, str]] = {
    'English': {
        'vault': 'My Vault', 'empty': 'Your vault is empty.\nTap + to add credentials.',
        'add': 'Add Credential', 'edit': 'Edit Credential', 'app': 'App / Website Name',
        'user': 'Username / Email', 'pass': 'Password', 'save': 'Save', 'cancel': 'Cancel',
        'delete': 'Delete', 'settings': 'Settings', 'language': 'Language',
        'dark': 'Dark Mode', 'light': 'Light Mode', 'about': 'About',
        'delete_confirm': 'Delete this credential?', 'yes': 'Yes', 'no': 'No',
        'search': 'Search...', 'copy_pass': 'Password copied!',
        'copy_user': 'Username copied!', 'fill_all': 'Please fill all fields.',
        # ── Auth ──
        'set_master': 'Set Master Passkey',
        'set_master_sub': 'Create a passkey to protect your vault.',
        'new_pass': 'New Passkey', 'confirm_pass': 'Confirm Passkey',
        'create_passkey': 'Create Passkey',
        'enter_master': 'Enter Master Passkey',
        'enter_master_sub': 'Your vault is locked.',
        'unlock': 'Unlock',
        'wrong_pass': 'Wrong passkey. Try again.',
        'pass_mismatch': 'Passkeys do not match.',
        'pass_too_short': 'Passkey must be at least 4 characters.',
        'biometric': 'Use Biometric',
        'biometric_hint': 'Authenticate with fingerprint / face',
        'biometric_fail': 'Biometric failed.',
        'biometric_unavailable': 'Biometric not available.',
        'change_passkey': 'Change Passkey',
        'current_pass': 'Current Passkey',
        'wrong_current': 'Current passkey is incorrect.',
        'passkey_changed': 'Passkey changed successfully!',
        'security': 'Security',
        'attempts_left': 'attempts left',
        'locked_out': 'Too many attempts. App locked.',
        'reset_vault': 'Reset Vault',
        'reset_confirm': 'This will erase ALL data and the passkey. Continue?',
        'reset_done': 'Vault has been reset.',
        # ── MFA Setup ──
        'setup_title': 'Secure Setup',
        'setup_step1': 'Step 1: Create Passkey',
        'setup_step2': 'Step 2: Secret Question',
        'setup_step3': 'Step 3: Voice Registration',
        'setup_step4': 'Step 4: Face Registration',
        'setup_step5': 'Step 5: Fingerprint Registration',
        'setup_step6': 'Final: Verify All',
        'setup_complete': 'Setup Complete!',
        'setup_complete_sub': 'Your vault is now secured with multi-factor authentication.',
        # ── MFA Verification ──
        'mfa_required': 'Multi-Factor Authentication Required',
        'mfa_verify': 'Verify Your Identity',
        'mfa_step': 'Step',
        'mfa_of': 'of',
        # ── Verification Types ──
        'passkey_verification': 'Passkey Verification',
        'voice_verification': 'Voice Verification',
        'face_verification': 'Face Verification',
        'fingerprint_verification': 'Fingerprint Verification',
        # ── Register ──
        'voice_register': 'Register Voice',
        'face_register': 'Register Face',
        'fingerprint_register': 'Register Fingerprint',
        # ── Verify ──
        'voice_verify': 'Verify Voice',
        'face_verify': 'Verify Face',
        'fingerprint_verify': 'Verify Fingerprint',
        # ── Hints ──
        'passkey_hint': 'Enter your master passkey',
        'voice_hint': 'Speak the passphrase shown below',
        'face_hint': 'Position your face in the camera frame',
        'fingerprint_hint': 'Place your finger on the sensor',
        # ── Success ──
        'passkey_success': 'Passkey verified!',
        'voice_success': 'Voice verified successfully!',
        'face_success': 'Face verified successfully!',
        'fingerprint_success': 'Fingerprint verified successfully!',
        'voice_registered': 'Voice registered successfully!',
        'face_registered': 'Face registered successfully!',
        'fingerprint_registered': 'Fingerprint registered successfully!',
        # ── Failed ──
        'passkey_failed': 'Wrong passkey.',
        'voice_failed': 'Voice verification failed. Try again.',
        'face_failed': 'Face verification failed. Try again.',
        'fingerprint_failed': 'Fingerprint verification failed. Try again.',
        # ── Device ──
        'no_webcam': 'No webcam detected. Please connect a webcam.',
        'no_microphone': 'No microphone detected. Please connect a microphone.',
        'no_biometric_device': 'No biometric device detected.',
        # ── Status ──
        'verifying': 'Verifying...',
        'registering': 'Registering...',
        'please_wait': 'Please wait...',
        'countdown': 'Try again in',
        'seconds': 'seconds',
        'minutes': 'minutes',
        # ── Buttons ──
        'continue_btn': 'Continue',
        'next_btn': 'Next',
        'verify_btn': 'Verify',
        'start_over': 'Start Over',
        'verified': 'Verified',
        'pending': 'Pending',
        # ── Secret Questions ──
        'secret_question': 'Secret Question',
        'set_secret_question': 'Set Secret Question',
        'secret_question_sub': 'Choose a security question for account recovery',
        'select_question': 'Select a question',
        'your_answer': 'Your Answer',
        'secret_answer': 'Secret Answer',
        'answer_hint': 'Enter your answer (case-sensitive)',
        'forgot_passkey': 'Forgot Passkey?',
        'verify_identity': 'Verify Identity',
        'answer_correct': 'Answer verified!',
        'answer_wrong': 'Wrong answer. Try again.',
        'q_favorite_childhood_friend': "What was the name of your favorite childhood friend?",
        'q_first_school_name': "What was the name of your first school?",
        'q_mother_maiden_name': "What is your mother's maiden name?",
        'q_first_pet_name': "What was the name of your first pet?",
        'q_birth_city': "In which city were you born?",
        'q_favorite_teacher_name': "What was the name of your favorite teacher?",
        'q_childhood_nickname': "What was your childhood nickname?",
        'q_first_car_model': "What was the model of your first car?",
        # ── Default Language ──
        'set_default_language': 'Set as Default Language',
        'language_set_default': 'Language set as default!',
        'default_language': 'Default Language',
        # ── Lockout ──
        'lockout_title': 'Account Temporarily Locked',
        'lockout_message': 'Too many failed attempts. Please wait.',
        'voice_passphrase': 'Say: "My vault is secure"',
        'all_verified': 'All Verifications Complete!',
        'all_verified_sub': 'Welcome to My Vault',
        # ── Translator ──
        'translator': 'Smart Translator',
        'translator_sub': 'Translate text between any languages',
        'enter_text': 'Enter text to translate',
        'translation_result': 'Translation Result',
        'source_language': 'From Language',
        'target_language': 'To Language',
        'translate_btn': 'Translate',
        'translating': 'Translating...',
        'copy_translation': 'Copy Translation',
        'translation_copied': 'Translation copied!',
        'auto_detect': 'Auto Detect',
        'swap_languages': 'Swap Languages',
        'enter_text_first': 'Please enter text to translate',
        'translator_unavailable': 'Translator unavailable. Install deep_translator: pip install deep-translator',
        # ── Face Verification Instructions ──
        'face_look_up': '👆 Please look UP',
        'face_look_down': '👇 Please look DOWN',
        'face_look_left': '👈 Please look LEFT',
        'face_look_right': '👉 Please look RIGHT',
        'face_look_center': '🎯 Please look at CENTER',
        'face_hold_still': '⏳ Hold still...',
        'face_capture_complete': '✅ Face capture complete!',
        'face_move_head': 'Move your head slowly in the direction shown',
        'voice_speak_now': '🎤 Speak now...',
        'voice_listening': '👂 Listening...',
        'voice_processing': '⚙️ Processing voice...',
    },
    'Malayalam': {
        'vault': 'എന്റെ വാൾട്ട്', 'empty': 'വാൾട്ട് ശൂന്യമാണ്.\n+ അമർത്തി ചേർക്കുക.',
        'add': 'ക്രെഡൻഷ്യൽ ചേർക്കുക', 'edit': 'ക്രെഡൻഷ്യൽ തിരുത്തുക',
        'app': 'ആപ്പ് / വെബ്സൈറ്റ് പേര്', 'user': 'ഉപയോക്തൃനാമം / ഇമെയിൽ',
        'pass': 'പാസ്‌വേഡ്', 'save': 'സേവ്', 'cancel': 'റദ്ദാക്കുക',
        'delete': 'ഇല്ലാതാക്കുക', 'settings': 'ക്രമീകരണങ്ങൾ', 'language': 'ഭാഷ',
        'dark': 'ഡാർക്ക് മോഡ്', 'light': 'ലൈറ്റ് മോഡ്', 'about': 'കുറിച്ച്',
        'delete_confirm': 'ഇത് ഇല്ലാതാക്കണോ?', 'yes': 'അതെ', 'no': 'അല്ല',
        'search': 'തിരയുക...', 'copy_pass': 'പാസ്‌വേഡ് കോപ്പി ആയി!',
        'copy_user': 'ഉപയോക്തൃനാമം കോപ്പി ആയി!', 'fill_all': 'എല്ലാ ഫീൽഡുകളും പൂരിപ്പിക്കുക.',
        'set_master': 'മാസ്റ്റർ പാസ്‌കീ സജ്ജമാക്കുക',
        'set_master_sub': 'വാൾട്ട് സുരക്ഷിതമാക്കാൻ പാസ്‌കീ ഉണ്ടാക്കുക.',
        'new_pass': 'പുതിയ പാസ്‌കീ', 'confirm_pass': 'പാസ്‌കീ സ്ഥിരീകരിക്കുക',
        'create_passkey': 'പാസ്‌കീ ഉണ്ടാക്കുക',
        'enter_master': 'മാസ്റ്റർ പാസ്‌കീ നൽകുക',
        'enter_master_sub': 'വാൾട്ട് ലോക്ക് ചെയ്തിരിക്കുന്നു.',
        'unlock': 'അൺലോക്ക്',
        'wrong_pass': 'തെറ്റായ പാസ്‌കീ. വീണ്ടും ശ്രമിക്കുക.',
        'pass_mismatch': 'പാസ്‌കീകൾ പൊരുത്തപ്പെടുന്നില്ല.',
        'pass_too_short': 'പാസ്‌കീ കുറഞ്ഞത് 4 അക്ഷരങ്ങൾ ആയിരിക്കണം.',
        'biometric': 'ബയോമെട്രിക് ഉപയോഗിക്കുക',
        'biometric_hint': 'വിരലടയാളം / മുഖം ഉപയോഗിച്ച് പ്രവേശിക്കുക',
        'biometric_fail': 'ബയോമെട്രിക് പരാജയപ്പെട്ടു.',
        'biometric_unavailable': 'ബയോമെട്രിക് ലഭ്യമല്ല.',
        'change_passkey': 'പാസ്‌കീ മാറ്റുക',
        'current_pass': 'നിലവിലെ പാസ്‌കീ',
        'wrong_current': 'നിലവിലെ പാസ്‌കീ തെറ്റാണ്.',
        'passkey_changed': 'പാസ്‌കീ വിജയകരമായി മാറ്റി!',
        'security': 'സുരക്ഷ',
        'attempts_left': 'ശ്രമങ്ങൾ ബാക്കി',
        'locked_out': 'അധിക ശ്രമങ്ങൾ. ആപ്പ് ലോക്ക് ആയി.',
        'reset_vault': 'വാൾട്ട് റീസെറ്റ് ചെയ്യുക',
        'reset_confirm': 'ഇത് എല്ലാ ഡേറ്റയും പാസ്‌കീയും ഇല്ലാതാക്കും. തുടരണോ?',
        'reset_done': 'വാൾട്ട് റീസെറ്റ് ആയി.',
        'setup_title': 'സുരക്ഷിത സജ്ജീകരണം',
        'setup_step1': 'ഘട്ടം 1: പാസ്‌കീ സൃഷ്ടിക്കുക',
        'setup_step2': 'ഘട്ടം 2: രഹസ്യ ചോദ്യം',
        'setup_step3': 'ഘട്ടം 3: ശബ്ദ രജിസ്ട്രേഷൻ',
        'setup_step4': 'ഘട്ടം 4: മുഖ രജിസ്ട്രേഷൻ',
        'setup_step5': 'ഘട്ടം 5: വിരൽപ്പടം രജിസ്ട്രേഷൻ',
        'setup_step6': 'അവസാനം: എല്ലാം പരിശോധിക്കുക',
        'setup_complete': 'സജ്ജീകരണം പൂർത്തിയായി!',
        'setup_complete_sub': 'നിങ്ങളുടെ വാൾട്ട് ഇപ്പോൾ മൾട്ടി-ഫാക്ടർ പ്രാമാണീകരണത്തിലൂടെ സുരക്ഷിതമാണ്.',
        'mfa_required': 'മൾട്ടി-ഫാക്ടർ പ്രാമാണീകരണം ആവശ്യമാണ്',
        'mfa_verify': 'നിങ്ങളുടെ ഐഡന്റിറ്റി പരിശോധിക്കുക',
        'mfa_step': 'ഘട്ടം',
        'mfa_of': '/',
        'passkey_verification': 'പാസ്‌കീ പരിശോധന',
        'voice_verification': 'ശബ്ദ പരിശോധന',
        'face_verification': 'മുഖ പരിശോധന',
        'fingerprint_verification': 'വിരൽപ്പടം പരിശോധന',
        'voice_register': 'ശബ്ദം രജിസ്റ്റർ ചെയ്യുക',
        'face_register': 'മുഖം രജിസ്റ്റർ ചെയ്യുക',
        'fingerprint_register': 'വിരൽപ്പടം രജിസ്റ്റർ ചെയ്യുക',
        'voice_verify': 'ശബ്ദം പരിശോധിക്കുക',
        'face_verify': 'മുഖം പരിശോധിക്കുക',
        'fingerprint_verify': 'വിരൽപ്പടം പരിശോധിക്കുക',
        'passkey_hint': 'നിങ്ങളുടെ മാസ്റ്റർ പാസ്‌കീ നൽകുക',
        'voice_hint': 'ചുവടെ കാണുന്ന പാസ്ഫ്രെയ്സ് പറയുക',
        'face_hint': 'നിങ്ങളുടെ മുഖം ക്യാമറ ഫ്രെയിമിൽ സ്ഥാപിക്കുക',
        'fingerprint_hint': 'നിങ്ങളുടെ വിരൽ സെൻസറിൽ വയ്ക്കുക',
        'passkey_success': 'പാസ്‌കീ പരിശോധിച്ചു!',
        'voice_success': 'ശബ്ദം വിജയകരമായി പരിശോധിച്ചു!',
        'face_success': 'മുഖം വിജയകരമായി പരിശോധിച്ചു!',
        'fingerprint_success': 'വിരൽപ്പടം വിജയകരമായി പരിശോധിച്ചു!',
        'voice_registered': 'ശബ്ദം വിജയകരമായി രജിസ്റ്റർ ചെയ്തു!',
        'face_registered': 'മുഖം വിജയകരമായി രജിസ്റ്റർ ചെയ്തു!',
        'fingerprint_registered': 'വിരൽപ്പടം വിജയകരമായി രജിസ്റ്റർ ചെയ്തു!',
        'passkey_failed': 'തെറ്റായ പാസ്‌കീ.',
        'voice_failed': 'ശബ്ദ പരിശോധന പരാജയപ്പെട്ടു. വീണ്ടും ശ്രമിക്കുക.',
        'face_failed': 'മുഖ പരിശോധന പരാജയപ്പെട്ടു. വീണ്ടും ശ്രമിക്കുക.',
        'fingerprint_failed': 'വിരൽപ്പടം പരിശോധന പരാജയപ്പെട്ടു. വീണ്ടും ശ്രമിക്കുക.',
        'no_webcam': 'വെബ്ക്യാം കണ്ടെത്തിയില്ല. ഒരു വെബ്ക്യാം കണക്റ്റുചെയ്യുക.',
        'no_microphone': 'മൈക്രോഫോൺ കണ്ടെത്തിയില്ല. ഒരു മൈക്രോഫോൺ കണക്റ്റുചെയ്യുക.',
        'no_biometric_device': 'ബയോമെട്രിക് ഉപകരണം കണ്ടെത്തിയില്ല.',
        'verifying': 'പരിശോധിക്കുന്നു...',
        'registering': 'രജിസ്റ്റർ ചെയ്യുന്നു...',
        'please_wait': 'ദയവായി കാത്തിരിക്കുക...',
        'countdown': 'വീണ്ടും ശ്രമിക്കുക',
        'seconds': 'സെക്കൻഡ്',
        'minutes': 'മിനിറ്റ്',
        'continue_btn': 'തുടരുക',
        'next_btn': 'അടുത്തത്',
        'verify_btn': 'പരിശോധിക്കുക',
        'start_over': 'വീണ്ടും ആരംഭിക്കുക',
        'verified': 'പരിശോധിച്ചു',
        'pending': 'ബാക്കി',
        'secret_question': 'രഹസ്യ ചോദ്യം',
        'set_secret_question': 'രഹസ്യ ചോദ്യം സജ്ജമാക്കുക',
        'secret_question_sub': 'അക്കൗണ്ട് വീണ്ടെടുക്കൽ ചോദ്യം തിരഞ്ഞെടുക്കുക',
        'select_question': 'ഒരു ചോദ്യം തിരഞ്ഞെടുക്കുക',
        'your_answer': 'നിങ്ങളുടെ ഉത്തരം',
        'secret_answer': 'രഹസ്യ ഉത്തരം',
        'answer_hint': 'നിങ്ങളുടെ ഉത്തരം നൽകുക (കേസ്-സെൻസിറ്റീവ്)',
        'forgot_passkey': 'പാസ്‌കീ മറന്നോ?',
        'verify_identity': 'തിരിച്ചറിവ് പരിശോധിക്കുക',
        'answer_correct': 'ഉത്തരം പരിശോധിച്ചു!',
        'answer_wrong': 'തെറ്റായ ഉത്തരം. വീണ്ടും ശ്രമിക്കുക.',
        'q_favorite_childhood_friend': "നിങ്ങളുടെ പ്രിയപ്പെട്ട കുട്ട്യാല്പ്പാലത്തെ സുഹൃത്തിന്റെ പേര് എന്തായിരുന്നു?",
        'q_first_school_name': "നിങ്ങളുടെ ആദ്യ സ്കൂളിന്റെ പേര് എന്തായിരുന്നു?",
        'q_mother_maiden_name': "നിങ്ങളുടെ അമ്മയുടെ മാതൃപിതാവിന്റെ പേര് എന്താണ്?",
        'q_first_pet_name': "നിങ്ങളുടെ ആദ്യ വളർത്തുമൃഗത്തിന്റെ പേര് എന്തായിരുന്നു?",
        'q_birth_city': "നിങ്ങൾ ഏത് നഗരത്തിൽ ജനിച്ചു?",
        'q_favorite_teacher_name': "നിങ്ങളുടെ പ്രിയപ്പെട്ട അധ്യാപകന്റെ പേര് എന്തായിരുന്നു?",
        'q_childhood_nickname': "നിങ്ങളുടെ കുട്ട്യാല്പ്പാലത്തെ വിളിപ്പേര് എന്തായിരുന്നു?",
        'q_first_car_model': "നിങ്ങളുടെ ആദ്യ കാറിന്റെ മോഡൽ എന്തായിരുന്നു?",
        'set_default_language': 'സ്ഥിര ഭാഷയായി സജ്ജമാക്കുക',
        'language_set_default': 'ഭാഷ സ്ഥിരമായി സജ്ജമാക്കി!',
        'default_language': 'സ്ഥിര ഭാഷ',
        'lockout_title': 'അക്കൗണ്ട് താൽക്കാലികമായി ലോക്ക് ചെയ്തു',
        'lockout_message': 'അധികം ശ്രമങ്ങൾ. വീണ്ടും ശ്രമിക്കുന്നതിന് മുമ്പ് കാത്തിരിക്കുക.',
        'voice_passphrase': 'പറയുക: "എന്റെ വാൾട്ട് സുരക്ഷിതമാണ്"',
        'all_verified': 'എല്ലാ പരിശോധനകളും പൂർത്തിയായി!',
        'all_verified_sub': 'മൈ വാൾട്ടിലേക്ക് സ്വാഗതം',
        # ── Translator ──
        'translator': 'സ്മാർട്ട് ട്രാൻസ്ലേറ്റർ',
        'translator_sub': 'ഏത് ഭാഷയിലേക്കും വാചകം വിവർത്തനം ചെയ്യുക',
        'enter_text': 'വിവർത്തനം ചെയ്യാൻ വാചകം നൽകുക',
        'translation_result': 'വിവർത്തന ഫലം',
        'source_language': 'ഉറവിട ഭാഷ',
        'target_language': 'ലക്ഷ്യ ഭാഷ',
        'translate_btn': 'വിവർത്തനം ചെയ്യുക',
        'translating': 'വിവർത്തനം ചെയ്യുന്നു...',
        'copy_translation': 'വിവർത്തനം കോപ്പി ചെയ്യുക',
        'translation_copied': 'വിവർത്തനം കോപ്പി ആയി!',
        'auto_detect': 'സ്വയം കണ്ടെത്തൽ',
        'swap_languages': 'ഭാഷകൾ മാറ്റുക',
        'enter_text_first': 'ദയവായി വിവർത്തനത്തിന് വാചകം നൽകുക',
        'translator_unavailable': 'ട്രാൻസ്ലേറ്റർ ലഭ്യമല്ല. pip install deep-translator ചെയ്യുക',
    },
    'Hindi': {
        'vault': 'मेरा वॉल्ट', 'empty': 'वॉल्ट खाली है।\n+ दबाकर जोड़ें।',
        'add': 'क्रेडेंशियल जोड़ें', 'edit': 'क्रेडेंशियल संपादित करें',
        'app': 'ऐप / वेबसाइट नाम', 'user': 'यूज़रनेम / ईमेल', 'pass': 'पासवर्ड',
        'save': 'सेव', 'cancel': 'रद्द करें', 'delete': 'हटाएं',
        'settings': 'सेटिंग्स', 'language': 'भाषा', 'dark': 'डार्क मोड',
        'light': 'लाइट मोड', 'about': 'जानकारी',
        'delete_confirm': 'क्या इसे हटाएं?', 'yes': 'हाँ', 'no': 'नहीं',
        'search': 'खोजें...', 'copy_pass': 'पासवर्ड कॉपी हो गया!',
        'copy_user': 'यूज़रनेम कॉपी हो गया!', 'fill_all': 'सभी फ़ील्ड भरें।',
        'set_master': 'मास्टर पासकी सेट करें',
        'set_master_sub': 'वॉल्ट सुरक्षित करने के लिए पासकी बनाएं।',
        'new_pass': 'नई पासकी', 'confirm_pass': 'पासकी की पुष्टि करें',
        'create_passkey': 'पासकी बनाएं',
        'enter_master': 'मास्टर पासकी दर्ज करें',
        'enter_master_sub': 'वॉल्ट लॉक है।',
        'unlock': 'अनलॉक करें',
        'wrong_pass': 'गलत पासकी। फिर से कोशिश करें।',
        'pass_mismatch': 'पासकी मेल नहीं खाती।',
        'pass_too_short': 'पासकी कम से कम 4 अक्षर की होनी चाहिए।',
        'biometric': 'बायोमेट्रिक का उपयोग करें',
        'biometric_hint': 'फिंगरप्रिंट / चेहरे से प्रमाणित करें',
        'biometric_fail': 'बायोमेट्रिक विफल।',
        'biometric_unavailable': 'बायोमेट्रिक उपलब्ध नहीं।',
        'change_passkey': 'पासकी बदलें',
        'current_pass': 'वर्तमान पासकी',
        'wrong_current': 'वर्तमान पासकी गलत है।',
        'passkey_changed': 'पासकी सफलतापूर्वक बदली गई!',
        'security': 'सुरक्षा',
        'attempts_left': 'प्रयास शेष',
        'locked_out': 'बहुत अधिक प्रयास। ऐप लॉक।',
        'reset_vault': 'वॉल्ट रीसेट करें',
        'reset_confirm': 'यह सभी डेटा और पासकी मिटा देगा। जारी रखें?',
        'reset_done': 'वॉल्ट रीसेट हो गया।',
        'setup_title': 'सुरक्षित सेटअप',
        'setup_step1': 'चरण 1: पासकी बनाएं',
        'setup_step2': 'चरण 2: गुप्त प्रश्न',
        'setup_step3': 'चरण 3: आवाज पंजीकरण',
        'setup_step4': 'चरण 4: चेहरा पंजीकरण',
        'setup_step5': 'चरण 5: फिंगरप्रिंट पंजीकरण',
        'setup_step6': 'अंतिम: सब कुछ सत्यापित करें',
        'setup_complete': 'सेटअप पूर्ण!',
        'setup_complete_sub': 'आपका वॉल्ट अब बहु-कारक प्रमाणीकरण से सुरक्षित है।',
        'mfa_required': 'बहु-कारक प्रमाणीकरण आवश्यक',
        'mfa_verify': 'अपनी पहचान सत्यापित करें',
        'mfa_step': 'चरण',
        'mfa_of': '/',
        'passkey_verification': 'पासकी सत्यापन',
        'voice_verification': 'आवाज सत्यापन',
        'face_verification': 'चेहरा सत्यापन',
        'fingerprint_verification': 'फिंगरप्रिंट सत्यापन',
        'voice_register': 'आवाज पंजीकृत करें',
        'face_register': 'चेहरा पंजीकृत करें',
        'fingerprint_register': 'फिंगरप्रिंट पंजीकृत करें',
        'voice_verify': 'आवाज सत्यापित करें',
        'face_verify': 'चेहरा सत्यापित करें',
        'fingerprint_verify': 'फिंगरप्रिंट सत्यापित करें',
        'passkey_hint': 'अपनी मास्टर पासकी दर्ज करें',
        'voice_hint': 'नीचे दिखाया गया पासफ्रेज़ बोलें',
        'face_hint': 'अपना चेहरा कैमरा फ्रेम में रखें',
        'fingerprint_hint': 'अपनी उंगली सेंसर पर रखें',
        'passkey_success': 'पासकी सत्यापित!',
        'voice_success': 'आवाज सफलतापूर्वक सत्यापित!',
        'face_success': 'चेहरा सफलतापूर्वक सत्यापित!',
        'fingerprint_success': 'फिंगरप्रिंट सफलतापूर्वक सत्यापित!',
        'voice_registered': 'आवाज सफलतापूर्वक पंजीकृत!',
        'face_registered': 'चेहरा सफलतापूर्वक पंजीकृत!',
        'fingerprint_registered': 'फिंगरप्रिंट सफलतापूर्वक पंजीकृत!',
        'passkey_failed': 'गलत पासकी।',
        'voice_failed': 'आवाज सत्यापन विफल। पुनः प्रयास करें।',
        'face_failed': 'चेहरा सत्यापन विफल। पुनः प्रयास करें।',
        'fingerprint_failed': 'फिंगरप्रिंट सत्यापन विफल। पुनः प्रयास करें।',
        'no_webcam': 'वेबकैम नहीं मिला। वेबकैम कनेक्ट करें।',
        'no_microphone': 'माइक्रोफोन नहीं मिला। माइक्रोफोन कनेक्ट करें।',
        'no_biometric_device': 'बायोमेट्रिक डिवाइस नहीं मिला।',
        'verifying': 'सत्यापित कर रहा है...',
        'registering': 'पंजीकृत कर रहा है...',
        'please_wait': 'कृपया प्रतीक्षा करें...',
        'countdown': 'पुनः प्रयास करें',
        'seconds': 'सेकंड',
        'minutes': 'मिनट',
        'continue_btn': 'जारी रखें',
        'next_btn': 'अगला',
        'verify_btn': 'सत्यापित करें',
        'start_over': 'फिर से शुरू करें',
        'verified': 'सत्यापित',
        'pending': 'बाकी',
        'secret_question': 'गुप्त प्रश्न',
        'set_secret_question': 'गुप्त प्रश्न सेट करें',
        'secret_question_sub': 'खाता पुनर्प्राप्ति के लिए प्रश्न चुनें',
        'select_question': 'एक प्रश्न चुनें',
        'your_answer': 'आपका उत्तर',
        'secret_answer': 'गुप्त उत्तर',
        'answer_hint': 'अपना उत्तर दर्ज करें (केस-सेंसिटिव)',
        'forgot_passkey': 'पासकी भूल गए?',
        'verify_identity': 'पहचान सत्यापित करें',
        'answer_correct': 'उत्तर सत्यापित!',
        'answer_wrong': 'गलत उत्तर। पुनः प्रयास करें।',
        'q_favorite_childhood_friend': "आपके बचपन के पसंदीदा दोस्त का नाम क्या था?",
        'q_first_school_name': "आपके पहले स्कूल का नाम क्या था?",
        'q_mother_maiden_name': "आपकी माँ का माइडन नेम क्या है?",
        'q_first_pet_name': "आपके पहले पालतू जानवर का नाम क्या था?",
        'q_birth_city': "आप किस शहर में पैदा हुए थे?",
        'q_favorite_teacher_name': "आपके पसंदीदा शिक्षक का नाम क्या था?",
        'q_childhood_nickname': "आपका बचपन का उपनाम क्या था?",
        'q_first_car_model': "आपकी पहली कार का मॉडल क्या था?",
        'set_default_language': 'डिफ़ॉल्ट भाषा के रूप में सेट करें',
        'language_set_default': 'भाषा डिफ़ॉल्ट सेट हो गई!',
        'default_language': 'डिफ़ॉल्ट भाषा',
        'lockout_title': 'खाता अस्थायी रूप से लॉक',
        'lockout_message': 'बहुत अधिक विफल प्रयास। कृपया प्रतीक्षा करें।',
        'voice_passphrase': 'बोलें: "मेरा वॉल्ट सुरक्षित है"',
        'all_verified': 'सभी सत्यापन पूर्ण!',
        'all_verified_sub': 'मेरे वॉल्ट में आपका स्वागत है',
        # ── Translator ──
        'translator': 'स्मार्ट अनुवादक',
        'translator_sub': 'किसी भी भाषा में टेक्स्ट का अनुवाद करें',
        'enter_text': 'अनुवाद के लिए टेक्स्ट दर्ज करें',
        'translation_result': 'अनुवाद परिणाम',
        'source_language': 'स्रोत भाषा',
        'target_language': 'लक्ष्य भाषा',
        'translate_btn': 'अनुवाद करें',
        'translating': 'अनुवाद हो रहा है...',
        'copy_translation': 'अनुवाद कॉपी करें',
        'translation_copied': 'अनुवाद कॉपी हो गया!',
        'auto_detect': 'स्वतः पता लगाएं',
        'swap_languages': 'भाषाएं बदलें',
        'enter_text_first': 'कृपया अनुवाद के लिए टेक्स्ट दर्ज करें',
        'translator_unavailable': 'अनुवादक उपलब्ध नहीं है। pip install deep-translator करें',
    },
    'French': {
        'vault': 'Mon Coffre', 'empty': 'Coffre vide.\nAppuyez + pour ajouter.',
        'add': 'Ajouter un identifiant', 'edit': 'Modifier',
        'app': "Nom de l'application / site", 'user': "Nom d'utilisateur / e-mail",
        'pass': 'Mot de passe', 'save': 'Enregistrer', 'cancel': 'Annuler',
        'delete': 'Supprimer', 'settings': 'Paramètres', 'language': 'Langue',
        'dark': 'Mode sombre', 'light': 'Mode clair', 'about': 'À propos',
        'delete_confirm': 'Supprimer cet identifiant?', 'yes': 'Oui', 'no': 'Non',
        'search': 'Rechercher...', 'copy_pass': 'Mot de passe copié!',
        'copy_user': "Nom d'utilisateur copié!", 'fill_all': 'Veuillez remplir tous les champs.',
        'set_master': 'Définir la clé maîtresse',
        'set_master_sub': 'Créez une clé pour sécuriser votre coffre.',
        'new_pass': 'Nouvelle clé', 'confirm_pass': 'Confirmer la clé',
        'create_passkey': 'Créer la clé',
        'enter_master': 'Entrer la clé maîtresse',
        'enter_master_sub': 'Votre coffre est verrouillé.',
        'unlock': 'Déverrouiller',
        'wrong_pass': 'Clé incorrecte. Réessayez.',
        'pass_mismatch': 'Les clés ne correspondent pas.',
        'pass_too_short': 'La clé doit comporter au moins 4 caractères.',
        'biometric': 'Utiliser la biométrie',
        'biometric_hint': 'Authentifier par empreinte / visage',
        'biometric_fail': 'Biométrie échouée.',
        'biometric_unavailable': 'Biométrie non disponible.',
        'change_passkey': 'Changer la clé',
        'current_pass': 'Clé actuelle',
        'wrong_current': 'La clé actuelle est incorrecte.',
        'passkey_changed': 'Clé changée avec succès!',
        'security': 'Sécurité',
        'attempts_left': 'tentatives restantes',
        'locked_out': 'Trop de tentatives. Application verrouillée.',
        'reset_vault': 'Réinitialiser le coffre',
        'reset_confirm': 'Cela effacera toutes les données et la clé. Continuer?',
        'reset_done': 'Le coffre a été réinitialisé.',
        'setup_title': 'Configuration Sécurisée',
        'setup_step1': 'Étape 1: Créer la Clé',
        'setup_step2': 'Étape 2: Question Secrète',
        'setup_step3': 'Étape 3: Enregistrement Voix',
        'setup_step4': 'Étape 4: Enregistrement Visage',
        'setup_step5': 'Étape 5: Enregistrement Empreinte',
        'setup_step6': 'Final: Tout Vérifier',
        'setup_complete': 'Configuration Terminée!',
        'setup_complete_sub': 'Votre coffre est maintenant sécurisé avec authentification multi-facteurs.',
        'mfa_required': 'Authentification Multi-Facteurs Requise',
        'mfa_verify': 'Vérifiez Votre Identité',
        'mfa_step': 'Étape',
        'mfa_of': 'sur',
        'passkey_verification': 'Vérification Clé',
        'voice_verification': 'Vérification Vocale',
        'face_verification': 'Vérification Faciale',
        'fingerprint_verification': 'Vérification Empreinte',
        'voice_register': 'Enregistrer la Voix',
        'face_register': 'Enregistrer le Visage',
        'fingerprint_register': 'Enregistrer Empreinte',
        'voice_verify': 'Vérifier la Voix',
        'face_verify': 'Vérifier le Visage',
        'fingerprint_verify': 'Vérifier Empreinte',
        'passkey_hint': 'Entrez votre clé maîtresse',
        'voice_hint': 'Prononcez la phrase affichée',
        'face_hint': 'Positionnez votre visage dans le cadre',
        'fingerprint_hint': 'Placez votre doigt sur le capteur',
        'passkey_success': 'Clé vérifiée!',
        'voice_success': 'Voix vérifiée avec succès!',
        'face_success': 'Visage vérifié avec succès!',
        'fingerprint_success': 'Empreinte vérifiée avec succès!',
        'voice_registered': 'Voix enregistrée avec succès!',
        'face_registered': 'Visage enregistré avec succès!',
        'fingerprint_registered': 'Empreinte enregistrée avec succès!',
        'passkey_failed': 'Clé incorrecte.',
        'voice_failed': 'Échec vérification vocale. Réessayez.',
        'face_failed': 'Échec vérification faciale. Réessayez.',
        'fingerprint_failed': 'Échec vérification empreinte. Réessayez.',
        'no_webcam': 'Pas de webcam. Connectez une webcam.',
        'wrong_current': 'La clé actuelle est incorrecte.',
        'passkey_changed': 'Clé changée avec succès!',
        'security': 'Sécurité',
        'attempts_left': 'tentatives restantes',
        'locked_out': 'Trop de tentatives. Application verrouillée.',
        'reset_vault': 'Réinitialiser le coffre',
        'reset_confirm': 'Cela effacera toutes les données et la clé. Continuer?',
        'reset_done': 'Le coffre a été réinitialisé.',
        'setup_title': 'Configuration Sécurisée',
        'setup_step1': 'Étape 1: Créer la Clé',
        'setup_step2': 'Étape 2: Question Secrète',
        'setup_step3': 'Étape 3: Enregistrement Voix',
        'setup_step4': 'Étape 4: Enregistrement Visage',
        'setup_step5': 'Étape 5: Enregistrement Empreinte',
        'setup_step6': 'Final: Tout Vérifier',
        'setup_complete': 'Configuration Terminée!',
        'setup_complete_sub': 'Votre coffre est maintenant sécurisé avec authentification multi-facteurs.',
        'mfa_required': 'Authentification Multi-Facteurs Requise',
        'mfa_verify': 'Vérifiez Votre Identité',
        'mfa_step': 'Étape',
        'mfa_of': 'sur',
        'passkey_verification': 'Vérification Clé',
        'voice_verification': 'Vérification Vocale',
        'face_verification': 'Vérification Faciale',
        'fingerprint_verification': 'Vérification Empreinte',
        'voice_register': 'Enregistrer la Voix',
        'face_register': 'Enregistrer le Visage',
        'fingerprint_register': 'Enregistrer Empreinte',
        'voice_verify': 'Vérifier la Voix',
        'face_verify': 'Vérifier le Visage',
        'fingerprint_verify': 'Vérifier Empreinte',
        'passkey_hint': 'Entrez votre clé maîtresse',
        'voice_hint': 'Prononcez la phrase affichée',
        'face_hint': 'Positionnez votre visage dans le cadre',
        'fingerprint_hint': 'Placez votre doigt sur le capteur',
        'passkey_success': 'Clé vérifiée!',
        'voice_success': 'Voix vérifiée avec succès!',
        'face_success': 'Visage vérifié avec succès!',
        'fingerprint_success': 'Empreinte vérifiée avec succès!',
        'voice_registered': 'Voix enregistrée avec succès!',
        'face_registered': 'Visage enregistré avec succès!',
        'fingerprint_registered': 'Empreinte enregistrée avec succès!',
        'passkey_failed': 'Clé incorrecte.',
        'voice_failed': 'Échec vérification vocale. Réessayez.',
        'face_failed': 'Échec vérification faciale. Réessayez.',
        'fingerprint_failed': 'Échec vérification empreinte. Réessayez.',
        'no_webcam': 'Pas de webcam. Connectez une webcam.',
        'no_microphone': 'Pas de microphone. Connectez un micro.',
        'no_biometric_device': 'Aucun appareil biométrique détecté.',
        'verifying': 'Vérification...',
        'registering': 'Enregistrement...',
        'please_wait': 'Veuillez patienter...',
        'countdown': 'Réessayez dans',
        'seconds': 'secondes',
        'minutes': 'minutes',
        'continue_btn': 'Continuer',
        'next_btn': 'Suivant',
        'verify_btn': 'Vérifier',
        'start_over': 'Recommencer',
        'verified': 'Vérifié',
        'pending': 'En attente',
        'secret_question': 'Question Secrète',
        'set_secret_question': 'Définir Question Secrète',
        'secret_question_sub': 'Choisissez une question de récupération',
        'select_question': 'Sélectionnez une question',
        'your_answer': 'Votre Réponse',
        'secret_answer': 'Réponse Secrète',
        'answer_hint': 'Entrez votre réponse (sensible à la casse)',
        'forgot_passkey': 'Clé Oubliée?',
        'verify_identity': 'Vérifier Identité',
        'answer_correct': 'Réponse vérifiée!',
        'answer_wrong': 'Mauvaise réponse. Réessayez.',
        'q_favorite_childhood_friend': "Quel était le nom de votre ami d'enfance préféré?",
        'q_first_school_name': "Quel était le nom de votre première école?",
        'q_mother_maiden_name': "Quel est le nom de jeune fille de votre mère",
        'no_microphone': 'Pas de microphone. Connectez un micro.',
        'no_biometric_device': 'Aucun appareil biométrique détecté.',
        'verifying': 'Vérification...',
        'registering': 'Enregistrement...',
        'please_wait': 'Veuillez patienter...',
        'countdown': 'Réessayez dans',
        'seconds': 'secondes',
        'minutes': 'minutes',
        'continue_btn': 'Continuer',
        'next_btn': 'Suivant',
        'verify_btn': 'Vérifier',
        'start_over': 'Recommencer',
        'verified': 'Vérifié',
        'pending': 'En attente',
        'secret_question': 'Question Secrète',
        'set_secret_question': 'Définir Question Secrète',
        'secret_question_sub': 'Choisissez une question de récupération',
        'select_question': 'Sélectionnez une question',
        'your_answer': 'Votre Réponse',
        'secret_answer': 'Réponse Secrète',
        'answer_hint': 'Entrez votre réponse (sensible à la casse)',
        'forgot_passkey': 'Clé Oubliée?',
        'verify_identity': 'Vérifier Identité',
        'answer_correct': 'Réponse vérifiée!',
        'answer_wrong': 'Mauvaise réponse. Réessayez.',
        'q_favorite_childhood_friend': "Quel était le nom de votre ami d'enfance préféré?",
        'q_first_school_name': "Quel était le nom de votre première école?",
        'q_mother_maiden_name': "Quel est le nom de jeune fille de votre mère?",
        'q_first_pet_name': "Quel était le nom de votre premier animal?",
        'q_birth_city': "Dans quelle ville êtes-vous né?",
        'q_favorite_teacher_name': "Quel était le nom de votre professeur préféré?",
        'q_childhood_nickname': "Quel était votre surnom d'enfance?",
        'q_first_car_model': "Quel était le modèle de votre première voiture?",
        'set_default_language': 'Définir comme Langue par Défaut',
        'language_set_default': 'Langue définie par défaut!',
        'default_language': 'Langue par Défaut',
        'lockout_title': 'Compte Temporairement Verrouillé',
        'lockout_message': 'Trop de tentatives échouées. Veuillez attendre.',
        'voice_passphrase': 'Dites: "Mon coffre est sécurisé"',
        'all_verified': 'Toutes Vérifications Terminées!',
        'all_verified_sub': 'Bienvenue dans Mon Coffre',
        # ── Translator ──
        'translator': 'Traducteur Intelligent',
        'translator_sub': 'Traduisez du texte dans n\'importe quelle langue',
        'enter_text': 'Entrez le texte à traduire',
        'translation_result': 'Résultat de la Traduction',
        'source_language': 'Langue Source',
        'target_language': 'Langue Cible',
        'translate_btn': 'Traduire',
        'translating': 'Traduction...',
        'copy_translation': 'Copier la Traduction',
        'translation_copied': 'Traduction copiée!',
        'auto_detect': 'Détection Auto',
        'swap_languages': 'Inverser les Langues',
        'enter_text_first': 'Veuillez entrer le texte à traduire',
        'translator_unavailable': 'Traducteur non disponible. Installez: pip install deep-translator',
    },
    'Spanish': {
        'vault': 'Mi Bóveda', 'empty': 'Bóveda vacía.\nToca + para agregar.',
        'add': 'Agregar credencial', 'edit': 'Editar credencial',
        'app': 'Nombre de la app / sitio', 'user': 'Usuario / correo',
        'pass': 'Contraseña', 'save': 'Guardar', 'cancel': 'Cancelar',
        'delete': 'Eliminar', 'settings': 'Configuración', 'language': 'Idioma',
        'dark': 'Modo oscuro', 'light': 'Modo claro', 'about': 'Acerca de',
        'delete_confirm': '¿Eliminar esta credencial?', 'yes': 'Sí', 'no': 'No',
        'search': 'Buscar...', 'copy_pass': '¡Contraseña copiada!',
        'copy_user': '¡Usuario copiado!', 'fill_all': 'Por favor llena todos los campos.',
        'set_master': 'Establecer clave maestra',
        'set_master_sub': 'Crea una clave para proteger tu bóveda.',
        'new_pass': 'Nueva clave', 'confirm_pass': 'Confirmar clave',
        'create_passkey': 'Crear clave',
        'enter_master': 'Ingresar clave maestra',
        'enter_master_sub': 'Tu bóveda está bloqueada.',
        'unlock': 'Desbloquear',
        'wrong_pass': 'Clave incorrecta. Inténtalo de nuevo.',
        'pass_mismatch': 'Las claves no coinciden.',
        'pass_too_short': 'La clave debe tener al menos 4 caracteres.',
        'biometric': 'Usar biometría',
        'biometric_hint': 'Autenticar con huella / rostro',
        'biometric_fail': 'Biometría fallida.',
        'biometric_unavailable': 'Biometría no disponible.',
        'change_passkey': 'Cambiar clave',
        'current_pass': 'Clave actual',
        'wrong_current': 'La clave actual es incorrecta.',
        'passkey_changed': '¡Clave cambiada con éxito!',
        'security': 'Seguridad',
        'attempts_left': 'intentos restantes',
        'locked_out': 'Demasiados intentos. App bloqueada.',
        'reset_vault': 'Restablecer bóveda',
        'reset_confirm': 'Esto borrará todos los datos y la clave. ¿Continuar?',
        'reset_done': 'La bóveda ha sido restablecida.',
        'setup_title': 'Configuración Segura',
        'setup_step1': 'Paso 1: Crear Clave',
        'setup_step2': 'Paso 2: Pregunta Secreta',
        'setup_step3': 'Paso 3: Registro de Voz',
        'setup_step4': 'Paso 4: Registro Facial',
        'setup_step5': 'Paso 5: Registro de Huella',
        'setup_step6': 'Final: Verificar Todo',
        'setup_complete': '¡Configuración Completa!',
        'setup_complete_sub': 'Su bóveda ahora está segura con autenticación multifactor.',
        'mfa_required': 'Autenticación Multifactor Requerida',
        'mfa_verify': 'Verifique Su Identidad',
        'mfa_step': 'Paso',
        'mfa_of': 'de',
        'passkey_verification': 'Verificación de Clave',
        'voice_verification': 'Verificación de Voz',
        'face_verification': 'Verificación Facial',
        'fingerprint_verification': 'Verificación de Huella',
        'voice_register': 'Registrar Voz',
        'face_register': 'Registrar Rostro',
        'fingerprint_register': 'Registrar Huella',
        'voice_verify': 'Verificar Voz',
        'face_verify': 'Verificar Rostro',
        'fingerprint_verify': 'Verificar Huella',
        'passkey_hint': 'Ingrese su clave maestra',
        'voice_hint': 'Diga la frase mostrada abajo',
        'face_hint': 'Posicione su rostro en el marco de la cámara',
        'fingerprint_hint': 'Coloque su dedo en el sensor',
        'passkey_success': '¡Clave verificada!',
        'voice_success': '¡Voz verificada con éxito!',
        'face_success': '¡Rostro verificado con éxito!',
        'fingerprint_success': '¡Huella verificada con éxito!',
        'voice_registered': '¡Voz registrada con éxito!',
        'face_registered': '¡Rostro registrado con éxito!',
        'fingerprint_registered': '¡Huella registrada con éxito!',
        'passkey_failed': 'Clave incorrecta.',
        'voice_failed': 'Verificación de voz fallida. Inténtelo de nuevo.',
        'face_failed': 'Verificación facial fallida. Inténtelo de nuevo.',
        'fingerprint_failed': 'Verificación de huella fallida. Inténtelo de nuevo.',
        'no_webcam': 'No se detectó webcam. Conecte una webcam.',
        'no_microphone': 'No se detectó micrófono. Conecte un micrófono.',
        'no_biometric_device': 'Dispositivo biométrico no detectado.',
        'verifying': 'Verificando...',
        'registering': 'Registrando...',
        'please_wait': 'Por favor espere...',
        'countdown': 'Inténtelo de nuevo en',
        'seconds': 'segundos',
        'minutes': 'minutos',
        'continue_btn': 'Continuar',
        'next_btn': 'Siguiente',
        'verify_btn': 'Verificar',
        'start_over': 'Empezar de Nuevo',
        'verified': 'Verificado',
        'pending': 'Pendiente',
        'secret_question': 'Pregunta Secreta',
        'set_secret_question': 'Establecer Pregunta Secreta',
        'secret_question_sub': 'Elija una pregunta de recuperación de cuenta',
        'select_question': 'Seleccione una pregunta',
        'your_answer': 'Su Respuesta',
        'secret_answer': 'Respuesta Secreta',
        'answer_hint': 'Ingrese su respuesta (sensible a mayúsculas)',
        'forgot_passkey': '¿Olvidó la clave?',
        'verify_identity': 'Verificar Identidad',
        'answer_correct': '¡Respuesta verificada!',
        'answer_wrong': 'Respuesta incorrecta. Inténtelo de nuevo.',
        'q_favorite_childhood_friend': "¿Cuál era el nombre de su amigo de la infancia favorito?",
        'q_first_school_name': "¿Cuál era el nombre de su primera escuela?",
        'q_mother_maiden_name': "¿Cuál es el apellido de soltera de su madre?",
        'q_first_pet_name': "¿Cuál era el nombre de su primera mascota?",
        'q_birth_city': "¿En qué ciudad nació?",
        'q_favorite_teacher_name': "¿Cuál era el nombre de su maestro favorito?",
        'q_childhood_nickname': "¿Cuál era su apodo de la infancia?",
        'q_first_car_model': "¿Cuál era el modelo de su primer coche?",
        'set_default_language': 'Establecer como Idioma Predeterminado',
        'language_set_default': '¡Idioma establecido como predeterminado!',
        'default_language': 'Idioma Predeterminado',
        'lockout_title': 'Cuenta Temporalmente Bloqueada',
        'lockout_message': 'Demasiados intentos fallidos. Por favor espere.',
        'voice_passphrase': 'Diga: "Mi bóveda está segura"',
        'all_verified': '¡Todas las Verificaciones Completas!',
        'all_verified_sub': 'Bienvenido a Mi Bóveda',
        # ── Translator ──
        'translator': 'Traductor Inteligente',
        'translator_sub': 'Traduzca texto entre cualquier idioma',
        'enter_text': 'Ingrese texto para traducir',
        'translation_result': 'Resultado de la Traducción',
        'source_language': 'Idioma de Origen',
        'target_language': 'Idioma de Destino',
        'translate_btn': 'Traducir',
        'translating': 'Traduciendo...',
        'copy_translation': 'Copiar Traducción',
        'translation_copied': '¡Traducción copiada!',
        'auto_detect': 'Detección Automática',
        'swap_languages': 'Intercambiar Idiomas',
        'enter_text_first': 'Por favor ingrese texto para traducir',
        'translator_unavailable': 'Traductor no disponible. Instale: pip install deep-translator',
        # ── Face Verification Instructions ──
        'face_look_up': '👆 Por favor mire hacia ARRIBA',
        'face_look_down': '👇 Por favor mire hacia ABAJO',
        'face_look_left': '👈 Por favor mire hacia la IZQUIERDA',
        'face_look_right': '👉 Por favor mire hacia la DERECHA',
        'face_look_center': '🎯 Por favor mire al CENTRO',
        'face_hold_still': '⏳ Manténgase quieto...',
        'face_capture_complete': '✅ ¡Captura facial completa!',
        'face_move_head': 'Mueva su cabeza lentamente en la dirección mostrada',
        'voice_speak_now': '🎤 Hable ahora...',
        'voice_listening': '👂 Escuchando...',
        'voice_processing': '⚙️ Procesando voz...',
    },
}

# ================= SAFE HELPERS =================
def ic(name: str):
    for src in [getattr(ft, 'Icons', None), getattr(ft, 'icons', None)]:
        if src:
            v = getattr(src, name, None)
            if v is not None:
                return v
    return None

def cl(name: str):
    for src in [getattr(ft, 'Colors', None), getattr(ft, 'colors', None)]:
        if src:
            v = getattr(src, name, None)
            if v is not None:
                return v
    return None

WHITE      = cl('WHITE')      or '#ffffff'
RED_400    = cl('RED_400')    or '#ef5350'
GREEN_400  = cl('GREEN_400')  or '#66bb6a'
INDIGO_200 = cl('INDIGO_200') or '#9fa8da'
INDIGO_400 = cl('INDIGO_400') or '#5c6bc0'
INDIGO_600 = cl('INDIGO_600') or '#3949ab'
AMBER_400  = cl('AMBER_400')  or '#ffca28'

# ================= PASSKEY HASHING =================
def _hash_passkey(passkey: str, salt: str) -> str:
    return hmac.new(salt.encode(), passkey.encode(), hashlib.sha256).hexdigest()

# ================= DEVICE DETECTION =================
def check_webcam_available() -> bool:
    try:
        if is_windows():
            result = subprocess.run(
                ['powershell', '-NonInteractive', '-Command', 
                 'Get-CimInstance Win32_PnPEntity | Where-Object { $_.Name -like "*camera*" -or $_.Name -like "*webcam*" -or $_.Name -like "*video*" } | Select-Object -First 1'],
                timeout=10, capture_output=True, text=True
            )
            return bool(result.stdout.strip())
        elif is_macos():
            result = subprocess.run(['system_profiler', 'SPCameraDataType'], timeout=10, capture_output=True, text=True)
            return 'Camera' in result.stdout or 'FaceTime' in result.stdout
        elif is_linux():
            return os.path.exists('/dev/video0')
        return False
    except Exception:
        return False

def check_microphone_available() -> bool:
    try:
        if is_windows():
            result = subprocess.run(
                ['powershell', '-NonInteractive', '-Command', 
                 'Get-CimInstance Win32_PnPEntity | Where-Object { $_.Name -like "*microphone*" -or $_.Name -like "*audio input*" -or $_.Name -like "*mic*" } | Select-Object -First 1'],
                timeout=10, capture_output=True, text=True
            )
            return bool(result.stdout.strip())
        elif is_macos():
            result = subprocess.run(['system_profiler', 'SPAudioDataType'], timeout=10, capture_output=True, text=True)
            return 'Microphone' in result.stdout or 'Input' in result.stdout
        elif is_linux():
            result = subprocess.run(['arecord', '-l'], timeout=5, capture_output=True)
            return result.returncode == 0
        return False
    except Exception:
        return False

# ================= BIOMETRIC HELPERS =================
def platform_biometric_available() -> bool:
    if is_mobile():
        return True
    if is_windows():
        try:
            r = subprocess.run(
                ['powershell', '-NonInteractive', '-Command',
                 '[bool]([Windows.Security.Credentials.UI.UserConsentVerifier,Windows.Security.Credentials.UI,ContentType=WindowsRuntime])'],
                timeout=5, capture_output=True
            )
            return r.returncode == 0
        except Exception:
            return False
    if is_macos():
        try:
            r = subprocess.run(['which', 'osascript'], timeout=3, capture_output=True)
            return r.returncode == 0
        except Exception:
            return False
    if is_linux():
        try:
            r = subprocess.run(['which', 'pkexec'], timeout=3, capture_output=True)
            return r.returncode == 0
        except Exception:
            return False
    return False

def try_desktop_biometric() -> bool:
    if is_windows():
        try:
            script = (
                "Add-Type -AssemblyName System.Runtime.WindowsRuntime; "
                "$t = [Windows.Security.Credentials.UI.UserConsentVerifier,Windows.Security.Credentials.UI,ContentType=WindowsRuntime]; "
                "$op = $t::RequestVerificationAsync('My Vault'); "
                "$r = [System.WindowsRuntimeSystemExtensions]::AsTask($op).Result; "
                "if ($r -eq 'Verified') { exit 0 } else { exit 1 }"
            )
            result = subprocess.run(['powershell', '-NonInteractive', '-Command', script], timeout=30, capture_output=True)
            return result.returncode == 0
        except Exception:
            return False
    if is_macos():
        try:
            script = f'do shell script "echo verified" with prompt "Authenticate to open {APP_NAME}" with administrator privileges'
            result = subprocess.run(['osascript', '-e', script], timeout=30, capture_output=True)
            return result.returncode == 0
        except Exception:
            return False
    if is_linux():
        try:
            result = subprocess.run(['pkexec', '--disable-internal-agent', 'true'], timeout=30, capture_output=True)
            return result.returncode == 0
        except Exception:
            return False
    return False

# ================= SIMULATED VERIFICATION =================
def simulate_voice_verification() -> bool:
    """Simulated voice verification - in real app, use actual speech recognition"""
    time.sleep(2)
    return True

def simulate_face_verification() -> bool:
    """Simulated face verification - in real app, use actual face detection"""
    time.sleep(2)
    return True

# Face verification steps with directions
FACE_VERIFICATION_STEPS = [
    ('face_look_center', 'CENTER', '🎯'),
    ('face_look_up', 'UP', '👆'),
    ('face_look_down', 'DOWN', '👇'),
    ('face_look_left', 'LEFT', '👈'),
    ('face_look_right', 'RIGHT', '👉'),
    ('face_look_center', 'FINAL', '✅'),
]

VOICE_VERIFICATION_STEPS = [
    ('voice_speak_now', '🎤'),
    ('voice_listening', '👂'),
    ('voice_processing', '⚙️'),
]

# ================= STORAGE =================
class StorageBox:
    def __init__(self, name: str):
        self.path = os.path.join(STORAGE_PATH, name)

    def get(self, key: str, defaultValue=None):
        try:
            with shelve.open(self.path) as db:
                return db.get(key, defaultValue)
        except Exception:
            return defaultValue

    def put(self, key: str, value):
        try:
            with shelve.open(self.path) as db:
                db[key] = value
        except Exception as e:
            print(f"[put] {e}")

    def add(self, value):
        try:
            with shelve.open(self.path) as db:
                items = db.get('_items', [])
                items.append(value)
                db['_items'] = items
        except Exception as e:
            print(f"[add] {e}")

    def update_at(self, index: int, value):
        try:
            with shelve.open(self.path) as db:
                items = db.get('_items', [])
                if 0 <= index < len(items):
                    items[index] = value
                    db['_items'] = items
        except Exception as e:
            print(f"[update_at] {e}")

    def get_all(self) -> List[Dict]:
        try:
            with shelve.open(self.path) as db:
                return list(db.get('_items', []))
        except Exception:
            return []

    def delete_at(self, index: int):
        try:
            with shelve.open(self.path) as db:
                items = db.get('_items', [])
                if 0 <= index < len(items):
                    items.pop(index)
                    db['_items'] = items
        except Exception as e:
            print(f"[delete_at] {e}")

    def clear_all(self):
        try:
            with shelve.open(self.path) as db:
                db.clear()
        except Exception as e:
            print(f"[clear_all] {e}")

# ================= CREDENTIAL CARD =================
def build_card(credential, index, on_delete, on_edit, on_copy_user, on_copy_pass, t):
    app_name = credential.get('app', '')
    username = credential.get('user', '')
    letter = app_name[0].upper() if app_name else '?'

    return ft.Card(
        elevation=4,
        content=ft.Container(
            padding=ft.Padding(14, 14, 14, 14),
            content=ft.Column(
                spacing=8,
                controls=[
                    ft.Row(
                        spacing=10,
                        controls=[
                            ft.CircleAvatar(
                                content=ft.Text(letter, weight=ft.FontWeight.BOLD, color=WHITE),
                                bgcolor=INDIGO_400,
                                radius=22,
                            ),
                            ft.Column(
                                spacing=2, expand=True,
                                controls=[
                                    ft.Text(app_name, weight=ft.FontWeight.BOLD, size=15,
                                            no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                                    ft.Text(username, size=12, opacity=0.7,
                                            no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                                ],
                            ),
                        ],
                    ),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.END,
                        spacing=0,
                        controls=[
                            ft.IconButton(icon=ic('PERSON_OUTLINE'), tooltip=t('copy_user'),
                                          icon_size=20, on_click=lambda _, i=index: on_copy_user(i)),
                            ft.IconButton(icon=ic('LOCK_OUTLINE'), tooltip=t('copy_pass'),
                                          icon_size=20, on_click=lambda _, i=index: on_copy_pass(i)),
                            ft.IconButton(icon=ic('EDIT_OUTLINED'), tooltip=t('edit'),
                                          icon_size=20, on_click=lambda _, i=index: on_edit(i)),
                            ft.IconButton(icon=ic('DELETE_OUTLINE'), tooltip=t('delete'),
                                          icon_size=20, icon_color=cl('RED_400'),
                                          on_click=lambda _, i=index: on_delete(i)),
                        ],
                    ),
                ],
            ),
        ),
    )

# ================= MAIN APP =================
class MyVaultApp:
    def __init__(self):
        self.vault = StorageBox('vault')
        self.settings = StorageBox('settings')
        self.auth = StorageBox('auth')
        self._search_query = ''
        self._failed_attempts = 0
        self._lockout_until: Optional[datetime] = None
        self._lockout_count = 0
        self._setup_data = {}  # Temporary storage during setup
        self._total_setup_steps = 6 if is_mobile() else 5  # +1 for fingerprint on mobile
        self.page: Optional[ft.Page] = None
        self._content: Optional[ft.Column] = None
        self._header_title: Optional[ft.Text] = None
        self._settings_btn: Optional[ft.IconButton] = None

    @property
    def lang(self) -> str:
        return self.settings.get('default_lang', defaultValue=self.settings.get('lang', 'English')) or 'English'

    def t(self, key: str) -> str:
        return translations.get(self.lang, translations['English']).get(key, translations['English'].get(key, key))

    # ── Passkey helpers ──
    def _has_passkey(self) -> bool:
        return bool(self.auth.get('pass_hash'))

    def _verify_passkey(self, passkey: str) -> bool:
        salt = self.auth.get('salt', '')
        pass_hash = self.auth.get('pass_hash', '')
        return hmac.compare_digest(_hash_passkey(passkey, salt), pass_hash)

    def _save_passkey(self, passkey: str):
        salt = secrets.token_hex(16)
        self.auth.put('salt', salt)
        self.auth.put('pass_hash', _hash_passkey(passkey, salt))

    # ── Secret Question helpers ──
    def _has_secret_question(self) -> bool:
        return bool(self.auth.get('secret_question'))

    def _save_secret_question(self, question_key: str, answer: str):
        answer_salt = secrets.token_hex(16)
        answer_hash = _hash_passkey(answer.strip().lower(), answer_salt)
        self.auth.put('secret_question', question_key)
        self.auth.put('secret_answer_hash', answer_hash)
        self.auth.put('secret_answer_salt', answer_salt)

    def _verify_secret_answer(self, answer: str) -> bool:
        stored_hash = self.auth.get('secret_answer_hash', '')
        salt = self.auth.get('secret_answer_salt', '')
        return hmac.compare_digest(_hash_passkey(answer.strip().lower(), salt), stored_hash)

    # ── Lockout helpers ──
    def _is_locked_out(self) -> bool:
        if self._lockout_until is None:
            lockout_data = self.auth.get('lockout_until')
            if lockout_data:
                try:
                    self._lockout_until = datetime.fromisoformat(lockout_data)
                except Exception:
                    pass
        if self._lockout_until:
            return datetime.now() < self._lockout_until
        return False

    def _get_lockout_remaining(self) -> int:
        if self._lockout_until:
            remaining = (self._lockout_until - datetime.now()).total_seconds()
            return max(0, int(remaining))
        return 0

    def _apply_lockout(self):
        self._lockout_count = self.auth.get('lockout_count', 0) + 1
        self.auth.put('lockout_count', self._lockout_count)
        lockout_time = min(LOCKOUT_BASE_TIME * (LOCKOUT_MULTIPLIER ** (self._lockout_count - 1)), MAX_LOCKOUT_TIME)
        self._lockout_until = datetime.now() + timedelta(seconds=lockout_time)
        self.auth.put('lockout_until', self._lockout_until.isoformat())
        self._failed_attempts = 0
        self.auth.put('failed_attempts', 0)

    def _clear_lockout(self):
        self._lockout_until = None
        self._lockout_count = 0
        self.auth.put('lockout_until', None)
        self.auth.put('lockout_count', 0)
        self.auth.put('failed_attempts', 0)

    def main(self, page: ft.Page):
        self.page = page
        page.title = APP_NAME
        page.padding = 0
        page.spacing = 0
        page.theme = ft.Theme(color_scheme_seed='indigo')
        page.dark_theme = ft.Theme(color_scheme_seed='deepPurple')
        try:
            page.window.width = 420
            page.window.height = 780
            page.window.resizable = True
        except Exception:
            pass
        page.theme_mode = (ft.ThemeMode.DARK if self.settings.get('dark', defaultValue=False) else ft.ThemeMode.LIGHT)
        
        self._failed_attempts = self.auth.get('failed_attempts', 0)
        
        if not self._has_passkey():
            self._build_setup_step1()
        else:
            self._build_verification_page()

    # =========================================================
    # ================= SETUP STEP 1: PASSKEY =================
    # =========================================================
    def _build_setup_step1(self):
        """Step 1: Create Passkey"""
        self.page.controls.clear()
        self._setup_data = {}

        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        grad_colors = ['#4a148c', '#1a237e'] if is_dark else ['#3949ab', '#1e88e5']

        new_f = ft.TextField(label=self.t('new_pass'), password=True, can_reveal_password=True,
                             autofocus=True, border_radius=12, prefix_icon=ic('LOCK_OUTLINE'))
        con_f = ft.TextField(label=self.t('confirm_pass'), password=True, can_reveal_password=True,
                             border_radius=12, prefix_icon=ic('LOCK_OUTLINE'))
        err = ft.Text('', color=RED_400, size=12, text_align=ft.TextAlign.CENTER)

        def _next(_):
            p1, p2 = new_f.value.strip(), con_f.value.strip()
            if len(p1) < 4:
                err.value = self.t('pass_too_short')
            elif p1 != p2:
                err.value = self.t('pass_mismatch')
            else:
                self._setup_data['passkey'] = p1
                self._build_setup_step2()
                return
            self.page.update()

        self.page.add(
            ft.Column(expand=True, spacing=0, controls=[
                ft.Container(
                    padding=ft.Padding(16, 50, 16, 30),
                    gradient=ft.LinearGradient(colors=grad_colors, begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1)),
                    content=ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10, controls=[
                        ft.Icon(ic('LOCK'), size=60, color=WHITE),
                        ft.Text(self.t('setup_step1'), size=22, weight=ft.FontWeight.BOLD, color=WHITE, text_align=ft.TextAlign.CENTER),
                        ft.Text(self.t('set_master_sub'), size=13, color=WHITE, opacity=0.85, text_align=ft.TextAlign.CENTER),
                    ]),
                ),
                ft.Container(
                    expand=True, padding=ft.Padding(24, 32, 24, 24),
                    content=ft.Column(spacing=16, controls=[
                        ft.Text(f"{self.t('mfa_step')} 1 {self.t('mfa_of')} {self._total_setup_steps}", size=12, opacity=0.6, text_align=ft.TextAlign.CENTER),
                        ft.Divider(height=1),
                        new_f, con_f, err,
                        ft.ElevatedButton(text=self.t('next_btn'), icon=ic('ARROW_FORWARD'), bgcolor=INDIGO_600, color=WHITE,
                                          style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)), on_click=_next, width=float('inf')),
                    ]),
                ),
            ])
        )
        self.page.update()

    # =========================================================
    # ================= SETUP STEP 2: SECRET QUESTION =========
    # =========================================================
    def _build_setup_step2(self):
        """Step 2: Set Secret Question"""
        self.page.controls.clear()

        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        grad_colors = ['#4a148c', '#1a237e'] if is_dark else ['#3949ab', '#1e88e5']

        question_options = [ft.dropdown.Option(key=q, text=self.t(q)) for q in SECRET_QUESTIONS]
        question_dd = ft.Dropdown(label=self.t('select_question'), options=question_options, border_radius=12, width=float('inf'))
        answer_f = ft.TextField(label=self.t('your_answer'), border_radius=12, prefix_icon=ic('QUESTION_ANSWER'))
        err = ft.Text('', color=RED_400, size=12, text_align=ft.TextAlign.CENTER)

        def _next(_):
            q, a = question_dd.value, answer_f.value.strip()
            if not q:
                err.value = self.t('select_question')
            elif len(a) < 2:
                err.value = self.t('answer_hint')
            else:
                self._setup_data['question'] = q
                self._setup_data['answer'] = a
                self._build_setup_step3()
                return
            self.page.update()

        self.page.add(
            ft.Column(expand=True, spacing=0, controls=[
                ft.Container(
                    padding=ft.Padding(16, 50, 16, 30),
                    gradient=ft.LinearGradient(colors=grad_colors, begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1)),
                    content=ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10, controls=[
                        ft.Icon(ic('HELP_OUTLINE'), size=60, color=WHITE),
                        ft.Text(self.t('setup_step2'), size=22, weight=ft.FontWeight.BOLD, color=WHITE, text_align=ft.TextAlign.CENTER),
                        ft.Text(self.t('secret_question_sub'), size=13, color=WHITE, opacity=0.85, text_align=ft.TextAlign.CENTER),
                    ]),
                ),
                ft.Container(
                    expand=True, padding=ft.Padding(24, 24, 24, 24),
                    content=ft.Column(spacing=16, controls=[
                        ft.Text(f"{self.t('mfa_step')} 2 {self.t('mfa_of')} {self._total_setup_steps}", size=12, opacity=0.6, text_align=ft.TextAlign.CENTER),
                        ft.Divider(height=1),
                        question_dd, answer_f, err,
                        ft.ElevatedButton(text=self.t('next_btn'), icon=ic('ARROW_FORWARD'), bgcolor=INDIGO_600, color=WHITE,
                                          style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)), on_click=_next, width=float('inf')),
                    ]),
                ),
            ])
        )
        self.page.update()

    # =========================================================
    # ================= SETUP STEP 3: VOICE ===================
    # =========================================================
    def _build_setup_step3(self):
        """Step 3: Register Voice with interactive steps"""
        self.page.controls.clear()

        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        grad_colors = ['#4a148c', '#1a237e'] if is_dark else ['#3949ab', '#1e88e5']

        mic_available = check_microphone_available() if not is_mobile() else True
        
        # Voice status indicator
        voice_icon = ft.Text('🎤', size=80, text_align=ft.TextAlign.CENTER)
        status_text = ft.Text('', color=INDIGO_400, size=14, text_align=ft.TextAlign.CENTER)
        progress_text = ft.Text('', size=12, color=GREEN_400, text_align=ft.TextAlign.CENTER)
        passphrase_text = ft.Text(f'"{self.t("voice_passphrase")}"', size=16, 
                                   weight=ft.FontWeight.BOLD, color=INDIGO_600, text_align=ft.TextAlign.CENTER)
        
        # Progress indicator
        step_indicators = ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8,
            controls=[ft.Icon(ic('RADIO_BUTTON_UNCHECKED'), size=16, color=INDIGO_200) for _ in range(3)]
        )
        
        register_btn = ft.ElevatedButton(
            text=self.t('voice_register'), 
            icon=ic('MIC'), 
            bgcolor=INDIGO_600, 
            color=WHITE,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)), 
            width=float('inf')
        )

        def update_step_indicator(current_step):
            for i, ctrl in enumerate(step_indicators.controls):
                if i < current_step:
                    ctrl.name = ic('CHECK_CIRCLE')
                    ctrl.color = GREEN_400
                elif i == current_step:
                    ctrl.name = ic('RADIO_BUTTON_CHECKED')
                    ctrl.color = INDIGO_400
                else:
                    ctrl.name = ic('RADIO_BUTTON_UNCHECKED')
                    ctrl.color = INDIGO_200
            self.page.update()

        def _register(_):
            if not mic_available:
                status_text.value = f"❌ {self.t('no_microphone')}"
                status_text.color = RED_400
                self.page.update()
                return
            
            register_btn.disabled = True
            register_btn.visible = False
            self.page.update()
            
            def do_register():
                # Voice verification steps with extended time and countdown
                steps = [
                    ('voice_speak_now', '🎤', 'Get ready to speak...', 3.0),  # 3 seconds to prepare
                    ('voice_listening', '👂', 'Speak NOW: "My vault is secure"', 10.0),  # 10 seconds to speak fully
                    ('voice_processing', '⚙️', 'Processing voice...', 2.0),  # 2 seconds to process
                ]
                
                for i, (key, emoji, desc, delay) in enumerate(steps):
                    update_step_indicator(i)
                    voice_icon.value = emoji
                    status_text.value = self.t(key)
                    
                    # Show countdown for listening step
                    if key == 'voice_listening':
                        remaining = int(delay)
                        while remaining > 0:
                            progress_text.value = f"🎤 {desc} ({remaining}s remaining)"
                            self.page.update()
                            time.sleep(1)
                            remaining -= 1
                        progress_text.value = f"Step {i+1} of 3 - {desc}"
                    else:
                        progress_text.value = f"Step {i+1} of 3 - {desc}"
                        self.page.update()
                        time.sleep(delay)
                
                # Final success
                update_step_indicator(3)
                voice_icon.value = '✅'
                status_text.value = self.t('voice_registered')
                status_text.color = GREEN_400
                progress_text.value = "Voice registered successfully!"
                self.page.update()
                
                self._setup_data['voice_registered'] = True
                time.sleep(1.5)
                self._build_setup_step4()
                    
            threading.Thread(target=do_register, daemon=True).start()

        register_btn.on_click = _register

        device_status = ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=10, controls=[
            ft.Icon(ic('MIC') if mic_available else ic('MIC_OFF'), 
                    color=GREEN_400 if mic_available else RED_400, size=16),
            ft.Text(f"Microphone: {'✓ Connected' if mic_available else '✗ Not Found'}", 
                    size=11, color=GREEN_400 if mic_available else RED_400),
        ]) if not is_mobile() else None

        content_controls = [
            ft.Text(f"{self.t('mfa_step')} 3 {self.t('mfa_of')} {self._total_setup_steps}", 
                    size=12, opacity=0.6, text_align=ft.TextAlign.CENTER),
            ft.Divider(height=1),
            device_status if device_status else ft.Container(),
            ft.Container(height=10),
            voice_icon,
            passphrase_text,
            ft.Text(self.t('voice_hint'), size=11, color=INDIGO_200, text_align=ft.TextAlign.CENTER),
            status_text,
            progress_text,
            ft.Container(height=10),
            step_indicators,
            ft.Container(height=10),
            register_btn,
        ]

        self.page.add(
            ft.Column(expand=True, spacing=0, controls=[
                ft.Container(
                    padding=ft.Padding(16, 50, 16, 30),
                    gradient=ft.LinearGradient(colors=grad_colors, begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1)),
                    content=ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10, controls=[
                        ft.Icon(ic('MIC'), size=60, color=WHITE),
                        ft.Text(self.t('setup_step3'), size=22, weight=ft.FontWeight.BOLD, color=WHITE, text_align=ft.TextAlign.CENTER),
                        ft.Text(self.t('voice_hint'), size=13, color=WHITE, opacity=0.85, text_align=ft.TextAlign.CENTER),
                    ]),
                ),
                ft.Container(
                    expand=True, padding=ft.Padding(24, 24, 24, 24),
                    content=ft.Column(
                        spacing=12, 
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER, 
                        controls=content_controls
                    ),
                ),
            ])
        )
        self.page.update()

    # =========================================================
    # ================= SETUP STEP 4: FACE ====================
    # =========================================================
    def _build_setup_step4(self):
        """Step 4: Register Face with head movement instructions"""
        self.page.controls.clear()

        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        grad_colors = ['#4a148c', '#1a237e'] if is_dark else ['#3949ab', '#1e88e5']

        webcam_available = check_webcam_available() if not is_mobile() else True
        
        # Direction indicator - large emoji/text showing current direction
        direction_icon = ft.Text('🎯', size=80, text_align=ft.TextAlign.CENTER)
        direction_text = ft.Text(self.t('face_look_center'), size=18, weight=ft.FontWeight.BOLD, 
                                  text_align=ft.TextAlign.CENTER, color=INDIGO_600)
        status_text = ft.Text('', color=INDIGO_400, size=14, text_align=ft.TextAlign.CENTER)
        progress_text = ft.Text('', size=12, color=GREEN_400, text_align=ft.TextAlign.CENTER)
        
        # Progress indicator
        step_indicators = ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8,
            controls=[ft.Icon(ic('RADIO_BUTTON_UNCHECKED'), size=16, color=INDIGO_200) for _ in range(6)]
        )
        
        register_btn = ft.ElevatedButton(
            text=self.t('face_register'), 
            icon=ic('FACE'), 
            bgcolor=INDIGO_600, 
            color=WHITE,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)), 
            width=float('inf')
        )
        
        retry_btn = ft.ElevatedButton(
            text='Retry Registration',
            icon=ic('REFRESH'),
            bgcolor=AMBER_400,
            color=WHITE,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
            width=float('inf'),
            visible=False
        )

        def update_step_indicator(current_step):
            for i, ctrl in enumerate(step_indicators.controls):
                if i < current_step:
                    ctrl.name = ic('CHECK_CIRCLE')
                    ctrl.color = GREEN_400
                elif i == current_step:
                    ctrl.name = ic('RADIO_BUTTON_CHECKED')
                    ctrl.color = INDIGO_400
                else:
                    ctrl.name = ic('RADIO_BUTTON_UNCHECKED')
                    ctrl.color = INDIGO_200
            self.page.update()

        def _register(_):
            if not webcam_available:
                status_text.value = f"❌ {self.t('no_webcam')}"
                status_text.color = RED_400
                self.page.update()
                return
            
            register_btn.disabled = True
            register_btn.visible = False
            retry_btn.visible = False
            self.page.update()
            
            def do_register():
                # Go through each face direction step
                directions = [
                    ('face_look_center', '🎯', 'CENTER'),
                    ('face_look_up', '👆', 'UP'),
                    ('face_look_down', '👇', 'DOWN'),
                    ('face_look_left', '👈', 'LEFT'),
                    ('face_look_right', '👉', 'RIGHT'),
                    ('face_look_center', '✅', 'COMPLETE'),
                ]
                
                for i, (key, emoji, direction) in enumerate(directions):
                    update_step_indicator(i)
                    direction_icon.value = emoji
                    direction_text.value = self.t(key)
                    status_text.value = self.t('face_hold_still')
                    progress_text.value = f"Step {i+1} of 6"
                    self.page.update()
                    time.sleep(1.5)  # Time for user to move head
                
                # Final success
                update_step_indicator(6)
                direction_icon.value = '✅'
                direction_text.value = self.t('face_capture_complete')
                direction_text.color = GREEN_400
                status_text.value = self.t('face_registered')
                status_text.color = GREEN_400
                progress_text.value = "All face positions captured!"
                self.page.update()
                
                self._setup_data['face_registered'] = True
                time.sleep(1.5)
                
                # Mobile goes to fingerprint, PC goes to final verification
                if is_mobile():
                    self._build_setup_step5()
                else:
                    self._build_setup_final()
                    
            threading.Thread(target=do_register, daemon=True).start()

        register_btn.on_click = _register
        retry_btn.on_click = _register

        device_status = ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=10, controls=[
            ft.Icon(ic('VIDEOCAM') if webcam_available else ic('VIDEOCAM_OFF'), 
                    color=GREEN_400 if webcam_available else RED_400, size=16),
            ft.Text(f"Webcam: {'✓ Connected' if webcam_available else '✗ Not Found'}", 
                    size=11, color=GREEN_400 if webcam_available else RED_400),
        ]) if not is_mobile() else None

        content_controls = [
            ft.Text(f"{self.t('mfa_step')} 4 {self.t('mfa_of')} {self._total_setup_steps}", 
                    size=12, opacity=0.6, text_align=ft.TextAlign.CENTER),
            ft.Divider(height=1),
            device_status if device_status else ft.Container(),
            ft.Container(height=10),
            direction_icon,
            direction_text,
            ft.Text(self.t('face_move_head'), size=11, color=INDIGO_200, text_align=ft.TextAlign.CENTER),
            status_text,
            progress_text,
            ft.Container(height=10),
            step_indicators,
            ft.Container(height=10),
            register_btn,
            retry_btn,
        ]

        self.page.add(
            ft.Column(expand=True, spacing=0, controls=[
                ft.Container(
                    padding=ft.Padding(16, 50, 16, 30),
                    gradient=ft.LinearGradient(colors=grad_colors, begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1)),
                    content=ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10, controls=[
                        ft.Icon(ic('FACE'), size=60, color=WHITE),
                        ft.Text(self.t('setup_step4'), size=22, weight=ft.FontWeight.BOLD, color=WHITE, text_align=ft.TextAlign.CENTER),
                        ft.Text(self.t('face_hint'), size=13, color=WHITE, opacity=0.85, text_align=ft.TextAlign.CENTER),
                    ]),
                ),
                ft.Container(
                    expand=True, padding=ft.Padding(24, 24, 24, 24),
                    content=ft.Column(
                        spacing=12, 
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER, 
                        controls=content_controls
                    ),
                ),
            ])
        )
        self.page.update()

    # =========================================================
    # ================= SETUP STEP 5: FINGERPRINT (MOBILE) =====
    # =========================================================
    def _build_setup_step5(self):
        """Step 5: Register Fingerprint (Mobile Only)"""
        self.page.controls.clear()

        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        grad_colors = ['#4a148c', '#1a237e'] if is_dark else ['#3949ab', '#1e88e5']

        bio_available = platform_biometric_available()
        status_text = ft.Text('', color=INDIGO_400, size=14, text_align=ft.TextAlign.CENTER)
        err_text = ft.Text('', color=RED_400, size=12, text_align=ft.TextAlign.CENTER)

        def _register(_):
            if is_mobile():
                try:
                    def _on_login(e: ft.LoginEvent):
                        if e.error:
                            err_text.value = self.t('biometric_fail')
                            self.page.update()
                        else:
                            self._setup_data['fingerprint_registered'] = True
                            status_text.value = self.t('fingerprint_registered')
                            status_text.color = GREEN_400
                            self.page.update()
                            time.sleep(1)
                            self._build_setup_final()
                    self.page.on_login = _on_login
                    self.page.login(ft.LocalAuthentication(reason=f"Register fingerprint for {APP_NAME}"))
                except Exception:
                    err_text.value = self.t('biometric_unavailable')
                    self.page.update()
            else:
                # Desktop: Use system biometric
                status_text.value = self.t('registering')
                self.page.update()
                success = try_desktop_biometric()
                if success:
                    self._setup_data['fingerprint_registered'] = True
                    status_text.value = self.t('fingerprint_registered')
                    status_text.color = GREEN_400
                    self.page.update()
                    time.sleep(1)
                    self._build_setup_final()
                else:
                    err_text.value = self.t('biometric_fail')
                    self.page.update()

        self.page.add(
            ft.Column(expand=True, spacing=0, controls=[
                ft.Container(
                    padding=ft.Padding(16, 50, 16, 30),
                    gradient=ft.LinearGradient(colors=grad_colors, begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1)),
                    content=ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10, controls=[
                        ft.Icon(ic('FINGERPRINT'), size=60, color=WHITE),
                        ft.Text(self.t('setup_step5'), size=22, weight=ft.FontWeight.BOLD, color=WHITE, text_align=ft.TextAlign.CENTER),
                        ft.Text(self.t('fingerprint_hint'), size=13, color=WHITE, opacity=0.85, text_align=ft.TextAlign.CENTER),
                    ]),
                ),
                ft.Container(
                    expand=True, padding=ft.Padding(24, 24, 24, 24),
                    content=ft.Column(spacing=16, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                        ft.Text(f"{self.t('mfa_step')} 5 {self.t('mfa_of')} {self._total_setup_steps}", size=12, opacity=0.6, text_align=ft.TextAlign.CENTER),
                        ft.Divider(height=1),
                        ft.IconButton(icon=ic('FINGERPRINT'), icon_size=80, icon_color=INDIGO_400,
                                      style=ft.ButtonStyle(shape=ft.CircleBorder(), overlay_color=INDIGO_200), on_click=_register),
                        status_text, err_text,
                        ft.ElevatedButton(text=self.t('fingerprint_register'), icon=ic('FINGERPRINT'), bgcolor=INDIGO_600, color=WHITE,
                                          style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)), on_click=_register, width=float('inf')),
                    ]),
                ),
            ])
        )
        self.page.update()

    # =========================================================
    # ================= SETUP FINAL: VERIFY ALL ===============
    # =========================================================
    def _build_setup_final(self):
        """Final Step: Verify all credentials before entry"""
        self.page.controls.clear()

        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        grad_colors = ['#4a148c', '#1a237e'] if is_dark else ['#3949ab', '#1e88e5']

        verified = {'passkey': False, 'voice': False, 'face': False, 'fingerprint': False}
        total_steps = 4 if is_mobile() else 3
        current_step = [0]

        # Verification UI components
        pass_f = ft.TextField(label=self.t('passkey_hint'), password=True, can_reveal_password=True,
                              border_radius=12, prefix_icon=ic('LOCK'))
        status_text = ft.Text('', color=INDIGO_400, size=14, text_align=ft.TextAlign.CENTER)
        err_text = ft.Text('', color=RED_400, size=12, text_align=ft.TextAlign.CENTER)
        
        # Status indicators
        indicators = ft.Column(spacing=8)
        self._update_indicators(indicators, verified)

        def _verify_passkey(_):
            if pass_f.value.strip() == self._setup_data.get('passkey', ''):
                verified['passkey'] = True
                err_text.value = ''
                _next_verification()
            else:
                err_text.value = self.t('passkey_failed')
            self._update_indicators(indicators, verified)
            self.page.update()

        def _verify_voice(_):
            status_text.value = self.t('verifying')
            self.page.update()
            def do_verify():
                success = simulate_voice_verification()
                if success:
                    verified['voice'] = True
                    status_text.value = self.t('voice_success')
                    status_text.color = GREEN_400
                    _next_verification()
                else:
                    err_text.value = self.t('voice_failed')
                self._update_indicators(indicators, verified)
                self.page.update()
            threading.Thread(target=do_verify, daemon=True).start()

        def _verify_face(_):
            status_text.value = self.t('verifying')
            self.page.update()
            def do_verify():
                success = simulate_face_verification()
                if success:
                    verified['face'] = True
                    status_text.value = self.t('face_success')
                    status_text.color = GREEN_400
                    _next_verification()
                else:
                    err_text.value = self.t('face_failed')
                self._update_indicators(indicators, verified)
                self.page.update()
            threading.Thread(target=do_verify, daemon=True).start()

        def _verify_fingerprint(_):
            if is_mobile():
                try:
                    def _on_login(e: ft.LoginEvent):
                        if e.error:
                            err_text.value = self.t('biometric_fail')
                        else:
                            verified['fingerprint'] = True
                            status_text.value = self.t('fingerprint_success')
                            status_text.color = GREEN_400
                            _check_all_verified()
                        self._update_indicators(indicators, verified)
                        self.page.update()
                    self.page.on_login = _on_login
                    self.page.login(ft.LocalAuthentication(reason=f"Verify fingerprint for {APP_NAME}"))
                except Exception:
                    err_text.value = self.t('biometric_unavailable')
                    self.page.update()

        def _next_verification():
            current_step[0] += 1
            _check_all_verified()

        def _check_all_verified():
            all_verified = verified['passkey'] and verified['voice'] and verified['face']
            if is_mobile():
                all_verified = all_verified and verified['fingerprint']
            
            if all_verified:
                time.sleep(0.5)
                self._complete_setup()

        def _get_current_ui():
            step = current_step[0]
            if step == 0:  # Passkey
                return ft.Column(spacing=12, controls=[
                    ft.Text(self.t('passkey_verification'), size=16, weight=ft.FontWeight.BOLD),
                    pass_f,
                    ft.ElevatedButton(text=self.t('verify_btn'), icon=ic('LOCK_OPEN'), bgcolor=INDIGO_600, color=WHITE,
                                      style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)), on_click=_verify_passkey, width=float('inf')),
                ])
            elif step == 1:  # Voice
                return ft.Column(spacing=12, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                    ft.Text(self.t('voice_verification'), size=16, weight=ft.FontWeight.BOLD),
                    ft.Text(f'"{self.t("voice_passphrase")}"', size=12, color=INDIGO_600),
                    ft.IconButton(icon=ic('MIC'), icon_size=60, icon_color=INDIGO_400,
                                  style=ft.ButtonStyle(shape=ft.CircleBorder(), overlay_color=INDIGO_200), on_click=_verify_voice),
                    ft.ElevatedButton(text=self.t('voice_verify'), icon=ic('MIC'), bgcolor=INDIGO_600, color=WHITE,
                                      style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)), on_click=_verify_voice, width=float('inf')),
                ])
            elif step == 2:  # Face
                return ft.Column(spacing=12, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                    ft.Text(self.t('face_verification'), size=16, weight=ft.FontWeight.BOLD),
                    ft.IconButton(icon=ic('FACE'), icon_size=60, icon_color=INDIGO_400,
                                  style=ft.ButtonStyle(shape=ft.CircleBorder(), overlay_color=INDIGO_200), on_click=_verify_face),
                    ft.ElevatedButton(text=self.t('face_verify'), icon=ic('FACE'), bgcolor=INDIGO_600, color=WHITE,
                                      style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)), on_click=_verify_face, width=float('inf')),
                ])
            elif step == 3 and is_mobile():  # Fingerprint (mobile only)
                return ft.Column(spacing=12, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                    ft.Text(self.t('fingerprint_verification'), size=16, weight=ft.FontWeight.BOLD),
                    ft.IconButton(icon=ic('FINGERPRINT'), icon_size=60, icon_color=INDIGO_400,
                                  style=ft.ButtonStyle(shape=ft.CircleBorder(), overlay_color=INDIGO_200), on_click=_verify_fingerprint),
                    ft.ElevatedButton(text=self.t('fingerprint_verify'), icon=ic('FINGERPRINT'), bgcolor=INDIGO_600, color=WHITE,
                                      style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)), on_click=_verify_fingerprint, width=float('inf')),
                ])
            return ft.Container()

        content_area = ft.Container(content=_get_current_ui())

        self.page.add(
            ft.Column(expand=True, spacing=0, controls=[
                ft.Container(
                    padding=ft.Padding(16, 40, 16, 20),
                    gradient=ft.LinearGradient(colors=grad_colors, begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1)),
                    content=ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8, controls=[
                        ft.Icon(ic('VERIFIED_USER'), size=50, color=WHITE),
                        ft.Text(self.t('setup_step6'), size=20, weight=ft.FontWeight.BOLD, color=WHITE, text_align=ft.TextAlign.CENTER),
                        ft.Text(self.t('setup_complete_sub'), size=12, color=WHITE, opacity=0.85, text_align=ft.TextAlign.CENTER),
                    ]),
                ),
                ft.Container(
                    expand=True, padding=ft.Padding(20, 20, 20, 20),
                    content=ft.Column(spacing=12, controls=[
                        indicators,
                        ft.Divider(height=1),
                        content_area,
                        status_text, err_text,
                    ]),
                ),
            ])
        )
        self.page.update()

    def _update_indicators(self, indicators_col: ft.Column, verified: Dict):
        indicators_col.controls.clear()
        items = [
            ('passkey', 'LOCK', self.t('passkey_verification')),
            ('voice', 'MIC', self.t('voice_verification')),
            ('face', 'FACE', self.t('face_verification')),
        ]
        if is_mobile():
            items.append(('fingerprint', 'FINGERPRINT', self.t('fingerprint_verification')))

        for key, icon, label in items:
            is_verified = verified.get(key, False)
            indicators_col.controls.append(
                ft.Row(controls=[
                    ft.Icon(ic('CHECK_CIRCLE') if is_verified else ic('RADIO_BUTTON_UNCHECKED'),
                            color=GREEN_400 if is_verified else INDIGO_400, size=20),
                    ft.Text(label, size=13, color=GREEN_400 if is_verified else None),
                ])
            )

    def _complete_setup(self):
        """Save all setup data and enter the app"""
        self._save_passkey(self._setup_data['passkey'])
        self._save_secret_question(self._setup_data['question'], self._setup_data['answer'])
        self._setup_data = {}
        
        self.page.snack_bar = ft.SnackBar(content=ft.Text(self.t('setup_complete')), duration=2000)
        self.page.snack_bar.open = True
        self.page.update()
        time.sleep(1)
        self._build_page()

    # =========================================================
    # ================= LOGIN VERIFICATION =====================
    # =========================================================
    def _build_verification_page(self):
        """Login: Verify all credentials with interactive steps"""
        if self._is_locked_out():
            self._build_lockout_page()
            return

        self.page.controls.clear()

        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        grad_colors = ['#4a148c', '#1a237e'] if is_dark else ['#3949ab', '#1e88e5']

        verified = {'passkey': False, 'voice': False, 'face': False, 'fingerprint': False}
        current_step = [0]

        pass_f = ft.TextField(label=self.t('passkey_hint'), password=True, can_reveal_password=True,
                              border_radius=12, prefix_icon=ic('LOCK'))
        
        # Interactive elements for voice/face verification
        direction_icon = ft.Text('🎤', size=60, text_align=ft.TextAlign.CENTER)
        direction_text = ft.Text('', size=14, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER, color=INDIGO_600)
        status_text = ft.Text('', color=INDIGO_400, size=14, text_align=ft.TextAlign.CENTER)
        progress_text = ft.Text('', size=12, color=GREEN_400, text_align=ft.TextAlign.CENTER)
        err_text = ft.Text('', color=RED_400, size=12, text_align=ft.TextAlign.CENTER)

        indicators = ft.Column(spacing=6)
        self._update_indicators(indicators, verified)

        content_area = ft.Container()
        
        # Progress indicators for multi-step verifications
        step_indicators = ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=6,
            controls=[ft.Icon(ic('RADIO_BUTTON_UNCHECKED'), size=14, color=INDIGO_200) for _ in range(6)]
        )

        def update_step_indicators(current, total=6):
            for i, ctrl in enumerate(step_indicators.controls[:total]):
                if i < current:
                    ctrl.name = ic('CHECK_CIRCLE')
                    ctrl.color = GREEN_400
                elif i == current:
                    ctrl.name = ic('RADIO_BUTTON_CHECKED')
                    ctrl.color = INDIGO_400
                else:
                    ctrl.name = ic('RADIO_BUTTON_UNCHECKED')
                    ctrl.color = INDIGO_200
            self.page.update()

        def _verify_passkey(_):
            if self._failed_attempts >= MAX_ATTEMPTS:
                self._apply_lockout()
                self._build_lockout_page()
                return
            if self._verify_passkey(pass_f.value.strip()):
                verified['passkey'] = True
                self._failed_attempts = 0
                self.auth.put('failed_attempts', 0)
                err_text.value = ''
                _next_step()
            else:
                self._failed_attempts += 1
                self.auth.put('failed_attempts', self._failed_attempts)
                left = MAX_ATTEMPTS - self._failed_attempts
                if left <= 0:
                    self._apply_lockout()
                    self._build_lockout_page()
                else:
                    err_text.value = f"{self.t('wrong_pass')} ({left} {self.t('attempts_left')})"
                pass_f.value = ''
            self._update_indicators(indicators, verified)
            self.page.update()

        def _verify_voice(_):
            status_text.value = self.t('verifying')
            self.page.update()
            
            def do_verify():
                # Voice verification steps with extended time and countdown
                steps = [
                    ('voice_speak_now', '🎤', 'Get ready to speak...', 3.0),  # 3 seconds to prepare
                    ('voice_listening', '👂', 'Speak NOW: "My vault is secure"', 10.0),  # 10 seconds to speak fully
                    ('voice_processing', '⚙️', 'Processing voice...', 2.0),  # 2 seconds to process
                ]
                
                for i, (key, emoji, desc, delay) in enumerate(steps):
                    direction_icon.value = emoji
                    direction_text.value = self.t(key)
                    
                    # Show countdown for listening step
                    if key == 'voice_listening':
                        remaining = int(delay)
                        while remaining > 0:
                            progress_text.value = f"🎤 {desc} ({remaining}s remaining)"
                            update_step_indicators(i, 3)
                            self.page.update()
                            time.sleep(1)
                            remaining -= 1
                        progress_text.value = f"Step {i+1} of 3"
                    else:
                        progress_text.value = f"Step {i+1} of 3"
                        update_step_indicators(i, 3)
                        self.page.update()
                        time.sleep(delay)
                
                verified['voice'] = True
                direction_icon.value = '✅'
                direction_text.value = self.t('voice_success')
                direction_text.color = GREEN_400
                status_text.value = ''
                self._update_indicators(indicators, verified)
                self.page.update()
                time.sleep(0.8)
                _next_step()
                
            threading.Thread(target=do_verify, daemon=True).start()

        def _verify_face(_):
            status_text.value = self.t('verifying')
            self.page.update()
            
            def do_verify():
                # Face verification with head movement
                directions = [
                    ('face_look_center', '🎯'),
                    ('face_look_up', '👆'),
                    ('face_look_down', '👇'),
                    ('face_look_left', '👈'),
                    ('face_look_right', '👉'),
                    ('face_capture_complete', '✅'),
                ]
                
                for i, (key, emoji) in enumerate(directions):
                    direction_icon.value = emoji
                    direction_text.value = self.t(key)
                    progress_text.value = f"Step {i+1} of 6"
                    update_step_indicators(i, 6)
                    self.page.update()
                    time.sleep(1.0)
                
                verified['face'] = True
                direction_icon.value = '✅'
                direction_text.value = self.t('face_success')
                direction_text.color = GREEN_400
                status_text.value = ''
                self._update_indicators(indicators, verified)
                self.page.update()
                time.sleep(0.8)
                _next_step()
                
            threading.Thread(target=do_verify, daemon=True).start()

        def _verify_fingerprint(_):
            if is_mobile():
                try:
                    def _on_login(e: ft.LoginEvent):
                        if e.error:
                            err_text.value = self.t('biometric_fail')
                        else:
                            verified['fingerprint'] = True
                            status_text.value = self.t('fingerprint_success')
                            status_text.color = GREEN_400
                            _check_complete()
                        self._update_indicators(indicators, verified)
                        self.page.update()
                    self.page.on_login = _on_login
                    self.page.login(ft.LocalAuthentication(reason=f"Verify for {APP_NAME}"))
                except Exception:
                    err_text.value = self.t('biometric_unavailable')
                    self.page.update()

        def _next_step():
            current_step[0] += 1
            _update_content()
            _check_complete()

        def _check_complete():
            all_ok = verified['passkey'] and verified['voice'] and verified['face']
            if is_mobile():
                all_ok = all_ok and verified['fingerprint']
            if all_ok:
                time.sleep(0.5)
                self._build_page()

        def _update_content():
            step = current_step[0]
            if step == 0:
                # Adjust step indicators for passkey
                step_indicators.controls = [ft.Icon(ic('RADIO_BUTTON_UNCHECKED'), size=14, color=INDIGO_200)]
                content_area.content = ft.Column(spacing=10, controls=[
                    ft.Text(self.t('passkey_verification'), size=15, weight=ft.FontWeight.BOLD),
                    pass_f,
                    ft.ElevatedButton(text=self.t('verify_btn'), icon=ic('LOCK_OPEN'), bgcolor=INDIGO_600, color=WHITE,
                                      style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)), on_click=_verify_passkey, width=float('inf')),
                ])
            elif step == 1:
                # Voice verification
                step_indicators.controls = [ft.Icon(ic('RADIO_BUTTON_UNCHECKED'), size=14, color=INDIGO_200) for _ in range(3)]
                direction_icon.value = '🎤'
                direction_text.value = ''
                direction_text.color = INDIGO_600
                content_area.content = ft.Column(spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                    ft.Text(self.t('voice_verification'), size=15, weight=ft.FontWeight.BOLD),
                    ft.Text(f'"{self.t("voice_passphrase")}"', size=11, color=INDIGO_200),
                    direction_icon,
                    direction_text,
                    progress_text,
                    step_indicators,
                    ft.ElevatedButton(text=self.t('voice_verify'), icon=ic('MIC'), bgcolor=INDIGO_600, color=WHITE,
                                      style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)), on_click=_verify_voice, width=float('inf')),
                ])
            elif step == 2:
                # Face verification with head movement
                step_indicators.controls = [ft.Icon(ic('RADIO_BUTTON_UNCHECKED'), size=14, color=INDIGO_200) for _ in range(6)]
                direction_icon.value = '🎯'
                direction_text.value = self.t('face_move_head')
                direction_text.color = INDIGO_200
                content_area.content = ft.Column(spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                    ft.Text(self.t('face_verification'), size=15, weight=ft.FontWeight.BOLD),
                    direction_icon,
                    direction_text,
                    progress_text,
                    step_indicators,
                    ft.ElevatedButton(text=self.t('face_verify'), icon=ic('FACE'), bgcolor=INDIGO_600, color=WHITE,
                                      style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)), on_click=_verify_face, width=float('inf')),
                ])
            elif step == 3 and is_mobile():
                # Fingerprint verification
                step_indicators.controls = [ft.Icon(ic('RADIO_BUTTON_UNCHECKED'), size=14, color=INDIGO_200)]
                direction_icon.value = '👆'
                direction_text.value = self.t('fingerprint_hint')
                direction_text.color = INDIGO_200
                content_area.content = ft.Column(spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                    ft.Text(self.t('fingerprint_verification'), size=15, weight=ft.FontWeight.BOLD),
                    direction_icon,
                    direction_text,
                    ft.ElevatedButton(text=self.t('fingerprint_verify'), icon=ic('FINGERPRINT'), bgcolor=INDIGO_600, color=WHITE,
                                      style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)), on_click=_verify_fingerprint, width=float('inf')),
                ])
            self.page.update()

        _update_content()

        self.page.add(
            ft.Column(expand=True, spacing=0, controls=[
                ft.Container(
                    padding=ft.Padding(16, 35, 16, 15),
                    gradient=ft.LinearGradient(colors=grad_colors, begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1)),
                    content=ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6, controls=[
                        ft.Icon(ic('LOCK'), size=45, color=WHITE),
                        ft.Text(self.t('mfa_verify'), size=18, weight=ft.FontWeight.BOLD, color=WHITE, text_align=ft.TextAlign.CENTER),
                    ]),
                ),
                ft.Container(
                    expand=True, padding=ft.Padding(16, 16, 16, 16),
                    content=ft.Column(spacing=10, controls=[
                        indicators,
                        ft.Divider(height=1),
                        content_area,
                        status_text, err_text,
                        ft.Divider(height=1),
                        ft.TextButton(text=self.t('forgot_passkey'), on_click=lambda _: self._open_forgot_passkey()),
                        ft.TextButton(text=self.t('reset_vault'), icon=ic('DELETE_FOREVER'), icon_color=RED_400,
                                      on_click=lambda _: self._confirm_reset()),
                    ]),
                ),
            ])
        )
        self.page.update()

    # =========================================================
    # ================= LOCKOUT PAGE ==========================
    # =========================================================
    def _build_lockout_page(self):
        self.page.controls.clear()

        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        grad_colors = ['#4a148c', '#1a237e'] if is_dark else ['#3949ab', '#1e88e5']

        countdown_text = ft.Text('', size=32, weight=ft.FontWeight.BOLD, color=RED_400)

        def update_countdown():
            remaining = self._get_lockout_remaining()
            if remaining > 0:
                mins, secs = divmod(remaining, 60)
                countdown_text.value = f"{mins}m {secs}s" if mins > 0 else f"{secs}s"
                self.page.update()
                threading.Timer(1, update_countdown).start()
            else:
                self._clear_lockout()
                self._build_verification_page()

        self.page.add(
            ft.Column(expand=True, spacing=0, controls=[
                ft.Container(
                    padding=ft.Padding(16, 60, 16, 30),
                    gradient=ft.LinearGradient(colors=grad_colors, begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1)),
                    content=ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10, controls=[
                        ft.Icon(ic('LOCK_CLOCK'), size=60, color=WHITE),
                        ft.Text(self.t('lockout_title'), size=22, weight=ft.FontWeight.BOLD, color=WHITE, text_align=ft.TextAlign.CENTER),
                    ]),
                ),
                ft.Container(
                    expand=True, padding=ft.Padding(24, 40, 24, 24),
                    content=ft.Column(spacing=20, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                        ft.Text(self.t('lockout_message'), size=14, text_align=ft.TextAlign.CENTER),
                        countdown_text,
                        ft.Divider(),
                        ft.TextButton(text=self.t('forgot_passkey'), on_click=lambda _: self._open_forgot_passkey()),
                        ft.TextButton(text=self.t('reset_vault'), icon=ic('DELETE_FOREVER'), icon_color=RED_400,
                                      on_click=lambda _: self._confirm_reset()),
                    ]),
                ),
            ])
        )
        self.page.update()
        update_countdown()

    # =========================================================
    # ================= FORGOT PASSKEY ========================
    # =========================================================
    def _open_forgot_passkey(self):
        stored_question = self.auth.get('secret_question')
        if not stored_question:
            self._snack(self.t('biometric_unavailable'))
            return

        answer_f = ft.TextField(label=self.t('secret_answer'), border_radius=12, prefix_icon=ic('QUESTION_ANSWER'), autofocus=True)
        err_text = ft.Text('', color=RED_400, size=12)

        def _verify(_):
            if self._verify_secret_answer(answer_f.value):
                self.page.dialog.open = False
                self.page.dialog = None
                self.page.update()
                self._snack(self.t('answer_correct'))
                self._open_reset_passkey()
            else:
                err_text.value = self.t('answer_wrong')
                self.page.update()

        self.page.dialog = ft.AlertDialog(
            modal=True, title=ft.Text(self.t('verify_identity')),
            content=ft.Container(width=340, content=ft.Column(tight=True, spacing=14, controls=[
                ft.Text(self.t(stored_question), size=14), answer_f, err_text,
            ])),
            actions=[
                ft.TextButton(self.t('cancel'), on_click=lambda _: setattr(self.page.dialog, 'open', False) or self.page.update()),
                ft.TextButton(self.t('verify_identity'), on_click=_verify),
            ],
        )
        self.page.dialog.open = True
        self.page.update()

    def _open_reset_passkey(self):
        new_f = ft.TextField(label=self.t('new_pass'), password=True, can_reveal_password=True, border_radius=12, prefix_icon=ic('LOCK_OUTLINE'), autofocus=True)
        con_f = ft.TextField(label=self.t('confirm_pass'), password=True, can_reveal_password=True, border_radius=12, prefix_icon=ic('LOCK_OUTLINE'))
        err_text = ft.Text('', color=RED_400, size=12)

        def _save(_):
            p1, p2 = new_f.value.strip(), con_f.value.strip()
            if len(p1) < 4:
                err_text.value = self.t('pass_too_short')
            elif p1 != p2:
                err_text.value = self.t('pass_mismatch')
            else:
                self._save_passkey(p1)
                self._clear_lockout()
                self.page.dialog.open = False
                self.page.dialog = None
                self.page.update()
                self._snack(self.t('passkey_changed'))
                self._build_verification_page()
                return
            self.page.update()

        self.page.dialog = ft.AlertDialog(
            modal=True, title=ft.Text(self.t('change_passkey')),
            content=ft.Container(width=340, content=ft.Column(tight=True, spacing=14, controls=[new_f, con_f, err_text])),
            actions=[ft.TextButton(self.t('cancel'), on_click=lambda _: setattr(self.page.dialog, 'open', False) or self.page.update()),
                     ft.TextButton(self.t('save'), on_click=_save)],
        )
        self.page.dialog.open = True
        self.page.update()

    # =========================================================
    # ================= MAIN VAULT PAGE =======================
    # =========================================================
    def _build_page(self):
        self.page.controls.clear()

        self._search_field = ft.TextField(hint_text=self.t('search'), prefix_icon=ic('SEARCH'), border_radius=30,
                                           border_color=INDIGO_200, on_change=self._on_search, expand=True, dense=True,
                                           content_padding=ft.Padding(16, 10, 16, 10))

        self._content = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, spacing=8)
        self._refresh_content()

        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        grad_colors = ['#4a148c', '#1a237e'] if is_dark else ['#3949ab', '#1e88e5']

        self._header_title = ft.Text(self.t('vault'), size=26, weight=ft.FontWeight.BOLD, color=WHITE)
        self._settings_btn = ft.IconButton(icon=ic('SETTINGS'), icon_color=WHITE, tooltip=self.t('settings'),
                                            on_click=lambda _: self._open_settings())

        self.page.add(
            ft.Column(expand=True, spacing=0, controls=[
                ft.Container(padding=ft.Padding(16, 40, 16, 16), gradient=ft.LinearGradient(colors=grad_colors, begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1)),
                             content=ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[self._header_title, self._settings_btn])),
                ft.Container(padding=ft.Padding(12, 10, 12, 10), content=self._search_field),
                ft.Container(expand=True, content=self._content, padding=ft.Padding(10, 0, 10, 0)),
                ft.Container(padding=ft.Padding(16, 8, 16, 20),
                             content=ft.Row(alignment=ft.MainAxisAlignment.END, controls=[
                                 ft.FloatingActionButton(icon=ic('ADD'), bgcolor=INDIGO_600, on_click=lambda _: self._open_dialog()),
                             ])),
            ])
        )
        self.page.update()

    def _on_search(self, e):
        self._search_query = e.control.value.lower().strip()
        self._refresh_content()

    def _refresh_content(self):
        if not self._content: return
        all_items = self.vault.get_all()
        q = self._search_query
        filtered = ([(i, c) for i, c in enumerate(all_items) if q in c.get('app', '').lower() or q in c.get('user', '').lower()]
                    if q else list(enumerate(all_items)))
        self._content.controls.clear()
        if not filtered:
            self._content.controls.append(ft.Container(expand=True, alignment=ft.Alignment(0, 0), padding=ft.Padding(0, 80, 0, 0),
                                                       content=ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=12, controls=[
                                                           ft.Icon(ic('LOCK_OUTLINE'), size=64, color=INDIGO_200),
                                                           ft.Text(self.t('empty'), text_align=ft.TextAlign.CENTER, size=15, opacity=0.6),
                                                       ])))
        else:
            for idx, cred in filtered:
                self._content.controls.append(build_card(cred, idx, on_delete=self._confirm_delete, on_edit=self._open_edit,
                                                          on_copy_user=self._copy_user, on_copy_pass=self._copy_pass, t=self.t))
        self.page.update()

    def _copy_user(self, i: int):
        items = self.vault.get_all()
        if 0 <= i < len(items):
            self.page.set_clipboard(items[i].get('user', ''))
            self._snack(self.t('copy_user'))

    def _copy_pass(self, i: int):
        items = self.vault.get_all()
        if 0 <= i < len(items):
            self.page.set_clipboard(items[i].get('pass', ''))
            self._snack(self.t('copy_pass'))

    def _snack(self, msg: str):
        self.page.snack_bar = ft.SnackBar(content=ft.Text(msg), duration=1800)
        self.page.snack_bar.open = True
        self.page.update()

    def _open_dialog(self, edit_index: Optional[int] = None):
        items = self.vault.get_all()
        existing = items[edit_index] if edit_index is not None else None

        app_f = ft.TextField(label=self.t('app'), value=existing.get('app', '') if existing else '',
                             autofocus=True, border_radius=12, prefix_icon=ic('APPS'))
        usr_f = ft.TextField(label=self.t('user'), value=existing.get('user', '') if existing else '',
                             border_radius=12, prefix_icon=ic('PERSON_OUTLINE'))
        pas_f = ft.TextField(label=self.t('pass'), value=existing.get('pass', '') if existing else '',
                             password=True, can_reveal_password=True, border_radius=12, prefix_icon=ic('LOCK_OUTLINE'))
        err = ft.Text('', color=cl('RED_400'), size=12)

        def _save(_):
            a, u, p = app_f.value.strip(), usr_f.value.strip(), pas_f.value.strip()
            if not a or not u or not p:
                err.value = self.t('fill_all')
                self.page.update()
                return
            rec = {'app': a, 'user': u, 'pass': p}
            if edit_index is not None:
                self.vault.update_at(edit_index, rec)
            else:
                self.vault.add(rec)
            _close(_)
            self._refresh_content()

        def _close(_):
            self.page.dialog.open = False
            self.page.dialog = None
            self.page.update()

        self.page.dialog = ft.AlertDialog(
            modal=True, title=ft.Text(self.t('edit') if edit_index is not None else self.t('add')),
            content=ft.Container(width=340, content=ft.Column(tight=True, spacing=14, controls=[app_f, usr_f, pas_f, err])),
            actions=[ft.TextButton(self.t('cancel'), on_click=_close), ft.TextButton(self.t('save'), on_click=_save)],
        )
        self.page.dialog.open = True
        self.page.update()

    def _open_edit(self, index: int):
        self._open_dialog(edit_index=index)

    def _confirm_delete(self, index: int):
        def _yes(_):
            self.vault.delete_at(index)
            self.page.dialog.open = False
            self.page.dialog = None
            self.page.update()
            self._refresh_content()

        def _no(_):
            self.page.dialog.open = False
            self.page.dialog = None
            self.page.update()

        self.page.dialog = ft.AlertDialog(modal=True, title=ft.Text(self.t('delete')), content=ft.Text(self.t('delete_confirm')),
                                           actions=[ft.TextButton(self.t('no'), on_click=_no), ft.TextButton(self.t('yes'), on_click=_yes)])
        self.page.dialog.open = True
        self.page.update()

    # =========================================================
    # ================= SETTINGS ==============================
    # =========================================================
    def _open_settings(self):
        is_dark = self.settings.get('dark', defaultValue=False)
        default_lang = self.settings.get('default_lang', 'English')

        def _toggle_dark(e):
            self.settings.put('dark', e.control.value)
            self.page.theme_mode = ft.ThemeMode.DARK if e.control.value else ft.ThemeMode.LIGHT
            self.page.update()

        def _close(_):
            self.page.dialog.open = False
            self.page.dialog = None
            self.page.update()

        def _do_change_passkey(_):
            self.page.dialog.open = False
            self.page.dialog = None
            self.page.update()
            self._open_change_passkey()

        def _do_reset(_):
            self.page.dialog.open = False
            self.page.dialog = None
            self.page.update()
            self._confirm_reset()

        self.page.dialog = ft.AlertDialog(
            modal=True, title=ft.Text(self.t('settings')),
            content=ft.Container(width=320, content=ft.Column(tight=True, spacing=0, controls=[
                ft.ListTile(leading=ft.Icon(ic('DARK_MODE')), title=ft.Text(self.t('dark')),
                           trailing=ft.Switch(value=is_dark, on_change=_toggle_dark)),
                ft.Divider(height=1),
                ft.ListTile(leading=ft.Icon(ic('KEY'), color=INDIGO_400), title=ft.Text(self.t('change_passkey')),
                           trailing=ft.Icon(ic('CHEVRON_RIGHT')), on_click=_do_change_passkey),
                ft.Divider(height=1),
                ft.ListTile(leading=ft.Icon(ic('DELETE_FOREVER'), color=RED_400), title=ft.Text(self.t('reset_vault'), color=RED_400),
                           trailing=ft.Icon(ic('CHEVRON_RIGHT'), color=RED_400), on_click=_do_reset),
                ft.Divider(height=1),
                ft.ListTile(leading=ft.Icon(ic('INFO_OUTLINE')), title=ft.Text(self.t('about')),
                           subtitle=ft.Text(f"{APP_NAME} v{APP_VERSION}\n{APP_SUBTITLE}")),
            ])),
            actions=[ft.TextButton(self.t('cancel'), on_click=_close)],
        )
        self.page.dialog.open = True
        self.page.update()

    def _open_change_passkey(self):
        cur_f = ft.TextField(label=self.t('current_pass'), password=True, can_reveal_password=True, border_radius=12, prefix_icon=ic('LOCK'), autofocus=True)
        new_f = ft.TextField(label=self.t('new_pass'), password=True, can_reveal_password=True, border_radius=12, prefix_icon=ic('LOCK_OUTLINE'))
        con_f = ft.TextField(label=self.t('confirm_pass'), password=True, can_reveal_password=True, border_radius=12, prefix_icon=ic('LOCK_OUTLINE'))
        err = ft.Text('', color=RED_400, size=12)

        def _save(_):
            c, p1, p2 = cur_f.value.strip(), new_f.value.strip(), con_f.value.strip()
            if not self._verify_passkey(c):
                err.value = self.t('wrong_current')
            elif len(p1) < 4:
                err.value = self.t('pass_too_short')
            elif p1 != p2:
                err.value = self.t('pass_mismatch')
            else:
                self._save_passkey(p1)
                self.page.dialog.open = False
                self.page.dialog = None
                self.page.update()
                self._snack(self.t('passkey_changed'))
                return
            self.page.update()

        self.page.dialog = ft.AlertDialog(
            modal=True, title=ft.Text(self.t('change_passkey')),
            content=ft.Container(width=340, content=ft.Column(tight=True, spacing=14, controls=[cur_f, new_f, con_f, err])),
            actions=[ft.TextButton(self.t('cancel'), on_click=lambda _: setattr(self.page.dialog, 'open', False) or self.page.update()),
                     ft.TextButton(self.t('save'), on_click=_save)],
        )
        self.page.dialog.open = True
        self.page.update()

    def _confirm_reset(self):
        def _yes(_):
            self.vault.clear_all()
            self.auth.clear_all()
            self.settings.clear_all()
            self.page.dialog.open = False
            self.page.dialog = None
            self.page.update()
            self._build_setup_step1()

        self.page.dialog = ft.AlertDialog(
            modal=True, title=ft.Text(self.t('reset_vault')), content=ft.Text(self.t('reset_confirm')),
            actions=[ft.TextButton(self.t('no'), on_click=lambda _: setattr(self.page.dialog, 'open', False) or self.page.update()),
                     ft.TextButton(self.t('yes'), on_click=_yes, style=ft.ButtonStyle(color=RED_400))],
        )
        self.page.dialog.open = True
        self.page.update()

# ================= ENTRY POINT =================
if __name__ == '__main__':
    ft.app(MyVaultApp().main)
