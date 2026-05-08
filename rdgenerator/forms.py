from django import forms
from PIL import Image

class GenerateForm(forms.Form):
    sh_secret_field = forms.CharField(required=False)
    #Platform
    platform = forms.ChoiceField(choices=[('windows','Windows 64 位'),('windows-x86','Windows 32 位'),('linux','Linux'),('android','Android'),('macos','macOS')], initial='windows')
    version = forms.ChoiceField(
        choices=[('master','nightly'),('1.4.6','1.4.6'),('1.4.5','1.4.5'),('1.4.4','1.4.4'),('1.4.3','1.4.3'),('1.4.2','1.4.2'),('1.4.1','1.4.1'),('1.4.0','1.4.0'),('1.3.9','1.3.9'),('1.3.8','1.3.8'),('1.3.7','1.3.7'),('1.3.6','1.3.6'),('1.3.5','1.3.5'),('1.3.4','1.3.4'),('1.3.3','1.3.3')],
        initial='1.4.6',
        help_text="nightly 是开发版，功能更新但稳定性可能较低"
    )
    delayFix = forms.BooleanField(initial=True, required=False)

    #General
    exename = forms.CharField(label="配置名称", required=True)
    appname = forms.CharField(label="应用名称", required=False)
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
    androidappid = forms.CharField(label="自定义 Android App ID", required=False)

    #Custom Server
    serverIP = forms.CharField(label="服务器地址", required=False)
    apiServer = forms.CharField(label="API 服务", required=False)
    key = forms.CharField(label="密钥", required=False)
    urlLink = forms.CharField(label="站内链接地址", required=False)
    downloadLink = forms.CharField(label="更新下载地址", required=False)
    compname = forms.CharField(label="公司名称",required=False)

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
    enableFileTransfer = forms.BooleanField(initial=True, required=False)
    enableAudio = forms.BooleanField(initial=True, required=False)
    enableTCP = forms.BooleanField(initial=True, required=False)
    enableRemoteRestart = forms.BooleanField(initial=True, required=False)
    enableRecording = forms.BooleanField(initial=True, required=False)
    enableBlockingInput = forms.BooleanField(initial=True, required=False)
    enableRemoteModi = forms.BooleanField(initial=False, required=False)
    hidecm = forms.BooleanField(initial=False, required=False)
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

    def clean_iconfile(self):
        print("checking icon")
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
