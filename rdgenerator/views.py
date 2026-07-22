import io
import hashlib
import hmac
import mimetypes
from datetime import timedelta
from pathlib import Path
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.core import signing
from django.core.signing import BadSignature, SignatureExpired
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.core.files.base import ContentFile
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from django.utils import timezone
import os
import secrets
import re
import requests
import base64
import json
import uuid
import pyzipper
from urllib.parse import urlencode
from django.conf import settings as _settings
from .forms import GenerateForm
from .models import (
    create_github_run_with_reservation,
    GenerationQuotaExceeded,
    GithubRun,
    mark_artifact_uploaded,
    release_generation_reservation,
)
from PIL import Image


ZIP_DOWNLOAD_MAX_AGE = 6 * 60 * 60
ZIP_DOWNLOAD_SALT = "rdgenerator.get_zip"
STATUS_UPDATE_MAX_AGE = 24 * 60 * 60
STATUS_UPDATE_SALT = "rdgenerator.update_status"
CALLBACK_TOKEN_MAX_AGE = timedelta(hours=24)
TERMINAL_RUN_STATUSES = {
    "success",
    "failure",
    "cancelled",
    "timed_out",
    "skipped",
    "action_required",
}
FAILED_TERMINAL_RUN_STATUSES = TERMINAL_RUN_STATUSES - {"success"}
VALID_ARTIFACT_SUFFIXES = (
    ".exe",
    ".msi",
    ".apk",
    ".deb",
    ".rpm",
    ".appimage",
    ".flatpak",
    ".dmg",
    ".pkg.tar.zst",
)


def _canonical_run_uuid(value):
    try:
        canonical = str(uuid.UUID(value))
    except (AttributeError, TypeError, ValueError):
        raise Http404("Build not found")
    if value != canonical:
        raise Http404("Build not found")
    return canonical


def _user_run_or_404(request, run_uuid):
    run_uuid = _canonical_run_uuid(run_uuid)
    return get_object_or_404(GithubRun, uuid=run_uuid, owner=request.user)


def _safe_output_filename(value):
    if (
        not value
        or len(value) > 255
        or value in {".", ".."}
        or os.path.basename(value) != value
        or any(char in value for char in ('/', '\\', '"', ';', '\r', '\n'))
        or any(ord(char) < 32 or ord(char) == 127 for char in value)
    ):
        raise Http404("Generated file not found")
    return value


