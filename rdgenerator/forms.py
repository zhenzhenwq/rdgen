import re

from django import forms
from django.core.validators import RegexValidator, URLValidator
from PIL import Image


SAFE_PACKAGE_NAME = RegexValidator(
    regex=r"^[A-Za-z0-9][A-Za-z0-9_-]*$",
    message="仅允许英文字母、数字、下划线和连字符，且首字符必须是字母或数字。",
)
SAFE_NAME_TEXT = RegexValidator(
    regex=r"""^[^\x00-\x1f\x7f"'`;&|$<>:\\/?*]+$""",
    message="名称包含构建脚本不支持的字符。",
)
SAFE_SCRIPT_VALUE = RegexValidator(
    regex=r"""^[^\x00-\x1f\x7f"'`;&|$<>\\]+$""",
    message="内容包含构建脚本不支持的字符。",
)
SAFE_COMPANY_VALUE = RegexValidator(
    regex=r"""^[^\x00-\x1f\x7f"'`;|$<>\\]+$""",
    message="公司名称包含构建脚本不支持的字符。",
)
HTTP_URL = URLValidator(
    schemes=("http", "https"),
    message="请输入以 http:// 或 https:// 开头的完整地址。",
)
ANDROID_APP_ID = RegexValidator(
    regex=r"^[A-Za-z][A-Za-z0-9_]*(\.[A-Za-z][A-Za-z0-9_]*)+$",
    message="Android App ID 必须是类似 com.example.app 的合法包名。",
)

WINDOWS_RESERVED_NAME = re.compile(
    r"^(?:CON|PRN|AUX|NUL|COM[1-9¹²³]|LPT[1-9¹²³])$",
    re.IGNORECASE,
)
MAX_BUILD_NAME_UTF8_BYTES = 200
BEIJING_LINUX_VERSIONS = {"1.4.7", "1.4.8", "1.4.9"}


def validate_portable_name(value):
    if len(value.encode("utf-8")) > MAX_BUILD_NAME_UTF8_BYTES:
        raise forms.ValidationError("名称的 UTF-8 编码长度不能超过 200 字节。")
    if value.startswith("-"):
        raise forms.ValidationError("名称不能以连字符开头。")
    if value.endswith((".", " ")):
        raise forms.ValidationError("名称不能以句点或空格结尾。")
    stem = value.split(".", 1)[0].rstrip(" ")
    if WINDOWS_RESERVED_NAME.fullmatch(stem):
        raise forms.ValidationError("名称不能使用 Windows 保留设备名。")


def parse_manual_settings(value):
    settings = {}
    for line_number, raw_line in enumerate((value or "").splitlines(), start=1):
        if not raw_line.strip():
            continue
        key, separator, setting_value = raw_line.partition("=")
        if not separator or not key.strip():
            raise forms.ValidationError(
                f"第 {line_number} 行必须使用 key=value 格式，且 key 不能为空。"
            )
        settings[key.strip()] = setting_value.strip()
    return settings


def version_at_least(value, minimum):
    if value == 'master':
        return True
    try:
        current = tuple(int(part) for part in value.split('.'))
    except (AttributeError, ValueError):
        return False
    return current >= minimum


