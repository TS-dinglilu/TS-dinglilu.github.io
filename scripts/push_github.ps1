<#
.SYNOPSIS
    统计推送兜底：绕过挂起的凭据助手，直接把提交推到 GitHub。

.DESCRIPTION
    背景：部分环境下 WorkBuddy 的 git 凭据助手（git-credential-helper-selector → GCM）
    在非交互场景会挂起，`git push` 长时间无响应（实测 >5 分钟不返回）。
    本脚本从 Windows 凭据管理器读取已保存的 GitHub 凭据 → 写入临时文件 →
    用 git 的 store 助手推送 → 立即删除临时文件。凭据不打印、不长期落盘。

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File D:\研二\github.auto\repo\scripts\push_github.ps1
#>
param(
    [string]$RepoPath = (Split-Path -Parent $PSScriptRoot),
    [string]$Target = 'git:https://github.com',
    [string]$Remote = 'origin',
    [string]$Branch = 'main',
    [string]$LogFile = (Join-Path $env:TEMP 'push_github.log')
)

function Log([string]$msg) {
    $line = (Get-Date -Format 'HH:mm:ss') + ' ' + $msg
    Add-Content -Path $LogFile -Value $line -Encoding utf8
    Write-Output $line
}

Set-Content -Path $LogFile -Value '' -Encoding utf8
Log "repo=$RepoPath"

if (-not (Test-Path (Join-Path $RepoPath '.git'))) {
    Log "ERROR: 不是 git 仓库"
    exit 1
}

function Resolve-Git {
    $c = Get-Command git -ErrorAction SilentlyContinue
    if ($c) { return $c.Source }
    $cands = @()
    $cands += (Get-ChildItem "$env:USERPROFILE\.workbuddy\binaries\PortableGit\versions\*\mingw64\bin\git.exe" -ErrorAction SilentlyContinue |
               Sort-Object FullName -Descending | Select-Object -ExpandProperty FullName)
    $cands += "$env:ProgramFiles\Git\cmd\git.exe"
    $cands += "${env:ProgramFiles(x86)}\Git\cmd\git.exe"
    foreach ($p in $cands) { if ($p -and (Test-Path $p)) { return $p } }
    return $null
}
$gitExe = Resolve-Git
if (-not $gitExe) { Log "ERROR: 找不到 git"; exit 4 }
Log "git=$gitExe"

$src = @'
using System;
using System.Runtime.InteropServices;
public class CredManPush {
    [DllImport("advapi32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
    public static extern bool CredRead(string target, int type, int reservedFlag, out IntPtr credentialPtr);
    [DllImport("advapi32.dll", SetLastError = true)]
    public static extern void CredFree(IntPtr cred);
    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    public struct CREDENTIAL {
        public int Flags; public int Type; public string TargetName; public string Comment;
        public long LastWritten; public int CredentialBlobSize; public IntPtr CredentialBlob;
        public int Persist; public int AttributeCount; public IntPtr Attributes;
        public string TargetAlias; public string UserName;
    }
}
'@
Add-Type -TypeDefinition $src

$ptr = [IntPtr]::Zero
if (-not [CredManPush]::CredRead($Target, 1, 0, [ref]$ptr)) {
    Log "ERROR: 凭据管理器中没有 '$Target'"
    exit 2
}
$cred = [System.Runtime.InteropServices.Marshal]::PtrToStructure($ptr, [type][CredManPush+CREDENTIAL])
$size = $cred.CredentialBlobSize
$bytes = New-Object byte[] $size
[System.Runtime.InteropServices.Marshal]::Copy($cred.CredentialBlob, $bytes, 0, $size)
[CredManPush]::CredFree($ptr)

$token = ''
foreach ($enc in @([System.Text.Encoding]::UTF8, [System.Text.Encoding]::Unicode)) {
    $t = $enc.GetString($bytes).Trim([char]0, "`r", "`n", ' ')
    if ($t -match '^[A-Za-z0-9_\-]{20,}$') { $token = $t; break }
}
if ($token -eq '') { Log "ERROR: 凭据解码失败 (size=$size)"; exit 3 }
Log ("credential ok user=" + $cred.UserName + " tokenlen=" + $token.Length)

$tmp = Join-Path $env:TEMP ('gitcred_' + [Guid]::NewGuid().ToString('N'))
$code = 1
try {
    [System.IO.File]::WriteAllText($tmp, ('https://' + $cred.UserName + ':' + $token + '@github.com'))
    $env:GIT_TERMINAL_PROMPT = '0'
    $out = & $gitExe -C $RepoPath -c credential.helper= -c "credential.helper=store --file=$tmp" push $Remote $Branch 2>&1
    $code = $LASTEXITCODE
    foreach ($l in $out) {
        Log ('git: ' + [regex]::Replace([string]$l, ':[^:@\s]*@', ':***@'))
    }
}
catch {
    Log ('EXCEPTION: ' + $_.Exception.Message)
}
finally {
    if (Test-Path $tmp) { Remove-Item $tmp -Force }
    Log 'temp credential removed'
}

if ($code -eq 0) { Log 'PUSH_OK' } else { Log "PUSH_FAILED exit=$code" }
exit $code
