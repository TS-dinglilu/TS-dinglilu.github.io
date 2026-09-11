<#
.SYNOPSIS
    从 Windows 凭据管理器导出 Git 的 GitHub 凭据到临时文件，供推送兜底使用。

.DESCRIPTION
    用途：部分环境下 WorkBuddy 的 git 凭据助手（git-credential-helper-selector → GCM）
    在非交互场景会挂起，`git push` 长时间无响应。此时可先运行本脚本导出凭据，
    再用 git 的 store 助手推送：

        git -c credential.helper= -c "credential.helper=store --file=<输出的临时文件>" push origin main
        rm "<输出的临时文件>"

    成功时 stdout 只输出临时文件路径（一行）；失败时输出以 ERROR: 开头的说明。
    凭据内容不会被打印。用完请删除临时文件。

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts\export_git_cred.ps1
#>
param(
    [string]$Target = 'git:https://github.com',
    [string]$CredHost = 'github.com',
    [string]$OutFile = (Join-Path $env:TEMP ('gitcred_' + [Guid]::NewGuid().ToString('N')))
)

# 让输出固定为 UTF-8，避免调用方按其它编码解码失败
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
} catch { }

$src = @'
using System;
using System.Runtime.InteropServices;
public class CredManExport {
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
if (-not [CredManExport]::CredRead($Target, 1, 0, [ref]$ptr)) {
    Write-Output "ERROR: 凭据管理器中没有 '$Target'"
    exit 2
}
$cred = [System.Runtime.InteropServices.Marshal]::PtrToStructure($ptr, [type][CredManExport+CREDENTIAL])
$size = $cred.CredentialBlobSize
$bytes = New-Object byte[] $size
[System.Runtime.InteropServices.Marshal]::Copy($cred.CredentialBlob, $bytes, 0, $size)
[CredManExport]::CredFree($ptr)

$token = ''
foreach ($enc in @([System.Text.Encoding]::UTF8, [System.Text.Encoding]::Unicode)) {
    $t = $enc.GetString($bytes).Trim([char]0, "`r", "`n", ' ')
    if ($t -match '^[A-Za-z0-9_\-]{20,}$') { $token = $t; break }
}
if ($token -eq '') {
    Write-Output "ERROR: 凭据解码失败 (size=$size)"
    exit 3
}

[System.IO.File]::WriteAllText($OutFile, ('https://' + $cred.UserName + ':' + $token + '@' + $CredHost))
Write-Output $OutFile
