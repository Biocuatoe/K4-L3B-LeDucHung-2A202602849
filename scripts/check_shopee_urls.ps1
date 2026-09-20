# scripts/check_shopee_urls.ps1
# HEAD-check Shopee URLs. Run once before creating data/urls.csv.
# User-Agent matches the configuration in scripts/fetch_public_pages.py

$urls = @(
    # --- help.shopee.vn (buyer) ---
    'https://help.shopee.vn/portal/4/article/120798-KB-',
    'https://help.shopee.vn/portal/4/article/120799-KB-',
    'https://help.shopee.vn/portal/4/article/120810-KB-',
    'https://help.shopee.vn/portal/4/article/120815-KB-',
    'https://help.shopee.vn/portal/4/article/120820-KB-',
    # --- seller.shopee.vn (seller) ---
    'https://seller.shopee.vn/edu/article/1234',
    'https://seller.shopee.vn/edu/article/1235',
    'https://seller.shopee.vn/edu/article/1236',
    # --- shopee.vn/legal (both) ---
    'https://shopee.vn/legal/terms',
    'https://shopee.vn/legal/privacy',
    'https://shopee.vn/legaldoc/policies'
)

$results = foreach ($u in $urls) {
    try {
        $r = Invoke-WebRequest -Uri $u -Method Head -UseBasicParsing -TimeoutSec 10 -Headers @{'User-Agent'='Day7DataFoundationsCourse/1.0'} -MaximumRedirection 5
        [PSCustomObject]@{
            URL     = $u
            Status  = $r.StatusCode
            FinalURL = $r.BaseResponse.ResponseUri.AbsoluteUri
            Type    = $r.Headers['Content-Type']
            Verdict = switch ($r.StatusCode) {
                200 { 'OK' }
                301 { 'REDIRECT' } 302 { 'REDIRECT' }
                403 { 'BLOCKED' }
                404 { 'DEAD' }
                default { 'CHECK' }
            }
        }
    } catch {
        $code = if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode } else { 0 }
        [PSCustomObject]@{
            URL=$u; Status=$code; FinalURL=''; Type=''
            Verdict = switch ($code) {
                404 { 'DEAD' } 403 { 'BLOCKED' } 0 { 'TIMEOUT' } default { 'CHECK' }
            }
        }
    }
}

$results | Format-Table -AutoSize -Wrap
Write-Host "`nTOM TAT:" -ForegroundColor Cyan
$results | Group-Object Verdict | ForEach-Object { Write-Host ("  {0,-10} : {1}" -f $_.Name, $_.Count) }

# Check robots.txt for each site
Write-Host "`n=== ROBOTS.TXT ===" -ForegroundColor Cyan
$sites = @('help.shopee.vn','seller.shopee.vn','shopee.vn')
foreach ($s in $sites) {
    Write-Host "`n--- https://$s/robots.txt ---" -ForegroundColor Yellow
    try {
        $r = Invoke-WebRequest -Uri "https://$s/robots.txt" -UseBasicParsing -TimeoutSec 10 -Headers @{'User-Agent'='Day7DataFoundationsCourse/1.0'}
        Write-Host $r.Content
    } catch {
        Write-Host "FAIL: $($_.Exception.Message)" -ForegroundColor Red
    }
}