class GenerateForm(forms.Form):
    sh_secret_field = forms.CharField(required=False)
    #Platform
    platform = forms.ChoiceField(choices=[('windows','Windows 64 位'),('windows-x86','Windows 32 位'),('linux','Linux'),('android','Android'),('macos','macOS')], initial='windows')
    version = forms.ChoiceField(
        choices=[('master','nightly'),('1.4.9','1.4.9'),('1.4.8','1.4.8'),('1.4.7','1.4.7'),('1.4.6','1.4.6'),('1.4.5','1.4.5'),('1.4.4','1.4.4'),('1.4.3','1.4.3'),('1.4.2','1.4.2'),('1.4.1','1.4.1'),('1.4.0','1.4.0'),('1.3.9','1.3.9'),('1.3.8','1.3.8'),('1.3.7','1.3.7'),('1.3.6','1.3.6'),('1.3.5','1.3.5'),('1.3.4','1.3.4'),('1.3.3','1.3.3')],
        initial='1.4.9',
        help_text="nightly 是开发版，功能更新但稳定性可能较低"
    )
    delayFix = forms.BooleanField(initial=True, required=False)
    beijingCustom = forms.BooleanField(label="北京 Linux 定制", initial=False, required=False)

    #General
    exename = forms.CharField(
        label="配置名称",
        required=True,
        max_length=64,
        validators=[SAFE_PACKAGE_NAME, validate_portable_name],
    )
    appname = forms.CharField(
        label="应用名称",
        required=False,
        max_length=64,
        validators=[SAFE_NAME_TEXT, validate_portable_name],
    )
    direction = forms.ChoiceField(widget=forms.RadioSelect, choices=[
        ('incoming', '仅允许被控'),
        ('outgoing', '仅允许主控'),
        ('both', '双向连接')
    ], initial='both')
    installation = forms.ChoiceField(label="安装能力", choices=[
        ('installationY', '允许安装'),
        ('installationN', '禁用安装')
    ], initial='installationY')
    settings = forms.ChoiceField(label="设置入口", choices=[
        ('settingsY', '允许设置'),
        ('settingsN', '禁用设置')
    ], initial='settingsY')
    hideNetworkSetting = forms.BooleanField(initial=False, required=False)
    defaultViewStyle = forms.ChoiceField(label="默认显示方式", choices=[
        ('adaptive', '适应窗口'),
        ('original', '原始尺寸')
    ], initial='adaptive')
    removeSetupServerTip = forms.BooleanField(initial=True, required=False)
    silentInstallOnDoubleClick = forms.BooleanField(initial=False, required=False)
    copyIdPasswordButton = forms.BooleanField(initial=False, required=False)
    manualTemporaryPassword = forms.BooleanField(initial=False, required=False)
    showStartOnBootCheckbox = forms.BooleanField(initial=False, required=False)
    incomingCompactMode = forms.BooleanField(initial=False, required=False)
    incomingContentWidth = forms.IntegerField(
        label="仅被控内容宽度",
        initial=220,
        required=False,
        min_value=180,
        max_value=640,
        widget=forms.NumberInput(attrs={'min': 180, 'max': 640, 'step': 1})
    )
    incomingContentHeight = forms.IntegerField(
        label="仅被控内容高度",
        initial=300,
        required=False,
        min_value=220,
        max_value=840,
        widget=forms.NumberInput(attrs={'min': 220, 'max': 840, 'step': 1})
    )
    androidappid = forms.CharField(
        label="自定义 Android App ID", required=False, validators=[ANDROID_APP_ID]
    )

    #Custom Server
    serverIP = forms.CharField(label="服务器地址", required=False, validators=[SAFE_SCRIPT_VALUE])
    apiServer = forms.CharField(
        label="API 服务", required=False, validators=[SAFE_SCRIPT_VALUE, HTTP_URL]
    )
    key = forms.CharField(label="密钥", required=False, validators=[SAFE_SCRIPT_VALUE])
    urlLink = forms.CharField(
        label="站内链接地址", required=False, validators=[SAFE_SCRIPT_VALUE, HTTP_URL]
    )
    downloadLink = forms.CharField(
        label="更新下载地址", required=False, validators=[SAFE_SCRIPT_VALUE, HTTP_URL]
    )
    compname = forms.CharField(label="公司名称", required=False, validators=[SAFE_COMPANY_VALUE])

    #Visual
    iconfile = forms.FileField(label="自定义应用图标（PNG）", required=False, widget=forms.FileInput(attrs={'accept': 'image/png'}))
    logofile = forms.FileField(label="自定义应用 Logo（PNG）", required=False, widget=forms.FileInput(attrs={'accept': 'image/png'}))
    privacyfile = forms.FileField(label="自定义隐私屏幕（PNG）", required=False, widget=forms.FileInput(attrs={'accept': 'image/png'}))
    iconbase64 = forms.CharField(required=False)
    logobase64 = forms.CharField(required=False)
    privacybase64 = forms.CharField(required=False)
    theme = forms.ChoiceField(choices=[
        ('light', '浅色'),
        ('dark', '深色'),
        ('system', '跟随系统')
    ], initial='system')
    themeDorO = forms.ChoiceField(choices=[('default', '默认'),('override', '强制覆盖')], initial='default')

    #Security
    passApproveMode = forms.ChoiceField(choices=[('password','通过密码接受连接'),('click','通过点击接受连接'),('password-click','密码和点击均可')],initial='password-click')
    permanentPassword = forms.CharField(widget=forms.PasswordInput(), required=False)
    #runasadmin = forms.ChoiceField(choices=[('false','No'),('true','Yes')], initial='false')
    denyLan = forms.BooleanField(initial=False, required=False)
    enableDirectIP = forms.BooleanField(initial=False, required=False)
    #ipWhitelist = forms.BooleanField(initial=False, required=False)
    autoClose = forms.BooleanField(initial=False, required=False)

    #Permissions
    permissionsDorO = forms.ChoiceField(choices=[('default', '默认'),('override', '强制覆盖')], initial='default')
    permissionsType = forms.ChoiceField(choices=[('custom', '自定义'),('full', '完全访问'),('view','仅屏幕共享')], initial='custom')
    enableKeyboard =  forms.BooleanField(initial=True, required=False)
    enableClipboard = forms.BooleanField(initial=True, required=False)
    enableFileCopyPaste = forms.BooleanField(initial=True, required=False)
    enableFileTransfer = forms.BooleanField(initial=True, required=False)
    forceDisableFileTransfer = forms.BooleanField(initial=False, required=False)
    enableAudio = forms.BooleanField(initial=True, required=False)
    enableTCP = forms.BooleanField(initial=True, required=False)
    enableRemoteRestart = forms.BooleanField(initial=True, required=False)
    enableRecording = forms.BooleanField(initial=True, required=False)
    enableBlockingInput = forms.BooleanField(initial=True, required=False)
    enableRemoteModi = forms.BooleanField(initial=True, required=False)
    hidecm = forms.BooleanField(
        label="启用隐藏连接窗口功能",
        initial=False,
        required=False,
    )
    hidecmDefaultEnabled = forms.BooleanField(
        label="构建后默认开启隐藏连接窗口",
        initial=False,
        required=False,
    )
    enablePrinter = forms.BooleanField(initial=True, required=False)
    enableCamera = forms.BooleanField(initial=True, required=False)
    enableTerminal = forms.BooleanField(initial=True, required=False)

    #Other
    removeWallpaper = forms.BooleanField(initial=True, required=False)

    defaultManual = forms.CharField(widget=forms.Textarea, required=False)
    overrideManual = forms.CharField(widget=forms.Textarea, required=False)

    #custom added features
    cycleMonitor = forms.BooleanField(initial=False, required=False)
    xOffline = forms.BooleanField(initial=False, required=False)
    removeNewVersionNotif = forms.BooleanField(initial=False, required=False)
    hideSettingsMenu = forms.BooleanField(initial=False, required=False)
    removeRecentSessions = forms.BooleanField(initial=False, required=False)

    def clean_defaultManual(self):
        value = self.cleaned_data.get('defaultManual', '')
        parse_manual_settings(value)
        return value

    def clean_overrideManual(self):
        value = self.cleaned_data.get('overrideManual', '')
        parse_manual_settings(value)
        return value

    def clean(self):
        cleaned = super().clean()
        platform = cleaned.get('platform')
        version = cleaned.get('version')

        if platform == 'linux' and cleaned.get('beijingCustom'):
            if version not in BEIJING_LINUX_VERSIONS:
                self.add_error(
                    'beijingCustom',
                    '北京 Linux 定制仅支持已验证的 RustDesk 1.4.7、1.4.8 和 1.4.9。',
                )
            if len(cleaned.get('exename') or '') < 2:
                self.add_error(
                    'exename',
                    '北京 Linux 定制的包名称至少需要 2 个字符。',
                )
            for field in ('appname', 'compname', 'urlLink'):
                value = cleaned.get(field) or ''
                if '%' in value:
                    self.add_error(
                        field,
                        '北京 Linux 定制的 RPM 包元数据不支持百分号。',
                    )
            if any(character.isspace() for character in (cleaned.get('urlLink') or '')):
                self.add_error(
                    'urlLink',
                    '北京 Linux 定制的 RPM 主页地址不能包含空白字符。',
                )

        version_requirements = {
            'incomingCompactMode': ((1, 4, 2), '仅被控紧凑布局'),
            'hideNetworkSetting': ((1, 4, 4), '隐藏网络设置'),
            'hideSettingsMenu': ((1, 4, 4), '隐藏主界面设置菜单'),
            'forceDisableFileTransfer': ((1, 4, 5), '从源码强制禁用文件传输'),
        }
        for field, (minimum, label) in version_requirements.items():
            if cleaned.get(field) and not version_at_least(version, minimum):
                minimum_text = '.'.join(str(part) for part in minimum)
                self.add_error(
                    field,
                    f'{label}要求 RustDesk {minimum_text} 或更高版本。',
                )

        if cleaned.get('hidecmDefaultEnabled') and not cleaned.get('hidecm'):
            self.add_error(
                'hidecmDefaultEnabled',
                '构建后默认隐藏前，必须先启用隐藏连接窗口功能。',
            )
        if cleaned.get('hidecmDefaultEnabled') and not (
            cleaned.get('permanentPassword') or ''
        ).strip():
            self.add_error(
                'permanentPassword',
                '构建后默认隐藏连接窗口时必须设置固定密码。',
            )
        if (
            cleaned.get('hidecm')
            and not cleaned.get('hidecmDefaultEnabled')
            and cleaned.get('settings') == 'settingsN'
        ):
            self.add_error(
                'settings',
                '隐藏连接窗口由客户端用户设置时，必须保留设置入口。',
            )

        if platform != 'windows' and (
            cleaned.get('privacyfile') or cleaned.get('privacybase64')
        ):
            self.add_error('privacyfile', '自定义隐私屏幕目前仅支持 Windows 64 位。')

        if platform in {'windows-x86', 'android'} and (
            cleaned.get('logofile') or cleaned.get('logobase64')
        ):
            self.add_error('logofile', 'Windows 32 位和 Android 暂不支持自定义 Logo。')

        if platform == 'windows-x86':
            unsupported = {
                'cycleMonitor': '显示器切换按钮',
                'xOffline': '离线 X 标记',
                'copyIdPasswordButton': 'ID/密码复制按钮',
                'manualTemporaryPassword': '手动临时密码',
                'showStartOnBootCheckbox': '开机自启选项',
                'incomingCompactMode': '仅被控紧凑布局',
            }
            for field, label in unsupported.items():
                if cleaned.get(field):
                    self.add_error(field, f'Windows 32 位不支持{label}。')

        if platform == 'android' and cleaned.get('hideSettingsMenu'):
            self.add_error('hideSettingsMenu', 'Android 不支持隐藏主界面设置菜单。')

        return cleaned

    def clean_iconfile(self):
        image = self.cleaned_data['iconfile']
        if image:
            try:
                # Open the image using Pillow
                img = Image.open(image)

                # Check if the image is a PNG (optional, but good practice)
                if img.format != 'PNG':
                    raise forms.ValidationError("仅允许上传 PNG 图片。")

                # Get image dimensions
                width, height = img.size

                # Check for square dimensions
                if width != height:
                    raise forms.ValidationError("自定义应用图标必须是正方形。")
                
                return image
            except OSError:  # Handle cases where the uploaded file is not a valid image
                raise forms.ValidationError("图标文件无效。")
            except Exception as e: # Catch any other image processing errors
                raise forms.ValidationError(f"处理图标时出错：{e}")