def _callback_token_hash(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def download_token_for_run(run_uuid):
    """Return a deterministic per-run share token without storing plaintext."""
    return hmac.new(
        str(_settings.SECRET_KEY).encode("utf-8"),
        str(run_uuid).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _valid_artifact_filename(filename, platform=None):
    platform_suffixes = {
        "windows": (".exe", ".msi"),
        "windows-x86": (".exe",),
        "android": (".apk",),
        "macos": (".dmg",),
        "linux": (".deb", ".rpm", ".appimage", ".flatpak", ".pkg.tar.zst"),
    }
    allowed_suffixes = platform_suffixes.get(platform, VALID_ARTIFACT_SUFFIXES)
    return bool(
        filename
        and filename.lower().endswith(allowed_suffixes)
    )


def _request_token(request):
    authorization = request.headers.get("Authorization", "")
    scheme, separator, token = authorization.partition(" ")
    if separator and scheme.lower() == "bearer":
        return token.strip()
    return ""


def _machine_run(request, raw_uuid):
    try:
        run_uuid = _canonical_run_uuid(raw_uuid)
    except Http404:
        return None, HttpResponse("Build not found", status=404)

    token = _request_token(request)
    if not token:
        return None, HttpResponse("Unauthorized", status=401)

    try:
        run = GithubRun.objects.get(uuid=run_uuid)
    except GithubRun.DoesNotExist:
        return None, HttpResponse("Build not found", status=404)
    if timezone.now() - run.created_at > CALLBACK_TOKEN_MAX_AGE:
        return None, HttpResponse("Unauthorized", status=401)

    supplied_hash = _callback_token_hash(token)
    if not run.callback_token_hash or not secrets.compare_digest(
        supplied_hash,
        run.callback_token_hash,
    ):
        return None, HttpResponse("Unauthorized", status=401)
    return run, None


def _status_run(request, raw_uuid):
    if _request_token(request):
        return _machine_run(request, raw_uuid)
    try:
        run_uuid = _canonical_run_uuid(raw_uuid)
    except Http404:
        return None, HttpResponse("Build not found", status=404)
    try:
        signed = signing.loads(
            request.GET.get("signature", ""),
            salt=STATUS_UPDATE_SALT,
            max_age=STATUS_UPDATE_MAX_AGE,
        )
    except (BadSignature, SignatureExpired):
        return None, HttpResponse("Unauthorized", status=401)
    if not isinstance(signed, dict) or signed.get("uuid") != run_uuid:
        return None, HttpResponse("Unauthorized", status=401)
    try:
        return GithubRun.objects.get(uuid=run_uuid), None
    except GithubRun.DoesNotExist:
        return None, HttpResponse("Build not found", status=404)


def _shared_api_authorized(request):
    token = _request_token(request)
    expected = _settings.API_SHARED_SECRET
    return bool(token and expected and secrets.compare_digest(token, expected))


def _generated_file_or_404(run_uuid, filename):
    output_dir = (Path("exe") / run_uuid).resolve()
    file_path = (output_dir / filename).resolve()
    try:
        file_path.relative_to(output_dir)
    except ValueError:
        raise Http404("Generated file not found")
    if not file_path.is_file():
        raise Http404("Generated file not found")
    return file_path

def list_generated_files(run_uuid):
    output_dir = os.path.join('exe', run_uuid)
    if not os.path.isdir(output_dir):
        return []
    files = [
        name
        for name in os.listdir(output_dir)
        if os.path.isfile(os.path.join(output_dir, name))
    ]
    android_order = ['-universal.apk', '-aarch64.apk', '-armv7.apk', '-x86_64.apk']
    return sorted(files, key=lambda name: (
        next((idx for idx, suffix in enumerate(android_order) if name.endswith(suffix)), len(android_order)),
        name.lower(),
    ))


def _download_links(run, files):
    """Build task-scoped links without exposing a token for login-only files."""
    expires_at = run.download_expires_at
    token = download_token_for_run(run.uuid) if run.download_token_hash else ""
    links = []
    for filename in files:
        params = {"filename": filename, "uuid": run.uuid}
        if run.download_access == "public" and token:
            params["token"] = token
        links.append(
            {
                "filename": filename,
                "url": f"/download?{urlencode(params)}",
                "requires_login": run.download_access != "public",
                "expires_at": expires_at,
            }
        )
    return links


def _delivery_context(run, files):
    return {
        "files": files,
        "download_links": _download_links(run, files),
        "download_access": run.download_access,
        "download_ttl_hours": run.download_ttl_hours,
        "download_expires_at": run.download_expires_at,
    }

@login_required
def generator_view(request):
    if request.method == 'POST':
        form = GenerateForm(request.POST, request.FILES)
        if form.is_valid():
            user_secret = form.cleaned_data['sh_secret_field']
            if _settings.SH_SECRET and _settings.SH_SECRET == user_secret:
                selfhosted = True
            else:
                selfhosted = False
            platform = form.cleaned_data['platform']
            desktop_platforms = {'windows', 'windows-x86', 'linux', 'macos'}
            flutter_desktop_platforms = {'windows', 'linux', 'macos'}
            windows_platforms = {'windows', 'windows-x86'}
            version = form.cleaned_data['version']
            beijingCustom = form.cleaned_data['beijingCustom'] and platform == 'linux'
            linuxCustomAllowed = platform != 'linux' or beijingCustom
            default_server = 'rs-ny.rustdesk.com'
            default_key = 'OeVuKk5nlHiXp+APNn0Y3pC1Iwpwn44JGqrQCsWqmBw='
            default_url_link = "https://rustdesk.com"
            default_download_link = "https://rustdesk.com/download"
            default_appname = "rustdesk"
            default_compname = "Purslane Tech Pte. Ltd."
            delayFix = form.cleaned_data['delayFix'] and linuxCustomAllowed
            cycleMonitor = form.cleaned_data['cycleMonitor'] and platform in flutter_desktop_platforms and linuxCustomAllowed
            xOffline = form.cleaned_data['xOffline'] and platform in (flutter_desktop_platforms | {'android'}) and linuxCustomAllowed
            hidecm = form.cleaned_data['hidecm'] and platform in desktop_platforms and linuxCustomAllowed
            hidecmDefaultEnabled = (
                form.cleaned_data['hidecmDefaultEnabled'] and hidecm
            )
            removeNewVersionNotif = form.cleaned_data['removeNewVersionNotif'] and linuxCustomAllowed
            hideSettingsMenu = form.cleaned_data['hideSettingsMenu'] and platform in desktop_platforms and linuxCustomAllowed
            removeRecentSessions = form.cleaned_data['removeRecentSessions'] and platform in desktop_platforms and linuxCustomAllowed
            server = form.cleaned_data['serverIP']
            key = form.cleaned_data['key']
            apiServer = form.cleaned_data['apiServer']
            urlLink = form.cleaned_data['urlLink']
            downloadLink = form.cleaned_data['downloadLink']
            if not server:
                server = default_server
            if not key:
                key = default_key
            if not apiServer:
                api_host = server.removeprefix("https://").removeprefix("http://").rstrip("/")
                apiServer = f"http://{api_host}:21114"
            if not urlLink:
                urlLink = default_url_link
            if not downloadLink:
                downloadLink = default_download_link
            direction = form.cleaned_data['direction']
            installation = form.cleaned_data['installation']
            settings = form.cleaned_data['settings']
            hideNetworkSetting = form.cleaned_data['hideNetworkSetting'] and platform in desktop_platforms and linuxCustomAllowed
            defaultViewStyle = form.cleaned_data['defaultViewStyle'] if linuxCustomAllowed else 'adaptive'
            removeSetupServerTip = form.cleaned_data['removeSetupServerTip'] and platform in desktop_platforms and linuxCustomAllowed
            silentInstallOnDoubleClick = form.cleaned_data['silentInstallOnDoubleClick'] and platform in windows_platforms
            copyIdPasswordButton = form.cleaned_data['copyIdPasswordButton'] and platform in flutter_desktop_platforms and linuxCustomAllowed
            manualTemporaryPassword = form.cleaned_data['manualTemporaryPassword'] and platform in flutter_desktop_platforms and linuxCustomAllowed
            showStartOnBootCheckbox = form.cleaned_data['showStartOnBootCheckbox'] and platform == 'windows'
            incomingCompactMode = (
                form.cleaned_data['incomingCompactMode']
                and direction == 'incoming'
                and platform in flutter_desktop_platforms
                and linuxCustomAllowed
            )
            incomingContentWidth = form.cleaned_data.get('incomingContentWidth') or 220
            incomingContentHeight = form.cleaned_data.get('incomingContentHeight') or 300
            appname = form.cleaned_data['appname']
            if not appname:
                appname = default_appname
            filename = form.cleaned_data['exename']
            compname = form.cleaned_data['compname']
            if not compname:
                compname = default_compname
            androidappid = form.cleaned_data['androidappid']
            if not androidappid:
                androidappid = "com.carriez.flutter_hbb"
            compname = compname.replace("&", "\\&")
            permPass = form.cleaned_data['permanentPassword']
            theme = form.cleaned_data['theme']
            themeDorO = form.cleaned_data['themeDorO']
            #runasadmin = form.cleaned_data['runasadmin']
            passApproveMode = form.cleaned_data['passApproveMode']
            denyLan = form.cleaned_data['denyLan']
            enableDirectIP = form.cleaned_data['enableDirectIP']
            #ipWhitelist = form.cleaned_data['ipWhitelist']
            autoClose = form.cleaned_data['autoClose']
            permissionsDorO = form.cleaned_data['permissionsDorO']
            permissionsType = form.cleaned_data['permissionsType']
            enableKeyboard = form.cleaned_data['enableKeyboard']
            enableClipboard = form.cleaned_data['enableClipboard']
            enableFileCopyPaste = form.cleaned_data['enableFileCopyPaste']
            enableFileTransfer = form.cleaned_data['enableFileTransfer']
            forceDisableFileTransfer = form.cleaned_data['forceDisableFileTransfer'] and linuxCustomAllowed
            enableAudio = form.cleaned_data['enableAudio']
            enableTCP = form.cleaned_data['enableTCP']
            enableRemoteRestart = form.cleaned_data['enableRemoteRestart']
            enableRecording = form.cleaned_data['enableRecording']
            enableBlockingInput = form.cleaned_data['enableBlockingInput']
            enableRemoteModi = form.cleaned_data['enableRemoteModi']
            removeWallpaper = form.cleaned_data['removeWallpaper']
            defaultManual = form.cleaned_data['defaultManual']
            overrideManual = form.cleaned_data['overrideManual']
            enablePrinter = form.cleaned_data['enablePrinter']
            enableCamera = form.cleaned_data['enableCamera']
            enableTerminal = form.cleaned_data['enableTerminal']

            if all(char.isascii() for char in filename):
                filename = re.sub(r'[^\w\s-]', '_', filename).strip()
                filename = filename.replace(" ","_")
            else:
                filename = "rustdesk"
            if not linuxCustomAllowed:
                server = default_server
                key = default_key
                apiServer = f"http://{default_server}:21114"
                urlLink = default_url_link
                downloadLink = default_download_link
                direction = "both"
                appname = default_appname
                filename = default_appname
                compname = default_compname
            myuuid = str(uuid.uuid4())
            protocol = _settings.PROTOCOL
            host = request.get_host()
            full_url = f"{protocol}://{host}"
            try:
                iconfile = form.cleaned_data.get('iconfile')
                if not iconfile:
                    iconfile = form.cleaned_data.get('iconbase64')
                iconlink_url, iconlink_uuid, iconlink_file = save_png(iconfile,myuuid,full_url,"icon.png")
            except:
                print("failed to get icon, using default")
                iconlink_url = "false"
                iconlink_uuid = "false"
                iconlink_file = "false"
            try:
                logofile = form.cleaned_data.get('logofile')
                if not logofile:
                    logofile = form.cleaned_data.get('logobase64')
                logolink_url, logolink_uuid, logolink_file = save_png(logofile,myuuid,full_url,"logo.png")
            except:
                print("failed to get logo")
                logolink_url = "false"
                logolink_uuid = "false"
                logolink_file = "false"
            try:
                privacyfile = form.cleaned_data.get('privacyfile')
                if not privacyfile:
                    privacyfile = form.cleaned_data.get('privacybase64')
                privacylink_url, privacylink_uuid, privacylink_file = save_png(privacyfile,myuuid,full_url,"privacy.png")
            except:
                print("failed to get logo")
                privacylink_url = "false"
                privacylink_uuid = "false"
                privacylink_file = "false"
            if not linuxCustomAllowed:
                iconlink_url = "false"
                iconlink_uuid = "false"
                iconlink_file = "false"
                logolink_url = "false"
                logolink_uuid = "false"
                logolink_file = "false"
                privacylink_url = "false"
                privacylink_uuid = "false"
                privacylink_file = "false"

            callback_token = secrets.token_urlsafe(32)

            ###create the custom.txt json here and send in as inputs below
            decodedCustom = {}
            if direction != "both":
                decodedCustom['conn-type'] = direction
            if installation == "installationN":
                decodedCustom['disable-installation'] = 'Y'
            if settings == "settingsN":
                decodedCustom['disable-settings'] = 'Y'
            if hideNetworkSetting:
                decodedCustom['hide-network-setting'] = 'Y'
            if appname.upper() != "RUSTDESK":
                decodedCustom['app-name'] = appname
            decodedCustom['custom-rendezvous-server'] = server
            decodedCustom['relay-server'] = server
            decodedCustom['api-server'] = apiServer
            decodedCustom['key'] = key
            decodedCustom['override-settings'] = {}
            decodedCustom['default-settings'] = {}
            if platform in desktop_platforms and linuxCustomAllowed:
                decodedCustom['default-settings']['view-style'] = defaultViewStyle
            if permPass != "":
                decodedCustom['password'] = permPass
            if theme != "system":
                if themeDorO == "default":
                    if platform == "windows-x86":
                        decodedCustom['default-settings']['allow-darktheme'] = 'Y' if theme == "dark" else 'N'
                    else:
                        decodedCustom['default-settings']['theme'] = theme
                elif themeDorO == "override":
                    if platform == "windows-x86":
                        decodedCustom['override-settings']['allow-darktheme'] = 'Y' if theme == "dark" else 'N'
                    else:
                        decodedCustom['override-settings']['theme'] = theme
            decodedCustom['enable-lan-discovery'] = 'N' if denyLan else 'Y'
            #decodedCustom['direct-server'] = 'Y' if enableDirectIP else 'N'
            decodedCustom['allow-auto-disconnect'] = 'Y' if autoClose else 'N'
            effectiveApproveMode = 'password' if hidecmDefaultEnabled else passApproveMode
            effectiveEnableFileTransfer = enableFileTransfer and not forceDisableFileTransfer
            if permissionsDorO == "default":
                decodedCustom['default-settings']['access-mode'] = permissionsType
                decodedCustom['default-settings']['enable-keyboard'] = 'Y' if enableKeyboard else 'N'
                decodedCustom['default-settings']['enable-clipboard'] = 'Y' if enableClipboard else 'N'
                decodedCustom['default-settings']['enable-file-copy-paste'] = 'Y' if enableFileCopyPaste else 'N'
                decodedCustom['default-settings']['enable-file-transfer'] = 'Y' if effectiveEnableFileTransfer else 'N'
                decodedCustom['default-settings']['enable-audio'] = 'Y' if enableAudio else 'N'
                decodedCustom['default-settings']['enable-tunnel'] = 'Y' if enableTCP else 'N'
                decodedCustom['default-settings']['enable-remote-restart'] = 'Y' if enableRemoteRestart else 'N'
                decodedCustom['default-settings']['enable-record-session'] = 'Y' if enableRecording else 'N'
                decodedCustom['default-settings']['enable-block-input'] = 'Y' if enableBlockingInput else 'N'
                decodedCustom['default-settings']['allow-remote-config-modification'] = 'Y' if enableRemoteModi else 'N'
                decodedCustom['default-settings']['direct-server'] = 'Y' if enableDirectIP else 'N'
                decodedCustom['default-settings']['verification-method'] = 'use-permanent-password' if hidecmDefaultEnabled else 'use-both-passwords'
                decodedCustom['default-settings']['approve-mode'] = effectiveApproveMode
                decodedCustom['default-settings']['allow-hide-cm'] = 'Y' if hidecmDefaultEnabled else 'N'
                decodedCustom['default-settings']['allow-remove-wallpaper'] = 'Y' if removeWallpaper else 'N'
                decodedCustom['default-settings']['enable-remote-printer'] = 'Y' if enablePrinter else 'N'
                decodedCustom['default-settings']['enable-camera'] = 'Y' if enableCamera else 'N'
                decodedCustom['default-settings']['enable-terminal'] = 'Y' if enableTerminal else 'N'
            else:
                decodedCustom['override-settings']['access-mode'] = permissionsType
                decodedCustom['override-settings']['enable-keyboard'] = 'Y' if enableKeyboard else 'N'
                decodedCustom['override-settings']['enable-clipboard'] = 'Y' if enableClipboard else 'N'
                decodedCustom['override-settings']['enable-file-copy-paste'] = 'Y' if enableFileCopyPaste else 'N'
                decodedCustom['override-settings']['enable-file-transfer'] = 'Y' if effectiveEnableFileTransfer else 'N'
                decodedCustom['override-settings']['enable-audio'] = 'Y' if enableAudio else 'N'
                decodedCustom['override-settings']['enable-tunnel'] = 'Y' if enableTCP else 'N'
                decodedCustom['override-settings']['enable-remote-restart'] = 'Y' if enableRemoteRestart else 'N'
                decodedCustom['override-settings']['enable-record-session'] = 'Y' if enableRecording else 'N'
                decodedCustom['override-settings']['enable-block-input'] = 'Y' if enableBlockingInput else 'N'
                decodedCustom['override-settings']['allow-remote-config-modification'] = 'Y' if enableRemoteModi else 'N'
                decodedCustom['override-settings']['direct-server'] = 'Y' if enableDirectIP else 'N'
                decodedCustom['override-settings']['verification-method'] = 'use-permanent-password' if hidecmDefaultEnabled else 'use-both-passwords'
                decodedCustom['override-settings']['approve-mode'] = effectiveApproveMode
                decodedCustom['override-settings']['allow-hide-cm'] = 'Y' if hidecmDefaultEnabled else 'N'
                decodedCustom['override-settings']['allow-remove-wallpaper'] = 'Y' if removeWallpaper else 'N'
                decodedCustom['override-settings']['enable-remote-printer'] = 'Y' if enablePrinter else 'N'
                decodedCustom['override-settings']['enable-camera'] = 'Y' if enableCamera else 'N'
                decodedCustom['override-settings']['enable-terminal'] = 'Y' if enableTerminal else 'N'

            if linuxCustomAllowed:
                for line in defaultManual.splitlines():
                    if not line.strip():
                        continue
                    k, _separator, value = line.partition('=')
                    decodedCustom['default-settings'][k.strip()] = value.strip()

                for line in overrideManual.splitlines():
                    if not line.strip():
                        continue
                    k, _separator, value = line.partition('=')
                    decodedCustom['override-settings'][k.strip()] = value.strip()

            hidecm_settings = (
                'approve-mode',
                'verification-method',
                'allow-hide-cm',
            )
            if hidecm:
                for key_name in hidecm_settings:
                    decodedCustom['override-settings'].pop(key_name, None)
                decodedCustom['default-settings'].update({
                    'approve-mode': 'password' if hidecmDefaultEnabled else passApproveMode,
                    'verification-method': (
                        'use-permanent-password'
                        if hidecmDefaultEnabled
                        else 'use-both-passwords'
                    ),
                    'allow-hide-cm': 'Y' if hidecmDefaultEnabled else 'N',
                })

            if not linuxCustomAllowed:
                decodedCustom = {}
            
            decodedCustomJson = json.dumps(decodedCustom)

            string_bytes = decodedCustomJson.encode("ascii")
            base64_bytes = base64.b64encode(string_bytes)
            encodedCustom = base64_bytes.decode("ascii")

            # #github limits inputs to 10, so lump extras into one with json
            # extras = {}
            # extras['genurl'] = _settings.GENURL
            # #extras['runasadmin'] = runasadmin
            # extras['urlLink'] = urlLink
            # extras['downloadLink'] = downloadLink
            # extras['delayFix'] = 'true' if delayFix else 'false'
            # extras['rdgen'] = 'true'
            # extras['cycleMonitor'] = 'true' if cycleMonitor else 'false'
            # extras['xOffline'] = 'true' if xOffline else 'false'
            # extras['removeNewVersionNotif'] = 'true' if removeNewVersionNotif else 'false'
            # extras['hideSettingsMenu'] = 'true' if hideSettingsMenu else 'false'
            # extras['compname'] = compname
            # extras['androidappid'] = androidappid
            # extra_input = json.dumps(extras)

            ####from here run the github action, we need user, repo, access token.
            if platform == 'windows':
                url = 'https://api.github.com/repos/'+_settings.GHUSER+'/'+_settings.REPONAME+'/actions/workflows/generator-windows.yml/dispatches'
                if selfhosted:
                    url = 'https://api.github.com/repos/'+_settings.GHUSER+'/'+_settings.REPONAME+'/actions/workflows/sh-generator-windows.yml/dispatches'
            if platform == 'windows-x86':
                url = 'https://api.github.com/repos/'+_settings.GHUSER+'/'+_settings.REPONAME+'/actions/workflows/generator-windows-x86.yml/dispatches'
            elif platform == 'linux':
                url = 'https://api.github.com/repos/'+_settings.GHUSER+'/'+_settings.REPONAME+'/actions/workflows/generator-linux.yml/dispatches'
            elif platform == 'android':
                url = 'https://api.github.com/repos/'+_settings.GHUSER+'/'+_settings.REPONAME+'/actions/workflows/generator-android.yml/dispatches'
            elif platform == 'macos':
                url = 'https://api.github.com/repos/'+_settings.GHUSER+'/'+_settings.REPONAME+'/actions/workflows/generator-macos.yml/dispatches'
            else:
                url = 'https://api.github.com/repos/'+_settings.GHUSER+'/'+_settings.REPONAME+'/actions/workflows/generator-windows.yml/dispatches'
                if selfhosted:
                    url = 'https://api.github.com/repos/'+_settings.GHUSER+'/'+_settings.REPONAME+'/actions/workflows/sh-generator-windows.yml/dispatches'

            #url = 'https://api.github.com/repos/'+_settings.GHUSER+'/rustdesk/actions/workflows/test.yml/dispatches'  
            inputs_raw = {
                "server":server,
                "key":key,
                "apiServer":apiServer,
                "custom":encodedCustom,
                "uuid":myuuid,
                "iconlink_url":iconlink_url,
                "iconlink_uuid":iconlink_uuid,
                "iconlink_file":iconlink_file,
                "logolink_url":logolink_url,
                "logolink_uuid":logolink_uuid,
                "logolink_file":logolink_file,
                "privacylink_url":privacylink_url,
                "privacylink_uuid":privacylink_uuid,
                "privacylink_file":privacylink_file,
                "appname":appname,
                "genurl":_settings.GENURL,
                "urlLink":urlLink,
                "downloadLink":downloadLink,
                "delayFix": 'true' if delayFix else 'false',
                "beijingCustom": 'true' if beijingCustom else 'false',
                "rdgen":'true',
                "direction": direction,
                "hideNetworkSetting": 'true' if hideNetworkSetting else 'false',
                "defaultViewStyle": defaultViewStyle,
                "removeSetupServerTip": 'true' if removeSetupServerTip else 'false',
                "silentInstallOnDoubleClick": 'true' if silentInstallOnDoubleClick else 'false',
                "hidecm": 'true' if hidecm else 'false',
                "hidecmDefaultEnabled": 'true' if hidecmDefaultEnabled else 'false',
                "copyIdPasswordButton": 'true' if copyIdPasswordButton else 'false',
                "manualTemporaryPassword": 'true' if manualTemporaryPassword else 'false',
                "showStartOnBootCheckbox": 'true' if showStartOnBootCheckbox else 'false',
                "incomingCompactMode": 'true' if incomingCompactMode else 'false',
                "incomingContentWidth": str(incomingContentWidth),
                "incomingContentHeight": str(incomingContentHeight),
                "forceDisableFileTransfer": 'true' if forceDisableFileTransfer else 'false',
                "cycleMonitor": 'true' if cycleMonitor else 'false',
                "xOffline": 'true' if xOffline else 'false',
                "removeNewVersionNotif": 'true' if removeNewVersionNotif else 'false',
                "hideSettingsMenu": 'true' if hideSettingsMenu else 'false',
                "removeRecentSessions": 'true' if removeRecentSessions else 'false',
                "compname": compname,
                "androidappid":androidappid,
                "filename":filename,
                "token": callback_token,
                "status_signature": signing.dumps(
                    {"uuid": myuuid},
                    salt=STATUS_UPDATE_SALT,
                ),
            }

            Path("temp_zips").mkdir(parents=True, exist_ok=True)
            zip_filename = f"secrets_{myuuid}_{uuid.uuid4()}.zip"
            zip_path = os.path.join("temp_zips", zip_filename)

            # Write the JSON directly into the encrypted archive. This avoids
            # a plaintext secret file and Windows file-lock races in cleanup.
            with pyzipper.AESZipFile(
                zip_path,
                "w",
                compression=pyzipper.ZIP_LZMA,
                encryption=pyzipper.WZ_AES,
            ) as zf:
                zf.setpassword(_settings.ZIP_PASSWORD.encode())
                zf.writestr("secrets.json", json.dumps(inputs_raw).encode("utf-8"))

            zipJson = {}
            zipJson['url'] = full_url
            zipJson['file'] = zip_filename
            zipJson['signature'] = signing.dumps(
                {'filename': zip_filename},
                salt=ZIP_DOWNLOAD_SALT,
            )

            zip_url = json.dumps(zipJson)

            data = {
                "ref":_settings.GHBRANCH,
                "inputs":{
                    "version":version,
                    "zip_url":zip_url
                },
                "return_run_details": True
            } 
            #print(data)
            headers = {
                'Accept':  'application/vnd.github+json',
                'Content-Type': 'application/json',
                'Authorization': 'Bearer '+_settings.GHBEARER,
                'X-GitHub-Api-Version': '2026-03-10'
            }
            download_access = form.cleaned_data.get("download_access") or "login"
            download_ttl_hours = min(
                max(int(form.cleaned_data.get("download_ttl_hours") or 168), 1),
                168,
            )
            download_token = download_token_for_run(myuuid)
            try:
                new_github_run = create_github_run_with_reservation(
                    request.user,
                    uuid=myuuid,
                    status="Starting generator...please wait",
                    callback_token_hash=_callback_token_hash(callback_token),
                    download_access=download_access,
                    download_ttl_hours=download_ttl_hours,
                    download_token_hash=_callback_token_hash(download_token),
                )
            except GenerationQuotaExceeded:
                # The form has already been normalized and temporary files
                # may exist; do not dispatch a workflow when the entitlement
                # is exhausted or expired.
                form.add_error(None, "当前账号的生成额度已用尽或已过期，无法开始新的生成任务。")
                return render(request, "generator.html", {"form": form})

            # Persist the run before dispatch so any rejected/failed request
            # can release a count reservation atomically.
            try:
                response = requests.post(url, json=data, headers=headers)
                print(response)
                if response.status_code == 204 or response.status_code == 200:
                    github_data = {}
                    if response.content:
                        try:
                            github_data = response.json()
                            print(github_data)
                        except ValueError as e:
                            print(f"GitHub dispatch returned non-JSON success body: {e}")
                    new_github_run.github_run_id = github_data.get('workflow_run_id')
                    new_github_run.status = "in_progress"
                    new_github_run.save(update_fields=["github_run_id", "status"])

                    log_url = github_data.get('html_url') or f"https://github.com/{_settings.GHUSER}/{_settings.REPONAME}/actions"
                    return render(request, 'waiting.html', {
                        'filename': filename,
                        'uuid': myuuid,
                        'status': "Starting generator...please wait",
                        'platform': platform,
                        'log_url': log_url,
                        'download_access': download_access,
                        'download_ttl_hours': download_ttl_hours,
                        'download_token': download_token,
                    })
                else:
                    release_generation_reservation(new_github_run)
                    new_github_run.status = "dispatch_failed"
                    new_github_run.save(update_fields=["status"])
                    return JsonResponse({"error": "GitHub rejected the start request", "details": response.text}, status=500)
            except Exception as e:
                release_generation_reservation(new_github_run)
                new_github_run.status = "dispatch_failed"
                new_github_run.save(update_fields=["status"])
                return JsonResponse({"error": f"Connection error: {str(e)}"}, status=500)
    else:
        form = GenerateForm()
    #return render(request, 'maintenance.html')
    return render(request, 'generator.html', {'form': form})


@login_required
@require_GET
def check_for_file(request):
    filename = request.GET.get('filename')
    run_uuid = request.GET.get('uuid')
    platform = request.GET.get('platform')
    gh_run = _user_run_or_404(request, run_uuid)
    current_status = (gh_run.status or '').lower()
    if gh_run.github_run_id:
        github_log_url = f"https://github.com/{_settings.GHUSER}/{_settings.REPONAME}/actions/runs/{gh_run.github_run_id}"
    else:
        github_log_url = f"https://github.com/{_settings.GHUSER}/{_settings.REPONAME}/actions"

    if gh_run.github_run_id and current_status not in ['success', 'failure', 'cancelled', 'timed_out', 'skipped']:
        headers = {
            "Authorization": f"Bearer {_settings.GHBEARER}",
            "Accept": "application/vnd.github+json"
        }
        api_url = f"https://api.github.com/repos/{_settings.GHUSER}/{_settings.REPONAME}/actions/runs/{gh_run.github_run_id}"
        
        try:
            gh_response = requests.get(api_url, headers=headers)
            if gh_response.status_code == 200:
                gh_data = gh_response.json()
                
                if gh_data['status'] == 'completed':
                    gh_run.status = gh_data['conclusion']
                    gh_run.save()
                    current_status = (gh_run.status or '').lower()
        except Exception as e:
            print(f"Error checking GitHub: {e}")

    if current_status in FAILED_TERMINAL_RUN_STATUSES and not gh_run.artifact_uploaded_at:
        # A failed/cancelled workflow must not hold a reserved count forever.
        release_generation_reservation(gh_run)
        gh_run.refresh_from_db()
    
    if current_status == "success":
        files = list_generated_files(run_uuid)
        return render(request, 'generated.html', {
            'filename': filename, 
            'uuid': run_uuid,
            'platform': platform,
            **_delivery_context(gh_run, files),
        })
        
    elif current_status in ['failure', 'cancelled', 'timed_out', 'skipped', 'action_required']:
        files = list_generated_files(run_uuid)
        return render(request, 'failure.html', {
            'log_url': github_log_url, 
            'filename': filename, 
            'uuid': run_uuid,
            'platform': platform,
            'status': gh_run.status,
            **_delivery_context(gh_run, files),
        })
        
    else:
        return render(request, 'waiting.html', {
            'filename': filename, 
            'uuid': run_uuid,
            'status': gh_run.status, 
            'platform': platform, 
            'log_url': github_log_url,
            'download_access': gh_run.download_access,
            'download_ttl_hours': gh_run.download_ttl_hours,
        })

@require_GET
def download(request):
    filename = _safe_output_filename(request.GET.get('filename'))
    run_uuid = _canonical_run_uuid(request.GET.get('uuid'))
    run = get_object_or_404(GithubRun, uuid=run_uuid)

    # A public link is authorized solely by its per-run token. The token is
    # deterministic so result pages can reconstruct it, while only its hash is
    # persisted for request-time verification.
    supplied_token = (request.GET.get("token") or "").strip()
    if run.download_access == "public" and run.download_token_hash:
        expected_hash = run.download_token_hash
        if not supplied_token or not secrets.compare_digest(
            _callback_token_hash(supplied_token),
            expected_hash,
        ):
            raise Http404("Download link not found")
    elif run.download_access == "public":
        # Legacy public rows cannot be safely shared because they have no
        # persisted token.  Treat them as unavailable rather than falling back
        # to UUID-only access.
        raise Http404("Download link not found")
    else:
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if run.owner_id != request.user.pk and not (
            request.user.is_staff or request.user.is_superuser
        ):
            raise Http404("Download link not found")

    now = timezone.now()
    if run.download_expires_at and now >= run.download_expires_at:
        return HttpResponse("Download link expired", status=410)
    artifact_expires_at = run.artifact_expires_at or (
        run.created_at + timedelta(days=7)
    )
    if now >= artifact_expires_at:
        return HttpResponse("Generated file expired", status=410)

    file_path = _generated_file_or_404(run_uuid, filename)
    with open(file_path, 'rb') as file:
        content = file.read()
    content_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
    response = HttpResponse(content, headers={
        'Content-Type': content_type,
        'Content-Disposition': f'attachment; filename="{filename}"'
    })
    return response

@require_GET
def get_png(request):
    filename = _safe_output_filename(request.GET.get('filename'))
    run_uuid = request.GET.get('uuid')
    run, error = _machine_run(request, run_uuid)
    if error:
        return error
    png_root = (Path("png") / run.uuid).resolve()
    file_path = (png_root / filename).resolve()
    try:
        file_path.relative_to(png_root)
    except ValueError:
        raise Http404("Image not found")
    if not file_path.is_file():
        raise Http404("Image not found")
    with open(file_path, "rb") as file:
        return HttpResponse(file.read(), headers={
            "Content-Type": "image/png",
            "Content-Disposition": f'inline; filename="{filename}"',
        })


@csrf_exempt
@require_POST
def update_github_run(request):
    try:
        data = json.loads(request.body or b"{}")
    except (TypeError, ValueError):
        return HttpResponse("Invalid JSON", status=400)
    myuuid = data.get("uuid")
    mystatus = str(data.get("status") or "").strip().lower()
    allowed_statuses = {
        "in_progress", "queued", "success", "failure", "cancelled",
        "timed_out", "skipped", "action_required",
    }
    if mystatus not in allowed_statuses:
        return HttpResponse("Invalid status", status=400)
    run, error = _status_run(request, myuuid)
    if error:
        return error
    run.status = mystatus
    run.save(update_fields=["status"])
    if mystatus in FAILED_TERMINAL_RUN_STATUSES and not run.artifact_uploaded_at:
        release_generation_reservation(run)
    return HttpResponse("")

def resize_and_encode_icon(imagefile):
    maxWidth = 200
    try:
        with io.BytesIO() as image_buffer:
            for chunk in imagefile.chunks():
                image_buffer.write(chunk)
            image_buffer.seek(0)

            img = Image.open(image_buffer)
            imgcopy = img.copy()
    except (IOError, OSError):
        raise ValueError("Uploaded file is not a valid image format.")

    # Check if resizing is necessary
    if img.size[0] <= maxWidth:
        with io.BytesIO() as image_buffer:
            imgcopy.save(image_buffer, format=imagefile.content_type.split('/')[1])
            image_buffer.seek(0)
            return_image = ContentFile(image_buffer.read(), name=imagefile.name)
        return base64.b64encode(return_image.read())

    # Calculate resized height based on aspect ratio
    wpercent = (maxWidth / float(img.size[0]))
    hsize = int((float(img.size[1]) * float(wpercent)))

    # Resize the image while maintaining aspect ratio using LANCZOS resampling
    imgcopy = imgcopy.resize((maxWidth, hsize), Image.Resampling.LANCZOS)

    with io.BytesIO() as resized_image_buffer:
        imgcopy.save(resized_image_buffer, format=imagefile.content_type.split('/')[1])
        resized_image_buffer.seek(0)

        resized_imagefile = ContentFile(resized_image_buffer.read(), name=imagefile.name)

    # Return the Base64 encoded representation of the resized image
    resized64 = base64.b64encode(resized_imagefile.read())
    #print(resized64)
    return resized64
 
@csrf_exempt
@require_POST
def startgh(request):
    #print(request)
    if not _shared_api_authorized(request):
        return HttpResponse("Unauthorized", status=401)
    try:
        data_ = json.loads(request.body or b"{}")
    except (TypeError, ValueError):
        return HttpResponse("Invalid JSON", status=400)
    ####from here run the github action, we need user, repo, access token.
    url = 'https://api.github.com/repos/'+_settings.GHUSER+'/'+_settings.REPONAME+'/actions/workflows/generator-'+data_.get('platform')+'.yml/dispatches'  
    data = {
        "ref": _settings.GHBRANCH,
        "inputs":{
            "server":data_.get('server'),
            "key":data_.get('key'),
            "apiServer":data_.get('apiServer'),
            "custom":data_.get('custom'),
            "uuid":data_.get('uuid'),
            "iconlink":data_.get('iconlink'),
            "logolink":data_.get('logolink'),
            "appname":data_.get('appname'),
            "extras":data_.get('extras'),
            "filename":data_.get('filename')
        }
    } 
    headers = {
        'Accept':  'application/vnd.github+json',
        'Content-Type': 'application/json',
        'Authorization': 'Bearer '+_settings.GHBEARER,
        'X-GitHub-Api-Version': '2026-03-10'
    }
    response = requests.post(url, json=data, headers=headers)
    print(response)
    return HttpResponse(status=204)

def save_png(file, uuid, domain, name):
    file_save_path = "png/%s/%s" % (uuid, name)
    Path("png/%s" % uuid).mkdir(parents=True, exist_ok=True)

    if isinstance(file, str):  # Check if it's a base64 string
        try:
            header, encoded = file.split(';base64,')
            decoded_img = base64.b64decode(encoded)
            file = ContentFile(decoded_img, name=name) # Create a file-like object
        except ValueError:
            print("Invalid base64 data")
            return None  # Or handle the error as you see fit
        except Exception as e:  # Catch general exceptions during decoding
            print(f"Error decoding base64: {e}")
            return None
        
    with open(file_save_path, "wb+") as f:
        for chunk in file.chunks():
            f.write(chunk)
    # imageJson = {}
    # imageJson['url'] = domain
    # imageJson['uuid'] = uuid
    # imageJson['file'] = name
    #return "%s/%s" % (domain, file_save_path)
    return domain, uuid, name

@csrf_exempt
@require_POST
def save_custom_client(request):
    file = request.FILES.get("file")
    myuuid = request.POST.get("uuid")
    if file is None or not myuuid:
        return HttpResponse("Missing file or UUID", status=400)
    run, error = _machine_run(request, myuuid)
    if error:
        return error
    filename = _safe_output_filename(file.name)
    output_root = (Path("exe") / run.uuid).resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    file_save_path = (output_root / filename).resolve()
    try:
        file_save_path.relative_to(output_root)
    except ValueError:
        raise Http404("Generated file not found")
    with open(file_save_path, "wb+") as f:
        for chunk in file.chunks():
            f.write(chunk)

    is_valid_artifact = bool(
        file_save_path.stat().st_size and _valid_artifact_filename(filename)
    )
    if is_valid_artifact:
        mark_artifact_uploaded(run)
        run.status = "success"
    run.save(update_fields=["status"])
    return HttpResponse("File saved successfully!")

@csrf_exempt
@require_POST
def cleanup_secrets(request):
    # Pass the UUID as a query param or in JSON body
    try:
        data = json.loads(request.body or b"{}")
    except (TypeError, ValueError):
        return HttpResponse("Invalid JSON", status=400)
    my_uuid = data.get('uuid')
    if not my_uuid:
        return HttpResponse("Missing UUID", status=400)
    run, error = _machine_run(request, my_uuid)
    if error:
        return error
    # 1. Find the files in your temp directory matching the UUID
    temp_dir = os.path.join('temp_zips')
    
    # We look for any file starting with 'secrets_' and containing the uuid
    for filename in os.listdir(temp_dir):
        if filename.startswith(f"secrets_{run.uuid}_") and filename.endswith('.zip'):
            file_path = os.path.join(temp_dir, filename)
            try:
                os.remove(file_path)
                print(f"Successfully deleted {file_path}")
            except OSError as e:
                print(f"Error deleting file: {e}")

    return HttpResponse("Cleanup successful", status=200)

@require_GET
def get_zip(request):
    filename = _safe_output_filename(request.GET.get("filename"))
    signature = request.GET.get("signature", "")
    try:
        signed = signing.loads(
            signature,
            salt=ZIP_DOWNLOAD_SALT,
            max_age=ZIP_DOWNLOAD_MAX_AGE,
        )
    except (BadSignature, SignatureExpired):
        return HttpResponse("Invalid or expired download link", status=403)
    if signed.get("filename") != filename:
        return HttpResponse("Invalid download link", status=403)
    if not filename.startswith("secrets_") or not filename.endswith(".zip"):
        return HttpResponse("Invalid download link", status=403)
    temp_root = Path("temp_zips").resolve()
    file_path = (temp_root / filename).resolve()
    try:
        file_path.relative_to(temp_root)
    except ValueError:
        raise Http404("Archive not found")
    if not file_path.is_file():
        raise Http404("Archive not found")
    with open(file_path, "rb") as file:
        return HttpResponse(file.read(), headers={
            "Content-Type": "application/zip",
            "Content-Disposition": f'attachment; filename="{filename}"',
        })
